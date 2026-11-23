import { learnerExplanation } from '../lib/answerStatus'
import { subjectChipClass } from '../lib/subjectChips'
import TestShare from './TestShare'
import { lazy, Suspense, useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { Link } from 'react-router-dom'
import { SourceQuestionContext, SourceQuestionText } from './SourceQuestionText'
import type { MockResult } from '../lib/api'

const AdjustedMockResults = lazy(() => import('./AdjustedMockResults'))

export const mmss = (s: number) =>
  `${String(Math.floor(Math.max(0, s) / 60)).padStart(2, '0')}:${String(Math.max(0, s) % 60).padStart(2, '0')}`

type ReviewRow = MockResult['review'][number]

/**
 * Focused distraction-free stepper for missed questions (§VII.19.10, ported
 * from ShikshaCom's QuizResult.jsx MistakesReview).
 */
function MistakesReviewModal({
  mistakes,
  onClose,
}: {
  mistakes: ReviewRow[]
  onClose: () => void
}) {
  const [idx, setIdx] = useState(0)
  const current = mistakes[idx]

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      else if (e.key === 'ArrowRight') setIdx((i) => Math.min(mistakes.length - 1, i + 1))
      else if (e.key === 'ArrowLeft') setIdx((i) => Math.max(0, i - 1))
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [mistakes.length, onClose])

  if (!current) return null

  return createPortal(
    <div
      className="finna-modal-backdrop"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        className="finna-mistake-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="mistake-review-title"
      >
        <div className="finna-help-head">
          <div>
            <div className="finna-eyebrow">
              Reviewing mistake {idx + 1} of {mistakes.length} · Q{current.position + 1}
            </div>
            <h2 id="mistake-review-title">{current.topic_label || 'Past-paper question'}</h2>
          </div>
          <button type="button" className="finna-btn finna-btn-quiet" onClick={onClose}>
            Close
          </button>
        </div>

        <SourceQuestionContext direction={current.direction} passage={current.passage} />
        <p className="mt-2 font-display text-md leading-snug">
          <SourceQuestionText text={current.question_markup ?? current.question} />
        </p>

        {current.chosen_text && (
          <div className="finna-mistake-row finna-mistake-row--wrong">
            ✗ Your pick: <SourceQuestionText text={current.chosen_text} />
          </div>
        )}
        <div className="finna-mistake-row finna-mistake-row--correct">
          ✓ Answer: {current.answer_text || 'Original key unavailable'}
        </div>

        {current.explanation && (
          <div className="mt-3 rounded-xl border border-hairline bg-paper p-3.5 text-sm leading-relaxed text-secondary">
            <strong className="text-ink">Why: </strong>
            <SourceQuestionText text={learnerExplanation(current.explanation)} />
          </div>
        )}

        <div className="finna-mistake-foot">
          <button
            type="button"
            className="finna-btn finna-btn-quiet"
            disabled={idx === 0}
            onClick={() => setIdx((i) => Math.max(0, i - 1))}
          >
            ← Previous
          </button>
          <Link
            to={`/bank/${current.question_id}`}
            className="text-sm font-semibold text-link underline"
            onClick={onClose}
          >
            Open question ↗
          </Link>
          {idx === mistakes.length - 1 ? (
            <button type="button" className="finna-btn" onClick={onClose}>
              Done
            </button>
          ) : (
            <button
              type="button"
              className="finna-btn"
              onClick={() => setIdx((i) => Math.min(mistakes.length - 1, i + 1))}
            >
              Next →
            </button>
          )}
        </div>
      </div>
    </div>,
    document.body,
  )
}

/** Shared by the mock runner (straight after submit) and the standalone
 *  results screen (revisiting a past paper), so the two cannot drift. */
