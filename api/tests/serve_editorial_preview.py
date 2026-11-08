#!/usr/bin/env python3
"""Loopback-only synthetic UI fixture. No production accounts or writes."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import json,mimetypes
ROOT=Path(__file__).resolve().parents[2]
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def send(self,value,status=200):
  body=json.dumps(value).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
 def do_GET(self):
  path=urlsplit(self.path).path
  if path=='/api/auth/session':return self.send({'authenticated':True,'state':'active','csrf':'synthetic'})
  if path=='/api/me/progress':return self.send({'answered':0,'correct':0})
  if path=='/api/auth/me':return self.send({'id':'synthetic','handle':'Synthetic reviewer','plan_code':'free','role':'learner'})
  if path=='/api/review/session':return self.send({'user_id':'synthetic','csrf':'synthetic','grants':[{'role':'owner','subject_id':None}],'mfa_required':False})
  if path=='/api/editorial/assignments':return self.send({'items':[{'id':'synthetic','collection_id':'udc','title':'Synthetic UDC rehearsal','state':'active','version':1,'papers':1}]})
  if path=='/api/editorial/manage':return self.send({'items':[{'id':'pending','collection_id':'combined-prelims','title':'Synthetic Prelims','email':'reviewer@example.test','state':'pending','version':1,'account_exists':False}]})
  if path=='/api/editorial/assignments/synthetic/papers':return self.send({'items':[{'id':'synthetic-paper','exam_name':'Synthetic UDC source comparison','year':2026,'questions':1,'source_pdf_url':None}]})
  if path=='/api/editorial/assignments/synthetic/questions':return self.send({'items':[{'appearance_id':'synthetic-appearance','canonical_id':'synthetic-question','qnum':'1','page':1,'question':'Synthetic test: which number is equal to 2 + 2?','answer_status':'needs-review','type':'mcq','previous_check':None}],'total':1,'offset':0})
  if path=='/api/review/questions/synthetic-question':return self.send({'baseline_token':'a'*64,'record':{'id':'synthetic-appearance','paperId':'synthetic-paper','type':'mcq','question':'Synthetic test: which number is equal to 2 + 2?','options':['3','4','5','6'],'answerIndex':1,'answerSource':'derived','answerKeyRef':None,'explanation':'Synthetic fixture only: adding two and two gives four.','qnum':'1','page':1,'classification':{'subject_id':'mathematics'}},'paper':{'id':'synthetic-paper','title':'Synthetic UDC source comparison','year':2026,'series':None,'source_pdf_url':None},'documents':[]})
  if path.startswith('/api/'):return self.send({'items':[],'total':0,'unread':0})
  file=ROOT/'web/dist'/path.lstrip('/')
  if not file.is_file():file=ROOT/'web/dist/index.html'
  data=file.read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(file.name)[0]or'application/octet-stream');self.end_headers();self.wfile.write(data)
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))) or '{}')
  if urlsplit(self.path).path=='/api/editorial/assignments/synthetic/checks':
   if body.get('outcome')=='checked' and not all(body.get(k)for k in ('source_checked','options_checked','answer_checked','explanation_checked')):return self.send({'detail':'Confirm all checks'},422)
   return self.send({'id':1,'message':'Synthetic check saved; no live data changed.'})
  return self.send({'detail':'This preview cannot create accounts, activate access or publish content.'},403)
ThreadingHTTPServer(('127.0.0.1',5197),Handler).serve_forever()
