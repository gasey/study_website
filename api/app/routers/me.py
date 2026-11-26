from datetime import date, timedelta
import re
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field

from ..db import cursor
from ..deps import current_user, require_account
from ..schemas import BrowseAllowance, Mistake, PrivateProfile, ProfileUpdate, Progress, DailyActivity, SubjectProgress, ScopeProgress, LearningProgressUpdate

router = APIRouter(prefix="/api/me", tags=["me"])


@router.get('/browse-allowance', response_model=BrowseAllowance)
async def browse_allowance(user_id: Annotated[str, Depends(current_user)]):
    from ..services.browse_allowance import allowance
    async with cursor() as cur:
        return await allowance(cur, user_id)


class EssayDraftUpdate(BaseModel):
    body: str = Field(max_length=30000)


@router.get("/essay-drafts/{question_id}")
async def essay_draft(question_id: str, user_id: Annotated[str, Depends(require_account)]) -> dict:
    async with cursor() as cur:
        await cur.execute(
            "SELECT body,updated_at FROM essay_drafts WHERE user_id=%s AND canonical_id=%s",
            (user_id, question_id),
        )
        row = await cur.fetchone()
    return {"question_id": question_id, "body": row["body"] if row else "",
            "updated_at": row["updated_at"] if row else None}


@router.put("/essay-drafts/{question_id}")
async def save_essay_draft(question_id: str, body: EssayDraftUpdate,
                           user_id: Annotated[str, Depends(require_account)]) -> dict:
    async with cursor() as cur:
        await cur.execute(
            """SELECT 1 FROM canonical_questions q JOIN appearances a ON a.canonical_id=q.id
                WHERE q.id=%s AND q.type='descriptive'
                  AND (a.essay_kind IN ('essay','letter','precis','comprehension') OR a.essay_kind IS NULL)
                LIMIT 1""",
            (question_id,),
        )
        if not await cur.fetchone():
            raise HTTPException(404, "essay prompt not found")
        await cur.execute(
            """INSERT INTO essay_drafts(user_id,canonical_id,body)
               VALUES (%s,%s,%s)
               ON CONFLICT(user_id,canonical_id) DO UPDATE
                 SET body=EXCLUDED.body,updated_at=now()
               RETURNING updated_at""",
            (user_id, question_id, body.body),
        )
        row = await cur.fetchone()
    return {"question_id": question_id, "body": body.body, "updated_at": row["updated_at"]}


def _validate_learning_module(module_id: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,39}", module_id):
        raise HTTPException(422, "invalid module id")
    return module_id


@router.get("/learning-progress/{module_id}")
async def learning_progress(
    module_id: str,
    user_id: Annotated[str, Depends(current_user)],
) -> dict:
    module_id = _validate_learning_module(module_id)
    async with cursor() as cur:
        await cur.execute(
            """SELECT item_id,visited,correct,updated_at
                 FROM module_learning_progress
                WHERE user_id=%s AND module_id=%s
                ORDER BY item_id""",
            (user_id, module_id),
        )
        items = await cur.fetchall()
    return {"module_id": module_id, "items": items}


@router.put("/learning-progress/{module_id}")
async def save_learning_progress(
    module_id: str,
    body: LearningProgressUpdate,
    user_id: Annotated[str, Depends(current_user)],
) -> dict:
    module_id = _validate_learning_module(module_id)
    # Client timestamps are deliberately ignored; server time is authoritative.
    async with cursor() as cur:
        for item in body.items:
            await cur.execute(
                """INSERT INTO module_learning_progress(user_id,module_id,item_id,visited,correct)
                   VALUES (%s,%s,%s,%s,%s)
                   ON CONFLICT(user_id,module_id,item_id) DO UPDATE SET
                     visited=EXCLUDED.visited,correct=EXCLUDED.correct,updated_at=now()""",
                (user_id, module_id, item.item_id, item.visited, item.correct),
            )
        await cur.execute(
            """SELECT item_id,visited,correct,updated_at
                 FROM module_learning_progress
                WHERE user_id=%s AND module_id=%s
                ORDER BY item_id""",
            (user_id, module_id),
        )
        items = await cur.fetchall()
    return {"module_id": module_id, "items": items}


