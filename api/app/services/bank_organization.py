"""Versioned source/scheme configuration, independent of printed question content."""
from datetime import date
from typing import Literal
from urllib.parse import urlsplit
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .review_identity import require_role
from .review_policy import digest
from ..source_files import source_pdf_url


class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)


def web_url(value):
    if value and (urlsplit(value).scheme not in ('https','http') or not urlsplit(value).netloc):
        raise ValueError('Use a complete http or https source URL')
    return value


class SchemeSection(Strict):
    key:str=Field(pattern=r'^[a-z0-9][a-z0-9-]{0,79}$')
    title:str=Field(min_length=2,max_length=200)
    format:Literal['mcq','written','mixed']='mcq'
    allocation:Literal['exact','indicative']='exact'
    marks:float|None=Field(default=None,gt=0,le=10000,allow_inf_nan=False)
    questions:int|None=Field(default=None,ge=1,le=2000)
    choose:int|None=Field(default=None,ge=1,le=2000)
    instructions:str=Field(default='',max_length=4000)
    paths:list[str]=Field(default_factory=list,max_length=30)

    @model_validator(mode='after')
    def choice(self):
        if self.choose and (not self.questions or self.choose>self.questions):
            raise ValueError('A choice count requires a larger or equal printed question count')
        return self


class SchemePaper(Strict):
    key:str=Field(pattern=r'^[a-z0-9][a-z0-9-]{0,79}$')
    title:str=Field(min_length=2,max_length=300)
    format:Literal['mcq','written','mixed']='mcq'
    duration_minutes:int|None=Field(default=None,ge=1,le=1440)
    marks:float|None=Field(default=None,gt=0,le=10000,allow_inf_nan=False)
    questions:int|None=Field(default=None,ge=1,le=2000)
    negative_fraction:float|None=Field(default=None,ge=0,le=1,allow_inf_nan=False)
    qualifying_percent:float|None=Field(default=None,ge=0,le=100,allow_inf_nan=False)
    counts_for_merit:bool|None=None
    instructions:str=Field(default='',max_length=6000)
    sections:list[SchemeSection]=Field(default_factory=list,max_length=40)

    @model_validator(mode='after')
    def sections_unique(self):
        if len({s.key for s in self.sections})!=len(self.sections):raise ValueError('Section keys must be unique')
        return self


class Scheme(Strict):
    title:str=Field(min_length=3,max_length=300)
    exam_key:str=Field(min_length=2,max_length=100)
    edition:str=Field(min_length=2,max_length=100)
    period:Literal['legacy','current','unknown']='unknown'
    effective_from:date|None=None
    effective_to:date|None=None
    state:Literal['draft','verified','archived']='draft'
    source_url:str=Field(default='',max_length=2000)
    source_sha256:str|None=Field(default=None,pattern=r'^[a-f0-9]{64}$')
    evidence_page:int|None=Field(default=None,ge=1,le=10000)
    source_checked:bool=False
    notes:str=Field(default='',max_length=6000)
    papers:list[SchemePaper]=Field(min_length=1,max_length=30)

    _url=field_validator('source_url')(web_url)

    @model_validator(mode='after')
    def coherent(self):
        if self.effective_from and self.effective_to and self.effective_to<self.effective_from:raise ValueError('The scheme end precedes its start')
        if len({p.key for p in self.papers})!=len(self.papers):raise ValueError('Paper keys must be unique')
        if self.state=='verified' and not(self.source_url and self.source_sha256 and self.evidence_page and self.source_checked):
            raise ValueError('A verified scheme requires an inspected source, checksum and evidence page')
        return self


class PaperProfile(Strict):
    provider_id:str=Field(min_length=2,max_length=100)
    corpus:str=Field(default='',max_length=200)
    period:Literal['legacy','current','unknown']='unknown'
    scheme_id:str|None=Field(default=None,max_length=100)
    scheme_revision:int|None=Field(default=None,ge=1)
    scheme_paper_key:str|None=Field(default=None,max_length=80)
    expected_questions:int|None=Field(default=None,ge=1,le=2000)
    appearance_order:list[str]=Field(default_factory=list,max_length=2000)
    # Explicit occurrence IDs also support restarted numbering and written choice groups.
    section_appearances:dict[str,list[str]]=Field(default_factory=dict,max_length=40)
    instructions:str=Field(default='',max_length=6000)
    source_checked:bool=False

    @model_validator(mode='after')
    def bound(self):
        refs=[self.scheme_id,self.scheme_revision,self.scheme_paper_key]
        if any(v is not None for v in refs) and not all(v is not None for v in refs):raise ValueError('Select an exact scheme revision and paper')
        if len(set(self.appearance_order))!=len(self.appearance_order):raise ValueError('Printed order must contain each appearance once')
        assigned=[a for ids in self.section_appearances.values() for a in ids]
        if len(assigned)>2000 or len(set(assigned))!=len(assigned):raise ValueError('Assign each printed appearance to one section only')
        return self


