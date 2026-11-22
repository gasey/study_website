"""Explicit Atlas provenance, current exam sections and dated-entry references.

No inferred topic links, bank writes, assessment disclosures or awards.
"""
import json,re
from datetime import date,datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from . import atlas_bindings,bank_dates
from .review_policy import safe_url,digest
from ..exam_scope import pool_view,DEFAULT_SCOPE

DISTRICTS=('Aizawl','Champhai','Hnahthial','Khawzawl','Kolasib','Lawngtlai','Lunglei','Mamit','Saitual','Serchhip','Siaha')

def validate_metadata(body,invalid):
    if body.get('district') is not None and body['district'] not in DISTRICTS:invalid('district','Choose a current Mizoram district')
    sources=body.get('sources',[])
    if not isinstance(sources,list) or len(sources)>30:invalid('sources','Use at most 30 named sources')
    ids=set()
    for i,s in enumerate(sources):
        p=f'sources.{i}'
        if not isinstance(s,dict):invalid(p,'Add a named source')
        for key,limit in [('id',100),('title',250),('url',2048),('attribution',1000),('note',3000)]:
            if not isinstance(s.get(key),str) or not s[key].strip() or len(s[key])>limit:invalid(p+'.'+key,'Add source text within the field limit')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}',s['id']) or s['id'] in ids:invalid(p+'.id','Use distinct stable source IDs')
        ids.add(s['id'])
        if s.get('download_path') and (not isinstance(s['download_path'],str) or not re.fullmatch(r'/maps/[a-z0-9-]+\.(geojson|json)',s['download_path'])):invalid(p+'.download_path','Use a bundled attributed map-data download')
        try:
            safe_url(s['url']);checked=date.fromisoformat(s.get('checked_on',''))
            if checked>datetime.now(ZoneInfo('Asia/Kolkata')).date():raise ValueError()
            if s.get('license_url'):safe_url(s['license_url'])
        except (ValueError,TypeError):invalid(p,'Use HTTPS references and a real, non-future checked date')
        if s.get('reuse') not in ('reference','licensed'):invalid(p+'.reuse','Choose reference only or licensed data')
        if s['reuse']=='licensed' and (not s.get('license_url') or not isinstance(s.get('license'),str) or not 1<=len(s['license'])<=200):invalid(p+'.license','Name and link the data license')
    for i,l in enumerate(body.get('layers',[])):
        refs=l.get('source_ids',[])
        if not isinstance(refs,list) or any(not isinstance(x,str) or x not in ids for x in refs):invalid(f'layers.{i}.source_ids','Choose sources listed on this chapter')
    for i,e in enumerate(body.get('events',[])):
        fields=[e.get(k) for k in ('chronicle_entry_id','chronicle_question_id','chronicle_source_sha256')]
        if any(fields):
            if not (isinstance(fields[0],str) and re.fullmatch(r'date_[0-9a-f]{20}',fields[0]) and isinstance(fields[1],str) and 1<=len(fields[1])<=120 and isinstance(fields[2],str) and re.fullmatch(r'[0-9a-f]{64}',fields[2])):invalid(f'events.{i}.chronicle_entry_id','Select a dated Chronicle entry with its current source snapshot')

async def exam_catalog(cur,user):
    from .atlas_studio import catalog
    from .today import saved_exam
    items=await catalog(cur);exam=await saved_exam(cur,user)
    relevant=set()
    if exam:
        # Only explicit current section topic/subject IDs, never chapter-title matching
        # or historic question frequency masquerading as syllabus relevance.
        await cur.execute('''SELECT DISTINCT b.live->>'chapter_id' AS id FROM atlas_topic_bindings b
          JOIN collection_sections s ON s.collection_id=%(exam)s
          JOIN collections c ON c.id=s.collection_id AND c.live_version=s.version
          AND c.kind='exam' AND c.visibility='public'
          WHERE '''+atlas_bindings.LIVE+''' AND s.query->>'subject_id'=b.live->>'subject_id'
          AND (s.query->>'topic_id' IS NULL OR s.query->>'topic_id'=b.live->>'topic_id')''',{'exam':exam['id']})
        relevant={r['id'] for r in await cur.fetchall()}
    return {'items':[x|{'exam_relevant':x['id'] in relevant} for x in items],
            'exam':{'id':exam['id'],'title':exam['title']} if exam else None,
            'basis':'Current published exam sections and live owner-curated topic bindings. All chapters remain available.'}

