#!/usr/bin/env python3
"""Add reviewed writing definitions on the canonical authority; never retag questions."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from bank_authority import require_writable,CANONICAL
from review_bank_store import bank_lock

WRITING={'id':'english/writing','label':'Writing','aliases':['Written English'],'keywords':[],
 'subtopics':[{'id':'english/writing/'+key,'label':label,'aliases':[]} for key,label in
 [('essay','Essay writing'),('precis','Précis writing'),('letter','Letter writing')]]}


def extend(data):
    result=copy.deepcopy(data)
    english=next((s for s in result['subjects'] if s['id']=='english'),None)
    if not english:raise ValueError('The canonical English subject is missing')
    found=next((t for t in english.get('topics',[]) if t['id']==WRITING['id']),None)
    if found:
        if found.get('label')!=WRITING['label']:raise ValueError('An existing writing topic conflicts with this definition')
        for node in WRITING['subtopics']:
            old=next((s for s in found.get('subtopics',[]) if s['id']==node['id']),None)
            if old and old.get('label')!=node['label']:raise ValueError('An existing writing subtopic conflicts with this definition')
            if not old:found.setdefault('subtopics',[]).append(copy.deepcopy(node))
    else:english.setdefault('topics',[]).append(copy.deepcopy(WRITING))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bank',type=Path,default=CANONICAL)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args();bank=args.bank.resolve();path=bank.parent.parent/'taxonomies/question-bank-v2.json'
    if args.apply:require_writable(bank,force=True)
    with bank_lock(bank):
        raw=path.read_bytes();before=json.loads(raw);after=extend(before)
        if before==after:print('Writing definitions already present; no change');return
        if not args.apply:print('Preview: add Writing, Essay writing, Précis writing and Letter writing; no question changes');return
        checksum=hashlib.sha256(raw).hexdigest()
        backup=path.with_name(path.name+'.before-writing-'+checksum[:16])
        if not backup.exists():shutil.copy2(path,backup)
        fd,name=tempfile.mkstemp(prefix='.writing-taxonomy-',dir=path.parent)
        try:
            with os.fdopen(fd,'w') as stream:
                json.dump(after,stream,ensure_ascii=False,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
            shutil.copymode(path,name);os.replace(name,path)
        finally:
            if os.path.exists(name):os.unlink(name)
        print('Added writing definitions; canonical question content unchanged. Backup: '+str(backup))


if __name__=='__main__':main()
