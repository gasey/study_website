from ..exam_scope import ExamScope, DEFAULT_SCOPE, pool_view, scope_condition, question_scope
from psycopg.types.json import Jsonb
import random
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from ..config import settings
from ..services import scoring_revisions

from ..db import cursor
from ..deps import current_user
from ..schemas import (
    MockQuestion,
    MockResult,
    MockSession,
    MockStart,
    MockSubmission,
    MockSummary,
    MockReviewRow,
    MockAnswerSave,
)
from ..source_files import source_pdf_url,figure_image_url

router = APIRouter(prefix="/api/mocks", tags=["mocks"])

#: Grace for a submit that was in flight when the clock ran out. Beyond this
#: the attempt still records, but is flagged `late` rather than silently
#: accepted — see migration 0006.
GRACE_SECONDS = 20


async def _candidate_ids(cur, collection_id: str, section_path: str | None,
                        answer_mode: str, exam_scope: ExamScope = DEFAULT_SCOPE) -> list[str]:
    """Scorable question ids for a collection or section.

    Sections may use paper IDs and/or approved taxonomy-v2 IDs. The scorable
    view remains the authority for which keys are eligible for a mock.
    """
    source_view = pool_view('mock_practice', exam_scope) if answer_mode == "derived-practice" else pool_view('scorable', exam_scope)
    if collection_id=='combined-prelims' and section_path=='papers':
        section_path=None
    if section_path:
        await cur.execute(
            """SELECT s.query, s.pins, s.excludes FROM collection_sections s
                 JOIN collections c ON c.id=s.collection_id AND c.live_version=s.version
                WHERE s.collection_id=%s AND s.path=%s""",
            (collection_id, section_path),
        )
    else:
        await cur.execute(
            """SELECT s.query, s.pins, s.excludes FROM collection_sections s
                 JOIN collections c ON c.id=s.collection_id AND c.live_version=s.version
                WHERE s.collection_id=%s""",
            (collection_id,),
        )
    rows = await cur.fetchall()
    if not rows:
        raise HTTPException(404, "no papers for that collection or section")

    candidates: set[str] = set()
    for row in rows:
        query = row["query"] or {}
        pins = row["pins"] or []
        excludes = row["excludes"] or []
        where = ["v.id <> ALL(%s)", "NOT EXISTS (SELECT 1 FROM appearances ca JOIN papers cp ON cp.id=ca.paper_id WHERE ca.canonical_id=v.id AND cp.exam_type='Community')"]
        params: list[object] = [excludes]
        selected = []
        if "paper_ids" in query:
            selected.append("a.paper_id = ANY(%s)")
            params.append([str(p) for p in query["paper_ids"]])
        if query.get("subject_id"):
            selected.append("EXISTS (SELECT 1 FROM v_question_paths qc WHERE qc.question_id=v.id AND qc.review_status='approved' AND qc.subject_id=%s)")
            params.append(query["subject_id"])
        if query.get("topic_id"):
            selected.append("EXISTS (SELECT 1 FROM v_question_paths qc WHERE qc.question_id=v.id AND qc.review_status='approved' AND qc.topic_id=%s)")
            params.append(query["topic_id"])
        if selected:
            where.append("(v.id = ANY(%s) OR (" + " AND ".join(selected) + "))")
            params.insert(1, pins)
        elif pins:
            where.append("v.id = ANY(%s)")
            params.append(pins)

        await cur.execute(
            f"""SELECT DISTINCT v.id FROM {source_view} v
                  LEFT JOIN appearances a ON a.canonical_id=v.id
                 WHERE {' AND '.join(where)}""",
            params,
        )
        candidates.update(r["id"] for r in await cur.fetchall())
    from ..services.repeat_selection import distinct_candidates
    return await distinct_candidates(cur,sorted(candidates))


