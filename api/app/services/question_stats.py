"""Aggregate per-question answer statistics, shown only once the answer is revealed.

Reads `v_question_stats` and `v_option_picks` (migration 0003). Both have been
indexed and read by nothing since the day they were created. `v_option_picks` was
written for exactly this feature — its own comment says "for the vote bars under a
revealed option" — and the prototype drew it as `opts(q, picked, onPick, votes)`
(`v3.dc.html` line 2603). This connects them (§VII.18 #2, §VIII.5 follow-on).

Two rules this module exists to keep:

**Aggregates only.** Nothing returned here is attributable to a learner, and the
caller must not pass it to a guest or shared cache beyond the reveal response it
rides in.

**Post-reveal only.** Pick distribution is interesting precisely because the most
popular option is often wrong, but handing it to someone who has not answered yet
is still a nudge. Both call sites are reveal moments.

The population gate is a **privacy control as much as a noise one**: with a handful
of attempts, a per-option breakdown can say what one identifiable person chose.
"""
from __future__ import annotations

# One constant, deliberately. The project gates other shared aggregates by
# population too (§0.11.3 cohorts at >=50 weekly actives); per question that would
# hide nearly everything, so this is lower. Tune it against real answer volume —
# it is not knowable from a developer checkout — rather than by guessing again.
MIN_ATTEMPTS = 20


async def question_stats(cur, canonical_id: str, options: list | None = None) -> dict | None:
    """Return aggregate stats for one question, or None below the population gate."""
    await cur.execute(
        'SELECT attempts,correct,learners,accuracy FROM v_question_stats WHERE canonical_id=%s',
        (canonical_id,),
    )
    row = await cur.fetchone()
    if not row or row['attempts'] < MIN_ATTEMPTS:
        return None

    await cur.execute(
        'SELECT chosen_text,picks FROM v_option_picks WHERE canonical_id=%s',
        (canonical_id,),
    )
    picked = {r['chosen_text']: r['picks'] for r in await cur.fetchall()}
    total = sum(picked.values())

    # Report against the question's own printed options, in printed order. Attempts
    # store the chosen *text*, so a question whose options were later corrected can
    # hold picks for text no longer on the paper; showing those would invent a
    # choice the learner was never offered. Picks for retired text are counted in
    # `attempts` but are not listed as options.
    texts = [o for o in (options or []) if o]
    return {
        'attempts': row['attempts'],
        'learners': row['learners'],
        'accuracy': float(row['accuracy']) if row['accuracy'] is not None else None,
        'picks': [
            {
                'text': text,
                'picks': picked.get(text, 0),
                'share': round(picked.get(text, 0) / total, 3) if total else 0.0,
            }
            for text in texts
        ],
    }
