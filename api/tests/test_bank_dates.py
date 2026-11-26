"""Date projection tests; synthetic bank records only, no canonical writes in feature."""
from uuid import uuid4
from psycopg.types.json import Jsonb
from app.services.bank_dates import dates_in, project, build_index, filtered


def row(question, answer=None, usable=False, **extra):
    return dict(id='q1',question=question,answer_text=answer,answer_usable=usable,
                answer_source='official',options=[answer,'6 June','7 June','8 June'] if answer not in ('6 June','7 June','8 June') else ['5 June','6 June','7 June','8 June'],**extra)


def test_month_year_not_misread_as_a_day_and_precision_preserved():
    assert dates_in('May 1915') == [dict(year=1915,month=5,day=None,precision='month')]
    assert dates_in('5th June, 1973') == [dict(year=1973,month=6,day=5,precision='date')]
    assert dates_in('June 5') == [dict(year=None,month=6,day=5,precision='date')]
    assert dates_in('326 BC') == [dict(year=326,month=None,day=None,precision='year',era='BCE')]
    assert dates_in('31 February 2020') == []  # Never salvage an impossible full date.
    assert not dates_in('03/04/19')
    assert dates_in('1757, a turning point.')[0]['year']==1757


def test_only_ready_date_answers_are_taken_not_distractors_or_explanations():
    observed=project(row('World Environment Day is observed on','5 June',True))
    assert observed['dates'][0]['month']==6 and observed['dates'][0]['day']==5
    assert observed['evidence']=='answer'
    assert project(row('World Environment Day is observed on','5 June',False))['dates']==[]
    assert project(row('World Environment Day is observed on',None,False))['dates']==[]
    first=project(row('World Environment Day was first observed on','5 June 1973',True))
    assert first['title']!=observed['title'] and first['dates'][0]['year']==1973
    assert project(row('World Environment Day is NOT observed on','6 June',True))['dates']==[]


def test_history_mentions_and_ambiguous_statements_are_distinct():
    battle=project(row('Why was the Battle of Plassey (1757) a turning point?'))
    assert battle['title']=='Battle of Plassey'
    assert battle['dates']==[dict(year=1757,month=None,day=None,precision='year')]
    assert battle['evidence']=='question'
    statement=project(row('Consider the following statements: The Battle of Plassey occurred in 1857. Which statement is correct?'))
    assert not statement['dates']
    law=project(row('When did the Indian Evidence Act, 1872 come into force?'))
    assert not law['dates'], 'The law title year cannot substitute for the unknown commencement date'
    assert not project(row('The revised CRZ notification under the Environment Protection Act 1986 was passed in:'))['dates']
    assert project(row('Compute compound interest at 5% per annum for 2015.', '2015', True)) is None
    assert project(row('Select the correct preposition for Independence Day on 15 August.',subject_id='english')) is not None  # It stays a quoted mention, never an answer-derived fact.


def test_groups_date_fact_but_retains_source_questions_and_first_observance():
    items=build_index([
      row('World Environment Day is observed on','5 June',True),
      {**row('When do we celebrate World Environment Day?','June 5',True),'id':'q2'},
      {**row('World Environment Day was first observed on','5 June 1973',True),'id':'q3'},
    ])
    assert len(items)==2
    assert sorted(len(item['questions']) for item in items)==[1,2]
    assert len(filtered(items,month=6))==2
    assert len(filtered(items,month=7))==0
    assert len(filtered(items,q='environment day'))==2
    assert len(filtered(items,q='5 June'))==2
    assert len(filtered(items,q='1973'))==1
    assert len(filtered(items,evidence='unresolved'))==0


def synthetic(conn, question, answer, *, ready=True, origin='Direct'):
    token=uuid4().hex;q='date-q-'+token;p='date-p-'+token
    options=[answer,'6 June','7 June','8 June'] if answer not in ('6 June','7 June','8 June') else ['5 June','6 June','7 June','8 June']
    conn.execute("INSERT INTO papers(id,exam_type,exam_name,year) VALUES(%s,%s,'Synthetic dates',2020)",(p,origin))
    conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq',%s,%s,%s,%s)",(q,question,Jsonb(options),answer,'official' if ready else 'inferred'))
    conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,page) VALUES(%s,%s,'mcq',%s,%s,0,%s,%s,true,'1',1)",('date-a-'+token,p,question,Jsonb(options),'official' if ready else 'inferred',q))
    return q


def test_bank_dates_reads_bank_not_manual_collections_and_filters(client,actor,database):
    actor('outsider');conn=database[1]
    q=synthetic(conn,'Synthetic Environment Day is observed on','5 June')
    before=conn.execute('SELECT count(*) FROM canonical_questions').fetchone()[0]
    response=client.get('/api/learning-catalog/bank-dates',params={'q':'Synthetic Environment','month':6})
    assert response.status_code==200,response.text
    body=response.json();assert body['total']==1 and body['question_count']==1
    assert response.headers['cache-control']=='private, no-store'
    event=body['items'][0];assert event['dates'][0]['day']==5
    assert 'answer_text' not in str(body) and 'options' not in str(body)
    detail=client.get('/api/learning-catalog/bank-dates',params={'event_id':event['id']}).json()
    assert detail['questions'][0]['id']==q
    assert client.get('/api/learning-catalog/bank-dates',params={'q':'Synthetic Environment','month':7}).json()['total']==0
    assert client.get('/api/learning-catalog/bank-dates',params={'q':'Synthetic Environment','origin':'community'}).json()['total']==0
    assert conn.execute('SELECT count(*) FROM canonical_questions').fetchone()[0]==before
    conn.execute("UPDATE canonical_questions SET status='withdrawn',answer_text=NULL,answer_source=NULL WHERE id=%s",(q,))
    assert client.get('/api/learning-catalog/bank-dates',params={'q':'Synthetic Environment'}).json()['total']==0


