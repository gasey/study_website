"""Compare published examiner evidence with separately published reviewed working.

Never promote an imported/model answer to a reviewed solution. Only applied,
source-matching publications can supply either lane; drafts/reverted revisions
and changed question contexts are excluded.
"""
CONTEXT = ('paperId','question','options','direction','passage','questionMarkup','optionsMarkup','hasDiagram','figureImage','qnum')


def source_matches(baseline, current):
    return all(baseline.get(k) == current.get(k) for k in CONTEXT)


def published_comparison(current, publications, documents, *, held=False, review_note=None):
    official = None
    solution = None
    for pub in publications:  # newest first
        if pub.get('state') != 'applied':
            continue
        manifest = pub.get('manifest', {})
        payload = manifest.get('payload', {})
        if payload.get('kind') not in ('answer','explanation') or not source_matches(manifest.get('baseline', {}).get('record', {}), current):
            continue
        patch = payload.get('patch', {})
        index = patch.get('answerIndex')
        options = current.get('options') or []
        decision=manifest.get('admin_decision', {})
        separate=(payload.get('kind')=='explanation' and decision.get('mode')=='verified'
            and decision.get('preserve_official_key') is True
            and set(patch)=={'explanation'})
        if separate:
            selected=decision.get('solution_answer_text')
            if options.count(selected)!=1 or not any(e.get('kind')=='reasoning' and e.get('answer_text')==selected for e in payload.get('evidence',[])):
                continue
            index=options.index(selected)
        if type(index) is not int or not 0 <= index < len(options) or not options[index]:
            continue
        entry = {'answer_index': index, 'answer_text': options[index],
                 'explanation': patch.get('explanation') or '', 'publication_id': pub['id'],
                 'published_at': pub.get('finished_at'), 'document': None}
        mode = decision.get('mode')
        if mode == 'official' and official is None and patch.get('answerSource') == 'official':
            ref = patch.get('answerKeyRef')
            doc = documents.get(ref)
            evidence = next((e for e in payload.get('evidence', [])
                if e.get('kind') == 'official-key' and e.get('document_id') == ref
                and doc and e.get('sha256') == doc.get('sha256')
                and e.get('printed_question') == str(current.get('qnum'))
                and e.get('answer_text') == options[index]
                and type(e.get('page')) is int and e['page'] >= 1), None)
            if not evidence or doc.get('kind') != 'official-key' or doc.get('key_status') == 'superseded' or doc.get('paper_id') != current.get('paperId'):
                continue
            entry['document'] = {'id': doc['id'], 'title': doc['title'],
                'key_status': doc.get('key_status'), 'page': evidence['page'],
                'url': None}
            official = entry
        elif mode == 'verified' and solution is None and (separate or patch.get('answerSource') == 'derived' and not patch.get('answerKeyRef')):
            solution = entry
    relation = ('agree' if official['answer_text'] == solution['answer_text'] else 'disagree') if official and solution else 'not-compared'
    return {'official': official, 'solution': solution, 'relation': relation,
            'held': bool(held), 'review_note': review_note,
            'notice': 'An official key records the examiner’s selection. A reviewed solution needs separate published reasoning; neither an imported answer nor a vote counts as verification.'}
