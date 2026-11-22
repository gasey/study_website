#!/usr/bin/env python3
"""Freeze the exact deployed reader and a transaction-local join-order proposal."""
from pathlib import Path
import ast,hashlib,json
ROOT=Path(__file__).resolve().parents[1];REPORT=ROOT/'reports/finna-collection-order-staged-20261119'
before=(ROOT/'api/app/routers/collections.py').read_text()
assert hashlib.sha256(before.encode()).hexdigest()=='2c2085447e727dc808728a3fb2d703380871c52d7fa2c0fe32bda9c5e98e4193'
needle='        matched_query = _MATCHED_QUERY.format('
assert before.count(needle)==1
ordered=before.replace(needle,'''        # Preserve the authority view's declared join order for this aggregate.
        # Default receipt estimates choose tens of thousands of index probes.
        # SET LOCAL ends with this read transaction, before the connection returns.
        await cur.execute("SET LOCAL join_collapse_limit=1")
'''+needle)
for name,source in [('before',before),('ordered',ordered)]:
 path=REPORT/('collections.'+name+'.py')
 if path.exists():assert path.read_text()==source
 else:path.write_text(source)
old=json.loads((ROOT/'reports/finna-collection-counts-adaptive-20261119/queries.json').read_text())
queries={scope:{'before':{**data['adaptive'],'_settings':{}},'ordered':{**data['adaptive'],'_settings':{'detail':{'join_collapse_limit':1}}}} for scope,data in old.items()}
path=REPORT/'queries.json';payload=json.dumps(queries,indent=2)+'\n'
if path.exists():assert path.read_text()==payload
else:path.write_text(payload)
print(hashlib.sha256(ordered.encode()).hexdigest())