class ExamProgressSummary(BaseModel):
    collection_id: str
    answered: int
    correct: int
    unique_questions: int
    accuracy: float


@router.get("/exam-bookmarks")
async def exam_bookmarks(user_id: Annotated[str, Depends(current_user)]) -> dict:
    async with cursor() as cur:
        await cur.execute("SELECT collection_id,is_primary FROM user_exam_bookmarks WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
        rows = await cur.fetchall()
    return {"collection_ids": [row["collection_id"] for row in rows],"primary_collection_id":next((r['collection_id'] for r in rows if r['is_primary']),None)}


@router.put('/exam-bookmarks/{collection_id}/primary')
async def primary_exam(collection_id:str,user_id:Annotated[str,Depends(require_account)]):
    async with cursor() as cur:
        await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(user_id,))
        await cur.execute("SELECT 1 FROM collections WHERE id=%s AND kind='exam' AND visibility='public'",(collection_id,))
        if not await cur.fetchone():raise HTTPException(404,'Published exam not found')
        await cur.execute('UPDATE user_exam_bookmarks SET is_primary=false WHERE user_id=%s AND is_primary',(user_id,))
        await cur.execute('''INSERT INTO user_exam_bookmarks(user_id,collection_id,is_primary) VALUES(%s,%s,true)
          ON CONFLICT(user_id,collection_id) DO UPDATE SET is_primary=true''',(user_id,collection_id))
    return {'primary_collection_id':collection_id}


@router.put("/exam-bookmarks/{collection_id}")
async def save_exam_bookmark(collection_id: str, user_id: Annotated[str, Depends(current_user)]) -> dict:
    async with cursor() as cur:
        await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(user_id,))
        await cur.execute("SELECT kind FROM collections WHERE id=%s AND visibility='public'", (collection_id,))
        collection=await cur.fetchone()
        if not collection:
            raise HTTPException(404, "exam collection not found")
        await cur.execute('''INSERT INTO user_exam_bookmarks(user_id,collection_id,is_primary)
          VALUES(%s,%s,%s AND NOT EXISTS(SELECT 1 FROM user_exam_bookmarks WHERE user_id=%s AND is_primary))
          ON CONFLICT DO NOTHING''',(user_id,collection_id,collection['kind']=='exam',user_id))
    return {"saved": True, "collection_id": collection_id}


@router.delete("/exam-bookmarks/{collection_id}")
async def remove_exam_bookmark(collection_id: str, user_id: Annotated[str, Depends(current_user)]) -> dict:
    async with cursor() as cur:
        await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(user_id,))
        await cur.execute("DELETE FROM user_exam_bookmarks WHERE user_id=%s AND collection_id=%s RETURNING is_primary", (user_id, collection_id))
        removed=await cur.fetchone()
        if removed and removed['is_primary']:
            await cur.execute('''UPDATE user_exam_bookmarks SET is_primary=true WHERE user_id=%s AND collection_id=(
              SELECT b.collection_id FROM user_exam_bookmarks b JOIN collections c ON c.id=b.collection_id
              WHERE b.user_id=%s AND c.visibility='public' AND c.kind='exam' ORDER BY b.created_at DESC,b.collection_id LIMIT 1)''',(user_id,user_id))
    return {"saved": False, "collection_id": collection_id}


@router.get("/exam-progress", response_model=list[ExamProgressSummary])
async def exam_progress(user_id: Annotated[str, Depends(current_user)]) -> list[ExamProgressSummary]:
    async with cursor() as cur:
        await cur.execute(
            """SELECT collection_id, COUNT(*)::int AS answered,
                      COUNT(*) FILTER (WHERE correct)::int AS correct,
                      COUNT(DISTINCT canonical_id)::int AS unique_questions,
                      CASE WHEN COUNT(*)=0 THEN 0 ELSE ROUND(100.0*COUNT(*) FILTER (WHERE correct)/COUNT(*),1) END AS accuracy
                 FROM attempts WHERE user_id=%s AND collection_id IS NOT NULL
                GROUP BY collection_id""",
            (user_id,),
        )
        return [ExamProgressSummary(**row) for row in await cur.fetchall()]