@router.post("", response_model=MockSession)
async def start_mock(
    body: MockStart, user_id: Annotated[str, Depends(current_user)]
, exam_scope: ExamScope = DEFAULT_SCOPE) -> MockSession:
    async with cursor() as cur:
        await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('learning-session:'+user_id,))
        await cur.execute('SELECT 1 FROM game_members WHERE user_id=%s AND released_at IS NULL',(user_id,))
        if await cur.fetchone():raise HTTPException(409,'Finish or leave your game before starting a mock')
        shared_test=None
        if body.learning_test_id:
            if body.learning_test_version is None:raise HTTPException(422,'Choose the published test edition')
            from ..services.shareable_tests import for_start
            shared_test=await for_start(cur,body.learning_test_id,body.learning_test_version,user_id)
            config=shared_test['payload']['test_config']
            body=body.model_copy(update={'collection_id':'shared-tests','section_path':None,'paper_id':None,'paper_mode':'practice',**config})
        elif body.learning_test_version is not None:raise HTTPException(422,'A test edition needs its test ID')
        if not shared_test:
            await cur.execute(f"""SELECT 1 FROM collections WHERE id=%s AND visibility='public' AND {scope_condition('collections', exam_scope)}""",(body.collection_id,))
            if not await cur.fetchone():raise HTTPException(404,'Exam not found in this scope')
        await cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ("mock:" + user_id,))
        await cur.execute("SELECT account_has_pro(id) AS pro FROM users WHERE id=%s", (user_id,))
        entitlement=await cur.fetchone()
        if not shared_test and (not entitlement or not entitlement["pro"]):
            # An expired/abandoned paper with no answers should not consume
            # the learner's one monthly free mock. Count only a submission
            # where they actually answered at least one question.
            await cur.execute("SELECT count(*)::int AS n FROM mock_sessions WHERE user_id=%s AND learning_test_id IS NULL AND started_at>=date_trunc('month',now()) AND submitted_at IS NOT NULL AND COALESCE(n_correct,0)+COALESCE(n_wrong,0)>0",(user_id,))
            if (await cur.fetchone())["n"] >= 1:
                raise HTTPException(429,"Your free plan includes one mock per month. Pro includes unlimited mocks.")
        await cur.execute(
            "SELECT id FROM mock_sessions WHERE user_id = %s AND submitted_at IS NULL",
            (user_id,),
        )
        if await cur.fetchone():
            raise HTTPException(409, "a mock is already open; resume or submit it first")

        paper_items = None
        full_readiness=None
        if body.paper_mode=='full' and (not body.paper_id or body.answer_mode!='official'):
            raise HTTPException(422,'Full simulation needs an exact original paper and official-key scoring')
        section_path = body.section_path
        duration_minutes = body.duration_minutes
        marks_correct = body.marks_correct
        marks_wrong = body.marks_wrong
        source_view = pool_view('mock_practice', exam_scope) if body.answer_mode == "derived-practice" else pool_view('scorable', exam_scope)
        if shared_test:
            chosen=shared_test['payload']['question_ids']
        elif body.paper_id:
            if body.section_path:
                raise HTTPException(422, "choose either a paper or a section mock")
            await cur.execute(
                f"""SELECT cp.as_mock,cp.section_path,cp.duration_minutes,cp.marks_correct,cp.marks_wrong
                     FROM collection_papers cp
                     JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
                    WHERE cp.collection_id=%s AND cp.paper_id=%s AND EXISTS(SELECT 1 FROM papers sp WHERE sp.id=cp.paper_id AND {scope_condition('sp', exam_scope)})""",
                (body.collection_id, body.paper_id),
            )
            paper = await cur.fetchone()
            if paper is None or (body.answer_mode == "official" and not paper["as_mock"]):
                raise HTTPException(422, "this paper is available to browse but not for a scored test")
            if body.paper_mode=='full':
                from ..services.bank_organization import readiness
                await cur.execute('SELECT c.id FROM canonical_questions c JOIN appearances a ON a.canonical_id=c.id WHERE a.paper_id=%s ORDER BY c.id FOR SHARE OF c',(body.paper_id,))
                await cur.fetchall()
                await cur.execute('SELECT id FROM appearances WHERE paper_id=%s ORDER BY id FOR SHARE',(body.paper_id,))
                await cur.fetchall()
                await cur.execute('SELECT id FROM papers WHERE id=%s FOR SHARE',(body.paper_id,))
                await cur.fetchone()
                await cur.execute('SELECT paper_id FROM bank_paper_profiles WHERE paper_id=%s FOR SHARE',(body.paper_id,))
                await cur.fetchone()
                full_readiness=await readiness(cur,body.paper_id)
                if not full_readiness['full_simulation_ready']:
                    raise HTTPException(422,'Full original-paper simulation is not ready: '+'; '.join(full_readiness['blockers']))
            section_path = paper["section_path"]
            # Preserve this paper's numbering and printed option order while
            # using the canonical key for scoring.
            await cur.execute(
                f"""SELECT v.id,a.id AS appearance_id,a.options
                     FROM appearances a JOIN {source_view} v ON v.id=a.canonical_id
                    WHERE a.paper_id=%s
                    ORDER BY a.qnum_seq NULLS LAST,a.qnum,a.id""",
                (body.paper_id,),
            )
            paper_items = []
            seen: set[str] = set()
            for r in await cur.fetchall():
                if r["id"] not in seen:
                    seen.add(r["id"])
                    paper_items.append(r)
            if full_readiness and full_readiness['appearance_order']:
                order={aid:i for i,aid in enumerate(full_readiness['appearance_order'])}
                paper_items.sort(key=lambda item:order[item['appearance_id']])
            if not paper_items:
                label = "reviewed-answer" if body.answer_mode == "derived-practice" else "verified-key"
                raise HTTPException(422, f"this paper has no {label} questions yet")
            if paper["duration_minutes"]:
                duration_minutes = paper["duration_minutes"]
            if paper["marks_correct"] is not None:
                marks_correct = float(paper["marks_correct"])
            if paper["marks_wrong"] is not None:
                marks_wrong = float(paper["marks_wrong"])
            if full_readiness:
                spec=full_readiness['scheme']['paper']
                duration_minutes=spec['duration_minutes']
                marks_correct=spec['marks']/full_readiness['appearances']
                marks_wrong=marks_correct*spec['negative_fraction']
            chosen = [r["id"] for r in paper_items]
        else:
            ids = await _candidate_ids(cur, body.collection_id, body.section_path, body.answer_mode, exam_scope)
            if len(ids) < body.count:
                label = "reviewed-answer" if body.answer_mode == "derived-practice" else "verified-key"
                raise HTTPException(422, f"only {len(ids)} {label} questions available; asked for {body.count}")
            # Draw in Python; avoid ORDER BY random() as the bank grows.
            chosen = random.sample(ids, body.count)
        # Lock in one stable order and revalidate after the draw. A concurrent
        # hold/publication cannot change the key between eligibility and freeze.
        await cur.execute("SELECT id FROM canonical_questions WHERE id=ANY(%s) ORDER BY id FOR SHARE",(chosen,))
        await cur.fetchall()
        view=pool_view('mock_practice', 'all' if shared_test else exam_scope) if body.answer_mode=='derived-practice' else pool_view('scorable', 'all' if shared_test else exam_scope)
        await cur.execute('SELECT id FROM '+view+' WHERE id=ANY(%s)',(chosen,))
        if {r['id'] for r in await cur.fetchall()}!=set(chosen):
            raise HTTPException(409,'The bank changed while preparing this mock. Please try again.')
        appearances=[r['appearance_id'] for r in paper_items] if paper_items is not None else [None]*len(chosen)
        captured=shared_test['questions'] if shared_test else await scoring_revisions.capture_mock_questions(cur,chosen,appearances,body.answer_mode)
        await cur.execute("SELECT question_id,COALESCE(subtopic_label,topic_label,subject_label) AS label FROM question_classifications WHERE question_id=ANY(%s) AND review_status='approved'",(chosen,))
        labels={r['question_id']:r['label'] for r in await cur.fetchall()}
        for item in captured:item['snapshot']['topic_label']=labels.get(item['id'])
        excluded_presentations=len(chosen)-len(captured)
        if not captured or (excluded_presentations and (paper_items is None or body.paper_mode=='full')):
            raise HTTPException(422,'The presented source context or options cannot be safely scored. Browse the paper or request a correction.')
        chosen=[r['id'] for r in captured]
        mock_id = uuid.uuid4().hex

        await cur.execute(
            """INSERT INTO mock_sessions
                 (id, user_id, collection_id, section_path, paper_id, question_ids, answer_mode,
                  duration_seconds, marks_correct, marks_wrong,excluded_presentations,paper_mode,scheme_snapshot,learning_test_id,learning_test_version,learning_test_title)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               RETURNING started_at""",
            (mock_id, user_id, body.collection_id, section_path, body.paper_id, chosen, body.answer_mode,
             duration_minutes * 60, marks_correct, marks_wrong,excluded_presentations,body.paper_mode,Jsonb(full_readiness['scheme']) if full_readiness else None,body.learning_test_id,shared_test['revision'] if shared_test else None,shared_test['payload']['title'] if shared_test else None),
        )
        started = (await cur.fetchone())["started_at"]
        for position,item in enumerate(captured):
            await cur.execute("""INSERT INTO mock_session_questions(mock_id,position,canonical_id,appearance_id,options,snapshot,snapshot_at)
                VALUES (%s,%s,%s,%s,%s,%s,now())""",(mock_id,position,item['id'],item['appearance_id'],Jsonb(item['snapshot']['options']),Jsonb(item['snapshot'])))
        questions = await _load_questions(cur, chosen, mock_id)

    return MockSession(
        id=mock_id,learning_test_id=body.learning_test_id,learning_test_version=shared_test['revision'] if shared_test else None,learning_test_title=shared_test['payload']['title'] if shared_test else None, collection_id=body.collection_id, answer_mode=body.answer_mode, section_path=section_path,
        paper_id=body.paper_id,paper_mode=body.paper_mode,
        duration_seconds=duration_minutes * 60, started_at=started,
        seconds_remaining=duration_minutes * 60, questions=questions,excluded_presentations=excluded_presentations,
    )


