"""Synthetic statistical releases on disposable PostgreSQL; no provider writes."""
import copy
from datetime import datetime,timezone
import pytest
from app.services import stats as store
from app.services import stats_connectors as connectors
from app.services.mobile_identity import allowed

@pytest.fixture(autouse=True)
def clean_stats(database):
 database[1].execute('TRUNCATE stats_decisions,stats_import_runs,stats_releases,stats_checks,stats_source_watches RESTART IDENTITY')

def payload(metric='gdp-growth',rows=None):
 return {'metric_id':metric,'source_url':'https://api.worldbank.org/v2/country/all/indicator/NY.GDP.MKTP.KD.ZG','edition':'Synthetic edition','reference_period':'2024','methodology':'Synthetic stable methodology','rows':rows or [
  {'place':'IND','name':'India','period':'2024','value':5},
  {'place':'AAA','name':'Synthetic A','period':'2024','value':7},
  {'place':'BBB','name':'Synthetic B','period':'2024','value':7},
  {'place':'CCC','name':'Synthetic C','period':'2024','value':None}]}

def publish(client,actor,body):
 h=actor('owner');r=client.post('/api/stats/admin/releases',headers=h,json=body);assert r.status_code==200,r.text
 i=r.json()['id'];r=client.post(f'/api/stats/admin/releases/{i}/decision',headers=h,json={'decision':'publish','note':'Synthetic source inspection for test only'})
 assert r.status_code==200,r.text
 return i

def test_pending_private_publication_and_pinned_history(client,actor):
 h=actor('owner');body=payload();r=client.post('/api/stats/admin/releases',headers=h,json=body);i=r.json()['id']
 assert client.get('/api/stats/metrics/gdp-growth').json()['release'] is None
 assert client.get('/api/stats/metrics/gdp-growth?release_id='+i).status_code==404
 assert client.post(f'/api/stats/admin/releases/{i}/decision',headers=h,json={'decision':'publish','note':'Synthetic owner inspection'}).status_code==200
 body['rows'][0]['value']=6;j=publish(client,actor,body)
 client.cookies.clear()
 assert client.get('/api/stats/metrics/gdp-growth').json()['release']['id']==j
 assert client.get('/api/stats/metrics/gdp-growth?release_id='+i).json()['observations'][0]['value']==5
 assert client.get('/api/stats/metrics/gdp-growth/releases').json()['items'][0]['id']==j

def test_roles_csrf_and_mobile_admin_boundary(client,actor):
 assert client.post('/api/stats/admin/releases',json=payload()).status_code==401
 h=actor('author');assert client.post('/api/stats/admin/releases',headers=h,json=payload()).status_code==403
 actor('owner');assert client.post('/api/stats/admin/releases',json=payload()).status_code==403
 assert allowed('GET','/api/stats/metrics/hdi/rankings')
 assert not allowed('GET','/api/stats/admin/releases')
 assert not allowed('POST','/api/stats/admin/releases')

@pytest.mark.parametrize('change',[
 lambda b:b['rows'].append(b['rows'][0]),
 lambda b:b['rows'][0].update(value=float('inf')),
 lambda b:b.update(source_url='https://untrusted.example.test/data'),
 lambda b:b['rows'][0].update(group='Aggregate region'),
 lambda b:b['rows'][0].update(rank=1),
 lambda b:b['rows'][0].update(period='2099'),
 lambda b:b['rows'][0].update(period='2023-99'),
 lambda b:b['rows'][0].update(period='2023-24'),
])
def test_reject_malformed_candidate(change):
 b=payload();change(b)
 with pytest.raises(ValueError):store.ReleaseInput.model_validate(b)

def test_rank_ties_nulls_pagination_search_and_etag(client,actor):
 publish(client,actor,payload());client.cookies.clear()
 r=client.get('/api/stats/metrics/gdp-growth/rankings?limit=2');b=r.json()
 assert b['derived'] and b['coverage']==3 and b['total']==3
 assert [x['rank'] for x in b['items']]==[1,1] and b['india']['rank']==3
 assert client.get('/api/stats/metrics/gdp-growth/rankings?offset=2').json()['items'][0]['place']=='IND'
 assert client.get('/api/stats/metrics/gdp-growth/rankings?q=india').json()['total']==1
 assert client.get('/api/stats/metrics/gdp-growth/rankings?limit=2',headers={'If-None-Match':r.headers['etag']}).status_code==304

