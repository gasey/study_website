#!/usr/bin/env python3
"""Export actual local API print pages from disposable synthetic accounts only."""
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'api/tests'),str(ROOT/'api')]
import conftest
from psycopg.types.json import Jsonb

def main(destination):
    destination.mkdir(parents=True,exist_ok=True)
    from app.config import settings
    from app.db import cursor
    from app.routers import account_tools
    @asynccontextmanager
    async def real_role():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    original_cursor=account_tools.cursor;account_tools.cursor=real_role
    original_flag=settings.study_desks_private_enabled
    prepared=conftest.fresh_database();database=next(prepared)
    clients=conftest.client.__wrapped__(database);client=next(clients)
    cases=[]
    try:
        settings.study_desks_private_enabled=True
        conn=database[1];client.cookies.set('ism_session','test-session-author')
        def capture(name,url,required,forbidden):
            response=client.get(url);assert response.status_code==200,response.text
            assert response.headers['cache-control']=='private, no-store'
            assert "default-src 'none'" in response.headers['content-security-policy']
            assert all(value in response.text for value in required)
            assert all(value not in response.text for value in forbidden)
            path=destination/(name+'.html');path.write_text(response.text)
            cases.append({'name':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'required':required,'forbidden':forbidden,'http_status':200,'private_no_store':True,'assets_and_scripts_blocked':True,'role':'mpsc'})
        def personal(notes):
            from app.routers.study_desks import Document
            Document.model_validate({'notes':notes})
            conn.execute("INSERT INTO personal_desks(user_id,document) VALUES('author',%s) ON CONFLICT(user_id) DO UPDATE SET document=EXCLUDED.document",(Jsonb({'notes':notes}),))
        notes=[]
        for i in range(8):
            text='\n'.join(f'Line {n:02d}: Revise one idea, explain the steps, then check the original source.' for n in range(1,34))
            title=('A long heading '+('revision '*16))[:140] if i==2 else 'Synthetic revision '+str(i+1)
            body=f'NOTE_{i+1}_START\nMizo: Ṭawng, ṭha, â, ê, î, ô, û. Literal: <script> & < >.\n'+text+'\nLong reference: '+('reference_'*28)+f'\nNOTE_{i+1}_END'
            assert len(body)<=4000
            notes.append({'id':'pdf-'+str(i),'title':title,'body':body,'subject':'Synthetic English','question_id':'cq_test' if i==0 else None})
        personal(notes)
        capture('personal-multipage','/api/me/desk-notes-print?user_id=author',[f'NOTE_{i}_END' for i in range(1,9)]+['Ṭawng'],['<script>'])
        personal([])
        capture('empty','/api/me/desk-notes-print?user_id=author',['No notes are available to print.'],['NOTE_1_END'])
        personal([{'id':'locked','title':'Assessment-hidden note','body':'ASSESSMENT_SECRET_SENTINEL','question_id':'cq_test'},{'id':'safe','title':'Available note','body':'AVAILABLE_NOTE_SENTINEL'}])
        mid=uuid4().hex
        conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'author','udc',%s,600)",(mid,['cq_test']))
        capture('assessment-filtered','/api/me/desk-notes-print?user_id=author',['AVAILABLE_NOTE_SENTINEL'],['ASSESSMENT_SECRET_SENTINEL','Assessment-hidden note'])
        did='desk_pdf_'+uuid4().hex
        conn.execute("INSERT INTO study_desks(id,owner_id,name,goal) VALUES(%s,'author','Synthetic PDF room','Local print validation')",(did,))
        conn.execute("INSERT INTO study_desk_members(desk_id,user_id) VALUES(%s,'author'),(%s,'outsider')",(did,did))
        for i in range(4):
            conn.execute("INSERT INTO study_desk_items(id,desk_id,author_id,kind,title,body,request_key,request_hash) VALUES(%s,%s,'author','note',%s,%s,%s,'synthetic-pdf')",('pdf_'+str(i),did,'My room note '+str(i+1),notes[i]['body'],uuid4().hex))
        conn.execute("INSERT INTO study_desk_items(id,desk_id,author_id,kind,title,body,request_key,request_hash) VALUES(%s,%s,'outsider','note','Other member private writing','OTHER_MEMBER_SECRET_SENTINEL',%s,'synthetic-pdf')",('pdf_'+uuid4().hex,did,uuid4().hex))
        capture('room-owned','/api/me/desk-notes-print?user_id=author&desk_id='+did,[f'NOTE_{i}_END' for i in range(1,5)]+['Your own shared notes in this room.'],['OTHER_MEMBER_SECRET_SENTINEL','ASSESSMENT_SECRET_SENTINEL'])
        ledger=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
        assert ledger==0
    finally:
        try:next(clients)
        except StopIteration:pass
        try:next(prepared)
        except StopIteration:pass
        account_tools.cursor=original_cursor;settings.study_desks_private_enabled=original_flag
    manifest={'synthetic_only':True,'production_access':False,'disposable_database_removed':True,'reward_ledger_rows':ledger,'cases':cases,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('api/app/services/desk_notes.py','api/app/routers/account_tools.py')}}
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Four authenticated real-role print pages captured; disposable database removed.')

if __name__=='__main__':
    assert len(sys.argv)==2
    main(Path(sys.argv[1]).resolve())
