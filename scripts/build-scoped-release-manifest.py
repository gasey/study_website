#!/usr/bin/env python3
"""Build and verify a deterministic, read-only scoped release manifest for Finna.

Splits the local checkout into two reviewable release bundles so an operator never
deploys the whole dirty checkout or replays historical one-shot scripts:
  - Bundle A: Core privacy, 18+ audience, reopen/retention (0130-0134) & billing refund
              foundation (requires empty schema deps 0116/0117/0119/0120/0121; excludes
              immutable 0110, Desk v4 0111-0115, and Atlas seed 0118).
  - Bundle B: Desk v4 (0111-0115) and Atlas v2/Studio seed (0118), gated behind an
              actual healthy-week operations check.

Read-only with respect to git and production. Never deploys or authorizes rollout.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

BUNDLE_A_SCHEMA_DEPS = [
    'api/migrations/0116_atlas_topic_bindings.sql',
    'api/migrations/0117_atlas_chapter_lifecycle.sql',
    'api/migrations/0119_atlas_drill_activity.sql',
    'api/migrations/0120_review_digest.sql',
    'api/migrations/0121_referral_access.sql',
]

BUNDLE_A_CORE_MIGRATIONS = [
    'api/migrations/0122_privacy_requests_and_audience.sql',
    'api/migrations/0123_game_audience_marker.sql',
    'api/migrations/0124_synchronous_activity_audience.sql',
    'api/migrations/0125_activity_admitted_owner.sql',
    'api/migrations/0126_publication_reward_audience.sql',
    'api/migrations/0127_community_tier_audience.sql',
    'api/migrations/0128_community_tier_lookup_path.sql',
    'api/migrations/0129_review_notice_audience.sql',
    'api/migrations/0130_account_reopen_window.sql',
    'api/migrations/0131_closed_study_history_retention.sql',
    'api/migrations/0132_billing_refund_reconciliation.sql',
    'api/migrations/0133_private_study_retention.sql',
    'api/migrations/0134_preferences_retention_and_audience_audit.sql',
]

BUNDLE_B_MIGRATIONS = [
    'api/migrations/0111_desk_weekly_goals.sql',
    'api/migrations/0112_desk_review_circle.sql',
    'api/migrations/0113_desk_practice_sessions.sql',
    'api/migrations/0114_desk_note_links.sql',
    'api/migrations/0115_calendar_desk_view.sql',
    'api/migrations/0118_atlas_current_site_seed.sql',
]

PAIRED_OPERATORS = [
    'scripts/bank-review-worker.py',
    'scripts/check-restore-privacy.py',
    'scripts/check-restore-billing.py',
    'scripts/check-restore-retention.py',
    'scripts/check-restore-private-study.py',
    'scripts/replay-restore-erasure-decisions.py',
]

REQUIRED_DEFAULT_OFF_FLAGS = [
    'study_desks_private_enabled',
    'account_mail_enabled',
    'review_digest_enabled',
    'referral_rewards_enabled',
    'study_history_retention_enabled',
    'private_study_retention_enabled',
    'private_preferences_retention_enabled',
    'audience_gate_enabled',
    'razorpay_checkout_enabled',
]

FORBIDDEN_IN_RELEASE = (
    'api/migrations/0110_site_maintenance.sql',
    '.admin-token',
    '.env',
)

FORBIDDEN_PREFIXES = (
    'reports/',
    'output/',
    'tmp/',
    'state/',
    'scripts/deploy-',
    'scripts/rehearse-',
    'scripts/prepare-',
    'scripts/benchmark-',
    'scripts/profile-',
    'scripts/rollback-',
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_default_off_flags(config_path: Path) -> dict[str, bool]:
    tree = ast.parse(config_path.read_text(encoding='utf-8'))
    found: dict[str, bool] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'Settings':
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    name = item.target.id
                    if name in REQUIRED_DEFAULT_OFF_FLAGS:
                        if not (isinstance(item.value, ast.Constant) and item.value.value is False):
                            raise ValueError(f'Launch/cleanup flag {name} must default to False')
                        found[name] = False
    missing = [f for f in REQUIRED_DEFAULT_OFF_FLAGS if f not in found]
    if missing:
        raise ValueError(f'Missing required default-off flags in config.py: {missing}')
    return found


def _collect_runtime_files() -> tuple[list[str], list[str]]:
    """Collect modified/untracked api/app and web/src files from git status."""
    out = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).splitlines()
    api_files = []
    web_files = []
    for line in out:
        rel = line[3:].strip()
        if rel.startswith('api/app/') and rel.endswith(('.py', '.json')):
            api_files.append(rel)
        elif rel == 'api/requirements.txt':
            api_files.append(rel)
        elif rel.startswith('web/src/') or rel in ('web/package.json', 'web/package-lock.json'):
            web_files.append(rel)
    return sorted(set(api_files)), sorted(set(web_files))


def _assert_clean_paths(paths: list[str], *, allow_bundle_b: bool = False):
    for rel in paths:
        if rel in FORBIDDEN_IN_RELEASE:
            raise ValueError(f'Forbidden file in release bundle: {rel}')
        if not allow_bundle_b and rel in BUNDLE_B_MIGRATIONS:
            raise ValueError(f'Healthy-week-gated Bundle B migration leaked into Bundle A: {rel}')
        if any(rel.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            raise ValueError(f'Forbidden non-release path in bundle: {rel}')
        full = ROOT / rel
        if not full.is_file():
            raise FileNotFoundError(f'Missing release file: {rel}')


def build_manifest() -> dict:
    flags = _verify_default_off_flags(ROOT / 'api/app/config.py')
    api_runtime, web_runtime = _collect_runtime_files()

    bundle_a_migrations = BUNDLE_A_SCHEMA_DEPS + BUNDLE_A_CORE_MIGRATIONS
    bundle_a_files = sorted(set(bundle_a_migrations + api_runtime + PAIRED_OPERATORS))
    _assert_clean_paths(bundle_a_files, allow_bundle_b=False)
    _assert_clean_paths(BUNDLE_B_MIGRATIONS, allow_bundle_b=True)
    _assert_clean_paths(web_runtime, allow_bundle_b=False)

    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()

    manifest = {
        'schema': 1,
        'source': 'finna-scoped-release-manifest-v1',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'git_head': head,
        'rollout_authorized': False,
        'production_touched': False,
        'default_off_flags_verified': flags,
        'excluded_from_bundle_a': {
            'immutable_already_applied_in_prod': ['api/migrations/0110_site_maintenance.sql'],
            'healthy_week_gated_bundle_b': BUNDLE_B_MIGRATIONS,
            'non_release_prefixes': list(FORBIDDEN_PREFIXES),
        },
        'bundle_a': {
            'description': 'Core privacy, 18+ audience, reopen/retention (0130-0134), billing refund reconciliation (0132), paired API & trusted publisher (all flags default off)',
            'migration_order': bundle_a_migrations,
            'paired_operators': PAIRED_OPERATORS,
            'api_runtime_count': len(api_runtime),
            'web_source_count': len(web_runtime),
            'files': {rel: _sha256(ROOT / rel) for rel in bundle_a_files},
        },
        'bundle_b': {
            'description': 'Desk v4 (0111-0115) and Atlas v2/Studio content seed (0118); gated after actual healthy-week operations receipt',
            'migration_order': BUNDLE_B_MIGRATIONS,
            'files': {rel: _sha256(ROOT / rel) for rel in BUNDLE_B_MIGRATIONS},
        },
    }
    raw = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode('utf-8')
    manifest['manifest_sha256'] = hashlib.sha256(raw).hexdigest()
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, help='Optional output JSON path for the manifest')
    args = parser.parse_args(argv)
    manifest = build_manifest()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    summary = {
        'schema': 1,
        'status': 'verified',
        'manifest_sha256': manifest['manifest_sha256'],
        'bundle_a_migrations': len(manifest['bundle_a']['migration_order']),
        'bundle_a_files': len(manifest['bundle_a']['files']),
        'bundle_b_migrations': len(manifest['bundle_b']['migration_order']),
        'default_off_flags_count': len(manifest['default_off_flags_verified']),
        'rollout_authorized': False,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
