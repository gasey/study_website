"""Source-bound independent or owner approval, plus an exact-payload AI scope.

The exceptional scope is installed with a reviewed release, not supplied by a
caller. It authorizes no other paper, source, owner or edited payload. It never
creates an independent-person inspection or changes frozen editorial assignments.
"""
import json
from pathlib import Path
from .review_policy import digest
from .review_identity import require_role,grants

SCOPE_FILE=Path(__file__).resolve().parents[1]/'data/gazetted-owner-ai-review-20261104.json'


def owner_ai_evidence(draft,owner_id):
 try:scope=json.loads(SCOPE_FILE.read_text())
 except (OSError,ValueError):raise ValueError('No owner-authorized AI review scope is installed')
 entry=next((x for x in scope.get('drafts',[]) if x['id']==draft['id']),None)
 if (scope.get('owner_id')!=owner_id or not entry
     or entry['source_sha256']!=draft['source_sha256']
     or entry['payload_hash']!=digest(draft['payload'])):
  raise ValueError('This paper or its current content is outside the owner-authorized AI review')
 if not scope.get('authorization') or not scope.get('model') or not scope.get('evidence_sha256'):
  raise ValueError('AI review attribution/evidence is incomplete')
 return {'scope_id':scope['id'],'scope_hash':digest(scope),'authorization':scope['authorization'],
         'model':scope['model'],'evidence_sha256':scope['evidence_sha256'],
         'draft_id':draft['id'],'source_sha256':draft['source_sha256'],'payload_hash':entry['payload_hash']}


def owner_preview_hash(draft,version=None):
 return digest({'source_sha256':draft['source_sha256'],'payload':draft['payload'],'version':draft['version'] if version is None else version})


def owner_evidence(draft,owner_id,preview_version):
 return {'approval_kind':'owner','owner_id':owner_id,'author_id':draft['author_id'],
   'source_sha256':draft['source_sha256'],'payload_hash':digest(draft['payload']),
   'submission_id':draft['submission_id'],'preview_version':preview_version,
   'preview_hash':owner_preview_hash(draft,preview_version),
   'inspections':['source','options-and-figures','answer-evidence','explanation-availability']}


async def validate_approval(cur,draft,review):
 if not review:raise ValueError('A matching paper approval is required')
 kind=review.get('review_kind','independent');reviewer=review['reviewer_id']
 if kind=='owner':
  await require_role(cur,reviewer,roles=('owner',))
  evidence=review.get('review_evidence') or {}
  if type(evidence.get('preview_version')) is not int or evidence!=owner_evidence(draft,reviewer,evidence['preview_version']) or review.get('review_model') is not None:
   raise ValueError('Owner decision no longer matches this source, author or submission')
  return
 if kind=='owner_ai':
  await require_role(cur,reviewer,roles=('owner',))
  expected=owner_ai_evidence(draft,reviewer)
  if review.get('review_model')!=expected['model'] or review.get('review_evidence')!=expected:
   raise ValueError('AI review evidence no longer matches the authorized source/content')
  return
 if kind!='independent' or reviewer==draft['author_id']:raise ValueError('Independent paper review is missing')
 await cur.execute("SELECT 1 FROM paper_workbench_history WHERE draft_id=%s AND actor_id=%s AND action IN ('created','saved') LIMIT 1",(draft['id'],reviewer))
 if await cur.fetchone():raise ValueError('An editor cannot provide independent approval')
 if not set(await grants(cur,reviewer))&{'owner','publisher','senior','reviewer'}:
  await cur.execute('SELECT 1 FROM paper_workbench_reviewers WHERE draft_id=%s AND user_id=%s AND active',(draft['id'],reviewer))
  if not await cur.fetchone():raise ValueError('Assigned paper reviewer access was revoked')