async def _load_questions(cur, ids: list[str], mock_id: str | None = None) -> list[MockQuestion]:
    """Fetch by primary key and restore the frozen order. Answers are not
    selected at all — the client never receives them until submit."""
    if mock_id:
        await cur.execute(
            """SELECT q.id,q.question,sq.options,sq.snapshot,a.page,p.source_file,p.pdf_url,
                      COALESCE(a.direction,q.direction) AS direction,
                      COALESCE(a.question_markup,q.question_markup) AS question_markup,
                      COALESCE(a.options_markup,q.options_markup) AS options_markup,
                      COALESCE(a.passage,q.passage) AS passage,a.figure_image
                  FROM mock_session_questions sq
                 JOIN canonical_questions q ON q.id=sq.canonical_id
                 LEFT JOIN appearances a ON a.id=sq.appearance_id
                 LEFT JOIN papers p ON p.id=a.paper_id
                WHERE sq.mock_id=%s ORDER BY sq.position""", (mock_id,),
        )
        rows = await cur.fetchall()
        if rows:
            for row in rows:
                if row['snapshot']:
                    row.update({key:value for key,value in row['snapshot'].items() if key not in {'answer_text','answer_source','explanation','policy_version'}})
            return [MockQuestion(
                id=r["id"], position=i, question=r["question"], options=r["options"],
                direction=r["direction"], question_markup=r["question_markup"],
                options_markup=r["options_markup"], passage=r["passage"],
                figure_image_url=figure_image_url(r.get("figure_image")),
                page=r["page"], source_pdf_url=source_pdf_url(r["source_file"], r["pdf_url"]),
            ) for i,r in enumerate(rows)]
    await cur.execute(
        """SELECT q.id,q.question,q.options,src.page,src.source_file,src.pdf_url,
                  COALESCE(src.direction,q.direction) AS direction,
                  COALESCE(src.question_markup,q.question_markup) AS question_markup,
                  COALESCE(src.options_markup,q.options_markup) AS options_markup,
                  COALESCE(src.passage,q.passage) AS passage,src.figure_image
             FROM canonical_questions q
             LEFT JOIN LATERAL (
               SELECT a.page,p.source_file,p.pdf_url,a.direction,a.question_markup,
                      a.options_markup,a.passage,a.figure_image
                 FROM appearances a JOIN papers p ON p.id=a.paper_id
                WHERE a.canonical_id=q.id
                ORDER BY p.year DESC NULLS LAST,a.page NULLS LAST,a.id
                LIMIT 1
             ) src ON TRUE
            WHERE q.id = ANY(%s)""", (ids,),
    )
    by_id = {r["id"]: r for r in await cur.fetchall()}
    return [
        MockQuestion(
            id=i, position=n, question=by_id[i]["question"], options=by_id[i]["options"],
            direction=by_id[i]["direction"], question_markup=by_id[i]["question_markup"],
            options_markup=by_id[i]["options_markup"], passage=by_id[i]["passage"],
            figure_image_url=figure_image_url(by_id[i].get("figure_image")),
            page=by_id[i]["page"],
            source_pdf_url=source_pdf_url(by_id[i]["source_file"], by_id[i]["pdf_url"]),
        )
        for n, i in enumerate(ids)
        if i in by_id
    ]


