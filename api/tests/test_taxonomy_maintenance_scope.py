from types import SimpleNamespace
from app.services.bank_review import maintenance_scope_allows


def scope(**changes):
    return dict(owner_id='owner',canonical_ids=frozenset(['q']),
                authorization='Owner explicitly authorizes this exact taxonomy run.',
                purpose='owner-taxonomy-publication',**changes)


def proposal(kind='taxonomy',patch=None):
    return SimpleNamespace(canonical_id='q',kind=kind,patch=patch or {'classification':{'subject_id':'english'}})


def test_taxonomy_scope_requires_specific_purpose_and_exact_target():
    s=scope()
    assert maintenance_scope_allows(s,'owner',proposal())
    assert not maintenance_scope_allows(s,'other',proposal())
    assert not maintenance_scope_allows({**s,'purpose':'old-source-run'},'owner',proposal())
    assert not maintenance_scope_allows({**s,'canonical_ids':{'other'}},'owner',proposal())


def test_taxonomy_scope_is_bounded_and_cannot_change_content_or_answers():
    s=scope()
    assert not maintenance_scope_allows({**s,'canonical_ids':set(map(str,range(101)))|{'q'}},'owner',proposal())
    assert not maintenance_scope_allows(s,'owner',proposal(patch={'answerIndex':0}))
    assert not maintenance_scope_allows(s,'owner',proposal(patch={'difficulty':'easy'}))
    assert not maintenance_scope_allows(s,'owner',proposal(kind='new_question'))


def test_existing_source_scopes_remain_usable_without_enabling_taxonomy():
    s={**scope(),'purpose':None}
    assert maintenance_scope_allows(s,'owner',proposal(kind='explanation',patch={'explanation':'Source-backed explanation'}))
    assert not maintenance_scope_allows(s,'owner',proposal())