@router.get("/progress", response_model=Progress)
async def my_progress(
    user_id: Annotated[str, Depends(current_user)], detail: bool = False,
    collection_id: str | None = Query(None, min_length=2, max_length=80),
    section_path: str | None = Query(None, min_length=2, max_length=160),
) -> Progress:
    if section_path and not collection_id:
        raise HTTPException(422,"section_path requires collection_id")
    scope = (" AND collection_id=%s" if collection_id else "") + (" AND section_path=%s" if section_path else "")
    scoped_params = (user_id,) + ((collection_id,) if collection_id else ()) + ((section_path,) if section_path else ())
    async with cursor() as cur:
        await cur.execute('SELECT email IS NOT NULL AS account FROM users WHERE id=%s',(user_id,))
        identity=await cur.fetchone()
        if identity and identity['account']:
            from ..services.activity_progress import read
            return await read(cur,user_id,detail,collection_id,section_path)
        await cur.execute(
            f"""SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date AS today,
                      COUNT(*)::int AS answered,
                      COUNT(*) FILTER (WHERE correct)::int AS correct,
                      COUNT(DISTINCT canonical_id)::int AS unique_questions,
                      MAX(at) AS last_active_at
                 FROM attempts WHERE user_id = %s{scope}""",
            scoped_params,
        )
        totals = await cur.fetchone() or {}
        if not detail:
            answered = totals.get("answered", 0) or 0
            correct = totals.get("correct", 0) or 0
            return Progress(
                answered=answered, correct=correct,
                unique_questions=totals.get("unique_questions", 0) or 0,
                accuracy=round(correct / answered * 100, 1) if answered else 0,
                last_active_at=totals.get("last_active_at"),
            )
        await cur.execute(
            f"""SELECT (at AT TIME ZONE 'Asia/Kolkata')::date AS day, COUNT(*)::int AS answered,
                      COUNT(*) FILTER (WHERE correct)::int AS correct
                 FROM attempts
                WHERE user_id=%s{scope} AND at >= (((now() AT TIME ZONE 'Asia/Kolkata')::date-29)::timestamp AT TIME ZONE 'Asia/Kolkata')
                GROUP BY (at AT TIME ZONE 'Asia/Kolkata')::date ORDER BY day""",
            scoped_params,
        )
        daily_rows = await cur.fetchall()
        await cur.execute(
            f"""SELECT qc.subject_id, qc.subject_label AS subject,
                      COUNT(*)::int AS answered,
                      COUNT(*) FILTER (WHERE a.correct)::int AS correct,
                      COUNT(DISTINCT a.canonical_id)::int AS unique_questions
                 FROM attempts a
                 JOIN question_classifications qc ON qc.question_id=a.canonical_id
                    AND qc.review_status='approved'
                WHERE a.user_id=%s{scope.replace('collection_id','a.collection_id').replace('section_path','a.section_path')} AND a.canonical_id IS NOT NULL
                GROUP BY qc.subject_id,qc.subject_label
                ORDER BY answered DESC,qc.subject_label""",
            scoped_params,
        )
        subjects = [SubjectProgress(**r) for r in await cur.fetchall()]
        if collection_id:
            await cur.execute(
                f"""SELECT COALESCE(a.section_path,'unsectioned') AS scope_id,
                          COALESCE(cs.title,'Other module practice') AS label,
                          COUNT(*)::int AS answered,
                          COUNT(*) FILTER (WHERE a.correct)::int AS correct,
                          COUNT(DISTINCT a.canonical_id)::int AS unique_questions,
                          CASE WHEN COUNT(*)=0 THEN 0 ELSE ROUND(100.0*COUNT(*) FILTER (WHERE a.correct)/COUNT(*),1) END AS accuracy
                     FROM attempts a
                     LEFT JOIN collections c ON c.id=a.collection_id
                     LEFT JOIN collection_sections cs ON cs.collection_id=a.collection_id
                       AND cs.version=c.live_version AND cs.path=a.section_path
                     WHERE a.user_id=%s AND a.collection_id=%s{(' AND a.section_path=%s' if section_path else '')}
                     GROUP BY a.section_path,cs.title ORDER BY answered DESC,label""",
                (user_id,collection_id) + ((section_path,) if section_path else ()),
            )
            sections = [ScopeProgress(**r) for r in await cur.fetchall()]
            collections = []
        else:
            await cur.execute(
                """SELECT COALESCE(a.collection_id,'general') AS scope_id,
                          COALESCE(c.title,'General study') AS label,
                          COUNT(*)::int AS answered,
                          COUNT(*) FILTER (WHERE a.correct)::int AS correct,
                          COUNT(DISTINCT a.canonical_id)::int AS unique_questions,
                          CASE WHEN COUNT(*)=0 THEN 0 ELSE ROUND(100.0*COUNT(*) FILTER (WHERE a.correct)/COUNT(*),1) END AS accuracy
                     FROM attempts a LEFT JOIN collections c ON c.id=a.collection_id
                    WHERE a.user_id=%s GROUP BY a.collection_id,c.title ORDER BY answered DESC,label""",
                (user_id,),
            )
            collections = [ScopeProgress(**r) for r in await cur.fetchall()]
            sections = []

    days = [DailyActivity(day=r["day"].isoformat(), answered=r["answered"], correct=r["correct"]) for r in daily_rows]
    activity_days = {date.fromisoformat(row.day) for row in days}
    today = totals.get("today") or date.today()
    anchor = today if today in activity_days else today - timedelta(days=1)
    streak = 0
    while anchor - timedelta(days=streak) in activity_days:
        streak += 1
    answered = totals.get("answered", 0) or 0
    correct = totals.get("correct", 0) or 0
    return Progress(
        answered=answered,
        correct=correct,
        unique_questions=totals.get("unique_questions", 0) or 0,
        accuracy=round(correct / answered * 100, 1) if answered else 0,
        current_streak=streak,
        active_days_30=len(days),
        last_active_at=totals.get("last_active_at"),
        daily_activity=days,
        subjects=subjects,
        collections=collections,
        sections=sections,
    )


