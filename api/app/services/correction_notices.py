"""Bounded durable fanout of generic correction notices; never send answer text."""
async def process(cur):
    await cur.execute('SELECT * FROM question_change_events WHERE finished_at IS NULL AND failures<5 ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED')
    event=await cur.fetchone()
    if not event:return False
    try:
        async with cur.connection.transaction():
            await cur.execute('''SELECT u.id FROM users u WHERE u.email IS NOT NULL AND u.id>%s
              AND (EXISTS(SELECT 1 FROM attempts a WHERE a.user_id=u.id AND a.canonical_id=%s AND a.at<=%s)
                OR EXISTS(SELECT 1 FROM personal_desks d WHERE d.user_id=u.id AND d.document->'saved' ? %s))
              ORDER BY u.id LIMIT 100''',(event['recipient_cursor'],event['question_id'],event['created_at'],event['question_id']))
            users=await cur.fetchall()
            fields=', '.join(event['changed_fields'])
            for user in users:
                await cur.execute('''INSERT INTO review_notifications(user_id,event_key,message,corrected_question_id,question_change_id)
                  VALUES(%s,%s,%s,%s,%s) ON CONFLICT(event_key) DO NOTHING''',
                  (user['id'],f"question-change:{event['id']}:{user['id']}",
                   f'A question you saved or attempted was updated ({fields}). Original attempts and mock scores are preserved; adjusted assessments are shown separately.',event['question_id'],event['id']))
            await cur.execute('''UPDATE question_change_events SET recipient_cursor=%s,
              finished_at=CASE WHEN %s THEN now() END,last_error=NULL WHERE id=%s''',
              (users[-1]['id'] if users else event['recipient_cursor'],len(users)<100,event['id']))
    except Exception:
        await cur.execute("UPDATE question_change_events SET failures=failures+1,last_error='Correction notification batch failed; operator investigation required' WHERE id=%s",(event['id'],))
    return True
