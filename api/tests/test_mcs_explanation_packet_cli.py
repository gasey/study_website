"""Selectable checked packets retain the existing exact-source publication guards."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'));s=importlib.util.spec_from_file_location('packet_cli',ROOT/'scripts/prepare-mcs-completion-explanations.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
from review_bank_store import record,digest
@pytest.fixture
def setup(tmp_path,monkeypatch):
 root=tmp_path/'app';bankroot=tmp_path/'workshop';(root/'docs/sources').mkdir(parents=True);(root/'reports').mkdir();(bankroot/'pdfs').mkdir(parents=True);(bankroot/'bank').mkdir();pdf=bankroot/'pdfs/source.pdf';pdf.write_bytes(b'Synthetic original source')
 q=dict(id='source-a',paperId='MCS Combined 2025 synthetic',type='mcq',question='Choose the explicitly stated synthetic fact.',options=['One','Two'],answerIndex=1,answerSource='official',answerKeyRef='preserved-key',qnum=1,page=1,explanation=None,classifications=[dict(subject_id='english',is_primary=True)])
 item=dict(appearance_id=q['id'],canonical_id='cq_fixture',reviewed_raw_record=copy.deepcopy(q),baseline_sha256=digest(q),expected_source=record(q),required_source_patch={},post_source_expected=record(q),source_document=dict(id='doc_fixture',kind='paper',paper_id=q['paperId'],source_file='pdfs/source.pdf',sha256=hashlib.sha256(pdf.read_bytes()).hexdigest()),physical_pdf_page=1,explanation='The source explicitly states the second alternative, which is the preserved keyed choice.',source_review_note='Read the exact source and checked the explanation.')
 packet=root/'docs/sources/new-packet.json';packet.write_text(json.dumps(dict(scope=dict(paper_ids=[q['paperId']]),items=[item])));bankpath=bankroot/'bank/mpsc_bank_v2.json';bankpath.write_text(json.dumps(dict(questions=[q],papers=[dict(id=q['paperId'],year=2025)])))
 output=root/'reports/request.json';monkeypatch.setattr(m,'ROOT',root);monkeypatch.setattr(m,'BANK_ROOT',bankroot);monkeypatch.setattr(sys,'argv',['prepare','--packet',str(packet),'--output',str(output)])
 return packet,output,bankpath

def test_checked_packet_selection_changes_only_explanation(setup):
 packet,output,bankpath=setup;before=bankpath.read_bytes();m.main();req=json.loads(output.read_text());assert len(req['items'])==1 and set(req['items'][0]['proposal']['patch'])=={'explanation'};assert bankpath.read_bytes()==before

def test_checked_packet_selection_does_not_bypass_changed_key(setup):
 _,output,bankpath=setup;bank=json.loads(bankpath.read_text());bank['questions'][0]['answerIndex']=0;bankpath.write_text(json.dumps(bank))
 with pytest.raises(ValueError):m.main()
 assert not output.exists()

def test_untrusted_packet_location_rejected_before_read(setup,monkeypatch):
 packet,output,_=setup;outside=packet.parents[3]/'outside.json';outside.write_text(packet.read_text());monkeypatch.setattr(sys,'argv',['prepare','--packet',str(outside),'--output',str(output)])
 with pytest.raises(SystemExit):m.main()
 assert not output.exists()
