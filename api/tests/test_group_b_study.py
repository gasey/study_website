"""Common learning selection must never promote whole specialist papers."""
from uuid import uuid4
from psycopg.types.json import Jsonb
from app.services.group_b_study import PAPER_ROLES


def seed(conn):
    suffix=uuid4().hex[:9]
    common=next(r['paper_id'] for r in PAPER_ROLES['rules'] if r['role']=='gk-gs')
    technical=next(r['paper_id'] for r in PAPER_ROLES['rules'] if r['role']=='technical')
    other='gb-unmapped-'+suffix
    gazetted='gb-gazetted-'+suffix
    for paper,cid in [(common,'group-b-non-gazetted'),(technical,'group-b-non-gazetted'),(other,'group-b-non-gazetted'),(gazetted,'group-b-gazetted')]:
        conn.execute("INSERT INTO papers(id,exam_type,exam_name,year,exam_scope_id) VALUES (%s,'Direct','Synthetic Group B',2024,'mizoram-recruitment') ON CONFLICT(id) DO UPDATE SET exam_scope_id='mizoram-recruitment'",(paper,))
        conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,as_mock) VALUES (%s,1,%s,false) ON CONFLICT DO NOTHING",(cid,paper))
    cases=[('english',technical,'approved'),('general-studies',common,'approved'),('general-knowledge',other,'approved'),('science',common,'approved'),('science',technical,'approved'),('medicine',technical,'approved'),('medicine',other,'approved'),('english',common,'pending'),('english',gazetted,'approved')]
    ids=[]
    for i,(subject,paper,status) in enumerate(cases):
        qid='cq_gb_'+suffix+str(i);ids.append(qid)
        conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES (%s,'mcq','Synthetic Group B area question',%s,'B','official')",(qid,Jsonb(['A','B','C','D'])))
        conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum) VALUES (%s,%s,'mcq','Synthetic Group B area question',%s,1,'official',%s,true,'1')",('a_'+qid,paper,Jsonb(['A','B','C','D']),qid))
        conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES (%s,%s,%s,'test','manual',%s)",(qid,subject,subject,status))
    # A secondary English/GK claim cannot turn a specialist primary into common content.
    conn.execute("INSERT INTO question_topic_links VALUES (%s,'general-studies','general-studies','General Studies',NULL,NULL,NULL,NULL,'test','manual','approved','Synthetic related link')",(ids[5],))
    # The same canonical question appears in both groups: totals must stay distinct.
    conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,canonical_id,is_primary,qnum) VALUES (%s,%s,'mcq','Repeated synthetic Group B question',%s,%s,false,'2')",('dup_'+ids[1],gazetted,Jsonb(['A','B','C','D']),ids[1]))
    return ids,common,technical,gazetted


def test_group_b_areas_and_counts(client,actor,database):
    actor('author')
    ids,common,technical,gazetted=seed(database[1])
    expected={'common':{0,1,2,3,8},'english':{0,8},'gk-gs':{1,2,3},'technical':{4,5}}
    for area,indexes in expected.items():
        params={'collection_id':'group-b','study_area':area,'q':'Synthetic Group B','limit':100}
        response=client.get('/api/questions',params=params)
        assert response.status_code==200,response.text
        got={q['id'] for q in response.json()['items']} & set(ids)
        assert got=={ids[i] for i in indexes},(area,got)
        topics=client.get('/api/collections/group-b/study-topics',params={'study_area':area})
        assert topics.status_code==200,topics.text
        all_questions=client.get('/api/questions',params={'collection_id':'group-b','study_area':area,'limit':1})
        assert topics.json()['questions']==all_questions.json()['total']
        if area=='gk-gs':
            assert {s['id'] for s in topics.json()['subjects']}=={'gk-gs'}
            narrowed=client.get('/api/questions',params={**params,'subject_id':'gk-gs'})
            assert narrowed.json()['total']==response.json()['total']
    # Related topic links cannot make the area topic map disagree with its filters.
    database[1].execute("INSERT INTO question_topic_links VALUES (%s,'english/secondary','english','English','english/secondary','Secondary',NULL,NULL,'test','manual','approved','Synthetic related topic')",(ids[0],))
    response=client.get('/api/questions',params={'collection_id':'group-b','study_area':'english','topic_id':'english/secondary'})
    assert response.status_code==200,response.text
    assert ids[0] not in {q['id'] for q in response.json()['items']}
    # Explicit paper filter works in the combined area and exposes that source.
    result=client.get('/api/questions',params={'collection_id':'group-b','study_area':'common','paper_id':gazetted,'limit':100})
    assert result.status_code==200,result.text
    assert ids[1] in {q['id'] for q in result.json()['items']}
    assert all(q['source_appearance']['paper_id']==gazetted for q in result.json()['items'])
    # Subset and invalid inputs cannot escape the source group or area contract.
    result=client.get('/api/questions',params={'collection_id':'group-b-non-gazetted','study_area':'english','limit':100})
    assert ids[8] not in {q['id'] for q in result.json()['items']}
    assert client.get('/api/questions',params={'collection_id':'ldc','study_area':'common'}).status_code==422
    assert client.get('/api/questions',params={'study_area':'unknown'}).status_code==422
    assert client.get('/api/questions',params={'collection_id':'group-b'}).status_code==422
    assert client.get('/api/questions',params={'study_area':'common','exam_scope':'all'}).status_code==200