def test_same_period_comparison_and_missing_values(client,actor):
 b=payload();b['rows'] += [{'place':'IND','name':'India','period':'2023','value':4},{'place':'CCC','name':'Synthetic C','period':'2023','value':2}]
 publish(client,actor,b)
 data=client.get('/api/stats/metrics/gdp-growth?places=IND,CCC').json()
 assert data['period']=='2023' and [r['value'] for r in data['observations']]==[4,2]
 data=client.get('/api/stats/metrics/gdp-growth?places=IND,CCC&period=2024').json()
 assert data['observations'][1]['value'] is None
 assert client.get('/api/stats/metrics/gdp-growth?places=IND,AAA,BBB,CCC,DDD').status_code==422

def test_groups_remain_separate_and_publisher_ranks_unchanged(client,actor):
 b=payload('state-health',[{'place':'IN-MZ','name':'Mizoram','period':'2019-20','value':75,'rank':1,'group':'Smaller states'},{'place':'IN-KL','name':'Kerala','period':'2019-20','value':82,'rank':1,'group':'Larger states'}]);b.update(source_url='https://www.niti.gov.in/report.pdf',reference_period='2019-20')
 publish(client,actor,b)
 data=client.get('/api/stats/metrics/state-health/rankings').json()
 assert data['coverage']==1 and data['india']['name']=='Mizoram' and not data['derived']
 data=client.get('/api/stats/metrics/state-health/rankings?group=Larger%20states').json()
 assert data['coverage']==1 and data['items'][0]['name']=='Kerala' and data['india'] is None


def test_content_replay_and_suspicious_automatic_revision(client,actor):
 body=payload();i=publish(client,actor,body)
 original=store.ReleaseInput.model_validate(body)
 result=client.portal.call(store.stage,original,True)
 assert result==(i,False)
 changed=copy.deepcopy(body);changed['rows'][0]['value']=500
 j,created=client.portal.call(store.stage,store.ReleaseInput.model_validate(changed),True)
 assert created and client.get('/api/stats/metrics/gdp-growth').json()['release']['id']==i
 assert client.get('/api/stats/metrics/gdp-growth?release_id='+j).status_code==404


def test_fetch_failure_keeps_published_release_and_last_success(client,actor,database):
 i=publish(client,actor,payload())
 database[1].execute("INSERT INTO stats_checks(metric_id,succeeded_at) VALUES('gdp-growth','2026-01-01T00:00:00Z')")
 def fail():raise connectors.SourceError('Synthetic provider outage')
 result=client.portal.call(connectors.run_import,'gdp-growth',fail,True)
 assert result['status']=='failed'
 data=client.get('/api/stats/metrics/gdp-growth').json()
 assert data['release']['id']==i and data['freshness']['delayed']
 assert data['freshness']['last_checked_at'].startswith('2026-01-01')
 assert database[1].execute("SELECT status FROM stats_import_runs ORDER BY id DESC LIMIT 1").fetchone()[0]=='failed'


def test_world_bank_excludes_aggregates_and_checks_pagination(monkeypatch):
 calls=[]
 class Reply:
  def __init__(self,b):self.body=b
  def json(self):return self.body
 def fake(url,params):
  calls.append(params['page'])
  if params['page']==1:return Reply([{'page':1,'pages':2,'total':2},[{'countryiso3code':'IND','date':'2024','value':5,'indicator':{'id':'NY.GDP.MKTP.KD.ZG'}}]])
  return Reply([{'page':2,'pages':2,'total':2},[{'countryiso3code':'WLD','date':'2024','value':3,'indicator':{'id':'NY.GDP.MKTP.KD.ZG'}}]])
 monkeypatch.setattr(connectors,'fetch',fake)
 body=connectors.world_bank('gdp-growth',{'IND':'India'})
 assert [r.place for r in body.rows]==['IND'] and calls==[1,2]
 def incomplete(url,params):return Reply([{'page':1,'pages':1,'total':2},[]])
 monkeypatch.setattr(connectors,'fetch',incomplete)
 with pytest.raises(connectors.SourceError):connectors.wb_pages('country')


