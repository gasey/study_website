"""Economy v2 limits and read-only launch checks. Never mints awards."""
from ..config import settings
import hashlib,json
from pathlib import Path

_API_ROOT=Path(__file__).resolve().parents[2]
_EVIDENCE_PATH=_API_ROOT/'app/data/learning-economy-v2.json'
RELEASE_FILES=(
 'app/services/account_retention.py','app/services/site_notice.py','app/routers/site_notice.py',
 'migrations/0110_site_maintenance.sql',
 'app/services/worker_health.py',
 'app/routers/rewards.py','app/routers/questions.py','app/routers/mocks.py','app/routers/study_sessions.py',
 'app/services/games.py','app/services/mastery.py','app/services/mastery_rewards.py','app/services/learning_rollups.py',
 'app/services/reward_economy.py','app/services/learning_habit.py','app/services/learning_rewards.py',
 'migrations/0094_learning_economy_limits.sql','migrations/0095_learning_completion_awards.sql',
 'migrations/0096_reviewed_contribution_rewards.sql',
 'app/services/cosmetic_shop.py','app/services/avatars.py','app/routers/avatars.py',
 'app/data/avatar_catalog.json','app/services/account_tools.py','app/routers/account_tools.py',
 'app/services/profile_identity.py','app/routers/profile_identity.py',
 'app/services/today.py','app/services/v5_release.py','app/data/finnaplan-v5-writes.json',
 'app/routers/auth.py','app/routers/me.py','app/routers/creators.py','app/routers/search.py',
 'app/routers/calendar.py','app/routers/calendar_owned.py','app/routers/learning_loop.py',
 'app/routers/games.py','app/routers/mobile.py','app/services/owned_calendar.py',
 'app/services/mobile_identity.py',
 'app/services/weekly_boards.py','app/services/weekly_recap.py','app/services/calendar_schedule.py',
 'migrations/0097_owned_calendar.sql','migrations/0098_mobile_review_grants.sql',
 'app/services/review_queue.py','app/routers/vocabulary.py','app/services/vocabulary_scheduler.py',
 'migrations/0105_bank_vocabulary_scheduler.sql','app/services/vocabulary_release.py',
 'app/services/curated_vocabulary.py','app/services/curated_practice.py','app/services/curated_sessions.py',
 'app/services/curated_release.py','app/services/content_studio.py','app/routers/materials.py',
 'migrations/0106_curated_vocabulary.sql',
 'app/config.py','app/services/account_mail.py','app/services/account_mail_release.py',
 'app/routers/account_recovery.py','migrations/0107_account_mail_delivery.sql',
 'app/services/onboarding.py','app/services/onboarding_release.py',
 'migrations/0108_onboarding_study_sets.sql',
 'app/routers/billing.py','app/routers/google_auth.py','app/routers/bulk_rates.py',
 'app/services/bulk_rates.py','app/services/bulk_rate_release.py','migrations/0109_bulk_account_rates.sql')
INFORMATIONAL_FIELDS={'account','legacy_receipts','mail_failed','mail_pending','mail_expired'}
INTEGRITY_FIELDS=frozenset('''curated_grade_receipt_mismatches curated_completion_mismatches curated_per_card_claims claims_without_receipts receipts_without_claims wallets_in_debt over_cap_days
 review_receipt_mismatches orphan_review_receipts review_over_cap_days duplicate_quest_slots
 daily_counter_mismatches missing_daily_counters v2_point_over_cap_days v2_pillar_over_cap_days
 game_completion_mismatches mock_completion_mismatches mastery_receipt_mismatches orphan_completion_receipts
 contribution_receipt_mismatches contribution_reversal_mismatches contribution_over_cap_days
 cosmetic_ledger_mismatches cosmetic_audit_mismatches duplicate_cosmetic_purchases'''.split())


