"""Central workflow storage only. No bank writes, decisions or publication APIs."""
import hashlib
import json
import secrets
import sqlite3
import time
from collections import Counter, defaultdict
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(path, timeout=120, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
          PRAGMA journal_mode=WAL;
          CREATE TABLE IF NOT EXISTS targets(
            canonical_id TEXT PRIMARY KEY, appearance_id TEXT UNIQUE NOT NULL,
            paper_id TEXT NOT NULL, lane TEXT NOT NULL, state TEXT NOT NULL,
            present INTEGER NOT NULL, payload TEXT NOT NULL, legacy TEXT);
          CREATE TABLE IF NOT EXISTS exclusions(id TEXT PRIMARY KEY, kind TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS packets(
            id TEXT PRIMARY KEY, worker TEXT NOT NULL, model TEXT NOT NULL,
            token_hash TEXT NOT NULL, state TEXT NOT NULL, created REAL NOT NULL,
            touched REAL NOT NULL, payload TEXT NOT NULL, result TEXT,
            result_hash TEXT);
          CREATE TABLE IF NOT EXISTS reservations(
            canonical_id TEXT PRIMARY KEY, appearance_id TEXT UNIQUE NOT NULL,
            packet_id TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY, at REAL NOT NULL, packet_id TEXT,
            action TEXT NOT NULL, detail TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS drafts(
            id INTEGER PRIMARY KEY, packet_id TEXT NOT NULL, at REAL NOT NULL,
            sha256 TEXT NOT NULL, payload TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        ''')

    def event(self, packet, action, detail):
        self.db.execute('INSERT INTO events(at,packet_id,action,detail) VALUES(?,?,?,?)',
                        (time.time(), packet, action, json.dumps(detail)))

    def transaction(self, fn):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            result = fn()
            self.db.execute('COMMIT')
            return result
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def sync(self, inventory, exclusions, followups, family):
        """Additive history; fresh roster replaces scheduling metadata, not results."""
        def run():
            for kind in ('canonical', 'appearance'):
                for identity in exclusions[kind]:
                    self.db.execute('INSERT OR IGNORE INTO exclusions VALUES(?,?)',
                                    (identity, kind))
            excluded = {r[0] for r in self.db.execute('SELECT id FROM exclusions')}
            completed = set(inventory.get('completed_ids', []))
            excluded.update(completed)
            docs = {d['paper_id'] for d in inventory['documents'] if d.get('sha256')}
            by_paper = defaultdict(list)
            for a in inventory['appearances']:
                by_paper[a['paper_id']].append(a)
            families = defaultdict(list)
            for paper, rows in by_paper.items():
                group = family(paper)
                if group:
                    families[group[0]].append((paper, group[1], rows))
            alternate = set()
            for variants in families.values():
                # Scheduling only. Shelved alternatives are never marked reviewed.
                variants.sort(key=lambda v: (v[0] not in docs, v[1] not in ('A', '1'),
                                            -sum(bool(r.get('page')) for r in v[2]), v[0]))
                alternate.update(v[0] for v in variants[1:])
            follow = {r['canonical_id']: json.loads(r['legacy']) for r in self.db.execute(
                "SELECT canonical_id,legacy FROM targets WHERE lane='followup' AND legacy IS NOT NULL")}
            follow.update({f['canonical_id']: f for f in followups})
            for cid in completed:
                follow.pop(cid, None)
            appearances = sorted(inventory['appearances'], key=lambda a: (
                a['paper_id'] in alternate, not a.get('is_primary', False), a['paper_id'], a['id']))
            chosen = {}
            for a in appearances:
                if a.get('canonical_id'):
                    chosen.setdefault(a['canonical_id'], a)
            by_aid = {a['id']: a for a in appearances}
            for cid, f in follow.items():
                if f['appearance_id'] in by_aid:
                    chosen[cid] = by_aid[f['appearance_id']]
            self.db.execute('UPDATE targets SET present=0')
            for cid, a in chosen.items():
                legacy = follow.get(cid)
                lane = 'followup' if legacy else 'new'
                state = ('ready' if legacy else 'excluded' if cid in excluded or a['id'] in excluded
                         else 'alternate' if a['paper_id'] in alternate else 'ready')
                old = self.db.execute('SELECT * FROM targets WHERE canonical_id=?', (cid,)).fetchone()
                if old and old['state'] in ('claimed', 'submitted', 'deferred'):
                    self.db.execute('UPDATE targets SET present=1,payload=? WHERE canonical_id=?',
                                    (json.dumps(a), cid))
                    continue
                # A newer local saved review can exclude ready work; never reopen a submission.
                self.db.execute('''INSERT INTO targets VALUES(?,?,?,?,?,1,?,?)
                  ON CONFLICT(canonical_id) DO UPDATE SET appearance_id=excluded.appearance_id,
                  paper_id=excluded.paper_id,lane=excluded.lane,state=excluded.state,present=1,
                  payload=excluded.payload,legacy=excluded.legacy''',
                  (cid, a['id'], a['paper_id'], lane, state, json.dumps(a),
                   json.dumps(legacy) if legacy else None))
            self.db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',
                            ('inventory', json.dumps({'at': inventory['exported_at'],
                                                     'sha256': digest(inventory)})))
            self.event(None, 'sync', {'inventory': inventory['exported_at'],
                                     'followups': len(follow), 'excluded_ids': len(excluded)})
            return self.status()
        return self.transaction(run)

    def owned(self, packet_id, token, active=True):
        p = self.db.execute('SELECT * FROM packets WHERE id=?', (packet_id,)).fetchone()
        if not p or not secrets.compare_digest(p['token_hash'], digest(token)):
            raise ValueError('Packet/token does not match. Do not take another worker’s packet.')
        if active and p['state'] != 'claimed':
            raise ValueError('Packet is already ' + p['state'])
        return p

    def claim(self, worker, model, lane, size, fetch, packet_id=None, token=None):
        if not worker.strip() or not model.strip() or not 1 <= size <= 100:
            raise ValueError('Worker/model required; packet size must be 1–100')
        if lane not in ('new', 'followup'):
            raise ValueError('Invalid lane')
        def run():
            if packet_id and self.db.execute('SELECT 1 FROM packets WHERE id=?', (packet_id,)).fetchone():
                previous = self.owned(packet_id, token, active=False)
                if previous['worker'] != worker or previous['model'] != model:
                    raise ValueError('Claim retry identity changed')
                return {'packet': json.loads(previous['payload']), 'token': token,
                        'state': previous['state'], 'idempotent': True}
            if self.db.execute("SELECT 1 FROM packets WHERE worker=? AND state='claimed'", (worker,)).fetchone():
                raise ValueError('Worker already has an active packet; resume it using its saved token')
            paper = self.db.execute('''SELECT paper_id FROM targets WHERE present=1 AND
              state='ready' AND lane=? ORDER BY
              CASE WHEN json_extract(payload,'$.page') IS NULL THEN 1 ELSE 0 END,
              paper_id,appearance_id LIMIT 1''', (lane,)).fetchone()
            if not paper:
                return {'empty': True, 'lane': lane}
            rows = self.db.execute('''SELECT * FROM targets WHERE present=1 AND state='ready'
              AND lane=? AND paper_id=? ORDER BY appearance_id LIMIT ?''',
                                   (lane, paper[0], size)).fetchall()
            packet = fetch([dict(r) for r in rows])
            expected = {(r['canonical_id'], r['appearance_id']) for r in rows}
            actual = {(i['canonical_id'], i['appearance_id']) for i in packet['items']}
            if actual != expected or len(packet['items']) != len(rows):
                raise ValueError('Fresh packet does not match reserved identities')
            pid = packet_id or 'tq_' + secrets.token_hex(12)
            claim_token = token or secrets.token_urlsafe(32)
            packet.update(packet_id=pid, worker=worker, model=model, lane=lane,
                          policy_version='study-tagging-v1', source_inspected=False,
                          publication_authorized=False)
            now = time.time()
            self.db.execute('INSERT INTO packets VALUES(?,?,?,?,?,?,?,?,NULL,NULL)',
                            (pid, worker, model, digest(claim_token), 'claimed', now, now, json.dumps(packet)))
            for row in rows:
                self.db.execute('INSERT INTO reservations VALUES(?,?,?)',
                                (row['canonical_id'], row['appearance_id'], pid))
                self.db.execute("UPDATE targets SET state='claimed' WHERE canonical_id=?", (row['canonical_id'],))
            self.event(pid, 'claim', {'worker': worker, 'model': model, 'targets': len(rows)})
            return {'packet': packet, 'token': claim_token}
        return self.transaction(run)

    def resume(self, pid, token):
        def run():
            p = self.owned(pid, token, active=False)
            self.db.execute('UPDATE packets SET touched=? WHERE id=?', (time.time(), pid))
            draft = self.db.execute('SELECT payload FROM drafts WHERE packet_id=? ORDER BY id DESC LIMIT 1', (pid,)).fetchone()
            return {'packet': json.loads(p['payload']), 'state': p['state'],
                    'draft': json.loads(draft[0]) if draft else None,
                    'result': json.loads(p['result']) if p['result'] else None}
        return self.transaction(run)

    def save(self, pid, token, draft):
        def run():
            self.owned(pid, token)
            sha = digest(draft)
            self.db.execute('INSERT INTO drafts(packet_id,at,sha256,payload) VALUES(?,?,?,?)',
                            (pid, time.time(), sha, json.dumps(draft)))
            self.db.execute('UPDATE packets SET touched=? WHERE id=?', (time.time(), pid))
            self.event(pid, 'draft', {'sha256': sha})
            return {'saved': True, 'sha256': sha, 'meaning': 'Draft only; not reviewed or published'}
        return self.transaction(run)

    def submit(self, pid, token, candidates, validate):
        def run():
            p = self.owned(pid, token, active=False)
            sha = digest(candidates)
            if p['state'] == 'submitted' and p['result_hash'] == sha:
                return {'submitted': True, 'sha256': sha, 'idempotent': True}
            if p['state'] != 'claimed':
                raise ValueError('Packet is already ' + p['state'])
            packet = json.loads(p['payload'])
            validate(packet, candidates)
            self.db.execute("UPDATE packets SET state='submitted',touched=?,result=?,result_hash=? WHERE id=?",
                            (time.time(), json.dumps(candidates), sha, pid))
            self.db.execute("UPDATE targets SET state='submitted' WHERE canonical_id IN (SELECT canonical_id FROM reservations WHERE packet_id=?)", (pid,))
            # Reservations survive submission: no competing new claim can reuse these IDs.
            self.event(pid, 'submit', {'sha256': sha, 'actions': dict(Counter(c['action'] for c in candidates))})
            return {'submitted': True, 'sha256': sha, 'meaning': 'Saved pending candidates; no publication or approval'}
        return self.transaction(run)

    def release(self, pid, token, reason, defer=False):
        if len(reason.strip()) < 10:
            raise ValueError('Give a useful reason (at least 10 characters)')
        def run():
            self.owned(pid, token)
            state = 'deferred' if defer else 'ready'
            self.db.execute('UPDATE targets SET state=? WHERE canonical_id IN (SELECT canonical_id FROM reservations WHERE packet_id=?)', (state, pid))
            self.db.execute('DELETE FROM reservations WHERE packet_id=?', (pid,))
            self.db.execute("UPDATE packets SET state='released',touched=? WHERE id=?", (time.time(), pid))
            self.event(pid, 'defer' if defer else 'release', {'reason': reason})
            return {'released': True, 'target_state': state, 'drafts_preserved': True}
        return self.transaction(run)

    def status(self):
        counts = [dict(r) for r in self.db.execute('SELECT lane,state,count(*) AS targets FROM targets WHERE present=1 GROUP BY lane,state')]
        active = [dict(r) for r in self.db.execute("SELECT id,worker,model,created,touched FROM packets WHERE state='claimed' ORDER BY created")]
        for p in active:
            p['idle_hours'] = round((time.time() - p['touched']) / 3600, 2)
        meta = self.db.execute("SELECT value FROM metadata WHERE key='inventory'").fetchone()
        return {'counts': counts, 'active': active, 'inventory': json.loads(meta[0]) if meta else None,
                'meaning': 'Scheduling/candidate states only; submitted is not published. Claims never expire automatically.'}


def validate_candidates(packet, candidates, current):
    """Evidence structure + live bindings, never a claim of semantic/source inspection."""
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= 100:
        raise ValueError('Expected 1–100 candidate records')
    expected = {(i['canonical_id'], i['appearance_id']): i for i in packet['items']}
    keys = [(c['canonical_id'], c['appearance_id']) for c in candidates]
    if len(set(keys)) != len(keys) or set(keys) != set(expected):
        raise ValueError('Submit exactly one candidate per claimed target')
    fresh = {(i['canonical_id'], i['appearance_id']): i for i in current['items']}
    nodes = {n['id']: n for n in current['taxonomy']}
    def path_valid(path):
        if not isinstance(path, dict) or set(path) != {'subject_id', 'topic_id', 'subtopic_id'} or not path['subject_id']:
            raise ValueError('Use complete subject/topic/subtopic objects')
        if path['subtopic_id'] and not path['topic_id']:
            raise ValueError('Subtopic requires its parent topic')
        parent = None
        for level in ('subject', 'topic', 'subtopic'):
            tid = path[level + '_id']
            if tid is None:
                continue
            n = nodes.get(tid)
            if not n or n.get('active') is False or n['level'] != level or n.get('parent_id') != parent:
                raise ValueError('Invalid active taxonomy path: ' + str(tid))
            parent = tid
    for c in candidates:
        key = (c['canonical_id'], c['appearance_id'])
        item = expected[key]
        live = fresh.get(key)
        if not live or live['source_fingerprint'] != item['source_fingerprint'] or live['documents'] != item['documents']:
            raise ValueError('Source/document changed; preserve draft and refresh the packet explicitly')
        if c.get('source_fingerprint') != item['source_fingerprint'] or c.get('current_primary') != item['snapshot']['record']['classification']:
            raise ValueError('Candidate baseline does not match claimed snapshot')
        if c.get('policy_version') != 'study-tagging-v1' or c.get('review_status') != 'pending':
            raise ValueError('Candidates must use current policy and remain pending')
        if not c.get('reviewer_model') or not c.get('reviewer_tool'):
            raise ValueError('Record the actual reviewer model and tool; do not invent attribution')
        action = c.get('action')
        if action not in ('keep', 'retag', 'hold') or len(c.get('rationale', '').strip()) < 20 or not c.get('tested_skill'):
            raise ValueError('Specific tested skill, rationale and keep/retag/hold action required')
        for field in ('source_issues', 'alternatives'):
            if not isinstance(c.get(field), list):
                raise ValueError('Missing candidate field: ' + field)
        for field in ('taxonomy_gap', 'owner_question', 'context_reason'):
            if field not in c:
                raise ValueError('Missing candidate field: ' + field)
        if action == 'hold':
            if not (c.get('owner_question') or c.get('source_issues') or c.get('taxonomy_gap')):
                raise ValueError('Hold needs an actionable reason')
            continue
        path_valid(c.get('proposed_primary'))
        related = c.get('proposed_related')
        if not isinstance(related, list) or len(related) > 12:
            raise ValueError('Explicit related path list required (maximum 12)')
        for p in related:
            path_valid(p)
        paths = [c['proposed_primary'], *related]
        if len({digest(p) for p in paths}) != len(paths):
            raise ValueError('Duplicate primary/related paths')
        before = item['snapshot']['record']
        unchanged = c['proposed_primary'] == before['classification'] and related == before.get('relatedClassifications', [])
        if (action == 'keep') != unchanged:
            raise ValueError('Keep must preserve exact primary/related paths; retag must change them')
        evidence = c.get('source_evidence') or {}
        if evidence.get('inspected') is not True or type(evidence.get('physical_page')) is not int or evidence['physical_page'] < 1 or len(evidence.get('note', '').strip()) < 20:
            raise ValueError('Keep/retag requires attributed source inspection, page and meaningful evidence note')
        if not any(d['id'] == evidence.get('document_id') and d['sha256'] == evidence.get('sha256') for d in live['documents']):
            raise ValueError('Evidence must bind an exact currently registered source document/hash')
        context = c.get('context_candidate') or {}
        if context.get('time_behavior') not in ('static', 'dated-event', 'changes-over-time', 'unknown') or context.get('reference_basis') not in ('printed', 'exam-date', 'reviewed-source', 'unknown'):
            raise ValueError('Use valid context enums')
        if any(p['topic_id'] == 'general-studies/current-affairs' for p in paths) or context['time_behavior'] in ('dated-event', 'changes-over-time'):
            if not context.get('reference_period') or context['reference_basis'] == 'unknown':
                raise ValueError('Dated/changing facts need supported historical context; otherwise use hold')
