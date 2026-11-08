#!/usr/bin/env python3
"""Trusted worker only: materialise one already-authorised publication intent.

Run as the local PostgreSQL operator. No browser authentication or review is made.
"""
import argparse,asyncio,json,os,sys
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

async def promote(database):
    api=Path('/srv/api') if os.environ.get('ISM_DB_TRANSPORT')=='local' else Path(__file__).resolve().parents[1]/'api'
    sys.path.insert(0,str(api))
    from app.services.bank_publication import promote_one
    async with await psycopg.AsyncConnection.connect(dbname=database,row_factory=dict_row,options='-c jit=off') as conn:
        async with conn.cursor() as cur:return await promote_one(cur)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--database',default='mpsc');args=parser.parse_args()
    if not all(c.isalnum() or c=='_' for c in args.database):raise SystemExit('Invalid database name')
    print(json.dumps(asyncio.run(promote(args.database)),default=str))