@router.get("/profile", response_model=PrivateProfile)
async def my_profile(user_id: Annotated[str, Depends(current_user)]) -> PrivateProfile:
    async with cursor() as cur:
        await cur.execute(
            "SELECT avatar,avatar_version,name,handle,role,GREATEST(1,floor(sqrt(GREATEST(0,COALESCE((SELECT sum(xp) FROM reward_ledger WHERE user_id=users.id),0))/40.0)))::int AS level,created_at,email,CASE WHEN account_has_pro(id) THEN 'pro' ELSE 'free' END AS plan_code,CASE WHEN EXISTS(SELECT 1 FROM reward_redemptions rr WHERE rr.user_id=users.id AND rr.starts_at<=now() AND rr.ends_at>now()) THEN 'rewarded' WHEN EXISTS(SELECT 1 FROM billing_access_grants bg WHERE bg.user_id=users.id AND bg.starts_at<=now() AND bg.ends_at>now()) THEN 'granted' WHEN NOT account_has_pro(id) THEN 'free' ELSE plan_status END AS plan_status,trial_ends_at,plan_ends_at FROM users WHERE id=%s",
            (user_id,),
        )
        user = await cur.fetchone()
    if user is None:
        raise HTTPException(404, "profile not found")
    progress = await my_progress(user_id, detail=True, collection_id=None, section_path=None)
    return PrivateProfile(**user, account_type="account" if user.get("email") else "browser", progress=progress)


@router.patch("/profile", response_model=PrivateProfile)
async def update_profile(
    body: ProfileUpdate,
    user_id: Annotated[str, Depends(current_user)],
) -> PrivateProfile:
    name = (body.name or "").strip() or None
    if name and any(ord(char) < 32 for char in name):
        raise HTTPException(422, "name must not contain control characters")
    async with cursor() as cur:
        await cur.execute(
            "UPDATE users SET name=%s,identity_version=identity_version+1 WHERE id=%s RETURNING avatar,avatar_version,name,handle,role,GREATEST(1,floor(sqrt(GREATEST(0,COALESCE((SELECT sum(xp) FROM reward_ledger WHERE user_id=users.id),0))/40.0)))::int AS level,created_at,email,CASE WHEN account_has_pro(id) THEN 'pro' ELSE 'free' END AS plan_code,CASE WHEN EXISTS(SELECT 1 FROM reward_redemptions rr WHERE rr.user_id=users.id AND rr.starts_at<=now() AND rr.ends_at>now()) THEN 'rewarded' WHEN EXISTS(SELECT 1 FROM billing_access_grants bg WHERE bg.user_id=users.id AND bg.starts_at<=now() AND bg.ends_at>now()) THEN 'granted' WHEN NOT account_has_pro(id) THEN 'free' ELSE plan_status END AS plan_status,trial_ends_at,plan_ends_at",
            (name, user_id),
        )
        user = await cur.fetchone()
    if user is None:
        raise HTTPException(404, "profile not found")
    progress = await my_progress(user_id, detail=True, collection_id=None, section_path=None)
    return PrivateProfile(**user, account_type="account" if user.get("email") else "browser", progress=progress)


