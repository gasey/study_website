#!/usr/bin/env python3
"""Exercise the real study-series SQL without opening database/network sockets."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'api'))
from app.services.study_series import study_series_pool


def literal(value):
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return "'" + str(value).replace("'", "''") + "'"


def main():
    pg_bin = Path(os.environ.get('PG_BIN', '/usr/lib/postgresql/16/bin'))
    with tempfile.TemporaryDirectory(prefix='ism-series-check-') as tmp:
        subprocess.run([str(pg_bin / 'initdb'), '-D', tmp, '-A', 'trust'], check=True, capture_output=True)

        def sql(statement, result=False):
            # Each generated statement is one physical input line for --single.
            output = subprocess.run([str(pg_bin / 'postgres'), '--single', '-D', tmp, 'postgres'],
                input=statement.replace('\n', ' ') + '\n', text=True, capture_output=True, check=True)
            assert not re.search(r'\b(ERROR|FATAL):', output.stderr), output.stderr
            if result:
                match = re.search(r'result = "(.*)"\s+\(typeid', output.stdout)
                assert match, output.stdout
                return json.loads(match[1])

        sql('''CREATE TABLE canonical_questions(id text PRIMARY KEY,type text,question text,options jsonb,
          direction text,passage text,question_markup text,options_markup jsonb,answer_text text,
          answer_source text,explanation text,status text,key_disputed boolean,source_defect text);
          CREATE TABLE papers(id text PRIMARY KEY,year int,paper_number text);
          CREATE TABLE collections(id text PRIMARY KEY,live_version int,visibility text);
          CREATE TABLE collection_papers(collection_id text,version int,paper_id text);
          CREATE TABLE appearances(id text PRIMARY KEY,canonical_id text,paper_id text,is_primary boolean,
            question text,options jsonb,direction text,passage text,question_markup text,options_markup jsonb,
            has_diagram boolean,figure_image text);
          CREATE TABLE attempts(id bigint,user_id text,canonical_id text,collection_id text,correct boolean);
          CREATE TABLE v_reviewed_answer_publications(canonical_id text);
          INSERT INTO collections VALUES ('udc',1,'public'),('combined-prelims',1,'public');''')

        checks = 0
        for collection, prefix in [('udc','Assistant UDC Paper-I'), ('combined-prelims','MCS Preliminary Paper-I')]:
            def seed(name, series='A', stem='Same question', **changes):
                paper = f'{collection}/{prefix} Series-{series}.pdf'
                qid = f'{collection}-{name}'
                values = dict(id=qid, type='mcq', question=stem, options='["A","B","C","D"]',
                    direction=None, passage=None, question_markup=None, options_markup=None,
                    answer_text='B', answer_source='official', explanation='Same explanation',
                    status='live', key_disputed=False, source_defect=None)
                diagram=changes.pop('diagram',False)
                year=changes.pop('year',2025)
                values.update(changes)
                sql(f'''INSERT INTO papers VALUES ({literal(paper)},{year},'I') ON CONFLICT DO NOTHING;
                  INSERT INTO collection_papers VALUES ({literal(collection)},1,{literal(paper)});
                  INSERT INTO canonical_questions ({','.join(values)}) VALUES ({','.join(map(literal,values.values()))});
                  INSERT INTO appearances(id,canonical_id,paper_id,is_primary,question,options,direction,passage,
                    question_markup,options_markup,has_diagram)
                    SELECT id,id,{literal(paper)},true,question,options,direction,passage,question_markup,
                      options_markup,{literal(diagram)} FROM canonical_questions WHERE id={literal(qid)};''')
                return qid

            first=seed('a')
            duplicate=seed('b','B')
            guards=[
                seed('direction','C',direction='Read the following carefully'),
                seed('passage','C',passage='A different reading passage'),
                seed('options','C',options='["B","A","C","D"]'),
                seed('answer','C',answer_text='C'),
                seed('explanation','C',explanation='A different explanation'),
                seed('figure','C',diagram=True),
                seed('markup','C',question_markup='Same <u>question</u>'),
                seed('case','C',stem='Same Question'),
                seed('other-family','C',stem='Different question'),
                seed('reviewed','C',answer_source='derived'),
                seed('unreviewed','C',answer_source='derived'),
            ]
            sql(f"INSERT INTO v_reviewed_answer_publications VALUES ({literal(collection+'-reviewed')})")
            # Same wording in another year/source family is a separate question.
            prefix += ' previous year'
            guards.append(seed('year','A',year=2024))
            base=f"WHERE v.id LIKE '{collection}-%'"
            pool=study_series_pool('canonical_questions',base)
            pool=pool.replace('%(series_collection)s',literal(collection)).replace('%(series_user)s',"'learner'")

            def ids(where='',tail=''):
                return sql(f"SELECT COALESCE(json_agg(id ORDER BY id),'[]') AS result FROM (SELECT v.id FROM {pool} v {where} ORDER BY v.id {tail}) result",True)

            assert ids()==sorted([first,*guards])
            assert len(ids(tail='LIMIT 2 OFFSET 1'))==2
            checks+=2
            # An already attempted non-default booklet becomes the representative.
            sql(f"INSERT INTO attempts VALUES (1,'learner',{literal(duplicate)},{literal(collection)},false)")
            assert ids()==sorted([duplicate,*guards])
            unseen=f"WHERE NOT EXISTS(SELECT 1 FROM attempts a WHERE a.user_id='learner' AND a.canonical_id=v.id AND a.collection_id={literal(collection)})"
            assert ids(unseen)==sorted(guards)
            wrong=f"WHERE EXISTS(SELECT 1 FROM attempts a WHERE a.user_id='learner' AND a.canonical_id=v.id AND a.collection_id={literal(collection)} AND NOT a.correct)"
            assert ids(wrong)==[duplicate]
            checks+=3
            # Another learner's attempt cannot select the current learner's member.
            sql(f"INSERT INTO attempts VALUES (99,'other',{literal(first)},{literal(collection)},true)")
            assert ids(wrong)==[duplicate]
            checks+=1
            # A figure on any additional appearance prevents collapse.
            sql(f"UPDATE appearances SET has_diagram=true WHERE canonical_id={literal(first)}")
            assert first in ids() and duplicate in ids()
            checks+=1
        print(f'{checks} PostgreSQL study-series checks passed (UDC and MCS Prelims).')


if __name__ == '__main__':
    main()