def test_unreviewed_answer_not_exposed_and_assessment_checks_even_warm_cache(client,actor,database):
    actor('outsider');conn=database[1]
    q=synthetic(conn,'Synthetic Water Day is celebrated on','5 June',ready=False)
    response=client.get('/api/learning-catalog/bank-dates',params={'q':'Synthetic Water','evidence':'unresolved'})
    assert response.status_code==200 and response.json()['items'][0]['dates']==[]
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES('date-active','outsider','combined-prelims',%s,600)",([q],))
    try:assert client.get('/api/learning-catalog/bank-dates').status_code==409
    finally:conn.execute("DELETE FROM mock_sessions WHERE id='date-active'")
    assert client.get('/api/learning-catalog/bank-dates',params={'event_id':'date_'+'0'*20}).status_code==404
    assert client.get('/api/learning-catalog/bank-dates',params={'month':13}).status_code==422


def test_calendar_sorts_known_dates_before_unresolved_events(client,actor,database):
    actor('outsider');conn=database[1]
    synthetic(conn,'Ordering: World Environment Day is observed on','5 June')
    synthetic(conn,'Ordering: World Environment Day is observed on','5 June',ready=False)
    body=client.get('/api/learning-catalog/bank-dates',params={'q':'Ordering'}).json()
    assert body['total']==2
    assert body['items'][0]['dates'] and not body['items'][1]['dates']


def test_calendar_counts_all_filtered_events_before_pagination_and_day(client,actor,database):
    actor('outsider');conn=database[1];token='Calendar-'+uuid4().hex
    for number in range(30):synthetic(conn,f'{token}: When was synthetic treaty {number} signed?','5 June')
    synthetic(conn,f'{token}: When was another synthetic treaty signed?','6 June',origin='Community')
    synthetic(conn,f'{token}: A synthetic treaty was signed in June 2000.','5 June')
    params={'q':token,'month':6,'evidence':'dated','limit':1}
    body=client.get('/api/learning-catalog/bank-dates',params=params).json()
    assert body['total']==32 and len(body['items'])==1
    counts={entry['day']:entry['events'] for entry in body['calendar_days']}
    assert counts[5]==30 and counts[6]==1 and body['month_only_count']==1
    chosen=client.get('/api/learning-catalog/bank-dates',params={**params,'day':6}).json()
    assert chosen['total']==1 and chosen['items'][0]['dates'][0]['day']==6
    assert chosen['calendar_days']==body['calendar_days'],'Selecting a day cannot erase the rest of the month counts'
    paper=client.get('/api/learning-catalog/bank-dates',params={**params,'origin':'paper'}).json()
    assert next(entry for entry in paper['calendar_days'] if entry['day']==6)['events']==0
    assert client.get('/api/learning-catalog/bank-dates',params={'day':5}).status_code==422


def test_chronology_orders_bce_and_ce_before_dates_without_year(client,actor,database):
    actor('outsider');conn=database[1];token='Chronology-'+uuid4().hex
    for label,answer in [('ancient','326 BC'),('later','1757'),('annual','5 June')]:
        synthetic(conn,f'{token}: When was the {label} treaty signed?',answer)
    body=client.get('/api/learning-catalog/bank-dates',params={'q':token,'order':'year'}).json()
    dates=[entry['dates'][0] for entry in body['items']]
    assert [value['year'] for value in dates]==[326,1757,None]
    assert dates[0]['era']=='BCE'


def test_numeric_false_positives_rejected_titles_cleaned_and_era_filters_work():
    assert dates_in('Number of deaths of infants under 1 week per 1000 total births') == []
    assert dates_in('When number of persons exceeds 1500 workers') == []
    assert project(row('The number of live birth per 1000 women in a year is called:')) is None
    assert project(row('A single-phase energy meter is operating on 230 V, 50 Hz, 1380 rpm')) is None
    cleaned = project(row('When did the the Great Bengal Famine occur?', '1770', True))
    assert cleaned['title'] == 'The Great Bengal Famine'
    assert cleaned['dates'][0]['year'] == 1770
    entries = build_index([
        row('When did Alexander invade India?', '326 BC', True),
        {**row('When was the Battle of Plassey fought?', '1757', True), 'id': 'q2'},
        {**row('When did the Quit India Movement begin?', '1942', True), 'id': 'q3'},
        {**row('When did Mizoram attain statehood?', '20 February 1987', True), 'id': 'q4'},
        {**row('World Environment Day is observed on', '5 June', True), 'id': 'q5'},
    ])
    assert len(filtered(entries, era='ancient')) == 1
    assert len(filtered(entries, era='company')) == 1
    assert len(filtered(entries, era='crown')) == 1
    assert len(filtered(entries, era='republic')) == 1
    assert len(filtered(entries, era='observances')) == 1