class LearningContext(Strict):
    region:Literal['','mizoram','india','international','other']=''
    region_detail:str=Field(default='',max_length=160)
    language:Literal['','en','lus','hi','other']=''
    time_behavior:Literal['unknown','static','dated-event','changes-over-time']='unknown'
    reference_period:str=Field(default='',max_length=160)
    reference_basis:Literal['unknown','printed','exam-date','reviewed-source']='unknown'
    source_url:str=Field(default='',max_length=2000)
    checked_on:date|None=None
    review_due:date|None=None
    broad_subject_intentional:bool=False

    _url=field_validator('source_url')(web_url)

    @model_validator(mode='after')
    def dates(self):
        if self.reference_period and self.reference_basis=='unknown':raise ValueError('Record the basis of the reference period')
        if self.review_due and (not self.checked_on or self.review_due<self.checked_on):raise ValueError('Review due must follow the checked date')
        return self


def provider_expression(alias='p',profile='bp'):
    return f"COALESCE({profile}.provider_id,CASE WHEN {alias}.exam_type='Community' THEN 'website' WHEN {alias}.exam_scope_id='mizoram-recruitment' THEN 'mpsc' ELSE 'unknown' END)"


async def access(cur,actor,write=False):
    await require_role(cur,actor.id,roles=('owner','publisher') if write else ('owner','publisher','senior','reviewer'))


async def question_access(cur,actor,qid,write=False):
    await cur.execute("SELECT subject_id FROM question_classifications WHERE question_id=%s AND review_status='approved'",(qid,))
    row=await cur.fetchone()
    await require_role(cur,actor.id,row['subject_id'] if row else None,roles=('owner','publisher') if write else ('owner','publisher','senior','reviewer'))


def signature_sql(a='a',c='c',p='p'):
    return f"md5(concat_ws('|',{a}.xmin::text,{c}.xmin::text,{p}.xmin::text))"


async def source_signature(cur,qid,aid):
    await cur.execute('SELECT '+signature_sql()+''' AS signature FROM appearances a
      JOIN canonical_questions c ON c.id=a.canonical_id JOIN papers p ON p.id=a.paper_id
      WHERE a.id=%s AND c.id=%s''',(aid,qid))
    row=await cur.fetchone()
    if not row:raise HTTPException(404,'Question appearance not found')
    return row['signature']


async def paper_context(cur,pid):
    from ..routers.exam_inventory import context_fingerprint
    await cur.execute('SELECT source_file,pdf_url FROM papers WHERE id=%s',(pid,));ref=await cur.fetchone()
    return digest({'context':await context_fingerprint(cur,pid),'reference':ref})


async def paper_rows(cur,pid):
    await cur.execute('''SELECT a.id,a.canonical_id,a.type,a.qnum,a.qnum_seq,a.page,a.options,a.option_order,
      a.has_diagram,a.figure_image,a.direction,a.passage,q.status,q.source_defect,q.key_disputed,
      EXISTS(SELECT 1 FROM v_scorable s WHERE s.id=a.canonical_id) AS scorable,
      EXISTS(SELECT 1 FROM v_mock_practice s WHERE s.id=a.canonical_id) AS practice
      FROM appearances a JOIN canonical_questions q ON q.id=a.canonical_id WHERE a.paper_id=%s
      ORDER BY a.qnum_seq NULLS LAST,a.qnum,a.id''',(pid,))
    return await cur.fetchall()


