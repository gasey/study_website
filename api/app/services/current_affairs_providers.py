"""Explicit free-only providers. No model/provider fallthrough or paid upgrade."""
import json,os,re,math
import requests
from pydantic import Field,model_validator
from . import youtube_current_affairs as yt

FREE_GEMINI_MODELS=frozenset({'gemini-3.8-flash'})

def gemini_settings():
 model=os.environ.get('CA_GEMINI_MODEL','gemini-3.8-flash')
 key=os.environ.get('CA_GEMINI_API_KEY','')
 if os.environ.get('CA_GENERATION_ENABLED')!='1' or not key:raise yt.ConfigurationError('Gemini Free is awaiting its private API key and enable setting')
 if os.environ.get('CA_GEMINI_FREE_PROJECT')!='1':raise yt.ConfigurationError('Gemini requires a billing-disabled Free-tier project confirmation')
 if model not in FREE_GEMINI_MODELS:raise yt.ConfigurationError('This Gemini model is not in the checked free-model allowlist')
 return key,model

def supadata_settings():
 if os.environ.get('CA_CAPTION_PROVIDER','yt-dlp')!='supadata':raise yt.ConfigurationError('Supadata native captions are not selected')
 key=os.environ.get('CA_SUPADATA_API_KEY','')
 if not key:raise yt.ConfigurationError('Supadata Free is awaiting its private API key')
 try:cap=int(os.environ.get('CA_SUPADATA_MONTHLY_LIMIT','90'))
 except ValueError:raise yt.ConfigurationError('Supadata monthly limit must be an integer') from None
 if not 1<=cap<=100:raise yt.ConfigurationError('Supadata monthly limit must be between 1 and 100 credits')
 return key,cap

def _json_get(url,headers,params=None):
 try:
  with requests.get(url,headers=headers,params=params,timeout=(5,40),allow_redirects=False,stream=True) as response:
   if response.status_code in {402,429,503}:raise yt.CaptionDeferred('Supadata free capacity or credits are unavailable; no upgrade attempted')
   if response.status_code==206:raise yt.CaptionUnavailable('Supadata has no native transcript for this video; AI transcription is disabled')
   if response.status_code!=200:raise yt.PipelineError('Supadata returned HTTP '+str(response.status_code))
   parts=[];size=0
   for part in response.iter_content(16384):
    size+=len(part)
    if size>yt.MAX_CAPTION_BYTES:raise yt.PipelineError('Supadata response exceeds the caption size limit')
    parts.append(part)
   return json.loads(b''.join(parts))
 except requests.RequestException:raise yt.PipelineError('Supadata is unavailable') from None
 except (ValueError,TypeError):raise yt.PipelineError('Supadata returned invalid JSON') from None

def supadata_captions(vid,languages,before_call):
 key,_=supadata_settings();headers={'x-api-key':key}
 # Account inspection is metadata-only. A paid plan is rejected before transcript use.
 account=_json_get('https://api.supadata.ai/v1/me',headers)
 if str(account.get('plan','')).strip().lower()!='free':raise yt.ConfigurationError('Only the Supadata Free plan is accepted; paid plans are blocked')
 try:
  maximum=float(account.get('maxCredits',0));used=float(account.get('usedCredits',0))
  if not all(math.isfinite(x) and x>=0 for x in [maximum,used]):raise ValueError()
 except (ValueError,TypeError):raise yt.PipelineError('Supadata account credit metadata is invalid') from None
 remaining=maximum-used
 if remaining<1:raise yt.CaptionDeferred('Supadata free credits are exhausted; no upgrade attempted')
 before_call()
 language=next((x.removesuffix('-orig') for x in languages if re.fullmatch(r'[A-Za-z-]{2,20}',x)),'hi')
 data=_json_get('https://api.supadata.ai/v1/transcript',headers,{'url':yt.source_url(vid),'mode':'native','text':'false','lang':language})
 content=data.get('content')
 if not isinstance(content,list) or not content:raise yt.CaptionUnavailable('Supadata did not return timestamped native captions')
 rows=[]
 try:
  for item in content:
   text=re.sub(r'\s+',' ',item['text']).strip()
   if text:rows.append(yt.Cue(id=len(rows),start=float(item['offset'])/1000,duration=float(item['duration'])/1000,text=text).model_dump())
  if not rows or len(rows)>20000 or sum(len(x['text']) for x in rows)>yt.MAX_TRANSCRIPT_CHARS:raise ValueError()
  if any(b['start']<a['start'] for a,b in zip(rows,rows[1:])):raise ValueError()
  language=str(data.get('lang',''))
  if not re.fullmatch(r'[A-Za-z0-9-]{2,20}',language):raise ValueError()
 except (ValueError,TypeError,KeyError):raise yt.PipelineError('Supadata native caption shape/timestamps failed validation') from None
 # The API does not identify whether the original captions were automatic/manual.
 return rows,language,None