def test_group_b_progress_uses_actual_recruitment(client,actor,database):
    ids,_,_,_=seed(database[1]);actor('author')
    conn=database[1]
    conn.execute("INSERT INTO attempts(user_id,canonical_id,chosen_text,correct,context,collection_id) VALUES ('author',%s,'A',false,'practice','group-b-non-gazetted')",(ids[0],))
    for status,include in [('answered',True),('wrong',True),('unseen',False)]:
        response=client.get('/api/questions',params={'collection_id':'group-b','study_area':'english','study_status':status,'limit':100})
        assert response.status_code==200,response.text
        assert (ids[0] in {q['id'] for q in response.json()['items']})==include
    from app.routers.learning import safe_route
    assert safe_route('/group-b?study_area=gk-gs&collection=group-b-gazetted&view=practice&paper=test&status=unseen')


def test_common_science_respects_printed_section_and_source_appearance(client,actor,database):
    actor('author');conn=database[1]
    role=next(r for r in PAPER_ROLES['rules'] if r.get('qnum_to')==75)
    paper=role['paper_id'];suffix=uuid4().hex[:8]
    conn.execute("INSERT INTO papers(id,exam_type,exam_name,year,exam_scope_id) VALUES (%s,'Direct','Synthetic mixed GK and Arithmetic paper',2021,'mizoram-recruitment') ON CONFLICT(id) DO UPDATE SET exam_scope_id='mizoram-recruitment'",(paper,))
    conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,as_mock) VALUES ('group-b-non-gazetted',1,%s,false) ON CONFLICT DO NOTHING",(paper,))
    ids=[]
    for i,number in enumerate(['75','76','75a','9999999999']):
        qid='cq_gb_bound_'+suffix+str(i);ids.append(qid)
        conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES (%s,'mcq','Synthetic science boundary question',%s,'B','official')",(qid,Jsonb(['A','B','C','D'])))
        conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,canonical_id,is_primary,qnum) VALUES (%s,%s,'mcq','Synthetic science boundary question',%s,%s,true,%s)",('a_'+qid,paper,Jsonb(['A','B','C','D']),qid,number))
        conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES (%s,'science','Science','test','manual','approved')",(qid,))
    # Even for an eligible canonical, provenance must use its eligible printed appearance.
    conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,canonical_id,is_primary,qnum,page) VALUES (%s,%s,'mcq','Synthetic alternative arithmetic appearance',%s,%s,false,'97',1)",('wrong_source_'+ids[0],paper,Jsonb(['A','B','C','D']),ids[0]))
    for area in ['common','gk-gs']:
        response=client.get('/api/questions',params={'collection_id':'group-b','study_area':area,'q':'Synthetic science boundary','limit':100})
        assert response.status_code==200,response.text
        items={q['id']:q for q in response.json()['items']}
        assert set(items)&set(ids)=={ids[0]}
        assert items[ids[0]]['source_appearance']['qnum']=='75'
    # Archive browsing still contains arithmetic and malformed-number questions.
    response=client.get('/api/questions',params={'paper_id':paper,'q':'Synthetic science boundary','limit':100})
    assert response.status_code==200,response.text
    assert set(ids)<={q['id'] for q in response.json()['items']}


def test_source_heading_is_independent_of_learning_taxonomy(client,actor,database):
    from app.services.group_b_study import source_paper_label
    prefix='Old_Questions/Direct_NG_2024-2027/'
    assert 'General Knowledge' in source_paper_label(prefix+'Assistant, UDC Paper-I Series A..pdf')
    assert source_paper_label(prefix+'General Studies Paper-II 2026..pdf')=='Paper II · General Studies'
    assert source_paper_label('Unreviewed UDC General Studies.pdf') is None
    actor('author')
    ids,common,_,_=seed(database[1])
    response=client.get('/api/questions',params={'collection_id':'group-b','study_area':'gk-gs','q':'Synthetic Group B','limit':100})
    question=next(q for q in response.json()['items'] if q['id']==ids[3])
    assert question['source_appearance']['paper_label']==source_paper_label(common)
    detail=client.get('/api/questions/'+ids[3])
    assert detail.status_code==200,detail.text
    assert detail.json()['appearances'][0]['paper_label']==source_paper_label(common)


def test_explicit_general_paper_subjects_keep_aptitude_accessible_without_specialist_leakage(client,actor,database,monkeypatch):
    actor('author')
    _,_,technical,gazetted=seed(database[1]);conn=database[1]
    monkeypatch.setitem(PAPER_ROLES,'rules',PAPER_ROLES['rules']+[{
        'collection_id':'group-b-gazetted','paper_id':gazetted,'role':'gk-gs',
        'common_subjects':['mathematics','reasoning-and-aptitude','computer-science']}])
    expected=set();all_ids=set()
    for paper in (gazetted,technical):
        for subject in ('mathematics','reasoning-and-aptitude','computer-science','medicine'):
            qid='general_subject_'+uuid4().hex;all_ids.add(qid)
            if paper==gazetted and subject!='medicine':expected.add(qid)
            conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_source,answer_text) VALUES (%s,'mcq','Explicit general-paper subject',%s,'official','B')",(qid,Jsonb(['A','B','C','D'])))
            conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,canonical_id,is_primary,qnum) VALUES (%s,%s,'mcq','Explicit general-paper subject',%s,%s,true,'1')",('a_'+qid,paper,Jsonb(['A','B','C','D']),qid))
            conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES (%s,%s,%s,'test','manual','approved')",(qid,subject,subject))
    for area in ('gk-gs','common'):
        response=client.get('/api/questions',params={'collection_id':'group-b','study_area':area,'q':'Explicit general-paper subject','limit':100})
        assert response.status_code==200,response.text
        assert {q['id'] for q in response.json()['items']} & all_ids==expected
