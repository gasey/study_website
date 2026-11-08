"""Attributed tagging decisions are separate from complete answer/source reviews."""
from .bank_review import event

ACTION='owner_ai_taxonomy_progress'

def signature_sql():
    return """md5(jsonb_build_array(a.id,a.canonical_id,a.paper_id,a.type,a.question,a.options,
      a.answer_index,a.answer_source,a.answer_key_ref,a.explanation,a.direction,a.question_markup,
      a.options_markup,a.passage,a.page,a.qnum,a.has_diagram,a.figure_image,a.series,
      c.status,c.source_defect,c.key_disputed,c.dispute_note,p.exam_name,p.year,p.source_file,p.pdf_url,
      qc.subject_id,qc.topic_id,qc.subtopic_id,
      (SELECT jsonb_agg(jsonb_build_array(l.subject_id,l.topic_id,l.subtopic_id)
         ORDER BY l.subject_id,l.topic_id,l.subtopic_id) FROM question_topic_links l
         WHERE l.question_id=c.id AND l.review_status='approved'))::text)"""

JOINS=""" FROM appearances a JOIN canonical_questions c ON c.id=a.canonical_id
    JOIN papers p ON p.id=a.paper_id LEFT JOIN question_classifications qc
    ON qc.question_id=c.id AND qc.review_status='approved' """

async def record(cur,owner,run,item,status,reason='',contribution_id=None,known_records=None):
    row=item['candidate'];qid=row['canonical_id'];aid=row['appearance_id']
    await cur.execute('SELECT '+signature_sql()+JOINS+'WHERE a.id=%s AND c.id=%s',(aid,qid))
    current=await cur.fetchone()
    signature=next(iter(current.values())) if current else None
    detail={'run_id':run['run_id'],'owner_id':owner,'canonical_id':qid,'appearance_id':aid,
            'candidate_file':item['candidate_file'],'candidate_signature':item['candidate_signature'],
            'status':status,'source_signature':signature,'reason':reason,
            'review_kind':'owner-delegated-ai-taxonomy','independent_human_review':False}
    key=(qid,status,signature)
    if known_records is None:
        await cur.execute("""SELECT 1 FROM contribution_events WHERE action=%s
           AND detail->>'run_id'=%s AND detail->>'canonical_id'=%s AND detail->>'status'=%s
           AND detail->>'source_signature' IS NOT DISTINCT FROM %s LIMIT 1""",
           (ACTION,run['run_id'],qid,status,signature))
        exists=bool(await cur.fetchone())
    else:
        # Trusted serial operator batches preload the exact run's immutable keys.
        # Still compute the live source signature above on every individual record.
        exists=key in known_records
    if not exists:
        await event(cur,contribution_id,'operator:owner-source-maintenance',ACTION,detail)
        if known_records is not None:known_records.add(key)

async def existing_records(cur,run_id):
    """Run-local history lookup once per serial operator transaction."""
    await cur.execute("SELECT detail FROM contribution_events WHERE action=%s AND detail->>'run_id'=%s",(ACTION,run_id))
    return {(r['detail']['canonical_id'],r['detail']['status'],r['detail'].get('source_signature'))for r in await cur.fetchall()}

async def progress(cur):
    await cur.execute("SELECT count(*)::int AS total FROM canonical_questions WHERE status<>'merged'")
    total=(await cur.fetchone())['total']
    await cur.execute("""WITH latest AS (
      SELECT DISTINCT ON (detail->>'canonical_id') detail,created_at FROM contribution_events
      WHERE action=%s ORDER BY detail->>'canonical_id',id DESC), checked AS (
      SELECT r.detail,r.created_at,"""+signature_sql()+""" AS current_signature FROM latest r
      LEFT JOIN appearances a ON a.id=r.detail->>'appearance_id'
      LEFT JOIN canonical_questions c ON c.id=a.canonical_id
      LEFT JOIN papers p ON p.id=a.paper_id
      LEFT JOIN question_classifications qc ON qc.question_id=c.id AND qc.review_status='approved')
      SELECT count(*) FILTER(WHERE detail->>'status'='published' AND detail->>'source_signature'=current_signature)::int AS published,
        count(*) FILTER(WHERE detail->>'status'='confirmed' AND detail->>'source_signature'=current_signature)::int AS confirmed,
        count(*) FILTER(WHERE detail->>'status'='blocked')::int AS blocked,
        count(*) FILTER(WHERE detail->>'status' IN ('published','confirmed') AND detail->>'source_signature' IS DISTINCT FROM current_signature)::int AS stale,
        max(created_at) AS updated_at FROM checked""",(ACTION,))
    counts=await cur.fetchone()
    return {**counts,'total':total,'remaining':max(0,total-counts['published']-counts['confirmed']),
            'review_kind':'owner-delegated-ai-taxonomy','includes_answer_verification':False}