@router.get("/current", response_model=MockSession | None)
async def current_mock(user_id: Annotated[str, Depends(current_user)]) -> MockSession | None:
    async with cursor() as cur:
        await cur.execute(
            """SELECT id, collection_id, answer_mode, section_path, paper_id, question_ids, duration_seconds,
                      current_position,excluded_presentations,paper_mode,learning_test_id,learning_test_version,learning_test_title,
                      started_at,
                      GREATEST(0, duration_seconds
                               - EXTRACT(EPOCH FROM (now() - started_at)))::int AS remaining
                 FROM mock_sessions
                WHERE user_id = %s AND submitted_at IS NULL""",
            (user_id,),
        )
        row = await cur.fetchone()
        if row is None:
            return None
        questions = await _load_questions(cur, row["question_ids"], row["id"])
        await cur.execute(
            "SELECT question_id,chosen_index,marked FROM mock_session_answers WHERE mock_id=%s",
            (row["id"],),
        )
        saved = await cur.fetchall()
    return MockSession(
        id=row["id"],learning_test_id=row["learning_test_id"],learning_test_version=row["learning_test_version"],learning_test_title=row["learning_test_title"], collection_id=row["collection_id"], answer_mode=row["answer_mode"], section_path=row["section_path"],
        paper_id=row["paper_id"],paper_mode=row["paper_mode"],
        duration_seconds=row["duration_seconds"], started_at=row["started_at"],
        current_position=row["current_position"],
        saved_answers={r["question_id"]:r["chosen_index"] for r in saved if r["chosen_index"] is not None},
        marked_questions=[r["question_id"] for r in saved if r["marked"]],
        seconds_remaining=row["remaining"], questions=questions,excluded_presentations=row["excluded_presentations"],
    )


