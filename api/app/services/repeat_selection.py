"""Reviewed repeats may share a practice slot; original appearances never collapse."""
from .editorial_access import source_versions


def option_identity(value):
    # Case can be meaningful in a language/science question. Never fold it.
    return ' '.join(str(value or '').split())


async def distinct_candidates(cur,ids):
    if len(ids)<2:return ids
    from .booklet_selection import distinct_booklet_candidates
    ids=await distinct_booklet_candidates(cur,ids)
    if len(ids)<2:return ids
    await cur.execute('''SELECT DISTINCT ON(r.left_id,r.right_id) r.*,
      la.paper_id AS left_paper,ra.paper_id AS right_paper
      FROM bank_repeat_relations r JOIN appearances la ON la.id=r.left_appearance
      JOIN appearances ra ON ra.id=r.right_appearance
      WHERE r.left_id=ANY(%s) AND r.right_id=ANY(%s)
      ORDER BY r.left_id,r.right_id,r.revision DESC''',(ids,ids))
    links=[r for r in await cur.fetchall() if r['relation'] in ('same-question','extraction-duplicate')]
    if not links:return ids
    versions=await source_versions(cur,list({r[k] for r in links for k in ('left_paper','right_paper')}))
    links=[r for r in links if versions.get(r['left_appearance'])==r['left_version'] and versions.get(r['right_appearance'])==r['right_version']]
    if not links:return ids
    members=list({r[k] for r in links for k in ('left_id','right_id')})
    await cur.execute('SELECT id,type,options,answer_text,answer_source FROM canonical_questions WHERE id=ANY(%s)',(members,))
    questions={r['id']:r for r in await cur.fetchall()};parents={q:q for q in members}
    def root(q):
        while parents[q]!=q:
            parents[q]=parents[parents[q]];q=parents[q]
        return q
    for link in links:
        left=questions[link['left_id']];right=questions[link['right_id']]
        # A review link never transfers an answer across changed options or conflicting keys.
        if left['type']!='mcq' or right['type']!='mcq':continue
        if not left['answer_text'] or not right['answer_text']:continue
        if option_identity(left['answer_text'])!=option_identity(right['answer_text']):continue
        if sorted(map(option_identity,left['options']))!=sorted(map(option_identity,right['options'])):continue
        parents[root(right['id'])]=root(left['id'])
    groups={}
    for q in members:groups.setdefault(root(q),[]).append(q)
    rank={'official':3,'key':2,'derived':1}
    retained={min(group,key=lambda q:(-rank.get(questions[q]['answer_source'],0),q)) for group in groups.values()}
    return [q for q in ids if q not in parents or q in retained]
