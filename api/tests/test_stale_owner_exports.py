"""Exercise the real remote retirement function against isolated async stubs."""
import asyncio
import copy
import importlib.util
import io
import json
import re
from pathlib import Path
from types import SimpleNamespace
import pytest
from app.services.review_policy import digest

SPEC=importlib.util.spec_from_file_location('stale_exports',Path(__file__).resolve().parents[2]/'scripts/retire-stale-owner-exports.py')
RETIRE=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(RETIRE)


def exercise(change=None):
    baseline={'record':{'id':'appearance','question':'Synthetic unchanged source'}}
    manifest={'author_id':'owner','bank_sha256':'a'*64,'admin_decision':{'actor_id':'owner'},'baseline_hash':digest(baseline)}
    pub={'id':'pub_test','manifest':manifest,'manifest_hash':digest(manifest),'contribution_id':'con_test','revision':1}
    data={'publication_ids':['pub_test'],'owner_email':'owner@example.test','authorization':'Owner authorized this isolated recovery fixture.',
          'reason':'A single item advanced the bank before batch publication.','bank_sha256':'b'*64}
    state={'baseline':baseline,'pub':pub,'bank':'b'*64,'waiting':['pub_test'],'delegated':True,'updates':[],'transitions':[]}
    if change:change(state,data)
    untouched=copy.deepcopy(pub['manifest'])
    class Cursor:
        async def __aenter__(self):return self
        async def __aexit__(self,*args):return False
        async def execute(self,query,params=None):
            self.query=query
            if query.startswith('UPDATE'):state['updates'].append(query)
        async def fetchall(self):
            if self.query.startswith('SELECT u.id'):return [{'id':'owner'}]
            if self.query.startswith('SELECT id FROM bank_publications'):return [{'id':i}for i in state['waiting']]
            return [pub]
        async def fetchone(self):
            if self.query.startswith('SELECT bank_checksum'):return {'bank_checksum':state['bank']}
            return {'exists':True}if state['delegated']else None
    async def nothing(*args,**kwargs):pass
    async def load(*args,**kwargs):return {'id':'con_test','state':'publishing','author_id':'owner','kind':'answer','revision':1,'canonical_id':'canonical','appearance_id':'appearance'}
    async def snapshot(*args):return state['baseline']
    async def update(cur,c,actor,status,detail):state['transitions'].append(status);return {**c,'state':status}
    env={'json':json,'re':re,'sys':SimpleNamespace(stdin=io.StringIO(json.dumps(data))),'open_pool':nothing,'close_pool':nothing,
         'cursor':Cursor,'digest':digest,'OPERATOR':'operator:owner-source-maintenance',
         'review':SimpleNamespace(load=load,snapshot=snapshot,update_state=update,event=nothing)}
    source=RETIRE.REMOTE[RETIRE.REMOTE.index('async def run():'):].removesuffix('asyncio.run(run())\n')
    exec(source,env)
    try:asyncio.run(env['run']())
    except ValueError:
        assert state['updates']==[] and state['transitions']==[]
        assert pub['manifest']==untouched
        raise
    assert pub['manifest']==untouched
    return state


def test_stale_export_with_unchanged_source_is_withdrawn_without_content_mutation():
    state=exercise();assert state['transitions']==['publication_failed','changes_requested','withdrawn']
    assert all('canonical_questions'not in q and 'manifest='not in q for q in state['updates'])


@pytest.mark.parametrize('change',[
    lambda s,d:s.update(bank='c'*64),
    lambda s,d:s.update(waiting=[]),
    lambda s,d:s.update(baseline={'record':{'question':'Changed source'}}),
    lambda s,d:s.update(delegated=False),
    lambda s,d:s['pub'].update(manifest_hash='c'*64),
])
def test_changed_bank_source_manifest_or_delegation_rejects_before_any_write(change):
    with pytest.raises(ValueError):exercise(change)
