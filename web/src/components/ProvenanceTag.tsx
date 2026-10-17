import type { AnswerSource } from '../lib/api'

/** The design's vocabulary for where an answer came from: "Official key",
 *  "Transcribed key", "No published key". Two more are needed because the
 *  bank distinguishes them and the difference matters to a learner:
 *  `derived` was worked out from the paper, `inferred` is a model's guess.
 *
 *  Only official and key are ever scored. Everything else must read as
 *  unverified at a glance — a learner who trusts a guess carries the error
 *  into the exam hall. See CLAUDE.md rule 1. */
const LABELS: Record<AnswerSource, { text: string; cls: string }> = {
  official: { text: 'Official key', cls: 'bg-correct-soft text-correct-dark' },
  key: { text: 'Transcribed key', cls: 'bg-correct-soft text-correct-dark' },
  derived: { text: 'Derived answer', cls: 'bg-exams-soft text-exams-dark' },
  inferred: { text: 'Unverified', cls: 'bg-attention-soft text-attention-dark' },
  none: { text: 'No published key', cls: 'bg-paper text-muted' },
}

export default function ProvenanceTag({ source }: { source: AnswerSource }) {
  const { text, cls } = LABELS[source] ?? LABELS.none
  return (
    <span
      className={`inline-flex shrink-0 items-center rounded-pill px-2 py-[2px] font-mono text-[9.5px] uppercase tracking-[0.06em] ${cls}`}
    >
      {text}
    </span>
  )
}

/** "Asked 3×" — only shown when it is actually a repeat, so the badge means
 *  something when it appears. */
export function RepeatBadge({ times }: { times: number }) {
  if (times < 2) return null
  return (
    <span className="inline-flex shrink-0 items-center rounded-pill bg-exams-soft px-2 py-[2px] font-mono text-[9.5px] uppercase tracking-[0.06em] text-exams-dark">
      Asked {times}×
    </span>
  )
}
