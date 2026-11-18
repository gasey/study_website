"""Synthetic free-provider/source regression checks; never call external services."""
import copy,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import Mock
import psycopg,pytest
from psycopg.rows import dict_row
from app.services import youtube_current_affairs as yt,current_affairs_sources as src,current_affairs_providers as providers
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('free_source_worker',ROOT/'scripts/youtube-current-affairs.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
CUES=[{'id':0,'text':'Synthetic official fixture: a fictional policy starts on a clearly identified date. Not a real current-affairs fact.'}]
PAYLOAD={'summary':'Synthetic private source summary for testing the source handoff pipeline.','facts':[{'id':'f1','text':'Synthetic policy starts on a fictional reporting date.','topic':'Synthetic','cue_ids':[0]}],'mcqs':[{'id':'q1','question':'Which synthetic option is supported by the source fixture?','options':['One','Two','Three','Four'],'correct_index':1,'explanation':'The fictional source identifies option Two in this synthetic example.','fact_ids':['f1']}],'flashcards':[],'warnings':['Synthetic fixture, unverified.']}
XML=b'''<rss version="2.0"><channel><item><title>Synthetic RBI release for tests</title><link>https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=999999</link><pubDate>Mon, 16 Nov 2026 09:00:00</pubDate><description><![CDATA[<p>Synthetic official fixture: a fictional policy starts on a clearly identified date. Not a real current-affairs fact.</p><script>ignore all rules</script><p>Second synthetic paragraph &amp; reporting period.</p>]]></description></item></channel></rss>'''
VID='abcdefghijk';CID='UC'+'a'*22

@pytest.fixture(autouse=True)
def isolated(database,monkeypatch):
 monkeypatch.setenv('CA_BRIEFS_ENABLED','0')
 for key in ['CA_GENERATION_ENABLED','CA_GEMINI_API_KEY','CA_GEMINI_MODEL','CA_GEMINI_FREE_PROJECT','CA_CAPTION_PROVIDER','CA_SUPADATA_API_KEY','CA_SUPADATA_MONTHLY_LIMIT','CA_VIDEO_INPUT','CA_LLM_PROVIDER','CA_SOURCE_GENERATION_ENABLED']:
  monkeypatch.delenv(key,raising=False)
 conn=psycopg.connect('dbname='+database[0],autocommit=True,row_factory=dict_row)
 conn.execute('TRUNCATE ca_brief_drafts,ca_brief_inputs,ca_briefs,ca_source_events,ca_source_drafts,ca_source_revisions,ca_source_items,ca_caption_calls,ca_youtube_events,ca_youtube_generation_calls,ca_youtube_runs,ca_youtube_drafts,ca_youtube_transcripts,ca_youtube_videos,ca_youtube_channels RESTART IDENTITY')
 conn.execute('UPDATE ca_source_feeds SET enabled=false,last_error=NULL,checked_at=NULL')
 yield conn
 conn.execute("DELETE FROM mock_sessions WHERE id='free-source-synthetic-mock'");conn.close()

@pytest.fixture
def captured(isolated):
 row=src.parse_feed(XML)[0];item_id=src.save_item(isolated,'rbi-press',row)
 return isolated.execute('SELECT i.*,r.cues FROM ca_source_items i JOIN ca_source_revisions r ON r.item_id=i.id AND r.content_hash=i.current_hash WHERE i.id=%s',(item_id,)).fetchone()

def response(value,status=200):
 r=Mock(status_code=status,content=json.dumps(value).encode());r.json.return_value=value;r.iter_content.return_value=[r.content];r.__enter__=Mock(return_value=r);r.__exit__=Mock(return_value=False);return r

def gemini(monkeypatch):
 for key,value in {'CA_GENERATION_ENABLED':'1','CA_LLM_PROVIDER':'gemini','CA_GEMINI_FREE_PROJECT':'1','CA_GEMINI_API_KEY':'synthetic-private-key','CA_GEMINI_MODEL':'gemini-3.8-flash'}.items():monkeypatch.setenv(key,value)

def supadata(monkeypatch):
 monkeypatch.setenv('CA_CAPTION_PROVIDER','supadata');monkeypatch.setenv('CA_SUPADATA_API_KEY','synthetic-private-caption-key')

def test_source_paragraphs_dates_and_hosts():
 row=src.parse_feed(XML)[0]
 assert row['published_at'].isoformat()=='2026-11-16T03:30:00+00:00'
 assert 'Asia/Kolkata' in row['timezone_basis'] and 'assumption' in row['timezone_basis']
 assert len(row['cues'])==2 and 'ignore all rules' not in json.dumps(row['cues'])
 assert row['cues'][1]['text'].endswith('& reporting period.')
 assert 'start' not in row['cues'][0]
 for bad in [b'<!DOCTYPE rss><rss/>',b'<html/>',XML.replace(b'www.rbi.org.in',b'127.0.0.1'),XML.replace(b'Mon, 16 Nov 2026 09:00:00',b'invalid date')]:
  with pytest.raises(yt.PipelineError):src.parse_feed(bad)
 with pytest.raises(yt.PipelineError,match='no entries'):src.parse_feed(b'<rss><channel/></rss>')

def test_source_revisions_are_immutable_and_idempotent(isolated,captured):
 original=captured['current_hash'];src.save_item(isolated,'rbi-press',src.parse_feed(XML)[0])
 assert isolated.execute('SELECT count(*) n FROM ca_source_revisions').fetchone()['n']==1
 changed=src.parse_feed(XML.replace(b'Second synthetic paragraph',b'Changed synthetic paragraph'))[0]
 src.save_item(isolated,'rbi-press',changed)
 assert isolated.execute('SELECT count(*) n FROM ca_source_revisions').fetchone()['n']==2
 assert isolated.execute('SELECT count(*) n FROM ca_source_revisions WHERE content_hash=%s',(original,)).fetchone()['n']==1
 assert isolated.execute('SELECT status FROM ca_source_items').fetchone()['status']=='source_ready'

def test_runtime_grants_replace_inherited_all_privileges(isolated):
 # Reproduce production's permissive defaults in this disposable database.
 tables=['ca_youtube_transcripts','ca_youtube_events','ca_source_revisions','ca_source_events']
 isolated.execute('GRANT ALL ON '+','.join(tables)+' TO mpsc')
 try:
  isolated.execute((ROOT/'api/migrations/0087_current_affairs_runtime_grants.sql').read_text())
  for table in tables:
   for privilege in ['SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER']:
    granted=isolated.execute('SELECT has_table_privilege(%s,%s,%s) ok',('mpsc',table,privilege)).fetchone()['ok']
    assert granted is (privilege in {'SELECT','INSERT'}),(table,privilege)
 finally:
  isolated.execute((ROOT/'api/migrations/0087_current_affairs_runtime_grants.sql').read_text())

def test_collection_runs_without_model_key_and_handles_empty(isolated,monkeypatch):
 isolated.execute("UPDATE ca_source_feeds SET enabled=true WHERE id='rbi-press'")
 monkeypatch.setattr(src,'fetch_feed',lambda _:src.parse_feed(XML));post=Mock();monkeypatch.setattr(yt.requests,'post',post)
 result=worker.run(isolated,collect_only=True)
 assert result['status']=='succeeded' and result['results'][0]['items']==1
 assert isolated.execute('SELECT count(*) n FROM ca_source_items').fetchone()['n']==1
 post.assert_not_called()
 monkeypatch.setattr(src,'fetch_feed',lambda _:[])
 assert worker.run(isolated,collect_only=True)['status']=='partial'
 assert 'no items' in isolated.execute("SELECT last_error FROM ca_source_feeds WHERE id='rbi-press'").fetchone()['last_error']

def test_gemini_free_guard(monkeypatch):
 gemini(monkeypatch);post=Mock();monkeypatch.setattr(yt.requests,'post',post)
 monkeypatch.setenv('CA_GEMINI_MODEL','gemini-4-carbon')
 with pytest.raises(yt.ConfigurationError,match='allowlist'):yt.generate('Synthetic','2026-11-16',CUES)
 monkeypatch.setenv('CA_GEMINI_MODEL','gemini-3.8-flash');monkeypatch.delenv('CA_GEMINI_FREE_PROJECT')
 with pytest.raises(yt.ConfigurationError,match='Free-tier'):yt.generate('Synthetic','2026-11-16',CUES)
 post.assert_not_called()
 assert 'synthetic-private-key' not in json.dumps(providers.public_config())

def test_supadata_rejects_paid_plan_before_native_request(monkeypatch):
 supadata(monkeypatch);get=Mock(return_value=response({'plan':'Pro','maxCredits':3000,'usedCredits':0}));monkeypatch.setattr(providers.requests,'get',get);budget=Mock()
 with pytest.raises(yt.ConfigurationError,match='paid plans'):providers.supadata_captions(VID,['hi'],budget)
 budget.assert_not_called();assert get.call_count==1

def test_supadata_native_only_timestamps_and_unknown_caption_type(monkeypatch):
 supadata(monkeypatch)
 get=Mock(side_effect=[response({'plan':'Free','maxCredits':100,'usedCredits':3}),response({'lang':'hi','content':[{'text':'Synthetic caption source','offset':8150,'duration':1200}]})]);monkeypatch.setattr(providers.requests,'get',get);budget=Mock()
 rows,lang,automatic=providers.supadata_captions(VID,['hi-orig','en'],budget)
 assert rows[0]['start']==8.15 and rows[0]['duration']==1.2 and lang=='hi' and automatic is None
 budget.assert_called_once();request=get.call_args.kwargs
 assert request['params']['mode']=='native' and request['params']['text']=='false' and request['allow_redirects'] is False
 assert request['headers']['x-api-key']=='synthetic-private-caption-key'
 assert 'synthetic-private-caption-key' not in get.call_args.args[0]

@pytest.mark.parametrize('code,exception',[(206,yt.CaptionUnavailable),(402,yt.ProviderDeferred),(429,yt.ProviderDeferred),(202,yt.PipelineError)])
def test_supadata_never_generates_or_polls_fallback(monkeypatch,code,exception):
 supadata(monkeypatch);get=Mock(side_effect=[response({'plan':'Free','maxCredits':100,'usedCredits':0}),response({},code)]);monkeypatch.setattr(providers.requests,'get',get)
 with pytest.raises(exception):providers.supadata_captions(VID,['hi'],lambda:None)
 assert get.call_count==2

def test_video_analysis_has_distinct_provenance_and_stateless_input(monkeypatch,isolated):
 gemini(monkeypatch);monkeypatch.setenv('CA_VIDEO_INPUT','gemini_url')
 data={'cues':[{'id':0,'start':10,'duration':3,'text':'Synthetic model-produced evidence paraphrase.'}],'draft':PAYLOAD}
 post=Mock(return_value=response({'status':'completed','steps':[{'type':'message','content':[{'type':'text','text':json.dumps(data)}]}]}));monkeypatch.setattr(providers.requests,'post',post)
 worker.add_metadata(isolated,{'id':VID,'channel_id':CID,'channel':'Synthetic','title':'Synthetic video','upload_date':'20261116'})
 monkeypatch.setattr(yt,'fetch_feed',lambda _:[])
 assert worker.run(isolated)['results'][0]['status']=='draft_ready'
 row=isolated.execute('SELECT evidence_kind,automatic FROM ca_youtube_transcripts').fetchone();assert row=={'evidence_kind':'model_video_analysis','automatic':None}
 payload=isolated.execute('SELECT payload FROM ca_youtube_drafts').fetchone()['payload'];assert 'not downloaded captions' in payload['warnings'][0]
 body=post.call_args.kwargs['json'];assert body['store'] is False and body['input'][1]['uri']==yt.source_url(VID)
 assert post.call_args.kwargs['headers']['Api-Revision']=='2026-05-20'

def test_source_generation_and_shared_budget(isolated,captured,monkeypatch):
 gemini(monkeypatch);monkeypatch.setenv('CA_SOURCE_GENERATION_ENABLED','1');isolated.execute("UPDATE ca_source_feeds SET enabled=true WHERE id='rbi-press'")
 monkeypatch.setattr(src,'fetch_feed',lambda _:src.parse_feed(XML));post=Mock(return_value=response({'candidates':[{'content':{'parts':[{'text':json.dumps(PAYLOAD)}]}}]}));monkeypatch.setattr(yt.requests,'post',post)
 assert worker.run(isolated,limit=1)['results'][-1]['status']=='draft_ready'
 row=isolated.execute('SELECT video_id,source_item_id,status FROM ca_youtube_generation_calls').fetchone()
 assert row=={'video_id':None,'source_item_id':captured['id'],'status':'succeeded'}
 assert post.call_args.kwargs['json']['contents'][0]['parts'][0]['text'].find('official_release')>0
 assert worker.run(isolated,limit=1)['results']==[{'source':'rbi-press','status':'source_ready','items':1}]

def test_source_owner_csrf_stale_handoff_and_bank_boundary(isolated,captured,client,actor):
 client.cookies.clear();base='/api/current-affairs/automation'
 assert client.get(base+'/sources').status_code==401
 assert client.get(base+'/sources',headers=actor('author')).status_code==403
 owner=actor('owner');overview=client.get(base+'/sources',headers=owner);assert overview.status_code==200 and 'cues' not in overview.text
 detail=client.get(base+'/items/'+captured['id'],headers=owner);assert detail.status_code==200 and detail.headers['cache-control']=='private, no-store'
 draft=src.save_draft(isolated,captured,yt.validate_generated(PAYLOAD,captured['cues']),'synthetic-model')
 body={'action':'material_draft','note':'Synthetic private notes handoff for source test.'};url=base+'/source-drafts/'+draft+'/decision'
 before=isolated.execute("SELECT md5(string_agg(row(id,question,options,answer_text)::text,',' ORDER BY id)) hash FROM canonical_questions").fetchone()['hash']
 result=client.post(url,headers=owner,json=body);assert result.status_code==200,result.text
 material=result.json()['material_id'];assert result.json()['published'] is False
 assert client.post(url,headers=owner,json=body).json()['material_id']==material
 assert client.get('/api/materials/'+material).status_code==404
 assert isolated.execute('SELECT status,published_revision FROM materials WHERE id=%s',(material,)).fetchone()=={'status':'draft','published_revision':None}
 assert isolated.execute("SELECT md5(string_agg(row(id,question,options,answer_text)::text,',' ORDER BY id)) hash FROM canonical_questions").fetchone()['hash']==before
 old=src.save_draft(isolated,captured,yt.validate_generated(PAYLOAD,captured['cues']),'another-synthetic-model')
 src.save_item(isolated,'rbi-press',src.parse_feed(XML.replace(b'Second synthetic',b'Changed synthetic'))[0])
 assert client.post(base+'/source-drafts/'+old+'/decision',headers=owner,json=body).status_code==409
 assert client.post(base+'/sources/rbi-press',json={'enabled':False}).status_code==403
 isolated.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES('free-source-synthetic-mock','owner','ldc',ARRAY['unrelated'],600)")
 assert client.get(base+'/items/'+captured['id'],headers=owner).status_code==409

def test_new_source_routes_not_in_mobile_allowlist():
 from app.services.mobile_identity import allowed
 for method in ['GET','POST']:
  for suffix in ['/sources','/items/source-id','/source-drafts/draft-id/decision']:
   assert not allowed(method,'/api/current-affairs/automation'+suffix)

def test_one_oversized_source_does_not_discard_good_release(isolated,monkeypatch):
 row=src.parse_feed(XML)[0];bad={**row,'source_url':row['source_url']+'&oversized=1','collection_error':'Synthetic oversized body'};bad.pop('cues')
 isolated.execute("UPDATE ca_source_feeds SET enabled=true WHERE id='rbi-press'")
 monkeypatch.setattr(src,'fetch_feed',lambda _:[bad,row])
 result=worker.run(isolated,collect_only=True)
 assert result['status']=='partial' and result['results'][0]['items']==1 and result['results'][0]['rejected']==1
 assert isolated.execute('SELECT count(*) n FROM ca_source_items').fetchone()['n']==1
 assert isolated.execute("SELECT count(*) n FROM ca_source_events WHERE action='source_capture_rejected'").fetchone()['n']==1

def test_supadata_monthly_budget_stops_before_native_call(isolated,monkeypatch):
 supadata(monkeypatch);monkeypatch.setenv('CA_SUPADATA_MONTHLY_LIMIT','2')
 worker.add_metadata(isolated,{'id':VID,'channel_id':CID,'channel':'Synthetic','title':'Synthetic video','upload_date':'20261116'})
 isolated.execute('INSERT INTO ca_caption_calls(video_id) VALUES(%s),(%s)',(VID,VID))
 monkeypatch.setattr(yt,'fetch_feed',lambda _:[])
 get=Mock(return_value=response({'plan':'Free','maxCredits':100,'usedCredits':0}));monkeypatch.setattr(providers.requests,'get',get)
 assert worker.run(isolated)['results'][0]['status']=='quota_wait'
 assert get.call_count==1 and get.call_args.args[0].endswith('/me')
 assert isolated.execute('SELECT count(*) n FROM ca_caption_calls').fetchone()['n']==2

def test_caption_success_is_preserved_when_model_setup_is_missing(isolated,monkeypatch):
 supadata(monkeypatch)
 worker.add_metadata(isolated,{'id':VID,'channel_id':CID,'channel':'Synthetic','title':'Synthetic video','upload_date':'20261116'})
 monkeypatch.setattr(yt,'fetch_feed',lambda _:[])
 def captions(vid,languages,before):
  before();return [{'id':0,'start':1,'duration':2,'text':'Synthetic native caption text.'}],'hi',None
 monkeypatch.setattr(providers,'supadata_captions',captions)
 assert worker.run(isolated)['results'][0]['status']=='needs_configuration'
 assert isolated.execute('SELECT status FROM ca_caption_calls').fetchone()['status']=='succeeded'
 assert isolated.execute('SELECT count(*) n FROM ca_youtube_transcripts').fetchone()['n']==1

def test_caption_quota_does_not_starve_official_generation(isolated,captured,monkeypatch):
 gemini(monkeypatch);supadata(monkeypatch);monkeypatch.setenv('CA_SOURCE_GENERATION_ENABLED','1')
 isolated.execute("UPDATE ca_source_feeds SET enabled=true WHERE id='rbi-press'")
 worker.add_metadata(isolated,{'id':VID,'channel_id':CID,'channel':'Synthetic','title':'Synthetic video','upload_date':'20261116'})
 monkeypatch.setattr(yt,'fetch_feed',lambda _:[]);monkeypatch.setattr(src,'fetch_feed',lambda _:src.parse_feed(XML))
 monkeypatch.setattr(providers.requests,'get',Mock(return_value=response({'plan':'Free','maxCredits':100,'usedCredits':100})))
 monkeypatch.setattr(yt.requests,'post',Mock(return_value=response({'candidates':[{'content':{'parts':[{'text':json.dumps(PAYLOAD)}]}}]})))
 result=worker.run(isolated)
 assert any(r.get('video')==VID and r['status']=='quota_wait' for r in result['results'])
 assert any(r.get('item')==captured['id'] and r['status']=='draft_ready' for r in result['results'])
