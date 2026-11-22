"""Flattened taxonomy membership preserves collection/source/version boundaries."""
from contextlib import asynccontextmanager
from pathlib import Path
from types import ModuleType
import ast,hashlib
import pytest
from app.db import cursor
from test_collection_count_queries import collection,workbench
from test_collection_count_queries import test_exact_list_section_and_paper_count_payloads_match_baseline as parity

REPORT=Path(__file__).resolve().parents[2]/'reports/finna-section-count-flat-20261119'

@pytest.fixture
def readers(client):
    @asynccontextmanager
    async def readonly():
        async with cursor() as cur:
            await cur.execute('SET TRANSACTION READ ONLY')
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    modules=[]
    for name in ('before','flat'):
        path=REPORT/('collections.'+name+'.py');source=path.read_text()
        if name=='before':assert hashlib.sha256(source.encode()).hexdigest()=='7c7ed11b7f5b76d0c741db3c0a9b5d51b5f33c21c22a4ad53ade8bf11d8f5356'
        module=ModuleType('app.routers._section_flat_'+name);module.__package__='app.routers'
        exec(compile(source,str(path),'exec'),module.__dict__);module.cursor=readonly;modules.append(module)
    return modules

@pytest.mark.parametrize('scope',['mizoram-recruitment','all'])
@pytest.mark.parametrize('change',['baseline','outside-source','practice-enabled','withdrawn','new-live-version','hidden'])
def test_collection_payload_parity(client,database,readers,collection,scope,change):
    parity(client,database,readers,collection,scope,change)

def test_only_the_membership_query_changes():
    def protected(path):
        return [ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body
                if not(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_MATCHED_QUERY' for t in n.targets))]
    assert protected(REPORT/'collections.before.py')==protected(REPORT/'collections.flat.py')

@pytest.mark.parametrize('scope',['mizoram-recruitment','all'])
@pytest.mark.parametrize('query',[
    {'subject_id':None,'topic_id':'english/count-test'},
    {'subject_id':'english','topic_id':None},
    {'subject_id':None,'topic_id':None},
    {'topic_id':'english/count-test'},
    {'subject_id':'english'},
    {'paper_ids':[],'subject_id':'english'},
    {},
])
def test_null_paths_duplicate_secondary_paths_and_orphan_source_boundaries(client,database,readers,collection,scope,query):
    from psycopg.types.json import Jsonb
    from uuid import uuid4
    name,ids,paper=collection;c=database[1]
    c.execute('DELETE FROM appearances WHERE canonical_id=%s',(ids['missing'],))
    for status,subject,topic in [('approved','english','english/count-test'),('pending','english','english/pending'),('rejected','english','english/rejected')]:
        c.execute("INSERT INTO question_topic_links(question_id,path_id,subject_id,subject_label,topic_id,topic_label,taxonomy_version,source,review_status,evidence) VALUES(%s,%s,%s,'Synthetic subject',%s,'Synthetic topic','test','manual',%s,'Synthetic evidence')",(ids['keyed'],topic,subject,topic,status))
    path='nulls-'+uuid4().hex
    c.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query,pins,excludes) VALUES(%s,2,%s,'Synthetic null/duplicate paths',99,%s,%s,%s)",(name,path,Jsonb(query),[ids['restricted']],[ids['unverified']]))
    old,new=readers
    for method,args in [('_section_stats',(name,scope)),('_section_stats',(None,scope)),('_list_collections',(scope,))]:
        assert client.portal.call(getattr(old,method),*args)==client.portal.call(getattr(new,method),*args)
    assert client.portal.call(old._get_collection,name,scope).model_dump()==client.portal.call(new._get_collection,name,scope).model_dump()
