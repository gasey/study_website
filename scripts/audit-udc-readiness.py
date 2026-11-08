#!/usr/bin/env python3
"""Read-only UDC source/quality inventory from a bank and public collection snapshot."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bank',type=Path,required=True)
    parser.add_argument('--collection',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    raw=args.bank.read_bytes();bank=json.loads(raw)
    collection=json.loads(args.collection.read_text())
    if collection.get('id')!='udc':
        raise SystemExit('Use an exact UDC collection snapshot')
    paper_ids={p['id'] for p in collection['paper_list']}
    questions=[q for q in bank['questions'] if q['paperId'] in paper_ids]
    subjects=Counter();issues={name:[] for name in ('missing-explanation','missing-figure','defect','malformed','missing')}
    for q in questions:
        paths=[c for c in q.get('classifications',[]) if c.get('review_status')=='approved' and c.get('is_primary')]
        subject=paths[0]['subject_id'] if paths else 'unclassified'
        subjects['gk-gs' if subject in ('science','general-studies','general-knowledge') else subject]+=1
        options=q.get('options') or [];index=q.get('answerIndex')
        usable=isinstance(index,int) and 0<=index<len(options) and bool(options[index]) and q.get('answerSource') not in (None,'none')
        malformed=q.get('type')=='mcq' and (len(options)<2 or any(not isinstance(o,str) or not o.strip() for o in options)
          or len(set(' '.join(o.split()) for o in options if isinstance(o,str)))!=len(options))
        flags={
          'missing-explanation':usable and not (q.get('explanation') or '').strip(),
          'missing-figure':bool(q.get('hasDiagram') and not q.get('figureImage')),
          'defect':bool(q.get('sourceDefect')),
          'malformed':malformed,
          'missing':q.get('type')=='mcq' and not usable,
        }
        for issue,flag in flags.items():
            if flag:issues[issue].append(q)
    report={
      'mode':'read-only local-bank audit','bank_sha256':hashlib.sha256(raw).hexdigest(),
      'scope':'Exact source IDs from the supplied UDC public collection snapshot',
      'limits':[
        'Counts are printed source appearances, not unique concepts or complete syllabus coverage.',
        'Server-owned holds, current independent review status and merged canonical identities are not available offline.',
        'Missing-figure flags are review leads, not permission to clear defects or infer missing artwork.',
        'Timing and marks below come from the supplied snapshot, not a fresh live rule verification.',
      ],
      'source_booklets':len(paper_ids),'source_questions':len(questions),
      'collection_snapshot_questions':collection.get('questions'),
      'question_types':dict(Counter(q.get('type') for q in questions)),
      'raw_answer_sources':dict(Counter(q.get('answerSource') or 'none' for q in questions)),
      'approved_primary_subject_counts':dict(sorted(subjects.items())),
      'paper_rule_sources_in_snapshot':dict(Counter(p.get('rule_source') or 'unknown' for p in collection['paper_list'])),
      'issues':{},
    }
    for issue,rows in issues.items():
        report['issues'][issue]={
          'count':len(rows),'admin_queue':'/admin/bank?'+urlencode({'tab':'questions','exam':'udc','issue':issue,'open_first':'1'}),
          'examples':[{'appearance_id':q['id'],'paper_id':q['paperId'],'qnum':q.get('qnum'),'page':q.get('page')} for q in rows[:8]],
        }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({key:report[key] for key in ('source_booklets','source_questions','question_types','raw_answer_sources')}))
    print(json.dumps({issue:value['count'] for issue,value in report['issues'].items()}))


if __name__=='__main__':main()
