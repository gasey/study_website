import asyncio
from uuid import uuid4
from psycopg.types.json import Jsonb
from app.services.booklet_selection import booklet_family,selection_key

def test_booklet_identity_keeps_distinct_papers_context_and_answers():
    assert booklet_family('Archive/1.Exam Series-A Paper-I.pdf',2025)==booklet_family('Archive/2.Exam Series B Paper-I..pdf',2025)
    assert booklet_family('Archive/Exam Booklet 1 Paper-I.pdf',2025)==booklet_family('Archive/Exam Booklet 2 Paper-I.pdf',2025)
    assert booklet_family('Archive/Exam Paper-I.pdf',2025) is None
    assert booklet_family('Archive/Exam Series A Paper-I.pdf',None) is None
    base={'paper_id':'Archive/Exam Booklet A Paper-I.pdf','year':2025,'type':'mcq','question':'Choose X','options':['X','Y'],'answer_text':'X','status':'live'}
    reordered={**base,'paper_id':'Archive/Exam Booklet B Paper-I.pdf','options':['Y','X']}
    assert selection_key(base)==selection_key(reordered)
    for changes in [{'passage':'Different passage'},{'direction':'Choose the incorrect answer'},{'answer_text':'Y'},{'figure_image':'different.png'},{'paper_id':'Archive/Exam Booklet B Paper-II.pdf'},{'year':2026},{'options':['X','X']},{'question':'Choose x'}]:
        assert selection_key(base)!=selection_key({**reordered,**changes})

def test_booklet_selection_keeps_sources_and_collapses_only_exact_repeats(database,client):
    import psycopg
    from psycopg.rows import dict_row
    from app.services.repeat_selection import distinct_candidates
    conn=database[1];key=uuid4().hex;ids=[]
    for index,series in enumerate(['A','B','C']):
        paper=f'BookletFixture/{key} Paper-I Booklet {series}.pdf';qid=f'booklet-{key}-{index}';ids.append(qid)
        conn.execute("INSERT INTO papers(id,exam_type,exam_name,year) VALUES(%s,'Direct','Synthetic booklet fixture',2025)",(paper,))
        opts=['X','Y'] if index!=1 else ['Y','X']
        conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq','Choose X',%s,'X','key')",(qid,Jsonb(opts)))
        conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,page,direction) VALUES(%s,%s,'mcq','Choose X',%s,%s,'key',%s,true,'1',1,%s)",('app-'+qid,paper,Jsonb(opts),opts.index('X'),qid,'Different task' if index==2 else 'Choose one'))
    async def select():
        async with await psycopg.AsyncConnection.connect('dbname='+database[0],row_factory=dict_row) as db:
            async with db.cursor() as cur:return await distinct_candidates(cur,ids)
    assert asyncio.run(select())==[ids[0],ids[2]]
    assert conn.execute('SELECT count(*) FROM canonical_questions WHERE id=ANY(%s)',(ids,)).fetchone()[0]==3
    conn.execute('UPDATE canonical_questions SET answer_text=%s WHERE id=%s',('Y',ids[1]))
    assert asyncio.run(select())==ids