def test_bootstrap_cannot_trust_hash_claim_alone(client):
 from app.services.stats_bootstrap import HDI_SHA,accepted
 b=payload('hdi');b.update(source_url='https://hdr.undp.org/fake.csv',upstream_hash=HDI_SHA)
 for r in b['rows']:r['value']=.5
 assert not accepted(store.ReleaseInput.model_validate(b))


def test_bootstrap_exact_reports_and_no_repeat(client):
 from app.services.stats_bootstrap import bootstrap
 first=client.portal.call(bootstrap)
 assert all(r['status']=='published' and r['changed'] for r in first)
 again=client.portal.call(bootstrap)
 assert all(not r['changed'] for r in again)
 hdi=client.get('/api/stats/metrics/hdi').json()
 assert hdi['observations'][0]['value']==.685 and hdi['observations'][0]['rank']==130
 health=client.get('/api/stats/metrics/state-health/rankings').json()
 assert health['india']['rank']==1 and health['coverage']==8 and health['india']['value']==75.77


def test_survey_preserves_estimates_and_verified_part_links(client):
 data=client.get('/api/stats/surveys/2025-26').json()
 assert data['chapters'][0]['figures'][0]['status']=='First advance estimate'
 assert data['chapters'][-1]['source_url'].endswith('echap16-2.pdf')
 assert client.get('/api/stats/surveys/2099-00').status_code==404


def test_world_bank_null_placeholders_do_not_extend_reference_period(monkeypatch):
 def fake(*args):return ([{'countryiso3code':'IND','date':'2025','value':None,'indicator':{'id':'SP.DYN.LE00.IN'}},{'countryiso3code':'IND','date':'2024','value':70,'indicator':{'id':'SP.DYN.LE00.IN'}}],{})
 monkeypatch.setattr(connectors,'wb_pages',fake)
 body=connectors.world_bank('life-expectancy',{'IND':'India'})
 assert body.reference_period=='2024' and len(body.rows)==1


def test_source_watch_recovers_and_flags_changed_release_links(client,database,monkeypatch):
 database[1].execute("INSERT INTO stats_source_watches(source_id,error) VALUES('survey','Synthetic outage')")
 class Reply:text='<a href="https://www.indiabudget.gov.in/report.pdf">Official file</a>'
 monkeypatch.setattr(connectors,'fetch',lambda *args:Reply())
 first=client.portal.call(connectors.watch_sources)
 assert all(r['status']=='checked' for r in first)
 r=database[1].execute("SELECT needs_review,error FROM stats_source_watches WHERE source_id='survey'").fetchone()
 assert r==(False,None)
 Reply.text='<a href="https://www.indiabudget.gov.in/new-report.pdf">New official file</a>'
 client.portal.call(connectors.watch_sources)
 assert database[1].execute("SELECT needs_review FROM stats_source_watches WHERE source_id='survey'").fetchone()[0]


def test_survey_catalogue_change_pauses_edition_links(client,database):
 database[1].execute("INSERT INTO stats_source_watches(source_id,needs_review) VALUES('survey',true)")
 data=client.get('/api/stats/surveys/2025-26').json()
 assert data['catalogue_status']['changed'] and len(data['tables'])==107
 assert data['tables'][0]['source_url'].endswith('/doc/stat/tab1.1.pdf')


def test_overview_selects_only_the_requested_place_and_replay_reports_actual_state(client,actor):
 body=payload();i=publish(client,actor,body)
 data=client.get('/api/stats/overview?country=AAA').json()
 m=next(x for x in data['items'] if x['id']=='gdp-growth')
 assert m['observation']['place']=='AAA' and m['observation']['value']==7
 r=client.post('/api/stats/admin/releases',headers=actor('owner'),json=body)
 assert r.json()['id']==i and r.json()['status']=='published' and not r.json()['created']


def test_provider_outage_restarts_with_smaller_complete_pages(monkeypatch):
 calls=[]
 class Reply:
  def json(self):return [{'page':1,'pages':1,'total':1},[{'id':'IND'}]]
 def fake(url,params):
  calls.append(params['per_page'])
  if params['per_page']==5000:raise connectors.SourceUnavailable('Synthetic cached gateway failure')
  return Reply()
 monkeypatch.setattr(connectors,'fetch',fake)
 rows,_=connectors.wb_pages('country')
 assert calls==[5000,1000] and rows==[{'id':'IND'}]
