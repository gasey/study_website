#!/usr/bin/env python3
"""Fresh full-dump V.5 recovery/economy rehearsal; never installs live code."""
import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT/'reports/finnaplan-v5-recovery-20261117'
sys.path.insert(0, str(ROOT/'api'))
from app.services.reward_economy import RELEASE_FILES, reconciled_release


def main():
    assert reconciled_release(), 'Prepare exact V.5 economy evidence first'
    spec = importlib.util.spec_from_file_location('account_rehearsal', ROOT/'scripts/rehearse-account-tools.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    names = tuple(dict.fromkeys(module.FILES + RELEASE_FILES + ('app/data/learning-economy-v2.json',)))
    sources = {name: (ROOT/'api'/name).read_text() for name in names}
    recovery = (ROOT/'scripts/recover-finnaplan-v5.py').read_text()
    verifier = (ROOT/'scripts/verify-finnaplan-v5.py').read_text()
    remote = module.REMOTE
    old = '                (code/relative).write_text(source)'
    assert old in remote
    # Data files in the rehearsal tree normally link to read-only live assets.
    # Explicit candidate data must replace the link, never write through it.
    remote = remote.replace(old, '''                target=code/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                if target.is_symlink():target.unlink()
                target.write_text(source)''')
    remote = remote.replace('            verification=asyncio.run(verify())', '''            verification=asyncio.run(verify())
            from app.services import reward_economy,v5_release
            assert reward_economy.reconciled_release()
            v5_release.require_writes()
            recovery_namespace={'__name__':'v5_recovery_rehearsal'}
            exec(RECOVERY_CODE,recovery_namespace)
            guard_snapshot=recovery_namespace['database_guards'](conn)
            async def diagnostics():
                db._pool=AsyncConnectionPool('dbname='+name,min_size=1,max_size=1,
                  kwargs={'row_factory':dict_row,'options':'-c role=mpsc -c default_transaction_read_only=on -c jit=off'},open=False)
                await db._pool.open(wait=True)
                try:
                    async with db.cursor() as cur:
                        values=await reward_economy.diagnostics(cur)
                        integrity={k:v for k,v in values.items() if k not in reward_economy.INFORMATIONAL_FIELDS}
                        assert set(integrity)==reward_economy.INTEGRITY_FIELDS
                        assert all(v==0 for v in integrity.values())
                        gates=await reward_economy.feature_gates(cur)
                        assert not gates['catalog_ready']
                        assert next(c['ready'] for c in gates['checks'] if c['key']=='economy_reconciliation')
                        return integrity
                finally:await db._pool.close()
            integrity=asyncio.run(diagnostics())
            verifier_namespace={'__name__':'v5_release_verifier'}
            exec(VERIFY_CODE,verifier_namespace)
            release_flow=asyncio.run(verifier_namespace['verify'](name))''')
    remote = remote.replace("'candidate_sha256':", "'source_bound_economy_ready':True,'reward_integrity':integrity,'v5_database_guards':guard_snapshot,'release_read_only_flow':release_flow,\n              'candidate_sha256':")
    # The frozen predecessor's export_bytes label referred to ICS bytes. Correct
    # it in this new receipt without rewriting that historical helper or report.
    remote = remote.replace("'export_bytes':len(content.encode())", "'ics_bytes':len(content.encode())")
    payload = ('SOURCES='+repr(sources)+'\nMIGRATION='+repr(module.MIGRATION)
               +'\nRECOVERY_CODE='+repr(recovery)+'\nVERIFY_CODE='+repr(verifier)+'\n'+remote).encode()
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        'ubuntu@152.67.31.231', 'sudo -u postgres /srv/api/.venv/bin/python -'],
        input=payload, capture_output=True, timeout=1200)
    (REPORT/'rehearsal-stderr.txt').write_bytes(result.stderr)
    if result.returncode:
        raise SystemExit(result.stderr.decode(errors='replace')[-4000:])
    report = json.loads(result.stdout)
    assert report['migration_sha256'] == hashlib.sha256((ROOT/'api/migrations/0097_owned_calendar.sql').read_bytes()).hexdigest()
    for name, source in sources.items():
        assert (ROOT/'api'/name).read_text() == source, 'Source changed during rehearsal: '+name
    assert (ROOT/'scripts/verify-finnaplan-v5.py').read_text() == verifier
    assert (ROOT/'scripts/recover-finnaplan-v5.py').read_text() == recovery
    report['verifier_sha256'] = hashlib.sha256(verifier.encode()).hexdigest()
    report['recovery_helper_sha256'] = hashlib.sha256(recovery.encode()).hexdigest()
    (REPORT/'migration-rehearsal.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in ('apply_ms', 'existing_tables_checked',
        'source_bound_economy_ready', 'reward_integrity', 'clone_and_dump_removed', 'both_site_health')}, indent=2))


if __name__ == '__main__':
    main()
