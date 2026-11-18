"""SQL-only policy recovery paired with the exact prior API/static backup.

No data is deleted, no award reversed and no entitlement changed. Called with
API stopped. Publisher transactions serialize at the affected table locks.
"""
import json

TRIGGERS=(('reward_ledger','enforce_learning_v2'),('reward_ledger','track_learning_v2'),
          ('game_rooms','award_game_completion'),('mock_sessions','yy_mock_completion'))


def capture(conn):
    return {'contribution_function':conn.execute("SELECT pg_get_functiondef('reward_contribution_credit()'::regprocedure)").fetchone()[0],
      'catalog':[dict(zip(('id','points','enabled','version'),r)) for r in conn.execute('SELECT id,points,enabled,version FROM reward_catalog ORDER BY id')]}


def suspend(conn,state):
    # The new schema/receipts remain for audit and a later forward repair.
    conn.execute("SET LOCAL lock_timeout='10s'")
    conn.execute('LOCK TABLE reward_catalog,game_rooms,mock_sessions,contribution_credit,reward_ledger IN SHARE ROW EXCLUSIVE MODE')
    for table,name in TRIGGERS:
        exists=conn.execute('SELECT 1 FROM pg_trigger WHERE tgname=%s AND tgrelid=%s::regclass',(name,table)).fetchone()
        if exists:conn.execute('ALTER TABLE '+table+' DISABLE TRIGGER '+name)
    conn.execute(state['contribution_function'])
    conn.execute('UPDATE reward_catalog SET enabled=false,version=version+1,updated_at=now() WHERE enabled')
    for row in state['catalog']:
        # Increment versions instead of reusing an old quoted price/version.
        conn.execute('UPDATE reward_catalog SET points=%s,enabled=%s,version=version+1,updated_at=now() WHERE id=%s',(row['points'],row['enabled'],row['id']))


def resume_counters(conn):
    """Before enabling v2 again, account for receipts minted by restored v1."""
    conn.execute('LOCK TABLE reward_ledger IN SHARE ROW EXCLUSIVE MODE')
    conn.execute('''INSERT INTO reward_daily_counters(user_id,day,xp,points,pillar_points)
      SELECT user_id,day,sum(xp)::int,sum(points)::int,jsonb_object_agg(pillar,points) FROM (
        SELECT user_id,(created_at AT TIME ZONE 'Asia/Kolkata')::date AS day,reward_pillar(event_key) AS pillar,
          sum(GREATEST(xp,0))::int AS xp,sum(GREATEST(points,0))::int AS points FROM reward_ledger
        WHERE kind IN ('study','game') GROUP BY user_id,day,pillar) p GROUP BY user_id,day
      ON CONFLICT(user_id,day) DO UPDATE SET xp=EXCLUDED.xp,points=EXCLUDED.points,pillar_points=EXCLUDED.pillar_points''')
    for table,name in TRIGGERS:conn.execute('ALTER TABLE '+table+' ENABLE TRIGGER '+name)


if __name__=='__main__':
    import sys,psycopg
    assert len(sys.argv)==3 and sys.argv[1]=='suspend'
    with psycopg.connect('dbname=mpsc') as conn:
        with open(sys.argv[2]) as f:suspend(conn,json.load(f))
