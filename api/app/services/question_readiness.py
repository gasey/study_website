"""Indexed readiness probes for a bounded question set.

Keep the CASE identical to v_bank_answer_status (migration 0050). The OFFSET
barrier keeps PostgreSQL from scanning every receipt for a small page. The
existing publication view remains the authority for independent review.
"""
def reviewed_answer_sql(alias='v'):
    return f"EXISTS (SELECT 1 FROM v_reviewed_answer_publications rp WHERE rp.canonical_id={alias}.id OFFSET 0)"


def answer_status_sql(alias='v'):
    return f"""CASE WHEN {alias}.type<>'mcq' THEN 'written'
        WHEN {alias}.status='held' OR {alias}.key_disputed OR {alias}.source_defect IN ('duplicate-options','unresolved-source') THEN 'needs-review'
        WHEN {alias}.answer_text IS NULL THEN 'unsolved'
        WHEN {alias}.answer_source IN ('official','key') THEN CASE WHEN valid_scoring_options({alias}.options) THEN 'official' ELSE 'needs-review' END
        WHEN {alias}.answer_source='derived' AND {reviewed_answer_sql(alias)} THEN 'verified'
        ELSE 'needs-review' END"""