export default function MockResultView({
  result,
  backTo,
  backLabel = '← Exam',
}: {
  result: MockResult
  backTo: string
  backLabel?: string
}) {
  const [outcome, setOutcome] = useState('all')
  const [topic, setTopic] = useState('all')
  const [query, setQuery] = useState('')
  const [showMistakes, setShowMistakes] = useState(false)

  const topics = useMemo(
    () => Array.from(new Set(result.review.map((r) => r.topic_label || 'Unclassified'))),
    [result.review],
  )

  const wrongQuestions = useMemo(
    () => result.review.filter((r) => !!r.chosen_text && !r.correct),
    [result.review],
  )

  // Preserves each question's original paper number (Q{r.position + 1}) when searching (§VII.19.10)
  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase()
    return result.review.filter((r) => {
      if (topic !== 'all' && (r.topic_label || 'Unclassified') !== topic) return false
      if (outcome === 'correct' && !r.correct) return false
      if (outcome === 'wrong' && (!r.chosen_text || r.correct)) return false
      if (outcome === 'skipped' && !!r.chosen_text) return false
      if (!needle) return true
      return [r.question, r.chosen_text, r.answer_text, r.topic_label].some((field) =>
        String(field || '').toLowerCase().includes(needle),
      )
    })
  }, [result.review, topic, outcome, query])

  const pct = Math.round((result.n_correct / Math.max(1, result.total)) * 100)

  return (
    <div className="exam-result mx-auto max-w-shell px-6 pb-24 pt-8">
      <Link to={backTo} className="text-sm text-secondary">
        {backLabel}
      </Link>

      <div className="mt-3 rounded-xl bg-practice-soft p-6">
        <div className="font-mono text-xs uppercase tracking-[0.1em] text-practice-dark">
          Original result ·{' '}
          {result.answer_mode === 'derived-practice' ? 'Practice estimate' : 'Official-key mock'}
        </div>
        {result.answer_mode === 'derived-practice' && (
          <p className="mt-2 text-sm leading-snug text-exams-dark">
            This practice estimate may include worked solutions. Your original result stays available; an updated result uses the answers currently approved for scoring.
          </p>
        )}
        <h1 className="mt-2 font-display text-[clamp(32px,4.6vw,48px)] font-medium -tracking-[0.02em]">
          {result.score} {result.score === 1 ? 'mark' : 'marks'} · {pct}%
        </h1>
        <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1.5 text-sm text-secondary">
          <span>{result.n_correct} correct</span>
          <span>{result.n_wrong} wrong</span>
          <span>{result.n_skipped} skipped</span>
          <span>{mmss(result.elapsed_seconds)} taken</span>
        </div>
        {wrongQuestions.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              className="finna-btn"
              onClick={() => setShowMistakes(true)}
            >
              Review {wrongQuestions.length} mistake{wrongQuestions.length === 1 ? '' : 's'} →
            </button>
            <button
              type="button"
              className="finna-btn finna-btn-quiet"
              onClick={() => {
                setOutcome('wrong')
                setTopic('all')
              }}
            >
              Filter to wrong answers
            </button>
          </div>
        )}
        {result.late && (
          <p className="mt-2 text-sm text-attention-dark">
            ! Submitted after the time limit. The attempt is recorded and marked late.
          </p>
        )}
      </div>

      {result.learning_test_id && (
        <TestShare
          id={result.learning_test_id}
          title={result.learning_test_title || 'Try this mock test'}
        />
      )}
      {result.score_breakdown && (
        <p className="mt-3 text-sm text-secondary">
          Original score for questions with official keys:{' '}
          {result.score_breakdown.official_subset.scorable_total
            ? `${result.score_breakdown.official_subset.score} / ${result.score_breakdown.official_subset.maximum} marks across ${result.score_breakdown.official_subset.scorable_total} questions`
            : 'No questions with official keys'}
          .
        </p>
      )}
      {result.legacy_unversioned && (
        <p className="mt-3 text-sm text-secondary">
          Legacy result: original question text and keys were not saved. Recorded marks remain original; review text may reflect the current catalogue.
        </p>
      )}
      <details className="mt-4 rounded-xl border border-hairline bg-card p-4">
        <summary className="min-h-11 cursor-pointer py-2 text-sm font-semibold text-ink">
          How this run was graded
        </summary>
        <div className="mt-2 space-y-2 border-t border-hairline pt-3 text-sm text-secondary">
          <p>
            Each question’s wording, options, and answer are saved as a snapshot when you start a timed run.
          </p>
          <p>
            If an answer key is later revised or disputed, your original result stays preserved alongside any updated assessment below.
          </p>
        </div>
      </details>

      <Suspense fallback={<p className="mt-5 text-sm text-muted">Loading adjusted results…</p>}>
        <AdjustedMockResults mockId={result.id} />
      </Suspense>

      <h2 className="mt-8 font-display text-xl font-medium">Topic performance</h2>
      <p className="mt-2 text-sm text-secondary">
        Based on this saved attempt and its original grading. Click any topic to filter the review below.
      </p>
      <div className="mt-3 grid gap-3 sm:grid-cols-3">
        {topics.map((t) => {
          const rows = result.review.filter((r) => (r.topic_label || 'Unclassified') === t)
          const correctCount = rows.filter((r) => r.correct).length
          const topicPct = rows.length ? Math.round((correctCount / rows.length) * 100) : 0
          const selected = topic === t
          return (
            <button
              key={t}
              type="button"
              aria-pressed={selected}
              onClick={() => setTopic(selected ? 'all' : t)}
              className={`rounded-panel border p-4 text-left transition-colors ${
                selected ? 'border-practice bg-practice-soft' : 'border-hairline bg-card'
              }`}
            >
              <span className={subjectChipClass(t)}>{t}</span>
              <p className="mt-2.5 text-sm font-semibold text-ink">
                {correctCount} / {rows.length} correct ({topicPct}%)
              </p>
              <div className="finna-progress mt-2">
                <span style={{ width: `${topicPct}%` }} />
              </div>
            </button>
          )
        })}
      </div>

      <h2 className="mt-8 font-display text-xl font-medium">Review</h2>
      <div className="my-3 flex flex-wrap items-end gap-3">
        <label className="text-sm font-semibold">
          Outcome{' '}
          <select
            className="ml-1 min-h-11 rounded-lg border border-hairline bg-card p-2 text-sm font-normal"
            value={outcome}
            onChange={(e) => setOutcome(e.target.value)}
          >
            {['all', 'correct', 'wrong', 'skipped'].map((x) => (
              <option key={x} value={x}>
                {x}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm font-semibold">
          Topic{' '}
          <select
            className="ml-1 min-h-11 rounded-lg border border-hairline bg-card p-2 text-sm font-normal"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          >
            <option value="all">All topics</option>
            {topics.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <label className="min-w-[200px] flex-1 text-sm font-semibold">
          <span className="sr-only">Search inside results</span>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by question text or answer…"
            className="min-h-11 w-full rounded-lg border border-hairline bg-card px-3 text-sm font-normal"
          />
        </label>
      </div>

      {!visible.length && (
        <p className="rounded-xl border border-hairline bg-card p-4 text-sm text-secondary">
          {query.trim()
            ? `No answers match “${query.trim()}”.`
            : 'No answers match these filters.'}
        </p>
      )}

      <div className="mt-3 flex flex-col gap-3">
        {visible.map((r) => (
          <div
            key={r.question_id}
            className="rounded-[14px] border border-hairline bg-card p-5 shadow-[0_1px_2px_rgba(29,27,24,.05)]"
          >
            <div className="flex flex-wrap items-center gap-2 font-mono text-xs uppercase tracking-[0.06em]">
              <span className="text-muted">Q{r.position + 1}</span>
              <span
                className={
                  r.correct ? 'text-keyed' : r.chosen_text ? 'text-mypick' : 'text-muted'
                }
              >
                {r.correct ? 'Correct' : r.chosen_text ? 'Wrong' : 'Skipped'}
              </span>
              {r.answer_source === 'derived' && (
                <span className="rounded-pill bg-exams-soft px-2 py-1 text-xs text-exams-dark">
                  Worked solution · unofficial
                </span>
              )}
              <span className="grow" />
              <Link to={`/bank/${r.question_id}`} className="text-link">
                Open ↗
              </Link>
            </div>
            <div className="mt-3">
              <SourceQuestionContext direction={r.direction} passage={r.passage} />
            </div>
            <p className="mt-2 font-display text-md leading-snug">
              <SourceQuestionText text={r.question_markup ?? r.question} />
            </p>
            {r.figure_image_url && (
              <a
                href={r.figure_image_url}
                target="_blank"
                rel="noreferrer"
                className="mt-3 block max-w-2xl rounded-[8px] border border-hairline bg-paper p-2"
                aria-label="Open original question figure"
              >
                <img
                  src={r.figure_image_url}
                  loading="lazy"
                  decoding="async"
                  alt="Original figure shown in this test"
                  className="max-h-[360px] w-full object-contain"
                />
              </a>
            )}
            <div className="mt-2 grid gap-1 text-sm">
              {r.chosen_text && (
                <span className={r.correct ? 'text-keyed' : 'text-mypick'}>
                  You chose: <SourceQuestionText text={r.chosen_text} />
                </span>
              )}
              {!r.correct && (
                <span className="text-keyed">
                  {r.answer_text ? `Answer: ${r.answer_text}` : 'Original key unavailable'}
                </span>
              )}
            </div>
            {r.explanation && (
              <p className="mt-2 text-sm leading-[1.6] text-secondary">
                <SourceQuestionText text={learnerExplanation(r.explanation)} />
              </p>
            )}
          </div>
        ))}
      </div>

      {showMistakes && (
        <MistakesReviewModal
          mistakes={wrongQuestions}
          onClose={() => setShowMistakes(false)}
        />
      )}
    </div>
  )
}
