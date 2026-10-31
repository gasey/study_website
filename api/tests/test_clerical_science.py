"""Clerical GK discovery includes science without rewriting source taxonomy."""
from test_admin_workbench import workbench


def test_science_gk_group_counts_links_and_legacy_paths(client, actor, database, workbench):
    ids, paper, _ = workbench
    conn = database[1]
    actor('author')
    cases = [('missing', 'science', 'Science', 'science/biology', 'Biology'),
             ('keyed', 'science', 'Science', 'science/chemistry', 'Chemistry'),
             ('unverified', 'general-studies', 'General Studies', 'general-studies/science-in-the-news', 'Science in the news')]
    for kind, subject, label, topic, topic_label in cases:
        conn.execute("UPDATE question_classifications SET subject_id=%s,subject_label=%s,topic_id=%s,topic_label=%s WHERE question_id=%s", (subject,label,topic,topic_label,ids[kind]))
    # A second approved discovery path must not double-count the same question.
    conn.execute("INSERT INTO question_topic_links(question_id,path_id,subject_id,subject_label,topic_id,topic_label,taxonomy_version,source,review_status,evidence) VALUES (%s,'general-knowledge/science-in-the-news','general-knowledge','General Knowledge','general-knowledge/science-in-the-news','Science in the news','test','manual','approved','Synthetic overlap')", (ids['missing'],))
    # Unapproved physics remains hidden, even when it would fit the new branch.
    conn.execute("UPDATE question_classifications SET subject_id='science',subject_label='Science',topic_id='science/physics',topic_label='Physics',review_status='pending' WHERE question_id=%s", (ids['descriptive'],))
    for exam in ['udc','ldc','assistant']:
        conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,as_mock) SELECT %s,live_version,%s,false FROM collections WHERE id=%s ON CONFLICT DO NOTHING",(exam,paper,exam))
    try:
        expected = {ids[kind] for kind, *_ in cases}
        for exam in ['udc','ldc','assistant']:
            tree = client.get(f'/api/collections/{exam}/study-topics').json()
            gk = next(s for s in tree['subjects'] if s['id']=='gk-gs')
            assert gk['title']=='General Knowledge'
            science = next(t for t in gk['topics'] if t['id']=='gk-gs:science')
            assert science['questions']==3
            assert {s['title'] for s in science['subtopics']}=={'Biology','Chemistry','Science in the news'}
            for node, params in [(gk,{'subject_id':'gk-gs'}),(science,{'subject_id':'gk-gs','topic_id':'gk-gs:science'})] + [(s,{'subject_id':'gk-gs','topic_id':'gk-gs:science','subtopic_id':s['id']}) for s in science['subtopics']]:
                response=client.get('/api/questions',params={'collection_id':exam,**params})
                assert response.status_code==200,response.text
                assert response.json()['total']==node['questions']
            rows=client.get('/api/questions',params={'collection_id':exam,'subject_id':'gk-gs','topic_id':'gk-gs:science'}).json()['items']
            assert {r['id'] for r in rows}==expected
            assert next(r for r in rows if r['id']==ids['missing'])['taxonomy_subject_id']=='science'
            assert all(r['source_appearance']['paper_id']==paper for r in rows)
            # Existing science and deeper canonical-topic links stay usable.
            legacy=client.get('/api/questions',params={'collection_id':exam,'subject_id':'science','topic_id':'science/biology'}).json()
            assert {r['id'] for r in legacy['items']}=={ids['missing']}
        # The overlay is specific to clerical exams; global bank GK is unchanged.
        global_rows=client.get('/api/questions',params={'subject_id':'gk-gs','q':'Synthetic repair keyed'}).json()['items']
        assert ids['keyed'] not in {r['id'] for r in global_rows}
    finally:
        conn.execute('DELETE FROM collection_papers WHERE paper_id=%s',(paper,))
