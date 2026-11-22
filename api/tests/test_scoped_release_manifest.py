"""Verify scoped release manifest integrity and Bundle A standalone migration chain."""
import importlib.util
import json
from pathlib import Path
import re
from uuid import uuid4

import psycopg
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    'scoped_release_manifest',
    ROOT / 'scripts/build-scoped-release-manifest.py',
)
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


def test_scoped_release_manifest_integrity_and_default_off_flags(tmp_path, capsys):
    out = tmp_path / 'manifest.json'
    assert packager.main(['--out', str(out)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary['status'] == 'verified'
    assert summary['rollout_authorized'] is False

    manifest = json.loads(out.read_text(encoding='utf-8'))
    assert manifest['rollout_authorized'] is False
    assert manifest['production_touched'] is False
    assert all(v is False for v in manifest['default_off_flags_verified'].values())
    assert len(manifest['default_off_flags_verified']) == len(packager.REQUIRED_DEFAULT_OFF_FLAGS)

    # Immutable 0110 and healthy-week-gated Bundle B (0111-0115, 0118) must NEVER appear in Bundle A.
    bundle_a_paths = set(manifest['bundle_a']['files'].keys())
    assert 'api/migrations/0110_site_maintenance.sql' not in bundle_a_paths
    for b_mig in packager.BUNDLE_B_MIGRATIONS:
        assert b_mig not in bundle_a_paths
    assert 'scripts/bank-review-worker.py' in bundle_a_paths
    assert 'scripts/replay-restore-erasure-decisions.py' in bundle_a_paths
    assert manifest['bundle_a']['migration_order'][-1] == 'api/migrations/0134_preferences_retention_and_audience_audit.sql'


def test_bundle_a_migrations_apply_cleanly_without_bundle_b_on_isolated_postgres():
    """Prove 0001..0110 + Bundle A (0116,0117,0119,0120,0121,0122..0134) applies cleanly without 0111..0115 or 0118."""
    manifest = packager.build_manifest()
    bundle_a_migs = manifest['bundle_a']['migration_order']
    mig_dir = ROOT / 'api/migrations'
    base_migs = sorted(
        p for p in mig_dir.glob('*.sql')
        if int(p.name.split('_')[0]) <= 110
    )
    selected = base_migs + [ROOT / rel for rel in bundle_a_migs]

    db_name = 'ism_bundle_a_test_' + uuid4().hex[:12]
    with psycopg.connect('dbname=postgres', autocommit=True) as admin:
        admin.execute(f'CREATE DATABASE {db_name}')
    try:
        with psycopg.connect(f'dbname={db_name}', autocommit=True) as conn:
            for path in selected:
                if path.name.startswith('0005_'):
                    refs = set()
                    for m in mig_dir.glob('*.sql'):
                        refs.update(re.findall(r"'(Old_Questions/[^']+\.pdf)'", m.read_text()))
                    for ref in refs:
                        conn.execute("INSERT INTO papers(id,exam_type,exam_name) VALUES (%s,'Direct','Synthetic migration fixture') ON CONFLICT DO NOTHING", (ref,))
                if path.name.startswith('0053_'):
                    ids = json.loads((ROOT / 'api/tests/fixtures/udc-v1-paper-ids.json').read_text())
                    for ref in ids:
                        conn.execute("INSERT INTO papers(id,exam_type,exam_name,exam_scope_id) VALUES (%s,'Direct','Synthetic UDC predecessor','mizoram-recruitment') ON CONFLICT DO NOTHING", (ref,))
                    conn.execute("DELETE FROM collection_papers WHERE collection_id='udc' AND version=1")
                    conn.execute("DELETE FROM collection_sections WHERE collection_id='udc' AND version=1")
                    conn.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query) VALUES ('udc',1,'papers','Synthetic predecessor',0,%s)", (Jsonb({'paper_ids': ids}),))
                    for ref in ids:
                        conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,as_mock,section_path) VALUES ('udc',1,%s,false,'papers')", (ref,))
                conn.execute(path.read_text(encoding='utf-8'))
            # Verify 0134 schema objects exist and 0118 Atlas seed did NOT run.
            cols = {
                r[0] for r in conn.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='users'"
                ).fetchall()
            }
            assert {'study_history_purged_at', 'private_study_purged_at', 'private_preferences_purged_at'} <= cols
            assert conn.execute('SELECT count(*) FROM atlas_chapter_versions').fetchone()[0] == 0
            # Verify mpsc can invoke all three sweepers cleanly on empty DB.
            with conn.transaction():
                conn.execute('SET LOCAL ROLE mpsc')
                assert conn.execute('SELECT sweep_expired_study_history(5, 200)').fetchone()[0]['accounts_scanned'] == 0
                assert conn.execute('SELECT sweep_expired_private_study(5, 200)').fetchone()[0]['accounts_scanned'] == 0
                assert conn.execute('SELECT sweep_expired_private_preferences(5, 200)').fetchone()[0]['accounts_scanned'] == 0
    finally:
        with psycopg.connect('dbname=postgres', autocommit=True) as admin:
            admin.execute(f'DROP DATABASE IF EXISTS {db_name} WITH (FORCE)')
