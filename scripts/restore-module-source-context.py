#!/usr/bin/env python3
"""Restore final module presentation only with exact source/content identity.

No answer, classification, canonical stem or option text is changed. Unmatched
module rows are an audit backlog, not a count of defective bank questions.
"""
import argparse,fcntl,hashlib,json,re,subprocess,unicodedata,os
from collections import defaultdict,Counter
from pathlib import Path
from editorial_protection import write_guarded
ROOT=Path(__file__).resolve().parents[1]
FIELDS=('direction','questionMarkup','optionsMarkup','passage','sourceContextRef')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def plain(t):
    t=re.sub(r'_{3,}',' ',str(t or ''))
    t=t.replace('*','').replace('__','')
    return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',t)).strip()
def equivalent(a,b):
    return a.get('type','mcq')==b.get('type','mcq') and plain(a.get('question'))==plain(b.get('question')) and [plain(x) for x in a.get('options') or []]==[plain(x) for x in b.get('options') or []]
def prepare(bank,modules,bankroot,legacy):
    cache={};stats=Counter();held=[];proposed={};proofs=defaultdict(list)
    def file_sha(path):
        path=path.resolve()
        if path not in cache:cache[path]=sha(path.read_bytes())
        return cache[path]
    bysha=defaultdict(list);byqnum=defaultdict(lambda:defaultdict(list))
    for p in bank['papers']:
        path=bankroot/(p.get('pdfPath') or '')
        if path.is_file():bysha[file_sha(path)].append(p['id'])
    for q in bank['questions']:byqnum[q['paperId']][str(q.get('qnum'))].append(q)
    for name,module,source_sha in modules:
        paper_sources={}
        for p in module['papers']:
            source=p.get('sourceFile','');path=legacy/('public'+source if source.startswith('/papers/') else source)
            if not path.is_file():continue
            h=file_sha(path)
            if bysha.get(h):paper_sources[p['id']]=(bysha[h],h)
        for q in module['questions']:
            if q.get('subject')!='english':continue
            stats['English module rows audited']+=1
            source=paper_sources.get(q.get('paperId'));n=re.search(r'-q(\d+)$',q['id'],re.I)
            if not source or not n:held.append({'module':q['id'],'reason':'source PDF or unique printed number unavailable'});continue
            number=str(int(n[1]));targets=[]
            for pid in source[0]:
                rows=byqnum[pid].get(number,[])
                if len(rows)==1 and equivalent(q,rows[0]):targets.append(rows[0])
            if not targets:held.append({'module':q['id'],'reason':'source/number/stem/ordered-options identity not established'});continue
            stats['source-verified equivalent module rows']+=1
            for target in targets:
                updates={}
                # Ignore arbitrary shortening of already visible blank lines.
                stem=q['question'];has_markup=bool(re.search(r'\*|__(?!_)\S',stem))
                if has_markup and target.get('questionMarkup')!=stem:updates['questionMarkup']=stem
                if not target.get('questionMarkup') and (stem!=target['question'] or re.search(r'_{3,}',stem)):updates['questionMarkup']=stem
                if q.get('direction') and q['direction']!=target.get('direction'):updates['direction']=q['direction']
                if q.get('passage') and q['passage']!=target.get('passage'):updates['passage']=q['passage']
                opts=q.get('options') or []
                if any(re.search(r'\*|__(?!_)\S',o or '') for o in opts) and opts!=target.get('optionsMarkup'):updates['optionsMarkup']=opts
                if not updates:continue
                record=proposed.setdefault(target['id'],{'id':target['id'],'before':{},'after':{}})
                for key,value in updates.items():
                    if key in record['after'] and record['after'][key]!=value:raise ValueError('Conflicting final module context for '+target['id'])
                    record['before'][key]=target.get(key);record['after'][key]=value
                proofs[target['id']].append({'module':q['id'],'module_source':name,'module_sha256':source_sha,'source_pdf_sha256':source[1],'paper_id':target['paperId'],'printed_number':number})
    for aid,r in proposed.items():r['proof']=proofs[aid]
    return {'statistics':dict(stats),'changes':list(proposed.values()),'held':held}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    bankroot=ROOT.parent/'mpsc-question-bankv2';legacy=ROOT.parent/'india-study-map';bankfile=bankroot/'bank/mpsc_bank_v2.json'
    with open(str(bankfile)+'.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);raw=bankfile.read_bytes();bank=json.loads(raw);modules=[]
        for name in ['mpsc-udc-ldc.ts','mpsc-group-b-general.ts']:
            p=legacy/'src/data/banks'/name
            data=json.loads(subprocess.check_output(['node','--max-old-space-size=3072',str(ROOT/'scripts/export-module-source.mjs'),str(p)],text=True))
            modules.append((name,data,sha(p.read_bytes())))
        report=prepare(bank,modules,bankroot,legacy);report['bank_before_sha256']=sha(raw);report['written']=False
        if args.write and report['changes']:
            # Back up the original exact bytes before any atomic bank mutation.
            backup=bankroot/'state/backups'/('english-format-'+sha(raw)[:16]+'.json');backup.parent.mkdir(parents=True,exist_ok=True)
            if not backup.exists():
                fd=os.open(backup,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                with os.fdopen(fd,'wb') as f:f.write(raw)
            if sha(backup.read_bytes())!=sha(raw):raise ValueError('Backup hash differs')
            byid={q['id']:q for q in bank['questions']}
            for r in report['changes']:byid[r['id']].update(r['after'])
            write_guarded(bankfile, bank, locked=True)
            report.update(written=True,backup=str(backup),bank_after_sha256=sha(bankfile.read_bytes()))
        args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps({'statistics':report['statistics'],'changed_questions':len(report['changes']),'fields':dict(Counter(k for r in report['changes'] for k in r['after'])),'held_module_rows':len(report['held']),'written':report['written']},indent=2))
if __name__=='__main__':main()
