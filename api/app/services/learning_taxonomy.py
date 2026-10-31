"""Virtual learning categories preserve original, bank-owned taxonomy IDs."""
GK_SUBJECTS = ('general-knowledge', 'general-studies')
CLERICAL_EXAMS = ('udc', 'ldc', 'assistant')


def topic_expression(alias='p', include_science=False):
    subjects = "'general-knowledge','general-studies'" + (",'science'" if include_science else '')
    return f"""CASE WHEN {alias}.subject_id IN ({subjects}) AND {alias}.topic_id IS NOT NULL
        THEN 'gk-gs:' || trim(both '-' from regexp_replace(lower(COALESCE({alias}.topic_label,{alias}.topic_id)), '[^a-z0-9]+','-','g'))
        ELSE {alias}.topic_id END"""


def path_projection(include_science=False, clerical_science=False):
    subjects = "'general-knowledge','general-studies'" + (",'science'" if include_science else '')
    base = f"""SELECT p.question_id,p.review_status,p.is_primary,
        CASE WHEN p.subject_id IN ({subjects}) THEN 'gk-gs' ELSE p.subject_id END AS subject_id,
        CASE WHEN p.subject_id IN ({subjects}) THEN 'General Knowledge & Studies' ELSE p.subject_label END AS subject_label,
        {topic_expression('p',include_science)} AS topic_id,p.topic_label,p.subtopic_id,p.subtopic_label
        FROM v_question_paths p"""

    if not clerical_science:
        return base
    # An exam discovery overlay only: retain original Science paths for deep
    # links, and add GK -> Science -> each canonical topic. Counts use DISTINCT.
    # News keeps its original GK topic too; neither alias is bank-authored.
    return base + """ UNION ALL
        SELECT p.question_id,p.review_status,p.is_primary,
          'gk-gs' AS subject_id,'General Knowledge' AS subject_label,
          'gk-gs:science' AS topic_id,'Science' AS topic_label,
          p.topic_id AS subtopic_id,p.topic_label AS subtopic_label
        FROM v_question_paths p
        WHERE p.subject_id='science'
          OR (p.subject_id IN ('general-knowledge','general-studies')
              AND trim(both '-' from regexp_replace(lower(COALESCE(p.topic_label,p.topic_id)), '[^a-z0-9]+','-','g'))='science-in-the-news')"""
