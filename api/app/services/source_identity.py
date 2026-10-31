"""Source wording is operational metadata, never a question classification."""
import re
from .group_b_study import source_paper_label


async def identities_for(cur, paper_ids):
    if not paper_ids:
        return {}
    await cur.execute('''SELECT i.paper_id,i.metadata FROM bank_paper_identities i
        JOIN papers p ON p.id=i.paper_id WHERE i.paper_id=ANY(%s)
        AND i.source_ref=jsonb_build_object('source_file',p.source_file,'pdf_url',p.pdf_url)''',
        (list(set(paper_ids)),))
    return {r['paper_id']: r['metadata'] for r in await cur.fetchall()}


def display_identity(paper_id, qnum, identities):
    metadata = identities.get(paper_id)
    result = {'paper_label': source_paper_label(paper_id), 'section_label': None}
    if metadata is None:
        return result
    result['paper_label'] = metadata['paper_title']
    if metadata.get('exam_title'):
        result['exam'] = metadata['exam_title']
    if metadata.get('exam_year'):
        result['year'] = metadata['exam_year']
    if re.fullmatch(r'[0-9]{1,6}', str(qnum or '')):
        number = int(qnum)
        result['section_label'] = next((s['title'] for s in metadata['sections']
            if s['qnum_from'] <= number <= s['qnum_to']), None)
    return result