def reconciled_release():
    """Operator-built fixture evidence is valid only for these exact artifacts."""
    try:
        evidence=json.loads(_EVIDENCE_PATH.read_text())
        hashes=evidence['source_sha256'];week=evidence['calibration']
        if set(hashes)!=set(RELEASE_FILES):return False
        if any(hashlib.sha256((_API_ROOT/name).read_bytes()).hexdigest()!=digest for name,digest in hashes.items()):return False
        return (week['days']==7 and week['heavy']['study_points']==175
          and week['heavy']['days_to_month']==60 and week['average']['study_points']==117
          and 89<week['average']['days_to_month']<91
          and week['catalog']=={'month_points':1500,'week_points':400,'standard_month_paise':10000,'points_per_rupee':15}
          and set(week['diagnostics'])==INTEGRITY_FIELDS and all(v==0 for v in week['diagnostics'].values())
          and len(evidence['recovery'])==8 and all(v is True for v in evidence['recovery'].values())
          and set(evidence['v5_recovery'])=={'write_quarantine','paired_static_restore','purchased_items_preserved',
            'moderated_bios_private','closed_accounts_anonymous','entitlements_preserved','database_guards_preserved'}
          and all(v is True for v in evidence['v5_recovery'].values()))
    except (OSError,ValueError,KeyError,TypeError):
        return False

RULE_VERSION = 'learning-v2'
POINT_CAP = 25
PILLAR_CAPS = {'learn':12,'revise':4,'prove':3,'play':4,'daily':1,'habit':10}


async def daily_budget(cur, user):
    # Read actual receipts, including today's pre-cutover awards. A GET never
    # creates counters, claims, profiles or launch evidence.
    await cur.execute('''SELECT reward_pillar(event_key) AS pillar,
      sum(GREATEST(points,0))::int AS points FROM reward_ledger
      WHERE user_id=%s AND kind IN ('study','game')
      AND created_at>=date_trunc('day',now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata'
      GROUP BY reward_pillar(event_key)''',(user,))
    earned={r['pillar']:r['points'] for r in await cur.fetchall()}
    points=sum(earned.values())
    return {'earned':points,'cap':POINT_CAP,'remaining':max(0,POINT_CAP-points),
      'pillars':[{'key':key,'earned':earned.get(key,0),'cap':cap,
                 'remaining':min(max(0,cap-earned.get(key,0)),max(0,POINT_CAP-points))}
                 for key,cap in PILLAR_CAPS.items()]}


