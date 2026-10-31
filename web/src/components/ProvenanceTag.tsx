import type { AnswerSource } from '../lib/api'

import AnswerProvenance from './AnswerProvenance'

export default function ProvenanceTag({source}:{source:AnswerSource}) {
  return <AnswerProvenance source={source}/>
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
