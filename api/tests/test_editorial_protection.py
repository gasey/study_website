"""Offline integrity/crash tests: synthetic banks, no production data/writes."""
import copy
import json
from pathlib import Path
import pytest
import editorial_protection as ep


@pytest.fixture
def protected(tmp_path):
    root = tmp_path / 'workshop'; (root / 'bank').mkdir(parents=True)
    (root / 'pdfs').mkdir(); (root / 'pdfs/source.pdf').write_bytes(b'synthetic PDF')
    bank = {'papers': [{'id': 'udc', 'sourceFile': 'source.pdf'}, {'id': 'other'}],
            'questions': [{'id': 'a', 'paperId': 'udc', 'question': 'Current human correction', 'options': ['A','B'], 'answerIndex': 1},
                          {'id': 'b', 'paperId': 'other', 'question': 'Unprotected'}]}
    path = root / 'bank/mpsc_bank_v2.json'; ep.atomic(path, bank)
    state_path = tmp_path / 'state.json'; policy = tmp_path / 'policy.json'
    ep.atomic(policy, {'schema': 1, 'required': True, 'state': 'state.json'})
    state = {'schema': 1, 'scopes': {'udc': {'version': 1, 'paper_ids': ['udc']}},
             'expected': ep.snapshot(bank, {'udc'}, root), 'last_publications': []}
    ep.atomic(state_path, state)
    return path, bank, policy, state_path


def test_raw_reparse_cannot_overwrite_human_edit(protected):
    path, bank, policy, state = protected
    candidate = copy.deepcopy(bank); candidate['questions'][0]['answerIndex'] = 0
    with pytest.raises(ValueError, match='stage a proposal'):
        ep.check_candidate(path, candidate, policy)
    assert json.loads(path.read_text()) == bank
    ep.atomic(path, candidate)  # simulate an old tool bypassing its guard
    with pytest.raises(ValueError, match='Unreviewed changes'):
        ep.check_candidate(path, policy_path=policy)  # final sync boundary stops it


@pytest.mark.parametrize('change', ['remove','add','move','rename','paper','duplicate','asset'])
def test_protected_context_and_identity_are_frozen(protected, change):
    path, bank, policy, state = protected
    candidate = copy.deepcopy(bank)
    if change == 'remove': candidate['questions'].pop(0)
    elif change == 'add': candidate['questions'].append({'id':'new','paperId':'udc'})
    elif change == 'move': candidate['questions'][0]['paperId'] = 'other'
    elif change == 'rename': candidate['questions'][0]['id'] = 'renumbered'
    elif change == 'paper': candidate['papers'][0]['sourceFile'] = 'replacement.pdf'
    elif change == 'duplicate': candidate['questions'].append(copy.deepcopy(candidate['questions'][0]))
    elif change == 'asset': (path.parents[1] / 'pdfs/source.pdf').write_bytes(b'replaced scan')
    with pytest.raises(ValueError): ep.check_candidate(path, candidate, policy)


def test_unprotected_work_and_formatting_still_allowed(protected):
    path, bank, policy, state = protected
    candidate = copy.deepcopy(bank); candidate['questions'][1]['question'] = 'Independent AI draft'
    ep.check_candidate(path, candidate, policy)
    path.write_text(json.dumps(bank, sort_keys=True))
    ep.check_candidate(path, policy_path=policy)


def test_missing_baseline_fails_closed(protected):
    path, bank, policy, state = protected; state.unlink()
    with pytest.raises(ValueError, match='baseline is missing'): ep.check_candidate(path, policy_path=policy)


def test_reviewed_publication_crash_recovery_and_next_change(protected):
    path, bank, policy, state = protected
    revised = copy.deepcopy(bank); revised['questions'][0]['question'] = 'Reviewed correction two'
    manifest = {'id':'pub_one','payload': {'kind':'transcription'},'baseline':{'record':{'id':'a'}}}
    ep.prepare_publication(path, bank, revised, [manifest], policy)
    ep.check_candidate(path, policy_path=policy)  # crash before replacement
    ep.atomic(path, revised)
    ep.check_candidate(path, policy_path=policy)  # crash after replacement
    ep.finish_publication(path, policy)
    assert not state.with_suffix('.pending.json').exists()
    assert json.loads(state.read_text())['last_publications'][0]['id']=='pub_one'
    third = copy.deepcopy(revised); third['questions'][0]['question'] = 'Reviewed correction three'
    ep.prepare_publication(path, revised, third, [manifest], policy)
    ep.atomic(path, third); ep.finish_publication(path, policy)
    ep.atomic(path, bank)  # stale restore must not reset human corrections
    with pytest.raises(ValueError, match='Unreviewed changes'): ep.check_candidate(path, policy_path=policy)


