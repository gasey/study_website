#!/usr/bin/env python3
"""Operator/scheduler entry point. DATABASE_URL must name the intended Stats DB."""
import argparse
import asyncio
import json
import sys
import os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'api'))
# systemd's shared db.env uses standard libpq variables. Prefer an explicit
# DATABASE_URL; otherwise honor PGDATABASE instead of Settings' dev default.
if not os.environ.get('DATABASE_URL') and os.environ.get('PGDATABASE'):
 from psycopg.conninfo import make_conninfo
 os.environ['DATABASE_URL']=make_conninfo(dbname=os.environ['PGDATABASE'])
from app.db import open_pool,close_pool
from app.services.stats_connectors import refresh,watch_sources

async def main():
 parser=argparse.ArgumentParser();parser.add_argument('--include-hdi',action='store_true',help='Stage the official HDI CSV for owner review')
 parser.add_argument('--bootstrap',action='store_true',help='Import the two exact source-checked initial report contracts')
 parser.add_argument('--watch-sources',action='store_true',help='Check official report catalogues for changed release links')
 parser.add_argument('--initial-bundle',help='Import a locally validated initial WDI bundle; skips remote refresh')
 args=parser.parse_args()
 await open_pool()
 try:
  if args.initial_bundle:
   from app.services.stats import ReleaseInput
   from app.services.stats_connectors import run_import
   bodies=[ReleaseInput.model_validate(b) for b in json.loads(Path(args.initial_bundle).read_text())]
   if {b.metric_id for b in bodies}!={'gdp','gdp-growth','gdp-per-capita','population','inflation','life-expectancy','infant-mortality'}:raise ValueError('Expected the seven approved WDI series')
   results=[await run_import(b.metric_id,lambda b=b:b,True) for b in bodies]
  else:results=await refresh(args.include_hdi)
  if args.bootstrap:
   from app.services.stats_bootstrap import bootstrap
   results+=await bootstrap()
  if args.watch_sources:results+=await watch_sources()
  print(json.dumps(results))
  return 1 if any(r['status']=='failed' for r in results) else 0
 finally:await close_pool()
if __name__=='__main__':sys.exit(asyncio.run(main()))
