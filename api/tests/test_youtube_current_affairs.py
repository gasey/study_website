"""Synthetic private pipeline tests. No real provider or production writes."""
import copy,importlib.util,json,sys
from pathlib import Path
from unittest.mock import Mock
import pytest
from psycopg.types.json import Jsonb
from app.services import youtube_current_affairs as yt
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('youtube_worker',ROOT/'scripts/youtube-current-affairs.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
CID='UC'+'a'*22;VID='abcdefghijk'
CUES=[{'id':0,'start':10.0,'duration':4.0,'text':'Synthetic event occurred in a fictional country.'},{'id':1,'start':20.0,'duration':3.0,'text':'Synthetic second cue for tests only.'}]
PAYLOAD={'summary':'Synthetic summary for the private pipeline test; not a real current-affairs fact.','facts':[{'id':'f1','text':'Synthetic fact with no real-world significance.','topic':'Synthetic topic','cue_ids':[0]}],'mcqs':[{'id':'q1','question':'Which synthetic option belongs to this synthetic fact?','options':['Synthetic A','Synthetic B','Synthetic C','Synthetic D'],'correct_index':1,'explanation':'The synthetic source names Synthetic B for this test.','fact_ids':['f1']}],'flashcards':[{'front':'Synthetic card question?','back':'Synthetic card answer.','fact_ids':['f1']}],'warnings':['Synthetic source only; unverified draft.']}

@pytest.fixture(autouse=True)
def clean(database,monkeypatch):
 monkeypatch.setenv('CA_BRIEFS_ENABLED','0')
 database[1].execute('TRUNCATE ca_brief_drafts,ca_brief_inputs,ca_briefs,ca_source_events,ca_source_drafts,ca_source_revisions,ca_source_items,ca_caption_calls,ca_youtube_events,ca_youtube_generation_calls,ca_youtube_runs,ca_youtube_drafts,ca_youtube_transcripts,ca_youtube_videos,ca_youtube_channels RESTART IDENTITY')
 database[1].execute('UPDATE ca_source_feeds SET enabled=false')
 for key in ['CA_GEMINI_FREE_PROJECT','CA_CAPTION_PROVIDER','CA_VIDEO_INPUT','CA_SOURCE_GENERATION_ENABLED','CA_SUPADATA_API_KEY','CA_GENERATION_ENABLED','CA_GEMINI_API_KEY','CA_GEMINI_MODEL','CA_LLM_PROVIDER','CA_OPENCODE_MODEL']:monkeypatch.delenv(key,raising=False)

@pytest.fixture
def seeded(database):
 import psycopg
 from psycopg.rows import dict_row
 conn=psycopg.connect('dbname='+database[0],autocommit=True,row_factory=dict_row)
 worker.add_metadata(conn,{'id':VID,'channel_id':CID,'channel':'Synthetic channel','title':'Synthetic source video','upload_date':'20261115'})
 digest=worker.save_transcript(conn,VID,CUES,'hi',True,'synthetic caption fixture')
 yield conn,digest
 conn.close()

def test_ids_and_caption_time_gaps():
 assert yt.video_id('https://www.youtube.com/watch?v='+VID)==VID
 for url in ['https://evil.example/watch?v='+VID,'file:///etc/passwd','https://youtube.com@evil.example/watch?v='+VID,'https://youtube.com/watch?v=bad']:
  with pytest.raises(ValueError):yt.video_id(url)
 raw={'events':[{'tStartMs':0,'dDurationMs':3000,'segs':[{'utf8':'First two words &amp; more'}]},{'tStartMs':2000,'dDurationMs':2000,'segs':[{'utf8':'&amp; more next phrase'}]},{'tStartMs':20000,'dDurationMs':2000,'segs':[{'utf8':'&amp; more next phrase'}]}]}
 rows=yt.normalized_cues(raw)
 assert [x['text'] for x in rows]==['First two words & more','next phrase','& more next phrase']
 assert rows[2]['start']==20
 with pytest.raises(yt.CaptionUnavailable):yt.normalized_cues({'events':[]})

def test_generated_evidence_options_duplicates():
 assert yt.validate_generated(PAYLOAD,CUES).mcqs[0].correct_index==1
 for mutate in [lambda p:p['facts'][0].update(cue_ids=[999]),lambda p:p['mcqs'][0].update(fact_ids=['missing']),lambda p:p['mcqs'][0].update(options=['same']*4),lambda p:p['mcqs'].append({**p['mcqs'][0],'id':'q2'})]:
  value=copy.deepcopy(PAYLOAD);mutate(value)
  with pytest.raises(ValueError):yt.validate_generated(value,CUES)

def test_generation_is_off_without_setup(monkeypatch):
 post=Mock();monkeypatch.setattr(yt.requests,'post',post)
 with pytest.raises(yt.ConfigurationError):yt.generate('Synthetic title','2026-11-15',CUES)
 post.assert_not_called()
 monkeypatch.setenv('CA_LLM_PROVIDER','opencode');monkeypatch.setenv('CA_GENERATION_ENABLED','1');monkeypatch.setenv('CA_OPENCODE_MODEL','openai/paid-model')
 with pytest.raises(yt.ConfigurationError,match='paid models'):yt.generate('Synthetic title','2026-11-15',CUES)

def test_generation_repair_is_bounded(monkeypatch):
 monkeypatch.setenv('CA_GENERATION_ENABLED','1');monkeypatch.setenv('CA_GEMINI_API_KEY','synthetic-key');monkeypatch.setenv('CA_GEMINI_MODEL','gemini-3.8-flash');monkeypatch.setenv('CA_GEMINI_FREE_PROJECT','1')
 response=Mock(status_code=200,content=b'{}');response.json.return_value={'candidates':[{'content':{'parts':[{'text':'not-json'}]}}]}
 post=Mock(return_value=response);monkeypatch.setattr(yt.requests,'post',post);calls=[]
 with pytest.raises(yt.PipelineError,match='one repair'):yt.generate('Synthetic title','2026-11-15',CUES,calls.append)
 assert len(calls)==post.call_count==2
 args=post.call_args;assert args.kwargs['headers']['x-goog-api-key']=='synthetic-key';assert 'synthetic-key' not in args.args[0]
 assert 'untrusted' in args.kwargs['json']['system_instruction']['parts'][0]['text']

def test_feed_identity_and_xml_limits(monkeypatch):
 xml=f'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015"><entry><yt:videoId>{VID}</yt:videoId><yt:channelId>{CID}</yt:channelId><title>Synthetic upload</title><published>2026-11-15T01:00:00Z</published></entry></feed>'.encode()
 response=Mock(status_code=200);response.__enter__=Mock(return_value=response);response.__exit__=Mock();response.iter_content.return_value=[xml]
 monkeypatch.setattr(yt.requests,'get',Mock(return_value=response));assert yt.fetch_feed(CID)[0]['id']==VID
 response.iter_content.return_value=[b'<!DOCTYPE feed><feed/>']
 with pytest.raises(yt.PipelineError,match='XML'):yt.fetch_feed(CID)
 response.iter_content.return_value=[xml.replace(CID.encode(),('UC'+'b'*22).encode())]
 with pytest.raises(yt.PipelineError,match='identity'):yt.fetch_feed(CID)

def test_staging_idempotence_and_immutable_transcript(seeded):
 conn,digest=seeded
 assert worker.save_transcript(conn,VID,CUES,'hi',True,'synthetic caption fixture')==digest
 first=worker.save_generated(conn,VID,digest,yt.validate_generated(PAYLOAD,CUES),'synthetic-model')
 second=worker.save_generated(conn,VID,digest,yt.validate_generated(PAYLOAD,CUES),'synthetic-model')
 assert first==second
 assert conn.execute('SELECT count(*) AS n FROM ca_youtube_transcripts').fetchone()['n']==1
 assert conn.execute('SELECT count(*) AS n FROM ca_youtube_drafts').fetchone()['n']==1
 assert conn.execute('SELECT published_precision FROM ca_youtube_videos WHERE id=%s',(VID,)).fetchone()['published_precision']=='day'

def test_worker_no_configuration_and_no_duplicates(seeded,database,monkeypatch):
 import psycopg
 from psycopg.rows import dict_row
 monkeypatch.setattr(yt,'fetch_feed',lambda _:[])
 with psycopg.connect('dbname='+database[0],autocommit=True,row_factory=dict_row) as conn:
  result=worker.run(conn);assert result['results'][0]['status']=='needs_configuration'
  assert conn.execute('SELECT count(*) AS n FROM ca_youtube_generation_calls').fetchone()['n']==0
  assert worker.run(conn)['results']==[]
  conn.execute("UPDATE ca_youtube_videos SET status='transcript_ready',next_attempt_at=now()")
  monkeypatch.setattr(yt,'generate',lambda *args:(yt.validate_generated(PAYLOAD,CUES),'synthetic',1))
  assert worker.run(conn)['results'][0]['status']=='draft_ready'
  assert worker.run(conn)['results']==[]

def test_owner_private_gates_and_cms_export(client,actor,seeded):
 conn,digest=seeded
 draft=worker.save_generated(conn,VID,digest,yt.validate_generated(PAYLOAD,CUES),'synthetic-model')
 url='/api/current-affairs/automation'
 client.cookies.clear()
 assert client.get(url).status_code==401
 assert client.get(url,headers=actor('author')).status_code==403
 assert client.get(url,headers=actor('reviewer1')).status_code==403
 owner=actor('owner');r=client.get(url,headers=owner);assert r.status_code==200 and r.headers['cache-control']=='private, no-store'
 assert 'cues' not in r.text and 'synthetic-key' not in r.text
 assert client.get(url+'/videos/'+VID,headers=owner).json()['transcript']['cues']==CUES
 before=conn.execute('SELECT md5(string_agg(id,\',\' ORDER BY id)) AS hash FROM canonical_questions').fetchone()['hash']
 decision=url+'/drafts/'+draft+'/decision';body={'action':'material_draft','note':'Synthetic private handoff for automated test.'}
 r=client.post(decision,headers=owner,json=body);assert r.status_code==200,r.text
 material=r.json()['material_id'];assert r.json()['published'] is False
 assert client.post(decision,headers=owner,json=body).json()['material_id']==material
 row=conn.execute('SELECT status,published_revision FROM materials WHERE id=%s',(material,)).fetchone();assert row['status']=='draft' and row['published_revision'] is None
 payload=conn.execute('SELECT payload FROM material_revisions WHERE material_id=%s',(material,)).fetchone()['payload']
 assert payload['blocks'][2]['url']==yt.source_url(VID,10)
 assert conn.execute('SELECT md5(string_agg(id,\',\' ORDER BY id)) AS hash FROM canonical_questions').fetchone()['hash']==before
 assert client.get('/api/materials/'+material).status_code==404
 assert client.post(url+'/videos/'+VID+'/retry',headers=owner,json={'mode':'captions'}).json()['queued']
 missing={k:v for k,v in owner.items() if k.lower()!='x-review-csrf'}
 assert client.post(url+'/videos/'+VID+'/retry',headers=missing,json={'mode':'captions'}).status_code==403
 assert client.post(url+'/videos/'+VID+'/retry',headers=owner,content=b'x'*33000).status_code==413

def test_learner_mobile_boundary():
 from app.services.mobile_identity import allowed
 for method in ['GET','POST']:
  assert not allowed(method,'/api/current-affairs/automation')
  assert not allowed(method,'/api/current-affairs/automation/videos/'+VID)

def test_free_quota_defers_without_paid_fallback(seeded,database,monkeypatch):
 import psycopg
 from psycopg.rows import dict_row
 monkeypatch.setattr(yt,'fetch_feed',lambda _:[])
 def unavailable(*args):raise yt.ProviderDeferred('OpenCode free usage limit reached (429)')
 monkeypatch.setattr(yt,'generate',unavailable)
 with psycopg.connect('dbname='+database[0],autocommit=True,row_factory=dict_row) as conn:
  assert worker.run(conn)['results'][0]['status']=='quota_wait'
  row=conn.execute('SELECT next_attempt_at>now() AS deferred FROM ca_youtube_videos WHERE id=%s',(VID,)).fetchone()
  assert row['deferred']
  assert worker.run(conn)['results']==[]

@pytest.mark.parametrize('output,outcome',[
 ({'type':'text','part':{'type':'text','text':json.dumps(PAYLOAD)}},'success'),
 ({'type':'error','error':{'type':'provider.quota','message':'Free usage limit reached','status':429}},'quota'),
 ({'type':'tool_call','part':{'type':'tool','tool':'bash'}},'tool'),
])
def test_opencode_isolated_free_runner(monkeypatch,output,outcome):
 import shutil
 monkeypatch.setattr(shutil,'which',lambda _: '/synthetic/opencode')
 monkeypatch.setenv('CA_LLM_PROVIDER','opencode');monkeypatch.setenv('CA_GENERATION_ENABLED','1')
 monkeypatch.setenv('DATABASE_URL','synthetic-secret-db');monkeypatch.setenv('CA_GEMINI_API_KEY','synthetic-secret-key')
 process=Mock(returncode=1 if outcome=='quota' else 0)
 process.communicate.return_value=(json.dumps(output).encode(),b'')
 def start(command,**kwargs):
  assert '--standalone' in command and '--auto' not in command
  assert command[command.index('--model')+1] in yt.FREE_OPENCODE_MODELS
  assert 'DATABASE_URL' not in kwargs['env'] and 'CA_GEMINI_API_KEY' not in kwargs['env']
  root=Path(kwargs['cwd']);config=json.loads((root/'opencode.json').read_text())
  assert config['permissions']==[{'action':'*','resource':'*','effect':'deny'}]
  assert config['share']=='disabled' and config['snapshots'] is False
  assert json.loads((root/'transcript.json').read_text())['transcript_cues']==CUES
  return process
 start_mock=Mock(side_effect=start);monkeypatch.setattr(yt.subprocess,'Popen',start_mock)
 calls=[]
 if outcome=='success':assert yt.generate('Synthetic title','2026-11-15',CUES,calls.append)[0].facts[0].id=='f1'
 else:
  with pytest.raises(yt.ProviderDeferred if outcome=='quota' else yt.PipelineError):yt.generate('Synthetic title','2026-11-15',CUES,calls.append)
 assert start_mock.call_count==len(calls)==1

def test_worker_global_budget_reserves_before_call(seeded,monkeypatch):
 conn,digest=seeded
 monkeypatch.setattr(yt,'fetch_feed',lambda _:[]);monkeypatch.setenv('CA_DAILY_CALL_LIMIT','1')
 conn.execute("INSERT INTO ca_youtube_generation_calls(video_id,model,status) VALUES(%s,'synthetic','failed')",(VID,))
 def generation(*args):
  args[-1]('synthetic')
  pytest.fail('An exhausted generation budget must stop before provider invocation')
 monkeypatch.setattr(yt,'generate',generation)
 assert worker.run(conn)['results'][0]['status']=='quota_wait'
 assert conn.execute('SELECT count(*) AS n FROM ca_youtube_generation_calls').fetchone()['n']==1

def test_owner_answers_withheld_during_active_mock(client,actor,seeded):
 conn,_=seeded
 conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES('yt-synthetic-mock','owner','ldc',ARRAY['unrelated-question'],600)")
 assert client.get('/api/current-affairs/automation',headers=actor('owner')).status_code==200
 assert client.get('/api/current-affairs/automation/videos/'+VID,headers=actor('owner')).status_code==409
 conn.execute("DELETE FROM mock_sessions WHERE id='yt-synthetic-mock'")

def test_worker_prioritizes_recent_videos_and_stops_quota_batch(seeded,monkeypatch):
 conn,_=seeded;newer='12345678901'
 worker.add_metadata(conn,{'id':newer,'channel_id':CID,'channel':'Synthetic channel','title':'Newest synthetic source','upload_date':'20261116'})
 worker.save_transcript(conn,newer,CUES,'hi',True,'synthetic fixture')
 monkeypatch.setattr(yt,'fetch_feed',lambda _:[]);titles=[]
 def deferred(title,*args):titles.append(title);raise yt.ProviderDeferred('Synthetic provider-wide free quota refusal')
 monkeypatch.setattr(yt,'generate',deferred)
 result=worker.run(conn)
 assert titles==['Newest synthetic source']
 assert len(result['results'])==1 and result['results'][0]['video']==newer
 assert conn.execute('SELECT status FROM ca_youtube_videos WHERE id=%s',(VID,)).fetchone()['status']=='transcript_ready'
