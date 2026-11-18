"""Actual paired-restore receipts; checksum-only backup probes cannot pass this."""
from datetime import datetime
import json,re


def observation(row,now):
    result={'state':'unknown','last_ok':None,'days_since':None,'backup_at':None,
            'note':'No successful paired-backup restore rehearsal recorded.'}
    if not row:return result
    try:
        data=json.loads(row['note'] or '')
        if data.get('schema')!=1 or data.get('source')!='paired-backup-restore-v1':raise ValueError()
        stamp=datetime.fromisoformat(data['completed_at'])
        if stamp.tzinfo is None or (stamp-now).total_seconds()>30:raise ValueError()
        if (stamp-row['last_beat']).total_seconds()>30:raise ValueError()
        if (row['last_beat']-now).total_seconds()>30:raise ValueError()
        last=row['last_ok']
        if last and (last-now).total_seconds()>30:raise ValueError()
        if data.get('state')=='failed':
            if last and (last-stamp).total_seconds()>30:raise ValueError()
            return {**result,'state':'attention','last_ok':last,
                    'days_since':max(0,(now-last).days) if last else None,
                    'note':'Latest restore rehearsal failed; inspect the private operator report.'}
        if data.get('state')!='verified' or last!=stamp:raise ValueError()
        for key in ('archive_sha256','database_sha256','bank_sha256','report_sha256','operator_sha256','api_snapshot_sha256'):
            if not re.fullmatch(r'[0-9a-f]{64}',data.get(key,'')):raise ValueError()
        if any(data.get(key) is not True for key in ('bank_pair_matches','database_restored','files_restored','read_only_role_checked','clone_removed','temporary_files_removed')):raise ValueError()
        if type(data.get('restored_tables')) is not int or data['restored_tables']<1:raise ValueError()
        if type(data.get('restored_files')) is not int or data['restored_files']<1:raise ValueError()
        backup=datetime.fromisoformat(data['backup_at'])
        if backup.tzinfo is None or backup>stamp:raise ValueError()
        days=max(0,(now-last).days)
        return {'state':'attention' if days>=40 else 'healthy','last_ok':last,'days_since':days,
                'backup_at':backup,'note':'Restore rehearsal is 40 days old; run the monthly checklist.' if days>=40 else 'Paired database and archive restored in isolation; temporary resources removed.'}
    except (TypeError,ValueError,KeyError,AttributeError):
        return {**result,'note':'Invalid restore receipt; inspect the private operator report.'}
