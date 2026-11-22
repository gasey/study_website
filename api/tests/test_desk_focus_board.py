"""The room board reuses consent-filtered server status, never client time."""
from uuid import uuid4
from test_study_desks import desk_setup, room, join


def test_focus_board_consent_blocks_expiry_pause_and_departure(client,actor,database):
    conn=database[1];did=room(client,actor);join(client,actor,did)
    sid='focus_'+uuid4().hex
    conn.execute("INSERT INTO study_focus_sessions(id,user_id,desk_id,duration_seconds,state,resumed_at) VALUES(%s,'outsider',%s,1500,'running',clock_timestamp())",(sid,did))
    def board(viewer='author'):
        actor(viewer)
        response=client.get('/api/desk/rooms/'+did)
        assert response.status_code==200,response.text
        assert response.headers['cache-control']=='private, no-store'
        return {m['user_id']:m for m in response.json()['members']}
    assert board()['outsider']['focusing'] is False
    assert board('outsider')['outsider']['focusing'] is False
    h=actor('outsider');assert client.post('/api/desk/rooms/'+did+'/sharing',headers=h,json={'times':True}).status_code==200
    assert board()['outsider']['focusing'] is True
    for a,b in [('author','outsider'),('outsider','author')]:
        conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
        row=board()['outsider']
        assert row['blocked'] and row['focusing'] is False and row['avatar'] is None
        conn.execute('DELETE FROM creator_blocks WHERE user_id=%s AND blocked_id=%s',(a,b))
    conn.execute("UPDATE study_focus_sessions SET state='paused',resumed_at=NULL WHERE id=%s",(sid,))
    assert board()['outsider']['focusing'] is False
    conn.execute("UPDATE study_focus_sessions SET state='running',resumed_at=now()-interval '26 minutes' WHERE id=%s",(sid,))
    assert board()['outsider']['focusing'] is False
    conn.execute('UPDATE study_focus_sessions SET resumed_at=clock_timestamp() WHERE id=%s',(sid,))
    assert board()['outsider']['focusing'] is True
    conn.execute("UPDATE study_desk_members SET sharing='{}' WHERE desk_id=%s AND user_id='outsider'",(did,))
    assert board()['outsider']['focusing'] is False
    conn.execute("UPDATE study_desk_members SET left_at=now() WHERE desk_id=%s AND user_id='outsider'",(did,))
    assert 'outsider' not in board()
