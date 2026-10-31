import importlib.util
from pathlib import Path
from uuid import uuid4
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('restore_context',ROOT/'scripts/restore-module-source-context.py');restore=importlib.util.module_from_spec(spec);spec.loader.exec_module(restore)

def test_context_restore_requires_exact_source_number_text_and_order(tmp_path):
    bankroot=tmp_path/'bank';legacy=tmp_path/'old';bankroot.mkdir();(legacy/'public/papers').mkdir(parents=True)
    (bankroot/'source.pdf').write_bytes(b'synthetic-source');(legacy/'public/papers/module.pdf').write_bytes(b'synthetic-source')
    bank={'papers':[{'id':'p','pdfPath':'source.pdf'}],'questions':[{'id':'q','paperId':'p','qnum':1,'type':'mcq','question':'The Bible is a book _____.','options':['A','B'],'answerIndex':1}]}
    q={'id':'module-Q001','paperId':'mp','subject':'english','type':'mcq','question':'The __*Bible*__ is a book ___.','options':['A','B'],'direction':'Choose **carefully**.'}
    m={'papers':[{'id':'mp','sourceFile':'/papers/module.pdf'}],'questions':[q]}
    out=restore.prepare(bank,[('module.ts',m,'proof')],bankroot,legacy)
    assert len(out['changes'])==1 and out['changes'][0]['after']['questionMarkup']==q['question']
    assert 'answerIndex' not in out['changes'][0]['after']
    q['options']=['B','A'];assert not restore.prepare(bank,[('module.ts',m,'proof')],bankroot,legacy)['changes']
    q['options']=['A','B'];bank['questions'].append(dict(bank['questions'][0],id='duplicate'))
    assert not restore.prepare(bank,[('module.ts',m,'proof')],bankroot,legacy)['changes']
    bank['questions'].pop();(legacy/'public/papers/module.pdf').write_bytes(b'another-source')
    assert not restore.prepare(bank,[('module.ts',m,'proof')],bankroot,legacy)['changes']

def test_source_context_survives_api_and_saved_mock_review(client,actor,database):
    conn=database[1];tag=uuid4().hex;qid='cq_format_'+tag;cid='fmt-'+tag
    markup='The __*Bible*__ is **important**. Fill _____.';direction='Select the word in *italics*.';passage='A **shared** source passage.'
    conn.execute("INSERT INTO canonical_questions(id,type,question,question_markup,direction,passage,options,answer_text,answer_source) VALUES (%s,'mcq','The Bible is important. Fill _____.',%s,%s,%s,%s,'B','official')",(qid,markup,direction,passage,Jsonb(['A','B'])))
    conn.execute("INSERT INTO appearances(id,paper_id,canonical_id,is_primary,type,question,question_markup,direction,passage,options,answer_index,answer_source) SELECT %s,'paper-test',id,true,type,question,question_markup,direction,passage,options,1,'official' FROM canonical_questions WHERE id=%s",('a_'+tag,qid))
    conn.execute("INSERT INTO collections(id,title,kind,live_version) VALUES (%s,'Formatting test','exam',1)",(cid,))
    conn.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query,pins) VALUES (%s,1,'test','Test',0,'{}',ARRAY[%s])",(cid,qid))
    conn.execute("UPDATE users SET plan_code='pro',plan_status='active' WHERE id='owner'")
    h=actor('owner');page=client.get('/api/questions?q='+qid).json()
    detail=client.get('/api/questions/'+qid).json();assert detail['question_markup']==markup and detail['direction']==direction
    r=client.post('/api/mocks',headers=h,json={'collection_id':cid,'count':1});assert r.status_code==200,r.text
    mid=r.json()['id'];assert r.json()['questions'][0]['question_markup']==markup
    r=client.post('/api/mocks/'+mid+'/submit',headers=h,json={'answers':[{'question_id':qid,'chosen_index':1}]});assert r.status_code==200,r.text
    assert r.json()['review'][0]['passage']==passage and r.json()['review'][0]['direction']==direction
    conn.execute("UPDATE canonical_questions SET direction='Changed current context' WHERE id=%s",(qid,))
    saved=client.get('/api/mocks/'+mid).json()['review'][0]
    assert saved['direction']==direction and saved['question_markup']==markup and saved['passage']==passage


def test_derived_label_is_not_a_reviewed_publication(client,actor,database):
    conn=database[1];qid='cq_unreviewed_'+uuid4().hex
    conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES (%s,'mcq','Synthetic provenance check',%s,'B','derived')",(qid,Jsonb(['A','B'])))
    conn.execute("INSERT INTO appearances(id,paper_id,canonical_id,is_primary,type,question,options,answer_index,answer_source) SELECT %s,'paper-test',id,true,type,question,options,1,'derived' FROM canonical_questions WHERE id=%s",('a_'+qid,qid))
    actor('author')
    detail=client.get('/api/questions/'+qid).json()
    assert detail['answer_source']=='derived' and detail['reviewed_derived'] is False and detail['verified'] is False
    assert 'answer_text' not in detail
    items=client.get('/api/questions?q=Synthetic%20provenance%20check').json()['items']
    assert next(q for q in items if q['id']==qid)['reviewed_derived'] is False