async def anchors(cur,ids):
    if not ids:return {}
    await cur.execute('''SELECT v.id,v.question,v.options,v.answer_text,v.answer_source,v.status,
      v.source_defect,v.key_disputed,qc.subject_id,qc.subject_label,
      EXISTS(SELECT 1 FROM v_mock_practice r WHERE r.id=v.id) AS answer_usable,
      CASE WHEN EXISTS(SELECT 1 FROM appearances a JOIN papers p ON p.id=a.paper_id
        WHERE a.canonical_id=v.id AND a.is_primary AND p.exam_type='Community')
        THEN 'community' ELSE 'paper' END AS origin
      FROM '''+pool_view('all',DEFAULT_SCOPE)+''' v LEFT JOIN question_classifications qc
      ON qc.question_id=v.id AND qc.review_status='approved' WHERE v.id=ANY(%s)''',(list(ids),))
    result={}
    for row in await cur.fetchall():
        entries=bank_dates.build_index([row])
        if entries and entries[0]['dates']:
            result[row['id']]={'entry':bank_dates.summary(entries[0]),'source_sha256':digest(row)}
    return result

async def check_references(cur,body):
    from fastapi import HTTPException
    linked=[e for e in body.get('events',[]) if e.get('chronicle_entry_id')]
    current=await anchors(cur,{e['chronicle_question_id'] for e in linked})
    for e in linked:
        ref=current.get(e['chronicle_question_id'])
        if not ref or ref['entry']['id']!=e['chronicle_entry_id'] or ref['source_sha256']!=e['chronicle_source_sha256']:
            raise HTTPException(409,'A Chronicle source changed or is unavailable. Select the dated entry again before publishing.')

async def chapter_chronicle(cur,user,cid):
    from .atlas_studio import published
    from ..routers.current_affairs import no_assessment
    await no_assessment(cur,user)
    chapter=await published(cur,cid);events=chapter['body'].get('events',[])
    current=await anchors(cur,{e['chronicle_question_id'] for e in events if e.get('chronicle_entry_id')})
    return {'items':[{'event_id':e['id'],'entry_id':e['chronicle_entry_id'],'title':current[e['chronicle_question_id']]['entry']['title']}
      for e in events if e.get('chronicle_question_id') in current
      and current[e['chronicle_question_id']]['entry']['id']==e.get('chronicle_entry_id')
      and current[e['chronicle_question_id']]['source_sha256']==e.get('chronicle_source_sha256')]}

async def chronicle_chapters(cur,user,eid):
    from ..routers.current_affairs import no_assessment
    await no_assessment(cur,user)
    await cur.execute('''SELECT c.id,v.body FROM atlas_chapters c JOIN atlas_chapter_versions v
      ON v.chapter_id=c.id AND v.revision=c.current_version WHERE c.status='published'
      AND v.body->'events' @> %s::jsonb ORDER BY c.position,c.id LIMIT 500''',(json.dumps([{'chronicle_entry_id':eid}]),))
    rows=await cur.fetchall();events=[(r,e) for r in rows for e in r['body'].get('events',[]) if e.get('chronicle_entry_id')==eid]
    current=await anchors(cur,{e['chronicle_question_id'] for _,e in events})
    return {'items':[{'chapter_id':r['id'],'event_id':e['id'],'layer_id':None,'title':r['body']['title']}
      for r,e in events if e['chronicle_question_id'] in current and current[e['chronicle_question_id']]['entry']['id']==eid
      and current[e['chronicle_question_id']]['source_sha256']==e['chronicle_source_sha256']][:30]}

def district_proposals():
    return json.loads((Path(__file__).resolve().parents[1]/'data/atlas-district-proposals.json').read_text())
