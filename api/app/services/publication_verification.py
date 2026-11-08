"""Read-only comparison of a publication receipt with current learner content."""

CANONICAL_FIELDS = {
    'type':'type', 'question':'question', 'options':'options',
    'answerSource':'answer_source', 'answerKeyRef':'answer_key_ref',
    'explanation':'explanation', 'direction':'direction', 'passage':'passage',
    'questionMarkup':'question_markup', 'optionsMarkup':'options_markup',
}


def publication_mismatches(expected, record, canonical, primary, patch):
    """Return field names only; never expose a replacement answer in the result."""
    if not record:
        return ['source.unavailable']
    differences = ['source.'+key for key in sorted(set(expected)|set(record))
                   if key not in expected or key not in record or expected[key]!=record[key]]
    if not canonical:
        return differences+['canonical.unavailable']
    if primary:
        for source, target in CANONICAL_FIELDS.items():
            if source not in expected:
                continue
            value=canonical.get(target)
            # Bank sync represents absent written-answer provenance as 'none'
            # in canonical rows while retaining NULL on source appearances.
            # Accept only this exact no-answer normalization; real provenance
            # drift and every MCQ source comparison remain strict.
            if (source=='answerSource' and expected.get('type')=='descriptive'
                    and expected[source] is None and value=='none'
                    and expected.get('answerIndex') is None and not expected.get('options')):
                value=None
            # Tag-only publications preserve legacy unanswered MCQs too. SQL
            # stores their absent provenance as 'none'; this cannot certify an
            # answer and does not relax answer/source correction verification.
            if (source=='answerSource' and expected.get('type')=='mcq'
                    and expected[source] is None and value=='none'
                    and expected.get('answerIndex') is None and canonical.get('answer_text') is None
                    and patch and not set(patch)-{'classification','relatedClassifications'}):
                value=None
            if source=='explanation':
                value=value or None
            if target not in canonical or value!=expected[source]:
                differences.append('canonical.'+target)
        index=expected.get('answerIndex')
        options=expected.get('options') or []
        answer=options[index] if isinstance(index,int) and 0<=index<len(options) else None
        if canonical.get('answer_text')!=answer:
            differences.append('canonical.answer_text')
        if canonical.get('difficulty') is not None:
            differences.append('canonical.difficulty')
        if 'sourceDefect' in patch and canonical.get('source_defect')!=patch['sourceDefect']:
            differences.append('canonical.source_defect')
    return differences


def verification_status(differences, newer_publication=False):
    if not differences:
        return 'matched'
    return 'changed_since_publication' if newer_publication else 'mismatch'