@router.put("/{mock_id}/answers")
async def save_mock_answer(
    mock_id: str, body: MockAnswerSave, user_id: Annotated[str, Depends(current_user)]
) -> None:
    """Persist a timed-paper answer, review flag, and current position."""
    async with cursor() as cur:
        await cur.execute(
            "SELECT question_ids FROM mock_sessions WHERE id=%s AND user_id=%s AND submitted_at IS NULL FOR UPDATE",
            (mock_id,user_id),
        )
        session = await cur.fetchone()
        if session is None:
            raise HTTPException(404,"no open mock for this device")
        if body.question_id not in session["question_ids"]:
            raise HTTPException(422,"question is not part of this mock")
        await cur.execute(
            """SELECT COALESCE(sq.options,q.options) AS options
                 FROM canonical_questions q LEFT JOIN mock_session_questions sq
                   ON sq.mock_id=%s AND sq.canonical_id=q.id
                WHERE q.id=%s""",
            (mock_id,body.question_id),
        )
        question = await cur.fetchone()
        if question is None:
            raise HTTPException(404,"question not found")
        if body.chosen_index is not None and body.chosen_index >= len(question["options"]):
            raise HTTPException(422,"chosen_index out of range")
        await cur.execute(
            """INSERT INTO mock_session_answers(mock_id,question_id,chosen_index,marked,updated_at)
               VALUES (%s,%s,%s,%s,now())
               ON CONFLICT(mock_id,question_id) DO UPDATE SET
                 chosen_index=EXCLUDED.chosen_index,marked=EXCLUDED.marked,updated_at=now()""",
            (mock_id,body.question_id,body.chosen_index,body.marked),
        )
        await cur.execute(
            "UPDATE mock_sessions SET current_position=LEAST(%s,cardinality(question_ids)-1) WHERE id=%s",
            (body.position,mock_id),
        )
    return {"ok":True}


