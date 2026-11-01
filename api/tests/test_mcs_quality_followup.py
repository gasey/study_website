"""Checked-source preparation has strict predecessor and provenance guards."""
import copy,importlib.util,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('quality_followup',ROOT/'scripts/prepare-mcs-quality-followup.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
packet=json.loads(m.PACKET.read_text())


def test_packet_preserves_unresolved_cases_and_correct_printed_choices():
    items={i['appearance_id']:i for i in packet['items']}
    assert len(items)==39 and sum(i['decision']=='retain-unresolved-source'for i in items.values())==4
    assert items['dc3b10001ee119b7440e']['transcription_patch']['options']==['45','36','25','18']
    assert items['03bdbed06710cd55413d']['transcription_patch']['options']==['10','23','18','15']
    assert items['03bdbed06710cd55413d']['answer_draft']['answer_index']==3
    for i in items.values():
        assert i['expected_source']['answerIndex'] is None
        assert 'answerIndex'not in i['transcription_patch'] and 'answerSource'not in i['transcription_patch']
        if i['decision']=='retain-unresolved-source':assert 'answer_draft'not in i
        if i.get('answer_draft',{}).get('mode')=='official':
            assert 'Recovered_MCS'not in i['paper_id'] and i['answer_draft']['key']['letter']=='ABCD'[i['answer_draft']['answer_index']]


def test_phase_order_refuses_to_clear_unrepaired_sources(monkeypatch):
    item=copy.deepcopy(packet['items'][0])
    current={'id':item['appearance_id'],'paperId':item['paper_id'],'answerIndex':None,'sourceDefect':item['source_defect']}
    monkeypatch.setattr(m,'validate_item',lambda *_:None)
    monkeypatch.setattr(m,'record',lambda _:item['expected_source'])
    with pytest.raises(ValueError,match='predecessor'):
        m.prepare('defect',{'items':[item]},{'questions':[current]})
    monkeypatch.setattr(m,'record',lambda _:item['post_transcription_source'])
    request=m.prepare('defect',{'items':[item]},{'questions':[current]})
    assert request['items'][0]['proposal']['patch']['sourceDefect']is None
    assert len(request['items'][0]['proposal']['patch']['disputeNote'])>=20
    with pytest.raises(ValueError,match='predecessor'):
        m.prepare('answers',{'items':[item]},{'questions':[current]})


def test_transcription_omits_unchanged_nullable_markup(monkeypatch):
    item=copy.deepcopy(next(i for i in packet['items'] if i['transcription_patch'].get('options')))
    item['expected_source']['optionsMarkup']=None
    item['transcription_patch']['optionsMarkup']=None
    current={'id':item['appearance_id']}
    monkeypatch.setattr(m,'validate_item',lambda *_:None)
    monkeypatch.setattr(m,'record',lambda _:item['expected_source'])
    monkeypatch.setattr(m,'digest',lambda _:item['baseline_sha256'])
    request=m.prepare('transcription',{'items':[item]},{'questions':[current]})
    patch=request['items'][0]['proposal']['patch']
    assert 'optionsMarkup' not in patch
    assert patch['options']==item['transcription_patch']['options']


def test_recovered_answers_remain_unofficial_and_transcription_is_source_only(monkeypatch):
    item=copy.deepcopy(packet['items'][0]);current={'id':item['appearance_id'],'paperId':item['paper_id'],'answerIndex':None,'sourceDefect':item['source_defect']}
    monkeypatch.setattr(m,'validate_item',lambda *_:None)
    current['sourceDefect']=None
    monkeypatch.setattr(m,'record',lambda _:item['post_transcription_source'])
    request=m.prepare('answers',{'items':[item]},{'questions':[current]})
    answer=request['repairs'][0]
    assert answer['mode']=='verified' and 'document_id'not in answer
    assert answer['explanation'] and 'sourceDefect'not in answer['expected_source']


def test_mathematical_checks_reproduce_the_reviewed_choices():
    from fractions import Fraction
    assert Fraction(1,12)-Fraction(1,30)==Fraction(1,20)
    assert 140/Fraction(35,100)==400
    assert (10*105+20*120)//30==115
    assert 5*65-2*81-2*38==87
    assert Fraction(17+15+16,80)==Fraction(3,5)
    assert Fraction(54,1)/(Fraction(18,100)*Fraction(5,6))==360
    assert sum(21-3*n for n in range(15))==0
    assert sum(1 for n in range(11,300)if n%4==3)==73
    assert [n for n in range(10,100)if n==4*(n//10+n%10)and n==2*(n//10)*(n%10)]==[36]
    assert [k for k in [1,2,5]if (5465*(604+10*k))%15==0]==[2,5]
    assert 4**3+2**3+1**3==73


def test_existing_explanations_retain_official_answer_and_do_not_overwrite_other_work():
    drafts=packet['existing_explanation_drafts']
    assert len(drafts)==4
    for d in drafts:
        assert d['expected_source']['answerSource']=='official'
        assert d['expected_source']['answerIndex']==d['existing_answer_index']
        assert d['expected_source']['options'][d['existing_answer_index']]==d['answer_text']
        assert not d['expected_source'].get('explanation')
        assert d['key']['letter']=='ABCD'[d['existing_answer_index']]