async def _v2_diagnostics(cur):
    await cur.execute('''WITH by_pillar AS (
      SELECT user_id,(created_at AT TIME ZONE 'Asia/Kolkata')::date AS day,
        reward_pillar(event_key) AS pillar,sum(GREATEST(xp,0))::int AS xp,
        sum(GREATEST(points,0))::int AS points,
        count(*) FILTER(WHERE rule_version='learning-v2')::int AS v2_events,
        sum(GREATEST(points,0)) FILTER(WHERE rule_version='learning-v2')::int AS v2_points,
        sum(GREATEST(points,0)) FILTER(WHERE rule_version<>'learning-v2')::int AS old_points
      FROM reward_ledger WHERE kind IN ('study','game') GROUP BY user_id,day,pillar
    ), by_day AS (
      SELECT user_id,day,sum(xp)::int AS xp,sum(points)::int AS points,
        sum(v2_events) AS v2_events,sum(COALESCE(v2_points,0)) AS v2_points,sum(COALESCE(old_points,0)) AS old_points,
        jsonb_object_agg(pillar,points) AS pillar_points FROM by_pillar GROUP BY user_id,day
    ) SELECT
      (SELECT count(*) FROM reward_daily_counters c LEFT JOIN by_day d USING(user_id,day)
        WHERE c.xp<>COALESCE(d.xp,0) OR c.points<>COALESCE(d.points,0)
          OR c.pillar_points<>COALESCE(d.pillar_points,'{}'::jsonb))::int AS daily_counter_mismatches,
      (SELECT count(*) FROM by_day d WHERE v2_events>0 AND NOT EXISTS(
        SELECT 1 FROM reward_daily_counters c WHERE c.user_id=d.user_id AND c.day=d.day))::int AS missing_daily_counters,
      (SELECT count(*) FROM by_day WHERE v2_points>GREATEST(0,25-old_points))::int AS v2_point_over_cap_days,
      (SELECT count(*) FROM by_pillar WHERE reward_pillar_cap(pillar) IS NOT NULL AND v2_points>GREATEST(0,reward_pillar_cap(pillar)-COALESCE(old_points,0)))::int AS v2_pillar_over_cap_days''')
    result=await cur.fetchone()
    await cur.execute("""SELECT
      (SELECT count(*) FROM game_completion_rewards c JOIN reward_ledger l ON l.id=c.ledger_id JOIN game_rooms r ON r.id=c.room_id
        WHERE l.user_id<>c.user_id OR l.kind<>'game' OR l.rule_version<>'learning-v2'
          OR l.event_key<>CASE WHEN r.mode='daily' THEN 'daily:'||c.user_id||':'||r.daily_id ELSE 'game:'||c.user_id||':'||c.room_id END
          OR l.xp NOT BETWEEN 0 AND CASE WHEN r.mode='daily' THEN 10 ELSE 15 END
          OR l.points NOT BETWEEN 0 AND CASE WHEN r.mode='daily' THEN 1 ELSE 2 END)::int AS game_completion_mismatches,
      (SELECT count(*) FROM mock_completion_rewards c JOIN reward_ledger l ON l.id=c.ledger_id
        WHERE l.user_id<>c.user_id OR l.kind<>'study' OR l.rule_version<>'learning-v2' OR l.event_key<>'mock:'||c.user_id||':'||c.mock_id
          OR l.xp NOT BETWEEN 0 AND 30 OR l.points NOT BETWEEN 0 AND 3)::int AS mock_completion_mismatches,
      (SELECT count(*) FROM mastery_milestones m JOIN reward_ledger l ON l.id=m.ledger_id
        WHERE m.origin<>'activity' OR l.user_id<>m.user_id OR l.kind<>'study' OR l.rule_version<>'learning-v2'
          OR l.event_key<>'mastery:'||m.user_id||':'||m.topic||':'||m.tier OR l.source_attempt_id IS DISTINCT FROM m.source_attempt_id
          OR l.xp NOT BETWEEN 0 AND CASE WHEN m.tier='mastered' THEN 60 ELSE 30 END
          OR l.points NOT BETWEEN 0 AND CASE WHEN m.tier='mastered' THEN 5 ELSE 3 END)::int AS mastery_receipt_mismatches,
      (SELECT count(*) FROM reward_ledger l WHERE l.rule_version='learning-v2' AND reward_pillar(l.event_key) IN ('play','daily','prove','milestone')
        AND NOT EXISTS(SELECT 1 FROM game_completion_rewards c WHERE c.ledger_id=l.id)
        AND NOT EXISTS(SELECT 1 FROM mock_completion_rewards c WHERE c.ledger_id=l.id)
        AND NOT EXISTS(SELECT 1 FROM mastery_milestones c WHERE c.ledger_id=l.id))::int AS orphan_completion_receipts,
      (SELECT count(*) FROM contribution_reward_claims c JOIN reward_ledger l ON l.id=c.ledger_id
        WHERE l.user_id<>c.user_id OR l.event_key<>'contribution-credit:'||c.credit_id OR l.kind<>'contribution'
          OR l.rule_version<>'learning-v2' OR (l.xp,l.points) NOT IN ((20,5),(40,10)))::int AS contribution_receipt_mismatches,
      (SELECT count(*) FROM contribution_reward_reversals r JOIN reward_ledger l ON l.id=r.ledger_id JOIN reward_ledger o ON o.id=r.original_ledger_id
        WHERE l.user_id<>o.user_id OR l.kind<>'contribution' OR l.reverses_id IS DISTINCT FROM o.id
          OR l.xp<>-o.xp OR l.points<>-o.points OR l.event_key<>'contribution-credit:'||r.credit_id)::int AS contribution_reversal_mismatches,
      (SELECT count(*) FROM (SELECT user_id,(created_at AT TIME ZONE 'Asia/Kolkata')::date AS day
        FROM reward_ledger WHERE kind='contribution' AND points>0 GROUP BY user_id,day
        HAVING count(*) FILTER(WHERE rule_version='learning-v2')>GREATEST(0,3-count(*) FILTER(WHERE rule_version<>'learning-v2'))) x)::int AS contribution_over_cap_days""")
    result.update(await cur.fetchone())
    return result


