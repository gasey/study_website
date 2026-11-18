"""Inject post-migration failure, preserve receipts, restore policy, resume v2."""
import importlib.util,json,os
from pathlib import Path
from uuid import uuid4
from test_rewards import learner,attempt
from test_contribution_rewards_v2 import publication,credit

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('economy_recovery',ROOT/'scripts/learning-economy-recovery.py')
recovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(recovery)


def test_failure_recovery_preserves_receipts_and_resumes_accounting(client,learner,database):
    conn=database[1];user,_=learner
    v2_function=recovery.capture(conn)['contribution_function']
    # Use the actual immutable v1 function body, not a test substitute.
    old=(ROOT/'api/migrations/0034_learning_rewards.sql').read_text().split('CREATE FUNCTION reward_contribution_credit()',1)[1].split('CREATE TRIGGER award_contribution_rewards',1)[0]
    old='CREATE OR REPLACE FUNCTION reward_contribution_credit()'+old
    conn.execute(old)
    conn.execute("UPDATE reward_catalog SET points=1000,enabled=false WHERE id='pro-week'")
    state=recovery.capture(conn)
    state['catalog']=[r for r in state['catalog'] if r['id']!='pro-month']
    conn.execute(v2_function)
    conn.execute("UPDATE reward_catalog SET points=400,enabled=false WHERE id='pro-week'")
    for _ in range(13):attempt(conn,user)
    before=conn.execute('SELECT id,event_key,xp,points,rule_version FROM reward_ledger WHERE user_id=%s ORDER BY id',(user,)).fetchall()
    assert sum(r[3] for r in before)==12
    # A previously redeemed entitlement must survive file/policy rollback.
    redemption=uuid4().hex
    conn.execute("INSERT INTO reward_redemptions(id,user_id,idempotency_key,catalog_id,catalog_version,points,starts_at,ends_at) VALUES(%s,%s,%s,'pro-month',1,1500,now(),now()+interval '30 days')",(redemption,user,redemption))
    access=conn.execute('SELECT * FROM reward_redemptions WHERE id=%s',(redemption,)).fetchone()
    with conn.transaction():recovery.suspend(conn,state)
    assert conn.execute("SELECT points,enabled FROM reward_catalog WHERE id='pro-week'").fetchone()==(1000,False)
    assert conn.execute("SELECT enabled FROM reward_catalog WHERE id='pro-month'").fetchone()[0] is False
    assert conn.execute('SELECT id,event_key,xp,points,rule_version FROM reward_ledger WHERE user_id=%s ORDER BY id LIMIT 13',(user,)).fetchall()==before
    assert conn.execute('SELECT * FROM reward_redemptions WHERE id=%s',(redemption,)).fetchone()==access
    assert conn.execute('SELECT account_has_pro(%s)',(user,)).fetchone()[0]
    attempt(conn,user)
    legacy=conn.execute('SELECT xp,points,rule_version FROM reward_ledger WHERE user_id=%s ORDER BY id DESC LIMIT 1',(user,)).fetchone()
    assert legacy==(10,1,'learning-v1')
    # A publisher still using the old policy pays the original credit amount.
    cid,pid=publication(conn,user);cc=credit(conn,user,cid,pid)[0]
    assert conn.execute('SELECT xp,points FROM reward_ledger WHERE event_key=%s',('contribution-credit:'+str(cc),)).fetchone()==(10,10)
    # Forward repair re-installs the new function and re-enables policy only
    # after rebuilding counters from receipts minted while it was suspended.
    with conn.transaction():
        conn.execute(v2_function);recovery.resume_counters(conn)
        conn.execute("UPDATE reward_catalog SET points=400,enabled=false,version=version+1 WHERE id='pro-week'")
    attempt(conn,user)
    assert conn.execute('SELECT xp,points,rule_version FROM reward_ledger WHERE user_id=%s ORDER BY id DESC LIMIT 1',(user,)).fetchone()==(10,0,'learning-v2')
    assert conn.execute('SELECT xp,points FROM reward_daily_counters WHERE user_id=%s',(user,)).fetchone()==(150,13)
    assert conn.execute('SELECT * FROM reward_redemptions WHERE id=%s',(redemption,)).fetchone()==access
    enabled=conn.execute("SELECT tgname,tgenabled FROM pg_trigger WHERE tgname=ANY(%s) ORDER BY tgname",([name for _,name in recovery.TRIGGERS],)).fetchall()
    assert all(r[1]=='O' for r in enabled) and len(enabled)==4
    if target:=os.environ.get('FINNA_RECOVERY_REPORT'):
        Path(target).write_text(json.dumps({'actual_v1_function_restored':True,'new_behavior_triggers_disabled':True,
          'catalog_restored_with_monotonic_versions':True,'immutable_awards_and_redemption_preserved':True,
          'v1_awards_during_recovery':True,'forward_counter_rebuild':True,'all_four_triggers_reenabled':True,
          'v2_points_respect_legacy_earnings':True},indent=2)+'\n')


def test_paired_file_restore_after_injected_candidate_failure(tmp_path):
    spec=importlib.util.spec_from_file_location('file_recovery',ROOT/'scripts/rollback-finnaplan-v4.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    backup,api,web=(tmp_path/n for n in ('backup','api','public'))
    for base in (backup/'api/app',backup/'public',api/'app',web):base.mkdir(parents=True,exist_ok=True)
    (backup/'api/app/prior.py').write_text('old API')
    (backup/'public/index.html').write_text('old web')
    (api/'app/prior.py').write_text('candidate API')
    (api/'app/new.py').write_text('candidate-only module')
    (api/'unrelated.py').write_text('unrelated API')
    (web/'index.html').write_text('candidate web');(web/'new.js').write_text('candidate chunk')
    manifest={'api':{'app/prior.py':'hash','app/new.py':'hash'}}
    try:raise RuntimeError('Injected failure after file installation')
    except RuntimeError:module.restore_files(backup,api,web,manifest)
    assert (api/'app/prior.py').read_text()=='old API' and not (api/'app/new.py').exists()
    assert (api/'unrelated.py').read_text()=='unrelated API'
    assert (web/'index.html').read_text()=='old web' and not (web/'new.js').exists()