def test_unrelated_or_stale_publication_cannot_launder_changes(protected):
    path, bank, policy, state = protected
    revised = copy.deepcopy(bank); revised['questions'][0]['question'] = 'Unreviewed'
    wrong = {'id':'pub_wrong','payload':{'kind':'transcription'},'baseline':{'record':{'id':'b'}}}
    with pytest.raises(ValueError, match='unreviewed protected target'):
        ep.prepare_publication(path, bank, revised, [wrong], policy)
    ep.atomic(path, revised)
    with pytest.raises(ValueError, match='Unreviewed changes'):
        ep.prepare_publication(path, revised, revised, [wrong], policy)


def test_crash_between_protection_commit_and_cleanup(protected):
    path, bank, policy, state = protected
    after = copy.deepcopy(bank); after['questions'][0]['question'] = 'Reviewed'
    m={'id':'pub_one','payload':{'kind':'transcription'},'baseline':{'record':{'id':'a'}}}
    ep.prepare_publication(path, bank, after, [m], policy)
    ep.atomic(path, after)
    pending=json.loads(state.with_suffix('.pending.json').read_text())
    ep.atomic(state, pending['next_state'])
    ep.check_candidate(path, policy_path=policy)
    ep.finish_publication(path, policy)


def test_wrong_pending_bank_never_becomes_new_baseline(protected):
    path, bank, policy, state = protected
    after=copy.deepcopy(bank); after['questions'][0]['question']='Reviewed'
    m={'id':'pub_one','payload':{'kind':'transcription'},'baseline':{'record':{'id':'a'}}}
    ep.prepare_publication(path, bank, after, [m], policy)
    after['questions'][0]['options']=['unexpected']
    ep.atomic(path,after)
    with pytest.raises(ValueError,match='Unreviewed changes'): ep.finish_publication(path,policy)


def test_supported_import_stages_draft_and_leaves_bank_unchanged(protected,monkeypatch):
    path,bank,policy,state=protected
    monkeypatch.setattr(ep,'CANONICAL',path);monkeypatch.setattr(ep,'POLICY',policy)
    candidate=copy.deepcopy(bank);candidate['questions'][0]['question']='Old AI parse'
    before=path.read_bytes()
    with pytest.raises(ValueError,match='Draft saved'):
        ep.write_guarded(path,candidate)
    assert path.read_bytes()==before
    drafts=list((path.parents[1]/'state/parser-drafts').glob('*.json'))
    assert len(drafts)==1
    draft=json.loads(drafts[0].read_text())
    assert draft['status']=='draft-only' and draft['changes'][0]['before']['question']=='Current human correction'


def test_actual_manifest_writer_advances_protection_and_rejects_old_ai(protected,monkeypatch):
    from review_bank_store import apply_manifest,record,sha,digest
    path,bank,policy,state=protected
    monkeypatch.setattr(ep,'CANONICAL',path);monkeypatch.setattr(ep,'POLICY',policy)
    m={'schema':1,'id':'pub_protected','contribution_id':'con_protected','author_id':'synthetic',
       'bank_sha256':sha(path),'baseline':{'record':record(bank['questions'][0])},
       'payload':{'kind':'answer','patch':{'answerIndex':0,'answerSource':'derived','explanation':'Synthetic reviewed correction supports the first option.'},'evidence':[]},'documents':[]}
    receipt=apply_manifest(path,path.parents[1],m,digest(m))
    assert receipt['after']['answerIndex']==0
    assert apply_manifest(path,path.parents[1],m,digest(m))==receipt
    assert json.loads(state.read_text())['last_publications'][0]['id']=='pub_protected'
    with pytest.raises(ValueError,match='stage a proposal'):ep.check_candidate(path,bank,policy)