@router.post("/{mock_id}/submit", response_model=MockResult)
async def submit_mock(
    mock_id: str, body: MockSubmission, user_id: Annotated[str, Depends(current_user)]
) -> MockResult:
    async with cursor() as cur:
        await cur.execute(
            """SELECT question_ids, collection_id, section_path, paper_id, answer_mode, duration_seconds, marks_correct, marks_wrong,learning_test_id,learning_test_version,learning_test_title,
                      submitted_at,
                      EXTRACT(EPOCH FROM (now() - started_at))::int AS elapsed
                 FROM mock_sessions WHERE id = %s AND user_id = %s FOR UPDATE""",
            (mock_id, user_id),
        )
        s = await cur.fetchone()
        if s is None:
            raise HTTPException(404, "no such mock for this device")
        if s["submitted_at"] is not None:
            raise HTTPException(409, "already submitted")

        # The clock is read here, from the row written at start. Nothing the
        # client sends influences it.
        elapsed = s["elapsed"]
        late = elapsed > s["duration_seconds"] + GRACE_SECONDS

        ids: list[str] = s["question_ids"]
        presented_options: dict[str, list[str | None]] = {}
        if s["paper_id"]:
            await cur.execute(
                "SELECT canonical_id,options FROM mock_session_questions WHERE mock_id=%s",
                (mock_id,),
            )
            presented_options = {r["canonical_id"]: r["options"] for r in await cur.fetchall()}
        await cur.execute(
            "SELECT id, question, options, answer_text, answer_source, explanation FROM canonical_questions WHERE id = ANY(%s)",
            (ids,),
        )
        qs = {r["id"]: r for r in await cur.fetchall()}
        await cur.execute("SELECT canonical_id,options,snapshot FROM mock_session_questions WHERE mock_id=%s",(mock_id,))
        frozen_ids=set()
        for frozen in await cur.fetchall():
            presented_options[frozen['canonical_id']]=frozen['options']
            if frozen['snapshot']:frozen_ids.add(frozen['canonical_id'])
            if frozen['snapshot'] and frozen['canonical_id'] in qs:
                qs[frozen['canonical_id']].update(frozen['snapshot'])
        await cur.execute("SELECT question_id,chosen_index FROM mock_session_answers WHERE mock_id=%s",(mock_id,))
        given = {r["question_id"]:r["chosen_index"] for r in await cur.fetchall() if r["chosen_index"] is not None}
        given.update({a.question_id:a.chosen_index for a in body.answers})

        rows, n_ok, n_bad, n_skip = [], 0, 0, 0
        for pos, qid in enumerate(ids):
            q = qs.get(qid)
            if q is None:
                continue
            opts: list[str | None] = presented_options.get(qid, q["options"])
            idx = given.get(qid)
            chosen_text = opts[idx] if idx is not None and 0 <= idx < len(opts) else None
            if chosen_text is None:
                n_skip += 1
                correct = False
            else:
                correct = chosen_text == q["answer_text"]
                n_ok += correct
                n_bad += not correct
                # chosen_text, not the index, so a later key fix can re-score.
                await cur.execute(
                    """INSERT INTO attempts
                         (user_id, canonical_id, correct, chosen_text, context, mock_id, position,
                          collection_id,paper_id,section_path)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (user_id, qid, correct, chosen_text,
                     "mock-derived" if s["answer_mode"] == "derived-practice" else "mock", mock_id, pos,
                     s["collection_id"],s["paper_id"],s["section_path"]),
                )
            rows.append(MockReviewRow(
                position=pos, question_id=qid, question=q["question"], topic_label=q.get("topic_label"),
                direction=q.get("direction"),question_markup=q.get("question_markup"),passage=q.get("passage"),
                figure_image_url=figure_image_url(q.get("figure_image")),
                chosen_text=chosen_text, answer_text=q["answer_text"], correct=correct,
                explanation=q["explanation"], answer_source=q["answer_source"],
            ))

        score = float(n_ok) * float(s["marks_correct"]) - float(n_bad) * float(s["marks_wrong"])
        await cur.execute(
            """UPDATE mock_sessions
                  SET submitted_at = now(), elapsed_seconds = %s, late = %s,
                      n_correct = %s, n_wrong = %s, n_skipped = %s, score = %s
                WHERE id = %s""",
            (elapsed, late, n_ok, n_bad, n_skip, score, mock_id),
        )

        await cur.execute("INSERT INTO new_score_jobs(mock_id) VALUES (%s) ON CONFLICT DO NOTHING",(mock_id,))

    return MockResult(
        id=mock_id,learning_test_id=s["learning_test_id"],learning_test_version=s["learning_test_version"],learning_test_title=s["learning_test_title"], collection_id=s["collection_id"],answer_mode=s["answer_mode"], n_correct=n_ok, n_wrong=n_bad, n_skipped=n_skip, score=score,
        total=len(ids), elapsed_seconds=elapsed, late=late, review=rows,
        score_breakdown=scoring_revisions.original_breakdown(rows,s['marks_correct'],s['marks_wrong']),
        legacy_unversioned=len(frozen_ids)<len(ids),
    )


@router.get("", response_model=list[MockSummary])
async def list_mocks(user_id: Annotated[str, Depends(current_user)]) -> list[MockSummary]:
    """Past papers, newest first. Open sessions are included so the UI can
    offer to resume rather than silently hiding a blocked slot."""
    async with cursor() as cur:
        await cur.execute(
            """SELECT m.id,m.learning_test_id,m.learning_test_version,m.learning_test_title, m.collection_id, COALESCE(m.learning_test_title,c.title) AS collection_title, m.section_path, m.answer_mode,
                      cardinality(m.question_ids) AS total,
                      m.n_correct, m.n_wrong, m.n_skipped, m.score,
                      m.elapsed_seconds, m.late, m.started_at, m.submitted_at
                 FROM mock_sessions m
                 JOIN collections c ON c.id = m.collection_id
                WHERE m.user_id = %s
                ORDER BY m.started_at DESC LIMIT 50""",
            (user_id,),
        )
        return [MockSummary(**r) for r in await cur.fetchall()]


@router.get("/{mock_id}", response_model=MockResult)
async def get_mock_result(
    mock_id: str, user_id: Annotated[str, Depends(current_user)]
) -> MockResult:
    """Re-read a finished paper. The review is rebuilt from attempts rather
    than stored twice — and a LEFT JOIN, because a skipped question has no
    attempt row at all and must still appear in the review."""
    async with cursor() as cur:
        await cur.execute(
            """SELECT collection_id,question_ids, answer_mode, n_correct, n_wrong, n_skipped, score,marks_correct,marks_wrong,learning_test_id,learning_test_version,learning_test_title,
                      elapsed_seconds, late, submitted_at
                 FROM mock_sessions WHERE id = %s AND user_id = %s""",
            (mock_id, user_id),
        )
        s = await cur.fetchone()
        if s is None:
            raise HTTPException(404, "no such mock for this device")
        if s["submitted_at"] is None:
            raise HTTPException(409, "that mock is still open")

        await cur.execute('SELECT 1 FROM mock_sessions WHERE user_id=%s AND submitted_at IS NULL AND question_ids && %s::text[]',(user_id,s['question_ids']))
        if await cur.fetchone():raise HTTPException(409,'Finish your active mock before opening answer-bearing result history')
        await cur.execute(
            """SELECT q.id, q.question, q.answer_text, q.answer_source, q.explanation,sq.snapshot,
                      a.chosen_text, COALESCE(a.correct, false) AS correct
                 FROM unnest(%s::text[]) WITH ORDINALITY AS u(qid, ord)
                 JOIN canonical_questions q ON q.id = u.qid
                 LEFT JOIN attempts a ON a.mock_id = %s AND a.canonical_id = q.id
                 LEFT JOIN mock_session_questions sq ON sq.mock_id=%s AND sq.canonical_id=q.id
                ORDER BY u.ord""",
            (s["question_ids"], mock_id,mock_id),
        )
        result_rows=await cur.fetchall()
        for row in result_rows:
            if row['snapshot']:
                row.update({key:row['snapshot'].get(key) for key in ('question','answer_text','answer_source','explanation','direction','question_markup','passage','figure_image','topic_label')})
            else:
                row.update(answer_text=None,answer_source=None,explanation=None)
        review = [
            MockReviewRow(position=i, question_id=r["id"], question=r["question"], topic_label=r.get("topic_label"),
                          direction=r.get("direction"),question_markup=r.get("question_markup"),passage=r.get("passage"),
                          figure_image_url=figure_image_url(r.get("figure_image")),
                          chosen_text=r["chosen_text"], answer_text=r["answer_text"],
                          correct=r["correct"], explanation=r["explanation"], answer_source=r["answer_source"])
            for i, r in enumerate(result_rows)
        ]

    return MockResult(
        id=mock_id,learning_test_id=s["learning_test_id"],learning_test_version=s["learning_test_version"],learning_test_title=s["learning_test_title"], collection_id=s["collection_id"],answer_mode=s["answer_mode"], n_correct=s["n_correct"], n_wrong=s["n_wrong"],
        n_skipped=s["n_skipped"], score=float(s["score"]),
        total=len(s["question_ids"]), elapsed_seconds=s["elapsed_seconds"],
        late=s["late"], review=review,
        score_breakdown=None if any(not r['snapshot'] for r in result_rows) else scoring_revisions.original_breakdown(review,s['marks_correct'],s['marks_wrong']),
        legacy_unversioned=any(not r['snapshot'] for r in result_rows),
    )


@router.get("/{mock_id}/assessments")
async def assessment_history(mock_id:str,user_id:Annotated[str,Depends(current_user)]):
    async with cursor() as cur:
        session,inputs=await scoring_revisions.mock_inputs(cur,mock_id,user_id)
        fingerprint=scoring_revisions.input_fingerprint(session,inputs)
        await cur.execute("SELECT id,created_at,payload,input_hash FROM mock_assessments WHERE mock_id=%s ORDER BY created_at DESC,id DESC LIMIT 20",(mock_id,))
        rows=await cur.fetchall()
    return {'items':[{**r['payload'],'id':r['id'],'computed_at':r['created_at']} for r in rows],'pending':not rows or rows[0]['input_hash']!=fingerprint}

@router.post("/{mock_id}/reassess")
async def reassess_mock(mock_id:str,request:Request,user_id:Annotated[str,Depends(current_user)]):
    if request.headers.get('origin')!=settings.public_origin:raise HTTPException(403,'A same-origin request is required')
    async with cursor() as cur:
        return await scoring_revisions.assess_mock(cur,mock_id,user_id)
