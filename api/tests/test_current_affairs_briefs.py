"""Synthetic official-page/brief tests. No provider requests or production DB."""
import copy,importlib.util,json
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import Mock
import psycopg,pytest
from psycopg.rows import dict_row
from app.services import current_affairs_sources as sources,current_affairs_pages as pages,current_affairs_briefs as briefs,youtube_current_affairs as yt
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('brief_test_worker',ROOT/'scripts/youtube-current-affairs.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
PIB='https://www.pib.gov.in/PressReleaseDetail.aspx?PRID=999999&reg=1&lang=1'
DIPR='https://dipr.mizoram.gov.in/post/synthetic-release'
BODY='Synthetic policy evidence only. A fictional programme supports education in a fictional district; this is not a real current-affairs fact.'
PIB_HTML=('<h1 id="Titleh2">Synthetic national policy</h1><div id="PrDateTime">Posted On: 16 NOV 2026 12:00PM by PIB Delhi</div><div id="pibReleaseBody"><p>'+BODY+'</p><script>untrusted command</script><table><tr><td>Year<p>2026</p></td><td>Amount<p>100</p></td></tr></table></div>').encode()
DIPR_HTML=('<div class="post-title">Synthetic Mizoram policy</div><div class="post-content"><p>'+BODY+'</p><div id="attachment-meta">Loading attachment...</div></div><div class="post-meta">Dated: 15<sup>th</sup> Nov 26 4:56 PM</div>').encode()
PAYLOAD={'summary':'Synthetic brief summary, unverified and for private workflow testing only.','facts':[{'id':'f1','text':'Synthetic programme supports education in a fictional district.','topic':'Synthetic governance','cue_ids':[0]}],'mcqs':[{'id':'q1','question':'Which sector does this fictional programme support?','options':['Education','Sports','Banking','Transport'],'correct_index':0,'explanation':'The synthetic source fixture identifies education as the sector.','fact_ids':['f1']}],'flashcards':[{'front':'Which fictional sector is supported?','back':'Education, according to the synthetic source.','fact_ids':['f1']}],'warnings':['Synthetic fixture; no verification or publication.']}
NOW=datetime(2026,11,16,8,tzinfo=timezone.utc)

@pytest.fixture(autouse=True)
def clean(database,monkeypatch):
 for key in ['CA_GENERATION_ENABLED','CA_GEMINI_API_KEY','CA_GEMINI_MODEL','CA_GEMINI_FREE_PROJECT','CA_SOURCE_GENERATION_ENABLED','CA_LLM_PROVIDER','CA_BRIEFS_ENABLED','CA_CAPTION_PROVIDER']:
  monkeypatch.delenv(key,raising=False)
 conn=psycopg.connect('dbname='+database[0],autocommit=True,row_factory=dict_row)
 conn.execute('TRUNCATE ca_brief_drafts,ca_brief_inputs,ca_briefs,ca_source_events,ca_source_drafts,ca_source_revisions,ca_source_items,ca_caption_calls,ca_youtube_events,ca_youtube_generation_calls,ca_youtube_runs,ca_youtube_drafts,ca_youtube_transcripts,ca_youtube_videos,ca_youtube_channels RESTART IDENTITY')
 conn.execute('UPDATE ca_source_feeds SET enabled=false,last_error=NULL,checked_at=NULL')
 yield conn
 conn.execute("DELETE FROM mock_sessions WHERE id='brief-synthetic-mock'");conn.close()

def capture(conn):
 row=pages.parse_article(PIB_HTML,PIB,'pib-releases');sources.save_item(conn,'pib-releases',row)
 conn.execute("UPDATE ca_source_feeds SET enabled=true WHERE id='pib-releases'")
 briefs.prepare(conn,NOW)
 return conn.execute('SELECT b.*,i.payload inputs FROM ca_briefs b JOIN ca_brief_inputs i ON i.brief_id=b.id AND i.content_hash=b.current_hash ORDER BY b.cadence LIMIT 1').fetchone()

def test_page_collectors_preserve_body_tables_dates_and_language():
 pib=pages.parse_article(PIB_HTML,PIB,'pib-releases');dipr=pages.parse_article(DIPR_HTML,DIPR,'mizoram-dipr')
 assert pib['published_at'].isoformat()=='2026-11-16T06:30:00+00:00'
 assert dipr['published_at'].isoformat()=='2026-11-15T11:26:00+00:00'
 assert 'assumption' in pib['timezone_basis'] and dipr['language']=='und'
 assert pib['cues'][1]['text']=='Year 2026 | Amount 100'
 assert 'untrusted command' not in str(pib['cues'])
 assert 'Loading attachment' not in str(dipr['cues'])
 with pytest.raises(yt.PipelineError,match='date'):pages.parse_article(PIB_HTML.replace(b'16 NOV 2026',b'invalid'),PIB,'pib-releases')
 with pytest.raises(yt.PipelineError,match='structure'):pages.parse_article(PIB_HTML.replace(b'pibReleaseBody',b'changedBody'),PIB,'pib-releases')

@pytest.mark.parametrize('bad',['http://www.pib.gov.in/PressReleaseDetail.aspx?PRID=999999','https://evil.test/PressReleaseDetail.aspx?PRID=999999','https://www.pib.gov.in:444/PressReleaseDetail.aspx?PRID=999999','https://www.pib.gov.in/PressReleaseDetail.aspx?PRID=999999&redirect=https://evil.test','https://www.pib.gov.in/PressReleaseDetail.aspx?PRID=999999&PRID=111111'])
def test_page_url_boundary(bad):
 with pytest.raises(yt.PipelineError):pages.approved_url(bad,'pib-releases')

def test_discovery_is_bounded_deduplicated_and_not_empty_success():
 html=''.join('<a href="/PressReleaseDetail.aspx?PRID='+str(i)+'">Synthetic</a>' for i in range(999990,1000010))
 assert len(pages.discover((html+html).encode(),'pib-releases'))==8
 with pytest.raises(yt.PipelineError,match='no approved'):pages.discover(b'<h1>Changed structure</h1>','pib-releases')

def test_partial_article_failure_keeps_valid_capture(monkeypatch):
 def get(url,feed_id,listing=False):
  if listing:return b'<a href="/post/synthetic-release">Good</a><a href="/post/bad-release">Bad</a>'
  if 'bad-release' in url:raise yt.PipelineError('Synthetic unavailable article')
  return DIPR_HTML
 monkeypatch.setattr(pages,'get_page',get);rows=pages.fetch_articles('mizoram-dipr')
 assert len(rows)==2 and rows[0]['cues'] and rows[1]['collection_error']

def test_page_byte_and_redirect_limits(monkeypatch):
 response=Mock(status_code=302);response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
 get=Mock(return_value=response);monkeypatch.setattr(pages.requests,'get',get)
 with pytest.raises(yt.PipelineError,match='302'):pages.get_page(PIB,'pib-releases')
 assert get.call_args.kwargs['allow_redirects'] is False
 response.status_code=200;response.iter_content.return_value=[b'x'*(pages.LIMIT+1)]
 with pytest.raises(yt.PipelineError,match='byte'):pages.get_page(PIB,'pib-releases')

def test_snapshot_exact_dedup_retains_both_citations_and_whole_source_limit():
 a={'id':'a','kind':'official','title':'Synthetic Mizoram scheme','content_hash':'a'*64,'source_url':PIB,'published_at':NOW,'cues':[{'id':0,'text':BODY}],'language':'en','evidence_kind':'official_release'}
 b={**a,'id':'b','kind':'video','source_url':yt.source_url('abcdefghijk'),'cues':[{'id':3,'start':15,'text':BODY}]}
 packet=briefs.snapshot([a,b]);assert len(packet['units'])==1 and len(packet['units'][0]['source_refs'])==2
 assert packet['coverage']['exact_duplicate_passages']==1
 many=briefs.snapshot([{**a,'id':str(i)} for i in range(12)])
 assert len(many['sources'])==8 and len(many['coverage']['omitted'])==4
 huge={**a,'id':'huge','cues':[{'id':0,'text':'x'*80001}]};assert briefs.snapshot([huge])['sources']==[]
 assert briefs.relevance({**a,'title':'Money Market Operations'})['priority']<briefs.relevance(a)['priority']

def test_daily_weekly_boundaries_and_revision_idempotence(clean):
 brief=capture(clean);assert clean.execute('SELECT count(*) n FROM ca_briefs').fetchone()['n']==2
 briefs.prepare(clean,NOW);assert clean.execute('SELECT count(*) n FROM ca_brief_inputs').fetchone()['n']==2
 assert brief['period_start'].isoformat()=='2026-11-16'
 assert clean.execute("SELECT period_start FROM ca_briefs WHERE cadence='weekly'").fetchone()['period_start'].isoformat()=='2026-11-10'
 row=pages.parse_article(PIB_HTML.replace(b'Synthetic policy evidence',b'Changed synthetic evidence'),PIB,'pib-releases');sources.save_item(clean,'pib-releases',row);briefs.prepare(clean,NOW)
 assert clean.execute('SELECT count(*) n FROM ca_brief_inputs').fetchone()['n']==4
 # At 18:30 UTC, the India publication day has rolled over.
 briefs.prepare(clean,datetime(2026,11,16,18,30,tzinfo=timezone.utc))
 assert clean.execute("SELECT count(*) n FROM ca_briefs WHERE cadence='daily' AND period_end='2026-11-17'").fetchone()['n']==0

def test_short_table_values_keep_context_and_dipr_keeps_state_topic(clean):
 source={'id':'a','kind':'official','title':'Synthetic release','content_hash':'a'*64,'source_url':PIB,'published_at':NOW,'cues':[{'id':0,'text':'2026 | 100'},{'id':1,'text':'2026 | 100'}]}
 packet=briefs.snapshot([source,{**source,'id':'b'}]);assert len(packet['units'])==4 and packet['coverage']['exact_duplicate_passages']==0
 row=pages.parse_article(DIPR_HTML,DIPR,'mizoram-dipr');row['title']='Synthetic local event with a Mizo title';row['published_at']=NOW;sources.save_item(clean,'mizoram-dipr',row)
 clean.execute("UPDATE ca_source_feeds SET enabled=true WHERE id='mizoram-dipr'");briefs.prepare(clean,NOW)
 inputs=clean.execute("SELECT payload FROM ca_brief_inputs WHERE brief_id='brief_daily_2026-11-16'").fetchone()['payload']
 assert 'Mizoram' in inputs['sources'][0]['relevance']['topics']

def test_worker_collect_only_stages_packets_without_provider_call(clean,monkeypatch):
 capture(clean);monkeypatch.setattr(sources,'fetch_feed',lambda _: [pages.parse_article(PIB_HTML,PIB,'pib-releases')]);post=Mock();monkeypatch.setattr(yt.requests,'post',post)
 result=worker.run(clean,collect_only=True);assert result['status']=='succeeded'
 assert any(r['status']=='brief_collected' for r in result['results']);post.assert_not_called()

def test_brief_generation_shared_budget_and_free_source_kind(clean,monkeypatch):
 capture(clean);clean.execute('UPDATE ca_briefs SET next_attempt_at=now()');monkeypatch.setattr(sources,'fetch_feed',lambda _: [pages.parse_article(PIB_HTML,PIB,'pib-releases')])
 for key,value in {'CA_GENERATION_ENABLED':'1','CA_GEMINI_FREE_PROJECT':'1','CA_GEMINI_API_KEY':'synthetic-key','CA_GEMINI_MODEL':'gemini-3.8-flash','CA_LLM_PROVIDER':'gemini','CA_DAILY_CALL_LIMIT':'1'}.items():monkeypatch.setenv(key,value)
 r=Mock(status_code=200,content=b'{}');r.json.return_value={'candidates':[{'content':{'parts':[{'text':json.dumps(PAYLOAD)}]}}]};post=Mock(return_value=r);monkeypatch.setattr(yt.requests,'post',post)
 result=worker.run(clean,limit=1);assert any(x['status']=='draft_ready' for x in result['results'])
 assert clean.execute('SELECT brief_id FROM ca_youtube_generation_calls').fetchone()['brief_id']
 # Fair scheduling can choose either cadence. Bind the provider request to
 # the actual brief selected, rather than assuming daily wins the first slot.
 cadence=clean.execute('SELECT b.cadence FROM ca_youtube_generation_calls c JOIN ca_briefs b ON b.id=c.brief_id').fetchone()['cadence']
 sent=json.loads(post.call_args.kwargs['json']['contents'][0]['parts'][0]['text'])
 assert sent['source_kind']==f'multi_source_{cadence}_brief'
 worker.run(clean,limit=1);assert post.call_count==1

def test_brief_handoff_private_stale_csrf_assessment_and_mobile(clean,client,actor):
 brief=capture(clean);draft=briefs.save_draft(clean,brief,briefs.validate(PAYLOAD,brief['inputs']),'synthetic-model')
 client.cookies.clear();base='/api/current-affairs/automation'
 assert client.get(base+'/briefs').status_code==401
 assert client.get(base+'/briefs',headers=actor('author')).status_code==403
 owner=actor('owner');assert client.get(base+'/briefs',headers=owner).status_code==200
 assert client.get(base+'/briefs/'+brief['id'],headers=owner).headers['cache-control']=='private, no-store'
 decision=base+'/brief-drafts/'+draft+'/decision';body={'action':'material_draft','note':'Synthetic source-bound brief handoff note.'}
 assert client.post(decision,json=body).status_code==403
 owner=actor('owner');result=client.post(decision,headers=owner,json=body);assert result.status_code==200,result.text
 material=result.json()['material_id'];assert result.json()['published'] is False
 assert client.post(decision,headers=owner,json=body).json()['material_id']==material
 assert client.get('/api/materials/'+material).status_code==404
 assert clean.execute('SELECT status FROM materials WHERE id=%s',(material,)).fetchone()['status']=='draft'
 old=briefs.save_draft(clean,brief,briefs.validate(PAYLOAD,brief['inputs']),'second-synthetic-model')
 row=pages.parse_article(PIB_HTML.replace(b'Synthetic policy evidence',b'Changed synthetic evidence'),PIB,'pib-releases');sources.save_item(clean,'pib-releases',row)
 # Stale underlying evidence is blocked even before the next packet refresh.
 assert client.post(base+'/brief-drafts/'+old+'/decision',headers=owner,json=body).status_code==409
 clean.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES('brief-synthetic-mock','owner','ldc',ARRAY['unrelated'],600)")
 assert client.get(base+'/briefs/'+brief['id'],headers=owner).status_code==409
 from app.services.mobile_identity import allowed
 assert not allowed('GET',base+'/briefs') and not allowed('POST',decision)

def test_brief_inputs_and_payload_are_runtime_immutable(clean):
 capture(clean)
 assert clean.execute("SELECT has_table_privilege('mpsc','ca_brief_inputs','INSERT') ok").fetchone()['ok']
 assert not clean.execute("SELECT has_table_privilege('mpsc','ca_brief_inputs','UPDATE') ok").fetchone()['ok']
 assert clean.execute("SELECT has_column_privilege('mpsc','ca_brief_drafts','status','UPDATE') ok").fetchone()['ok']
 assert not clean.execute("SELECT has_column_privilege('mpsc','ca_brief_drafts','payload','UPDATE') ok").fetchone()['ok']

def test_worker_time_budget_defers_before_reserving_provider_attempt(clean):
 brief=capture(clean)
 with pytest.raises(yt.ProviderDeferred,match='time budget'):
  worker.reserve_generation(clean,[],'synthetic-model',brief_id=brief['id'],deadline=0)
 assert clean.execute('SELECT count(*) n FROM ca_youtube_generation_calls').fetchone()['n']==0

def test_duplicate_claims_rejected_and_unknown_citations_invalid():
 inputs={'units':[{'id':0,'text':BODY}]};bad=copy.deepcopy(PAYLOAD);bad['facts'].append({**bad['facts'][0],'id':'f2'})
 with pytest.raises(yt.PipelineError,match='duplicate facts'):briefs.validate(bad,inputs)
 bad=copy.deepcopy(PAYLOAD);bad['facts'][0]['cue_ids']=[99]
 with pytest.raises(ValueError):briefs.validate(bad,inputs)
