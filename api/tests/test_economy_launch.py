"""Release evidence and live reconciliation launch guards."""


def test_launch_evidence_rejects_missing_stale_sources_and_live_drift(client,actor,database,monkeypatch,tmp_path):
    import hashlib,json
    from app.services import reward_economy as economy
    monkeypatch.setattr(economy,'_API_ROOT',tmp_path)
    target=tmp_path/'evidence.json';monkeypatch.setattr(economy,'_EVIDENCE_PATH',target)
    assert not economy.reconciled_release()
    hashes={}
    for name in economy.RELEASE_FILES:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('isolated artifact')
        hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    # Fixture values are checked here; the real mixed week is settled in
    # test_reward_calibration and packaged by the bounded release preparation.
    evidence={'source_sha256':hashes,'calibration':{'days':7,'heavy':{'study_points':175,'days_to_month':60},
      'average':{'study_points':117,'days_to_month':89.74358974358974},
      'catalog':{'month_points':1500,'week_points':400,'standard_month_paise':10000,'points_per_rupee':15},
      'diagnostics':{key:0 for key in economy.INTEGRITY_FIELDS}},'recovery':{str(i):True for i in range(8)},
      'v5_recovery':{key:True for key in ('write_quarantine','paired_static_restore','purchased_items_preserved',
        'moderated_bios_private','closed_accounts_anonymous','entitlements_preserved','database_guards_preserved')}}
    target.write_text(json.dumps(evidence));assert economy.reconciled_release()
    actor('owner')
    def ready():return next(c['ready'] for c in client.get('/api/admin/bank/reward-feature-gates').json()['checks'] if c['key']=='economy_reconciliation')
    assert ready()
    conn=database[1]
    conn.execute('ALTER TABLE reward_ledger DISABLE TRIGGER enforce_learning_v2')
    try:assert not ready()
    finally:conn.execute('ALTER TABLE reward_ledger ENABLE TRIGGER enforce_learning_v2')
    conn.execute("INSERT INTO reward_daily_counters(user_id,day,xp,points,pillar_points) VALUES('author',CURRENT_DATE,1,0,'{}')")
    assert not ready()
    conn.execute("DELETE FROM reward_daily_counters WHERE user_id='author'")
    assert ready()
    # Cosmetics must participate in the actual launch check, not just the admin
    # report. An orphan negative receipt cannot be masked by clean study caps.
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,points,note) VALUES('author','launch-test-funds','adjustment',100,'Synthetic launch fixture')")
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,points,note) VALUES('author','cosmetic:author:missing','redemption',-25,'Synthetic orphan spend')")
    assert not ready()
    (tmp_path/economy.RELEASE_FILES[0]).write_text('changed after calibration')
    assert not economy.reconciled_release() and not ready()
    target.write_text('{invalid');assert not economy.reconciled_release()