async def feature_gates(cur):
    from .account_mail import configured
    from ..routers.billing import enabled
    await cur.execute('''SELECT EXISTS(SELECT 1 FROM account_mail_outbox o
      JOIN account_security_events e ON e.user_id=o.user_id AND e.action='password_recovered'
      AND e.created_at>=o.sent_at WHERE o.purpose='reset' AND o.sent_at IS NOT NULL) AS recovered''')
    recovered=(await cur.fetchone())['recovered']
    # Both the settled fixture and current receipts must reconcile. A stale
    # artifact or a suspended rollback policy must never turn this check green.
    reconciled=False
    if reconciled_release():
        await cur.execute("""SELECT count(*)=4 AND bool_and(tgenabled='O') AS enabled FROM pg_trigger
          WHERE (tgrelid,tgname) IN (('reward_ledger'::regclass,'enforce_learning_v2'),
            ('reward_ledger'::regclass,'track_learning_v2'),('game_rooms'::regclass,'award_game_completion'),
            ('mock_sessions'::regclass,'yy_mock_completion'))""")
        policy=(await cur.fetchone())['enabled']
        current=await diagnostics(cur)
        reconciled=bool(policy and all(v==0 for k,v in current.items() if k not in INFORMATIONAL_FIELDS))
    checks=[
      {'key':'legal_pages','label':'Published terms, privacy and refund pages','ready':False,
       'detail':'Legal pages have not shipped yet (§13.1).'},
      {'key':'email_recovery','label':'Working email password recovery',
       'ready':bool(configured() and recovered),'detail':'Requires configured mail and a completed recovery after a delivered reset email.'},
      {'key':'paid_checkout','label':'Paid checkout launched',
       'ready':bool(enabled() and settings.razorpay_key_id.startswith('rzp_live_')),
       'detail':'Requires enabled checkout with live provider credentials.'},
      {'key':'economy_reconciliation','label':'Full v2 mixed-week reconciliation',
       'ready':reconciled,'detail':'Requires matching seven-day calibration artifacts, active v2 policy and clean current reward diagnostics.'},
    ]
    return {'catalog_ready':all(c['ready'] for c in checks),'checks':checks,
      'checkout_managed_by':'operator configuration','rule_version':RULE_VERSION}


