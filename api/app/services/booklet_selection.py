"""Exact booklet repeats share a selection slot; source records remain untouched."""
import re
from collections import defaultdict,Counter
MARKER=re.compile(r"\b(?:series|booklet(?:\s+series)?|set)(?:\s+(?:no\.?|number|code))?[\s_:'\"()\-]*([A-D1-4])(?=$|[\s.\-_'\"()])",re.I)
def booklet_family(paper_id,year):
    directory,_,name=paper_id.rpartition('/')
    if year is None or not MARKER.search(name):return None
    name=re.sub(r'^\d+[.]\s*','',name)
    name=MARKER.sub('',name)
    name=re.sub(r'\.pdf$','',name,flags=re.I).strip(' .-_')
    name=re.sub(r'[\s_-]+',' ',name).lower()
    return directory.lower(),year,name

def selection_key(row):
    family=booklet_family(row['paper_id'],row['year'])
    options=row['options'] or []
    if not family or row['type']!='mcq' or not row['answer_text'] or len(options)<2 or any(not isinstance(v,str) or not v.strip() for v in options) or len(set(options))!=len(options):return None
    if row['answer_text'] not in options:return None
    markup=row.get('options_markup') or [None]*len(options)
    if len(markup)!=len(options):return None
    # Preserve case, instructions, passages, figures and formatting exactly.
    return (family,row['question'],row.get('direction'),row.get('passage'),row.get('question_markup'),
      tuple(sorted((v,markup[i] or '') for i,v in enumerate(options))),row.get('has_diagram'),row.get('figure_image'),
      row['answer_text'],row.get('status'),row.get('key_disputed'),row.get('source_defect'))

async def distinct_booklet_candidates(cur,ids):
    await cur.execute('''SELECT q.id,q.type,q.answer_text,q.answer_source,q.status,q.key_disputed,q.source_defect,
      a.paper_id,p.year,a.question,a.options,a.direction,a.passage,a.question_markup,a.options_markup,a.has_diagram,a.figure_image
      FROM canonical_questions q JOIN appearances a ON a.canonical_id=q.id AND a.is_primary
      JOIN papers p ON p.id=a.paper_id WHERE q.id=ANY(%s) AND p.year IS NOT NULL
      AND a.paper_id ~* '(series|booklet|set)'
      AND NOT EXISTS(SELECT 1 FROM appearances other WHERE other.canonical_id=q.id
        AND other.is_primary AND other.id<>a.id)''',(ids,))
    rows=await cur.fetchall();groups=defaultdict(list);counts=Counter(row['id'] for row in rows)
    for row in rows:
        if counts[row['id']]!=1:continue
        key=selection_key(row)
        if key is not None:groups[key].append(row)
    removed=set();rank={'official':3,'key':2,'derived':1}
    for group in groups.values():
        if len(group)<2:continue
        keep=min(group,key=lambda r:(-rank.get(r['answer_source'],0),r['id']))['id']
        removed.update(r['id'] for r in group if r['id']!=keep)
    return [qid for qid in ids if qid not in removed]
