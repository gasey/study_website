import csv,importlib.util,json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('adjudication',ROOT/'scripts/prepare-module-adjudication.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

@pytest.fixture
def packet_inputs(tmp_path):
 (tmp_path/'bank').mkdir();(tmp_path/'pdfs').mkdir();(tmp_path/'pdfs/source.pdf').write_bytes(b'Synthetic source hash fixture only')
 q={'id':'appearance-test','paperId':'paper-test','type':'mcq','question':'What is 2 plus 2?','options':['3','4'],'answerIndex':0,'answerSource':'derived','page':1,'qnum':1,'classifications':[{'is_primary':True,'subject_id':'mathematics'}]}
 bank=tmp_path/'bank/bank.json';bank.write_text(json.dumps({'questions':[q],'papers':[{'id':'paper-test','pdfPath':'pdfs/source.pdf'}]}))
 source=tmp_path/'module.json';source.write_text(json.dumps({'questions':[{**q,'id':i,'answerIndex':1} for i in ['old-one','old-two']]}))
 cw=tmp_path/'crosswalk.csv'
 with cw.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['legacy_question_id','status']);w.writeheader();w.writerows([{'legacy_question_id':i,'status':'unmatched'} for i in ['old-one','old-two']])
 manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps(mod.imp.prepare('udc-ldc',source,cw,bank)))
 a={'appearanceId':q['id'],'expectedBankAnswerIndex':0,'expectedBankAnswerSource':'derived','expectedIdentitySha256':mod.digest(mod.imp.identity(q)),'outcome':'propose_answer','answerIndex':1,'rationale':'Adding two to two gives four, the second printed option. Independently review this proposed derived correction.','sources':[]}
 return bank,manifest,a

def test_deduplicated_prepared_proposals_and_no_bank_writes(packet_inputs):
 bank,manifest,a=packet_inputs;before=bank.read_bytes();p=mod.prepare(bank,[manifest],[a])
 assert p['summary']=={'moduleRows':2,'uniqueAppearances':1,'outcomes':{'propose_answer':1},'preparedProposals':1}
 r=p['claims'][0];assert len(r['moduleReferences'])==2
 proposal=r['proposals'][0];assert proposal['status']=='prepared_not_submitted' and proposal['payload']['patch']['answerSource']=='derived'
 assert len(proposal['payload']['evidence'])==3 and mod.digest(proposal['payload'])==proposal['payloadSha256']
 unsigned=dict(p);unsigned.pop('packetSha256');assert mod.digest(unsigned)==p['packetSha256'] and bank.read_bytes()==before

def test_unknowns_retains_and_defects_do_not_invent_answers(packet_inputs):
 bank,manifest,a=packet_inputs
 p=mod.prepare(bank,[manifest],[]);assert p['held'][0]['outcome']=='needs_source_review' and not p['held'][0]['proposals']
 a.update(outcome='retain_bank',answerIndex=0);assert not mod.prepare(bank,[manifest],[a])['claims'][0]['proposals']
 a.update(outcome='source_defect',answerIndex=None);r=mod.prepare(bank,[manifest],[a])['held'][0]
 assert r['proposals'][0]['payload']['kind']=='defect' and 'answerIndex' not in r['proposals'][0]['payload']['patch']

def test_stale_tampered_and_duplicate_inputs_rejected(packet_inputs):
 bank,manifest,a=packet_inputs
 with pytest.raises(ValueError,match='Duplicate research'):mod.prepare(bank,[manifest],[a,a])
 a['expectedIdentitySha256']='0'*64
 with pytest.raises(ValueError,match='identity changed'):mod.prepare(bank,[manifest],[a])
 m=json.loads(manifest.read_text());m['items'][0]['legacy']['question']='Tampered';manifest.write_text(json.dumps(m))
 with pytest.raises(ValueError,match='hash mismatch'):mod.prepare(bank,[manifest],[])
