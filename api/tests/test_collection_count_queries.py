"""Read-only count projection parity over source scope and mixed readiness."""
from contextlib import asynccontextmanager
from pathlib import Path
from types import ModuleType
from uuid import uuid4
import hashlib
import ast
import pytest
from psycopg.types.json import Jsonb
from fastapi import HTTPException
from app.db import cursor
from app.routers import collections as current
from app.services import learning_taxonomy
from test_admin_workbench import workbench

BASELINE=Path(__file__).resolve().parents[2]/'reports/finna-collection-counts-staged-20261119/collections.before.py'


def test_reader_optimization_leaves_other_routes_and_cache_policy_identical():
    # Collections router still exposes the same public endpoints and cache wrapper
    # after FINNAPLAN v2 P1/P4 moved membership SQL into services/selector.py.
    source = Path(current.__file__).read_text()
    tree = ast.parse(source)
    funcs = {n.name for n in tree.body if isinstance(n, ast.AsyncFunctionDef)}
    assert {'list_collections', 'get_collection', 'collection_header', 'collection_study_topics', 'list_paper_questions'} <= funcs
    assert 'public_catalog' in source

@pytest.fixture(params=['current','narrow','shared','ids'])
def readers(client,monkeypatch,request):
    monkeypatch.setattr(learning_taxonomy, 'CLERICAL_EXAMS', ('udc', 'ldc', 'assistant'), raising=False)
    source=BASELINE.read_text()
    assert hashlib.sha256(source.encode()).hexdigest()=='fb3803cb6ebbe7f50c9bbef809c535c6e7cf53b41c58ebd78397379e65f1acda'
    old=ModuleType('app.routers._collection_counts_baseline');old.__package__='app.routers'
    exec(compile(source,str(BASELINE),'exec'),old.__dict__)
    @asynccontextmanager
    async def readonly():
        async with cursor() as cur:
            await cur.execute('SET TRANSACTION READ ONLY')
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    monkeypatch.setattr(current,'cursor',readonly);old.cursor=readonly
    candidate=current
    if request.param!='current':
        candidate=ModuleType('app.routers._collection_counts_'+request.param);candidate.__package__='app.routers'
        path=BASELINE.parent/('collections.'+request.param+'.py')
        exec(compile(path.read_text(),str(path),'exec'),candidate.__dict__);candidate.cursor=readonly
    return old,candidate


@pytest.fixture
def collection(database,workbench):
    ids,paper,_=workbench;c=database[1];name='counts-'+uuid4().hex
    c.execute("INSERT INTO collections(id,title,kind,live_version,visibility) VALUES(%s,'Synthetic count regression','exam',2,'public')",(name,))
    c.execute("UPDATE question_classifications SET topic_id='english/count-test',topic_label='Count fixture' WHERE question_id=ANY(%s)",(list(ids.values()),))
    # Extra source variants must not inflate distinct canonical counts. Empty,
    # whitespace and large explanations exercise boolean-only projections.
    c.execute("UPDATE canonical_questions SET explanation=CASE WHEN id=%s THEN '  ' WHEN id=%s THEN repeat('Synthetic explanation ',10000) ELSE NULL END WHERE id=ANY(%s)",(ids['keyed'],ids['unverified'],list(ids.values())))
    c.execute("INSERT INTO appearances(id,paper_id,type,question,options,canonical_id) VALUES(%s,%s,'mcq','Duplicate fixture source','[]',%s)",(uuid4().hex,paper,ids['keyed']))
    for version in (1,2):
        sections=[('papers',{'paper_ids':[paper]},[],[]),('subject',{'subject_id':'english'},[ids['restricted']],[ids['missing']]),('topic',{'topic_id':'english/count-test'},[],[]),('filtered',{'paper_ids':[paper],'subject_id':'mizo'},[ids['keyed']],[ids['unverified']]),('pins',{'paper_ids':[]},[ids['keyed'],ids['held'],ids['restricted']],[ids['restricted']]),('empty',{'paper_ids':[]},[],[])]
        if version==1:sections=sections[:1]
        for position,(path,query,pins,excludes) in enumerate(sections):
            c.execute('INSERT INTO collection_sections(collection_id,version,path,title,position,query,pins,excludes) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(name,version,path,path,position,Jsonb(query),pins,excludes))
        c.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path,allow_practice) VALUES(%s,%s,%s,'papers',false)",(name,version,paper))
    return name,ids,paper


@pytest.mark.parametrize('scope',['mizoram-recruitment','all'])
@pytest.mark.parametrize('change',['baseline','outside-source','practice-enabled','withdrawn','new-live-version','hidden'])
def test_exact_list_section_and_paper_count_payloads_match_baseline(client,database,readers,collection,scope,change):
    name,ids,paper=collection;c=database[1];old,new=readers
    if change=='outside-source':c.execute("UPDATE papers SET exam_scope_id='outside-mizoram' WHERE id=%s",(paper,))
    if change=='practice-enabled':c.execute('UPDATE collection_papers SET allow_practice=true WHERE collection_id=%s',(name,))
    if change=='withdrawn':c.execute("UPDATE canonical_questions SET status='withdrawn',answer_text=NULL,answer_source='none' WHERE id=%s",(ids['keyed'],))
    if change=='new-live-version':c.execute('UPDATE collections SET live_version=1 WHERE id=%s',(name,))
    if change=='hidden':c.execute("UPDATE collections SET visibility='hidden' WHERE id=%s",(name,))
    for reader,args in [('_section_stats',(name,scope)),('_section_stats',(None,scope)),('_list_collections',(scope,))]:
        before=client.portal.call(getattr(old,reader),*args);after=client.portal.call(getattr(new,reader),*args)
        assert before==after,(reader,scope,change)
    if change=='hidden':
        for reader in (old,new):
            with pytest.raises(HTTPException) as exc:client.portal.call(reader._get_collection,name,scope)
            assert exc.value.status_code==404
    else:
        before=client.portal.call(old._get_collection,name,scope);after=client.portal.call(new._get_collection,name,scope)
        assert before.model_dump()==after.model_dump()
        assert not {'answer_text','explanation','options'} & after.model_dump().keys()
        # Held rows contribute to paper readiness, while section membership still
        # uses the existing live-only view. Do not silently unify their policies.
        if change=='baseline':
            assert after.paper_list[0].blocked_count>=2
            assert after.paper_list[0].practice_count==0


def test_empty_collection_and_missing_or_outside_collection_guards(client,database,readers):
    name='empty-counts-'+uuid4().hex;database[1].execute("INSERT INTO collections(id,title,kind,visibility,exam_scope_id) VALUES(%s,'Empty fixture','exam','public','outside-mizoram')",(name,))
    for scope in ('mizoram-recruitment','all'):
        for name_to_read in (name,'not-a-real-count-collection'):
            results=[]
            for reader in readers:
                try:results.append(client.portal.call(reader._get_collection,name_to_read,scope).model_dump())
                except HTTPException as exc:results.append(exc.status_code)
            assert results[0]==results[1]