async def diagnostics(cur):
    await cur.execute("""SELECT
      (SELECT count(*) FROM reward_question_claims c LEFT JOIN reward_ledger l ON l.event_key='question:'||c.user_id||':'||c.canonical_id WHERE l.id IS NULL)::int AS claims_without_receipts,
      (SELECT count(*) FROM reward_ledger l WHERE l.event_key LIKE 'question:%' AND NOT EXISTS(SELECT 1 FROM reward_question_claims c WHERE c.user_id=l.user_id AND l.event_key='question:'||c.user_id||':'||c.canonical_id))::int AS receipts_without_claims,
      (SELECT count(*) FROM (SELECT user_id FROM reward_ledger GROUP BY user_id HAVING sum(points)<0) d)::int AS wallets_in_debt,
      (SELECT count(*) FROM (SELECT user_id,(created_at AT TIME ZONE 'Asia/Kolkata')::date AS day FROM reward_ledger WHERE kind IN ('study','game') GROUP BY user_id,day HAVING sum(xp)>300) d)::int AS over_cap_days,
      (SELECT count(*) FROM reward_ledger WHERE rule_version='legacy-v1')::int AS legacy_receipts,
      (SELECT count(*) FROM account_mail_outbox WHERE sent_at IS NULL AND token_cipher<>'' AND attempts>=5)::int AS mail_failed,
      (SELECT count(*) FROM account_mail_outbox WHERE sent_at IS NULL AND token_cipher<>'' AND attempts<5 AND created_at>now()-interval '30 minutes')::int AS mail_pending,
      (SELECT count(*) FROM account_mail_outbox WHERE sent_at IS NULL AND token_cipher<>'' AND created_at<=now()-interval '30 minutes')::int AS mail_expired""")
    result=await cur.fetchone()
    await cur.execute('''SELECT
      (SELECT count(*) FROM review_session_rewards r LEFT JOIN reward_ledger l ON l.id=r.ledger_id
        WHERE l.id IS NULL OR l.user_id<>r.user_id OR l.event_key<>'review:'||r.user_id||':'||r.day::text||':'||r.slot::text
          OR l.kind<>'study' OR l.points NOT BETWEEN 0 AND 2 OR l.xp NOT BETWEEN 0 AND 20)::int AS review_receipt_mismatches,
      (SELECT count(*) FROM reward_ledger l WHERE l.event_key LIKE 'review:%%'
        AND NOT EXISTS(SELECT 1 FROM review_session_rewards r WHERE r.ledger_id=l.id))::int AS orphan_review_receipts,
      (SELECT count(*) FROM (SELECT user_id,day FROM review_session_rewards GROUP BY user_id,day HAVING count(*)>2) x)::int AS review_over_cap_days,
      (SELECT count(*) FROM (SELECT user_id,ist_date FROM daily_quest_claims
        WHERE quest_key IN ('review_ring','cross_stream_triad','plan_ring','mastery_closure')
        GROUP BY user_id,ist_date,CASE WHEN quest_key IN ('review_ring','cross_stream_triad') THEN 'review' ELSE 'plan' END
        HAVING count(*)>1) x)::int AS duplicate_quest_slots''')
    result.update(await cur.fetchone())
    result.update(await _v2_diagnostics(cur))
    from .cosmetic_shop import diagnostics as cosmetic_diagnostics
    result.update(await cosmetic_diagnostics(cur))
    await cur.execute('''SELECT
      (SELECT count(*) FROM vocab_attempts a LEFT JOIN vocab_presentations p ON p.id=a.presentation_id
        LEFT JOIN vocab_card_revisions v ON v.card_id=a.card_id AND v.revision=a.revision
        LEFT JOIN vocab_practice_receipts receipt ON receipt.attempt_id=a.id
        LEFT JOIN practice_study_sessions session ON session.id=a.session_id
        WHERE p.id IS NULL OR v.card_id IS NULL OR p.user_id<>a.user_id OR p.card_id<>a.card_id
          OR p.revision<>a.revision OR p.content_hash<>a.content_hash OR v.content_hash<>a.content_hash
          OR p.mode<>a.mode OR p.action IS DISTINCT FROM 'answer' OR p.answered_at IS DISTINCT FROM a.at
          OR p.chosen_index IS DISTINCT FROM a.chosen_index OR p.snapshot->'options'->>a.chosen_index IS DISTINCT FROM a.chosen_text
          OR p.snapshot->'card' IS DISTINCT FROM v.payload OR p.result->'correct' IS DISTINCT FROM to_jsonb(a.correct)
          OR (a.session_id IS NULL AND receipt.attempt_id IS NOT NULL)
          OR (a.session_id IS NOT NULL AND (receipt.attempt_id IS NULL OR session.user_id<>a.user_id
            OR session.kind<>'review' OR session.collection_id IS NOT NULL OR NOT a.card_id=ANY(session.question_ids)
            OR receipt.user_id<>a.user_id OR receipt.response IS DISTINCT FROM p.result
            OR receipt.request_key<>'study:'||session.id||':'||left(encode(sha256(convert_to(a.card_id,'UTF8')),'hex'),32)))
          OR a.correct IS DISTINCT FROM (a.chosen_index=CASE WHEN p.snapshot->>'answer_index' ~ '^[0-5]$' THEN (p.snapshot->>'answer_index')::int END))::int AS curated_grade_receipt_mismatches,
      (SELECT count(*) FROM vocab_review_completions c LEFT JOIN vocab_attempts a ON a.id=c.attempt_id
        LEFT JOIN practice_study_sessions s ON s.id=c.session_id LEFT JOIN vocab_review_session_items i
          ON i.session_id=c.session_id AND i.card_id=c.card_id
        LEFT JOIN vocab_practice_receipts r ON r.attempt_id=a.id AND r.user_id=c.user_id
        WHERE a.id IS NULL OR s.id IS NULL OR i.card_id IS NULL OR r.attempt_id IS NULL
          OR a.user_id<>c.user_id OR a.card_id<>c.card_id OR a.session_id IS DISTINCT FROM c.session_id
          OR s.user_id<>c.user_id OR s.kind<>'review' OR s.finished_at IS NULL OR NOT a.card_id=ANY(s.question_ids)
          OR s.paper_ids[array_position(s.question_ids,a.card_id)] IS NOT NULL OR i.attempt_id IS DISTINCT FROM a.id
          OR i.content_hash<>a.content_hash OR i.revision<>a.revision OR NOT i.was_due
          OR i.due_on<>c.scheduled_due OR i.due_on>(s.created_at AT TIME ZONE 'Asia/Kolkata')::date
          OR c.correct<>a.correct OR a.at<s.created_at OR a.at>s.finished_at
          OR i.opened_at IS NULL OR a.at<i.opened_at+interval '3 seconds'
          OR r.request_key<>'study:'||s.id||':'||left(encode(sha256(convert_to(a.card_id,'UTF8')),'hex'),32))::int AS curated_completion_mismatches,
      (SELECT count(*) FROM reward_ledger l WHERE EXISTS(SELECT 1 FROM vocab_cards c
        WHERE l.event_key='question:'||l.user_id||':'||c.id))::int AS curated_per_card_claims''')
    result.update(await cur.fetchone())
    return result