@router.get("/mistakes", response_model=list[Mistake])
async def my_mistakes(
    user_id: Annotated[str, Depends(current_user)],
    limit: int = Query(50, ge=1, le=200),
    collection_id: str | None = Query(None,min_length=2,max_length=80),
    section_path: str | None = Query(None,min_length=2,max_length=160),
) -> list[Mistake]:
    """Questions this device has got wrong and not since got right.

    A question answered wrong in March and right in April is not a mistake
    any more — showing it would waste the learner's time and understate
    their progress. So the filter is on the LATEST attempt per question,
    not on the existence of any wrong one.
    """
    if section_path and not collection_id:
        raise HTTPException(422,"section_path requires collection_id")
    async with cursor() as cur:
        await cur.execute("SELECT account_has_pro(id) AS pro FROM users WHERE id=%s",(user_id,))
        entitlement=await cur.fetchone()
    if not entitlement or not entitlement["pro"]:
        limit=min(limit,20)
    scope = (" AND collection_id=%s" if collection_id else "") + (" AND section_path=%s" if section_path else "")
    scope_params = ((collection_id,) if collection_id else ()) + ((section_path,) if section_path else ())
    params = (user_id,) + scope_params + (user_id,) + scope_params + (limit,)
    async with cursor() as cur:
        await cur.execute(
            f"""WITH latest AS (
                 SELECT DISTINCT ON (canonical_id)
                        canonical_id, correct, chosen_text, at
                   FROM attempts
                  WHERE user_id = %s{scope} AND canonical_id IS NOT NULL
                  ORDER BY canonical_id, at DESC
               )
               SELECT q.id, q.question, q.options, q.answer_text, q.explanation,
                      l.chosen_text, l.at AS last_attempt,
                      (SELECT COUNT(*) FROM attempts a2
                        WHERE a2.user_id = %s{scope.replace('collection_id','a2.collection_id').replace('section_path','a2.section_path')} AND a2.canonical_id = q.id
                          AND NOT a2.correct)::int AS times_wrong
                 FROM latest l
                 JOIN canonical_questions q ON q.id = l.canonical_id
                WHERE NOT l.correct
                ORDER BY l.at DESC
                LIMIT %s""",
            params,
        )
        return [Mistake(**r) for r in await cur.fetchall()]


@router.get('/score-summary')
async def score_summary(user_id:Annotated[str,Depends(current_user)]):
    async with cursor() as cur:
        await cur.execute('''WITH latest AS (
           SELECT DISTINCT ON (aa.attempt_id) aa.attempt_id,aa.payload
           FROM attempt_assessments aa JOIN attempts a ON a.id=aa.attempt_id
           WHERE a.user_id=%s AND a.context='practice' ORDER BY aa.attempt_id,aa.id DESC)
           SELECT count(*)::int AS assessed,
             count(*) FILTER (WHERE payload->>'outcome'='correct')::int AS correct,
             count(*) FILTER (WHERE payload->>'outcome'='wrong')::int AS wrong,
             count(*) FILTER (WHERE payload->>'outcome'='excluded')::int AS excluded FROM latest''',(user_id,))
        practice=await cur.fetchone()
        await cur.execute("SELECT count(*)::int AS total FROM attempts WHERE user_id=%s AND context='practice'",(user_id,))
        practice['total']=(await cur.fetchone())['total']
        await cur.execute('SELECT count(*)::int AS completed,COALESCE(sum(score),0)::float AS original_marks FROM mock_sessions WHERE user_id=%s AND submitted_at IS NOT NULL',(user_id,))
        mocks=await cur.fetchone()
    return {'practice_adjusted':practice,'mocks_original':mocks,'profile_basis':'Recorded original attempts and original mock scores. Adjusted assessments are shown separately; excluded questions are not marked wrong.'}


