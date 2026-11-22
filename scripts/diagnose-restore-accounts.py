#!/usr/bin/env python3
"""Read-only aggregate diagnosis of account differences in two isolated restores.

No account identifiers, values or fingerprints are exported. This prepares a
repair review; it never repairs records or certifies currentness/promotion.
"""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets

from psycopg import sql

HELPER = Path(__file__).with_name('check-restore-privacy.py')
spec = importlib.util.spec_from_file_location('account_diagnosis_readonly', HELPER)
readonly = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readonly)


def account_rows(conn, salt):
    # Every value, including the primary key, is salted and hashed inside SQL.
    # Field names and broad presence categories are the only cleartext metadata.
    query = """SELECT encode(sha256(convert_to(%s || x.id,'UTF8')),'hex'),
      (SELECT jsonb_object_agg(k,encode(sha256(convert_to(%s || k || v::text,'UTF8')),'hex'))
       FROM jsonb_each(to_jsonb(x)) AS fields(k,v)),
      CASE WHEN x.closed_at IS NOT NULL THEN 'closed'
           WHEN x.email IS NOT NULL THEN 'open_with_email' ELSE 'open_without_email' END
      FROM public.users x"""
    rows = {}
    with conn.cursor(name='restore_account_diagnosis') as cur:
        cur.execute(query, (salt, salt))
        while batch := cur.fetchmany(500):
            for key, values, category in batch:
                rows[key] = (values, category)
    return rows


def summarize(reference, candidate):
    shared = reference.keys() & candidate.keys()
    current_only = reference.keys() - candidate.keys()
    old_only = candidate.keys() - reference.keys()
    changed = {key for key in shared if reference[key][0] != candidate[key][0]}
    fields = {}
    for key in changed:
        current, old = reference[key][0], candidate[key][0]
        for field in current.keys() | old.keys():
            if current.get(field) != old.get(field):
                fields[field] = fields.get(field, 0) + 1
    def categories(rows, keys):
        return {category: sum(rows[key][1] == category for key in keys)
                for category in ('closed', 'open_with_email', 'open_without_email')}
    return {
        'user_counts': {'reference': len(reference), 'candidate': len(candidate),
                        'shared': len(shared), 'reference_only': len(current_only),
                        'candidate_only': len(old_only), 'shared_changed': len(changed),
                        'shared_identical': len(shared)-len(changed)},
        'reference_only_categories': categories(reference, current_only),
        'candidate_only_categories': categories(candidate, old_only),
        'shared_field_change_counts': dict(sorted(fields.items())),
    }, current_only, old_only, changed


def foreign_keys(conn):
    return conn.execute("""SELECT ns.nspname,t.relname,a.attname,
      cardinality(c.conkey),cardinality(c.confkey),target.attname
      FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid
      JOIN pg_namespace ns ON ns.oid=t.relnamespace
      JOIN pg_attribute a ON a.attrelid=t.oid AND a.attnum=c.conkey[1]
      JOIN pg_attribute target ON target.attrelid=c.confrelid AND target.attnum=c.confkey[1]
      WHERE c.contype='f' AND c.confrelid='public.users'::regclass
      ORDER BY 1,2,3""").fetchall()


def dependency_counts(conn, schema, table, column, salt, only, changed):
    if not conn.execute('SELECT has_column_privilege(current_user,%s,%s,\'SELECT\')',
                        (sql.Identifier(schema, table).as_string(conn), column)).fetchone()[0]:
        return {'reviewed': False, 'reason': 'read_privilege_missing'}
    counts = {'only_users_rows': 0, 'shared_changed_users_rows': 0}
    if only or changed:
        # Group before hashing: study tables can hold millions of rows, while the
        # number of account groups is small. Raw keys never leave the database.
        query = sql.SQL("SELECT encode(sha256(convert_to(%s || g.account_key::text,'UTF8')),'hex'),g.n "
                        'FROM (SELECT {} account_key,count(*) n FROM {}.{} '
                        'WHERE {} IS NOT NULL GROUP BY {}) g').format(
                            sql.Identifier(column), sql.Identifier(schema), sql.Identifier(table),
                            sql.Identifier(column), sql.Identifier(column))
        with conn.cursor(name='restore_account_dependency') as cur:
            cur.execute(query, (salt,))
            while rows := cur.fetchmany(500):
                for key, count in rows:
                    if key in only:
                        counts['only_users_rows'] += count
                    if key in changed:
                        counts['shared_changed_users_rows'] += count
    return {'reviewed': True, **counts}


def diagnose(reference_dsn, candidate_dsn):
    checked = datetime.now(timezone.utc)
    salt = secrets.token_hex(32)
    with ExitStack() as stack:
        reference = readonly.connect_readonly(stack, reference_dsn)
        candidate = readonly.connect_readonly(stack, candidate_dsn)
        if readonly.identity(reference) == readonly.identity(candidate):
            raise ValueError('A distinct restored candidate is required')
        # An empty table must not hide a missing/different account column schema.
        columns_query = """SELECT attname,format_type(atttypid,atttypmod)
          FROM pg_attribute WHERE attrelid='public.users'::regclass AND attnum>0
          AND NOT attisdropped ORDER BY attname"""
        if reference.execute(columns_query).fetchall() != candidate.execute(columns_query).fetchall():
            raise ValueError('Matching account column schemas required')
        current, old = account_rows(reference, salt), account_rows(candidate, salt)
        summary, current_only, old_only, changed = summarize(current, old)
        current_fks, old_fks = foreign_keys(reference), foreign_keys(candidate)
        if current_fks != old_fks:
            raise ValueError('Matching account foreign-key inventories required')
        dependencies, gaps = [], []
        for schema, table, column, width, target_width, target_column in current_fks:
            label = {'schema': schema, 'table': table, 'column': column}
            if width != 1 or target_width != 1 or target_column != 'id':
                gaps.append({**label, 'reason': 'non_simple_account_id_reference'})
                continue
            ref = dependency_counts(reference, schema, table, column, salt, current_only, changed)
            cand = dependency_counts(candidate, schema, table, column, salt, old_only, changed)
            dependencies.append({**label, 'reference': ref, 'candidate': cand})
            if not ref['reviewed'] or not cand['reviewed']:
                gaps.append({**label, 'reason': 'read_privilege_missing'})
    return {
        'schema': 1, 'source': 'restore-account-diagnosis-v1',
        'status': 'diagnosed_with_dependency_gaps' if gaps else 'diagnosed',
        'checked_at': checked.isoformat(), 'read_only_role': 'mpsc', **summary,
        'direct_foreign_key_counts': dependencies, 'dependency_gaps': gaps,
        'reference_currentness_verified': False, 'repair_authorized': False,
        'promotion_authorized': False,
        'scope': 'all account fields and direct users(id) foreign keys only; excludes '
                 'indirect/unconstrained references, external providers, erasure decisions and final cutoff',
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', required=True)
    parser.parse_args(argv)
    try:
        result = diagnose(os.environ['FINNA_RESTORE_REFERENCE_DSN'],
                          os.environ['FINNA_RESTORE_CANDIDATE_DSN'])
        code = 2 if result['dependency_gaps'] else 0
    except Exception as exc:
        result = {'schema': 1, 'source': 'restore-account-diagnosis-v1',
                  'status': 'error', 'error_kind': type(exc).__name__,
                  'repair_authorized': False, 'promotion_authorized': False}
        code = 1
    result['operator_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['readonly_helper_sha256'] = hashlib.sha256(HELPER.read_bytes()).hexdigest()
    print(json.dumps(result, indent=2))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
