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

REPORT=Path(__file__).resolve().parents[2]/'reports/finna-subject-count-order-staged-20261119'

@pytest.fixture(params=['subject','wide-forced','wide-batch-forced'])
def readers(client,request):
    @asynccontextmanager
    async def readonly():
        async with cursor() as cur:
            await cur.execute('SET TRANSACTION READ ONLY')
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    modules=[]
    for name in ('before','subject'):
        path=REPORT/('collections.'+name+'.py');source=path.read_text()
        if name=='subject' and request.param!='subject':source=source.replace('collection_id == "subject-wise-practice"','True')
        if name=='subject' and request.param=='wide-batch-forced':source=source.replace('>=50000','>=0')
        if name=='before':assert hashlib.sha256(source.encode()).hexdigest()=='2c2085447e727dc808728a3fb2d703380871c52d7fa2c0fe32bda9c5e98e4193'
        module=ModuleType('app.routers._bulk_'+name);module.__package__='app.routers'
        exec(compile(source,str(path),'exec'),module.__dict__);module.cursor=readonly;module._forced_order=request.param!='subject';modules.append(module)
    return modules

@pytest.mark.parametrize('scope',['mizoram-recruitment','all'])
@pytest.mark.parametrize('change',['baseline','outside-source','practice-enabled','withdrawn','new-live-version','hidden'])
def test_bulk_count_payload_parity(client,database,readers,collection,scope,change):
    parity(client,database,readers,collection,scope,change)

@pytest.mark.parametrize('name',['subject'])
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


def test_only_one_conditional_local_setting_changes_the_deployed_reader_ast():
    class RemoveOrderSetting(ast.NodeTransformer):
        count=0
        prepare_count=0
        def visit_Call(self,node):
            if node.args and isinstance(node.args[0],ast.BinOp) and isinstance(node.args[0].left,ast.Name) and node.args[0].left.id=='matched_query':
                assert len(node.keywords)==1 and node.keywords[0].arg=='prepare' and node.keywords[0].value.value is False
                node.keywords=[];self.prepare_count+=1
            return self.generic_visit(node)
        def visit_If(self,node):
            expected=ast.parse('collection_id == "subject-wise-practice"',mode='eval').body
            if ast.dump(node.test)==ast.dump(expected):
                assert len(node.body)==1 and not node.orelse
                statement=node.body[0].value
                assert isinstance(statement,ast.Await) and statement.value.func.attr=='execute'
                assert statement.value.args[0].value=='SET LOCAL join_collapse_limit=1'
                self.count+=1
                return None
            return self.generic_visit(node)
    old=ast.parse((REPORT/'collections.before.py').read_text())
    change=RemoveOrderSetting();new=change.visit(ast.parse((REPORT/'collections.subject.py').read_text()))
    assert change.count==1 and change.prepare_count==1 and ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False)


def test_setting_only_affects_detail_transaction_and_resets_on_same_connection(client,database,readers,collection,monkeypatch):
    import psycopg
    from psycopg.rows import dict_row
    name,_,_=collection;candidate=readers[1]
    async def run():
        connection=await psycopg.AsyncConnection.connect('dbname='+database[0],autocommit=True,prepare_threshold=0,row_factory=dict_row,options='-c role=mpsc -c jit=off')
        seen=[]
        try:
            @asynccontextmanager
            async def local_cursor():
                async with connection.transaction(),connection.cursor() as cur:
                    await cur.execute('SET TRANSACTION READ ONLY')
                    await cur.execute('SHOW join_collapse_limit');assert (await cur.fetchone())['join_collapse_limit']=='8'
                    yield cur
                    await cur.execute('SHOW join_collapse_limit');seen.append((await cur.fetchone())['join_collapse_limit'])
            monkeypatch.setattr(candidate,'cursor',local_cursor)
            await candidate._get_collection(name,'mizoram-recruitment')
            assert seen==['8','1' if candidate._forced_order else '8']
            prepared=await (await connection.execute('SELECT statement FROM pg_prepared_statements')).fetchall()
            assert not any('GROUP BY GROUPING SETS ((mx.path),())' in p['statement'] for p in prepared)
            assert any(p['statement'].startswith('WITH paper_questions AS MATERIALIZED') for p in prepared)
            row=await (await connection.execute('SHOW join_collapse_limit')).fetchone()
            assert row['join_collapse_limit']=='8'
        finally:await connection.close()
    client.portal.call(run)