HOME_WIDGET_IDS = (
    "kpi",
    "today",
    "leaderboard",
    "games",
    "discover",
    "pulse",
    "return",
    "tracked_exams",
    "subjects",
    "feed",
    "vault",
    "calendar",
    "shortcuts",
    "desk",
    "quests",
    "explore",
)
HOME_WIDGET_SET = set(HOME_WIDGET_IDS)
HOME_PRESET_HIDDEN: dict[str, list[str]] = {
    "minimal": [
        "kpi",
        "leaderboard",
        "games",
        "pulse",
        "tracked_exams",
        "feed",
        "vault",
        "calendar",
        "shortcuts",
        "desk",
        "explore",
    ],
    "balanced": [
        "pulse",
        "feed",
        "vault",
        "calendar",
        "desk",
    ],
    "everything": [],
}


class HomePreferencesUpdate(BaseModel):
    preset: Literal["minimal", "balanced", "everything"] = "balanced"
    hidden: list[str] = Field(default_factory=list, max_length=40)
    onboarded: bool = True


def _normalize_hidden(items: list[str] | None) -> list[str]:
    if not items:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if isinstance(item, str) and item in HOME_WIDGET_SET and item not in seen:
            seen.add(item)
            out.append(item)
    return out


@router.get("/home-preferences")
async def get_home_preferences(user_id: Annotated[str, Depends(current_user)]) -> dict:
    async with cursor() as cur:
        await cur.execute(
            "SELECT prefs, onboarded_at, updated_at FROM user_home_preferences WHERE user_id=%s",
            (user_id,),
        )
        row = await cur.fetchone()
    if not row:
        return {
            "exists": False,
            "preset": "balanced",
            "hidden": list(HOME_PRESET_HIDDEN["balanced"]),
            "onboarded": False,
            "onboarded_at": None,
            "updated_at": None,
        }
    raw = row["prefs"] if isinstance(row["prefs"], dict) else {}
    preset = raw.get("preset") if raw.get("preset") in HOME_PRESET_HIDDEN else "balanced"
    hidden = _normalize_hidden(raw.get("hidden")) if "hidden" in raw else list(HOME_PRESET_HIDDEN[preset])
    onboarded = bool(raw.get("onboarded", row["onboarded_at"] is not None))
    return {
        "exists": True,
        "preset": preset,
        "hidden": hidden,
        "onboarded": onboarded,
        "onboarded_at": row["onboarded_at"],
        "updated_at": row["updated_at"],
    }


@router.put("/home-preferences")
async def save_home_preferences(
    body: HomePreferencesUpdate,
    user_id: Annotated[str, Depends(current_user)],
) -> dict:
    hidden = _normalize_hidden(body.hidden)
    payload = {
        "preset": body.preset,
        "hidden": hidden,
        "onboarded": bool(body.onboarded),
    }
    async with cursor() as cur:
        await cur.execute(
            """INSERT INTO user_home_preferences (user_id, prefs, onboarded_at, updated_at)
               VALUES (%s, %s, CASE WHEN %s THEN now() ELSE NULL END, now())
               ON CONFLICT (user_id) DO UPDATE SET
                 prefs = EXCLUDED.prefs,
                 onboarded_at = COALESCE(user_home_preferences.onboarded_at, EXCLUDED.onboarded_at),
                 updated_at = now()
               RETURNING onboarded_at, updated_at""",
            (user_id, Jsonb(payload), bool(body.onboarded)),
        )
        row = await cur.fetchone()
    return {
        "exists": True,
        **payload,
        "onboarded_at": row["onboarded_at"] if row else None,
        "updated_at": row["updated_at"] if row else None,
    }


from . import profile_identity
router.include_router(profile_identity.router)

from . import account_tools
router.include_router(account_tools.router)
