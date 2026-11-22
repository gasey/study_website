"""Bulk counts retain the same source-bound answer authority as bounded reads."""
from contextlib import asynccontextmanager
from pathlib import Path
from types import ModuleType
from uuid import uuid4
import ast,hashlib
import pytest
from psycopg.types.json import Jsonb
from app.db import cursor
from test_collection_count_queries import collection,workbench
from test_collection_count_queries import test_exact_list_section_and_paper_count_payloads_match_baseline as parity

REPORT=Path(__file__).resolve().parents[2]/'reports/finna-query-performance-20261120'

@pytest.fixture(params=['inline','inline-bulk-forced','inline-small-forced','branch','branch-bulk-forced','branch-small-forced'])
def readers(client,request):
    @asynccontextmanager
    async def readonly():
        async with cursor() as cur:
            await cur.execute('SET TRANSACTION READ ONLY')
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    modules=[]
    candidate=request.param.split('-')[0]
    for name in ('before',candidate):
        path=REPORT/('collections.'+name+'.py');source=path.read_text()
        if name!='before':
            if 'bulk-forced' in request.param:source=source.replace('>=50000','>=0').replace('<50000','<0')
            if 'small-forced' in request.param:source=source.replace('>=50000','>=999999').replace('<50000','<999999')
        if name=='before':assert hashlib.sha256(source.encode()).hexdigest()=='7c7ed11b7f5b76d0c741db3c0a9b5d51b5f33c21c22a4ad53ade8bf11d8f5356'
        module=ModuleType('app.routers._bulk_'+name);module.__package__='app.routers'
        exec(compile(source,str(path),'exec'),module.__dict__)
        helper=ModuleType('readiness_candidate')
        exec(compile((REPORT/'question_readiness.inline.py').read_text(),'<readiness>','exec'),helper.__dict__)
        module.answer_status_sql=helper.answer_status_sql
        # Synthetic collections intentionally share titles. SQL orders by title,
        # so tie order is unspecified; compare list payloads by collection id.
        original_list=module._list_collections
        async def stable_list(scope, original=original_list):
            return sorted(await original(scope),key=lambda item:item.id)
        module._list_collections=stable_list
        module.cursor=readonly;modules.append(module)
    return modules

@pytest.mark.parametrize('scope',['mizoram-recruitment','all'])
@pytest.mark.parametrize('change',['baseline','outside-source','practice-enabled','withdrawn','new-live-version','hidden'])
def test_bulk_count_payload_parity(client,database,readers,collection,scope,change):
    parity(client,database,readers,collection,scope,change)

@pytest.mark.parametrize('name',['inline','branch'])
def test_only_detail_readiness_and_its_import_change(name):
    def protected(path):
        return [ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body
                if not(isinstance(n,ast.AsyncFunctionDef) and n.name=='_get_collection')
                and not(isinstance(n,ast.ImportFrom) and n.module=='services.question_readiness')]
    assert protected(REPORT/'collections.before.py')==protected(REPORT/('collections.'+name+'.py'))

@pytest.mark.parametrize('mutation',['none','duplicate-receipt','stale-options','stale-direction','reverted','held','disputed'])
def test_fresh_receipts_and_withdrawal_are_not_cached(client,database,readers,collection,mutation):
    name,ids,paper=collection;c=database[1];qid=ids['unverified'];contribution=uuid4().hex;publication=uuid4().hex
    receipt={'after':{'answerSource':'derived','question':'Synthetic repair unverified','options':['A','B','C','D'],'answerIndex':1,'direction':'Choose one option','passage':None,'questionMarkup':'**Synthetic repair**','optionsMarkup':None,'hasDiagram':False,'figureImage':None}}
    c.execute("INSERT INTO bank_contributions(id,author_id,canonical_id,appearance_id,kind,subject_id,title,state,idempotency_key,request_hash) VALUES(%s,'owner',%s,%s,'answer','english','Synthetic reviewed answer','published',%s,'test')",(contribution,qid,'app-'+qid,contribution))
    c.execute("INSERT INTO bank_publications(id,contribution_id,revision,manifest,manifest_hash,exported_by,state,receipt) VALUES(%s,%s,1,%s,'test','owner','applied',%s)",(publication,contribution,Jsonb({'payload':{'patch':{'answerIndex':1}}}),Jsonb(receipt)))
    c.execute('UPDATE collection_papers SET allow_practice=true WHERE collection_id=%s',(name,))
    def compare():
        bodies=[client.portal.call(reader._get_collection,name,'mizoram-recruitment').model_dump() for reader in readers]
        assert bodies[0]==bodies[1]
        return next(p for p in bodies[1]['paper_list'] if p['id']==paper)
    assert compare()['verified_solutions']==1
    if mutation=='duplicate-receipt':
        c.execute("INSERT INTO bank_publications(id,contribution_id,revision,manifest,manifest_hash,exported_by,state,receipt) SELECT %s,contribution_id,2,manifest,manifest_hash,exported_by,state,receipt FROM bank_publications WHERE id=%s",(uuid4().hex,publication))
    elif mutation=='stale-options':c.execute("UPDATE canonical_questions SET options='[\"A\",\"B\",\"D\",\"C\"]' WHERE id=%s",(qid,))
    elif mutation=='stale-direction':c.execute("UPDATE appearances SET direction='Changed source context' WHERE id=%s",('app-'+qid,))
    elif mutation=='reverted':c.execute("UPDATE bank_publications SET state='reverted' WHERE id=%s",(publication,))
    elif mutation=='held':c.execute("UPDATE canonical_questions SET status='held' WHERE id=%s",(qid,))
    elif mutation=='disputed':c.execute('UPDATE canonical_questions SET key_disputed=true WHERE id=%s',(qid,))
    assert compare()['verified_solutions']==(1 if mutation in ('none','duplicate-receipt') else 0)


def test_default_readiness_sql_is_unchanged_and_bulk_matches_authority(client,database,readers,collection):
    from app.services.question_readiness import answer_status_sql as current
    candidate=readers[1].answer_status_sql
    assert current('av')==candidate('av')
    c=database[1]
    c.execute('SET ROLE mpsc')
    try:
        rows=c.execute('SELECT q.id,bs.answer_status AS authority,'+candidate('q')+' AS small,'+candidate('q',bulk=True)+' AS bulk FROM canonical_questions q JOIN v_bank_answer_status bs ON bs.id=q.id').fetchall()
        assert rows and all(r[1]==r[2]==r[3] for r in rows)
    finally:c.execute('RESET ROLE')