async def readiness(cur,pid):
    await cur.execute('SELECT id,source_file,pdf_url FROM papers WHERE id=%s',(pid,));paper=await cur.fetchone()
    if not paper:raise HTTPException(404,'Paper not found')
    await cur.execute('SELECT * FROM bank_paper_profiles WHERE paper_id=%s',(pid,));profile=await cur.fetchone()
    rows=await paper_rows(cur,pid)
    context_current=bool(profile and profile['context_fingerprint']==await paper_context(cur,pid))
    config=profile['payload'] if profile else {}
    spec=None;scheme=None
    if profile and profile['scheme_id']:
        await cur.execute('SELECT payload FROM bank_scheme_revisions WHERE scheme_id=%s AND revision=%s',(profile['scheme_id'],profile['scheme_revision']))
        scheme=(await cur.fetchone())['payload'];spec=next((p for p in scheme['papers'] if p['key']==profile['scheme_paper_key']),None)
    expected=config.get('expected_questions') or (spec or {}).get('questions')
    blockers=[]
    if not source_pdf_url(paper['source_file'],paper['pdf_url']):blockers.append('Original PDF is not linked')
    if not rows:blockers.append('Questions have not been extracted')
    if expected is None:blockers.append('Printed question count is unconfirmed')
    elif expected!=len(rows):blockers.append(f'Printed count {expected}; stored appearances {len(rows)}')
    if not context_current:blockers.append('Source layout has not been checked for the current text and options')
    if not config.get('source_checked'):blockers.append('Printed layout is not confirmed')
    if not spec or not scheme or scheme['state']!='verified':blockers.append('No verified scheme revision is linked')
    elif spec['format']!='mcq':blockers.append('This paper includes written work; use original-paper study')
    if spec and (not spec.get('duration_minutes') or spec.get('marks') is None or spec.get('negative_fraction') is None):blockers.append('Timing or marking rules are incomplete')
    if any(r['type']!='mcq' for r in rows):blockers.append('Written questions require manual marking')
    if any(not r['qnum'] or not r['page'] for r in rows):blockers.append('Some printed numbers or page locators are missing')
    if any(r['has_diagram'] and not r['figure_image'] for r in rows):blockers.append('Some source figures are missing')
    if len({r['canonical_id'] for r in rows})!=len(rows):blockers.append('Repeated identities need occurrence-based scoring; browse every printed position')
    eligible=sum(r['scorable'] for r in rows)
    if eligible!=len(rows):blockers.append('Some printed questions are not eligible for official-key scoring')
    # The final snapshot capture still validates option mapping and source defects.
    if any(r['type']=='mcq' and (not r['option_order'] or len(r['option_order'])!=len(r['options'] or [])) for r in rows):blockers.append('Some printed options have no complete canonical mapping')
    sections=(spec or {}).get('sections',[]);mapped=config.get('section_appearances',{})
    if sections:
        assigned=[a for ids in mapped.values() for a in ids]
        if set(assigned)!={r['id'] for r in rows} or any(s.get('allocation','exact')=='exact' and s.get('questions') and len(mapped.get(s['key'],[]))!=s['questions'] for s in sections):blockers.append('Printed sections are not fully mapped')
    if spec and sections and spec.get('marks') is not None and rows:
        unit=spec['marks']/len(rows)
        if any(s.get('allocation','exact')=='exact' and s.get('marks') is not None and mapped.get(s['key']) and abs(s['marks']/len(mapped[s['key']])-unit)>0.00001 for s in sections):blockers.append('Section marks require a variable-mark scoring scheme; use original-paper study')
    order=config.get('appearance_order',[])
    if order and set(order)!={r['id'] for r in rows}:blockers.append('Saved printed order no longer matches the source')
    return {'paper_id':pid,'appearances':len(rows),'expected_questions':expected,'official_eligible':eligible,
      'practice_eligible':sum(r['practice'] for r in rows),'written':sum(r['type']!='mcq' for r in rows),
      'original_available':bool(source_pdf_url(paper['source_file'],paper['pdf_url'])),
      'context_current':context_current,'scheme':None if not scheme else {'id':profile['scheme_id'],'revision':profile['scheme_revision'],
       'title':scheme['title'],'edition':scheme['edition'],'state':scheme['state'],'period':scheme['period'],'paper':spec},
      'full_simulation_ready':bool(rows) and not blockers,'blockers':blockers,
      'appearance_order':order if context_current else [],'section_appearances':mapped if context_current else {},
      'instructions':config.get('instructions','') if context_current else ''}


def safe_filters(filters):
    allowed={'tag_issue','tag_q','tag_bank','tag_module','tag_subject','tag_topic','tag_subtopic','tag_path','tag_paper','tag_year',
      'tag_period','tag_region','tag_time','tag_sort','tag_offset','tag_selected','tag_appearance'}
    if any(k not in allowed or not isinstance(v,str) or len(v)>600 or any(ord(c)<32 for c in v) for k,v in filters.items()):raise HTTPException(422,'Choose supported cleanup filters')
    return filters