class VideoEvidence(yt.Strict):
 cues:list[yt.Cue]=Field(min_length=1,max_length=30)
 draft:yt.Generated
 @model_validator(mode='after')
 def references(self):
  rows=[x.model_dump() for x in self.cues]
  if len({x['id'] for x in rows})!=len(rows):raise ValueError('Video evidence IDs must be distinct')
  if any(b['start']<a['start'] for a,b in zip(rows,rows[1:])):raise ValueError('Video evidence timestamps must be ordered')
  yt.validate_generated(self.draft.model_dump(),rows)
  return self

def gemini_video(vid,title,published_at,before_call):
 if os.environ.get('CA_VIDEO_INPUT')!='gemini_url' or os.environ.get('CA_LLM_PROVIDER')!='gemini':raise yt.ConfigurationError('Direct Gemini video analysis is not selected')
 key,model=gemini_settings();url=yt.source_url(vid)
 prompt=yt.SYSTEM_PROMPT+'''\nAnalyze the supplied public video. Return an object with cues and draft. Cues are at most 30 concise model-produced evidence paraphrases, each with integer id, numeric start and duration in seconds, and text. Cite an observed time, not an invented transcript timestamp. The draft has the normal summary/facts/mcqs/flashcards/warnings shape, with cue_ids referencing these cues. These paraphrases are not literal publisher captions. Include uncertainty; do not generate details from the title if you cannot access the video. A warning is not permission to fabricate evidence.'''
 before_call(model)
 try:
  response=requests.post('https://generativelanguage.googleapis.com/v1beta/interactions',headers={'x-goog-api-key':key,'Api-Revision':'2026-05-20'},json={'model':model,'store':False,'system_instruction':prompt,'input':[{'type':'text','text':json.dumps({'title':title,'video_published_at':published_at},ensure_ascii=False)},{'type':'video','uri':url}],'response_format':{'type':'text','mime_type':'application/json','schema':VideoEvidence.model_json_schema()},'generation_config':{'temperature':0.2,'max_output_tokens':10000}},timeout=(5,150),allow_redirects=False)
  if response.status_code in {429,503}:raise yt.ProviderDeferred('Gemini Free video quota/capacity is unavailable; no paid fallback')
  if response.status_code!=200:raise yt.PipelineError('Gemini video analysis returned HTTP '+str(response.status_code))
  if len(response.content)>250000:raise yt.PipelineError('Gemini video response exceeds the limit')
  data=response.json()
  if data.get('status')!='completed':raise yt.PipelineError('Gemini video analysis did not complete')
  parts=[]
  for step in data.get('steps',[]):
   if 'tool' in str(step.get('type','')):raise yt.PipelineError('Unexpected tool step in video analysis')
   for part in step.get('content',[]):
    if part.get('type')=='text':parts.append(part.get('text',''))
  result=VideoEvidence.model_validate_json(''.join(parts))
  result.draft.warnings=['Video evidence is model-produced analysis, not downloaded captions or independently verified facts.',*result.draft.warnings][:15]
  return [c.model_dump() for c in result.cues],result.draft,model
 except requests.RequestException:raise yt.PipelineError('Gemini video API is unavailable') from None
 except (ValueError,TypeError,KeyError):raise yt.PipelineError('Gemini video evidence/output failed validation; no draft saved') from None

def public_config():
 try:gemini_settings();gemini=True
 except yt.ConfigurationError:gemini=False
 try:_,cap=supadata_settings();supadata=True
 except yt.ConfigurationError:cap=90;supadata=False
 generation=yt.generation_config()
 return {'generation_ready':generation['configured'],'generation_model':generation['model'],'free_only':True,'gemini_ready':gemini,'gemini_model':os.environ.get('CA_GEMINI_MODEL','gemini-3.8-flash'),'caption_provider':os.environ.get('CA_CAPTION_PROVIDER','yt-dlp'),'supadata_ready':supadata,'supadata_monthly_limit':cap,'video_input':os.environ.get('CA_VIDEO_INPUT','captions'),'source_generation_enabled':os.environ.get('CA_SOURCE_GENERATION_ENABLED')=='1'}
