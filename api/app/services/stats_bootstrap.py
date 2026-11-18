"""Exact initial report contracts source checked by Codex on 15 November 2026.
This records agent source inspection, not an independent human/owner sign-off.
Future report changes go through the ordinary protected review queue.
"""
import hashlib
import json
from pathlib import Path
from .stats import canonical
HDI_SHA='61ed82e5b66c88dfca8ff9fac775c63981ecab6a254862af97acacc41c143117'
NITI_SHA='6cde38e5f0c0c90a1c19fccda7bf089d477e577b3dcc62ddce15861d51bda5da'

def accepted(data):
 if data.metric_id=='hdi':
  # The connector parses this exact official CSV; never approve a submitted body
  # on a caller-supplied upstream hash alone. Compare the entire saved release.
  path=Path(__file__).parents[1]/'data/stats/hdi-hdr2025.json'
 elif data.metric_id=='state-health':path=Path(__file__).parents[1]/'data/stats/state-health-round-iv.json'
 else:return False
 if not path.exists():return False
 from .stats import ReleaseInput
 expected=ReleaseInput.model_validate_json(path.read_text())
 return canonical(data)==canonical(expected)

async def bootstrap():
 from .stats import ReleaseInput
 from .stats_connectors import run_import
 results=[]
 for i,name in [('hdi','hdi-hdr2025.json'),('state-health','state-health-round-iv.json')]:
  body=ReleaseInput.model_validate_json((Path(__file__).parents[1]/'data/stats'/name).read_text())
  results.append(await run_import(i,lambda body=body:body,bootstrap=True))
 return results
