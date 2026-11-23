import { SourceQuestionText } from './SourceQuestionText'

export interface QuestionStatsData {
  attempts: number
  learners: number
  accuracy: number | null
  picks: { text: string; picks: number; share: number }[]
}

/** "How others answered" — the vote bars migration 0003 built `v_option_picks` for
 *  and nothing ever rendered. Shown only after the answer is revealed, and only
 *  above the server's population gate, so it is never a nudge and never thin enough
 *  to point at one identifiable learner.
 *
 *  The teaching happens when a popular option is wrong: seeing that most people fell
 *  for the same distractor is the difference between a question bank and a quiz. The
 *  correct option and the learner's own pick are labelled in text, not by colour
 *  alone. */
export default function QuestionStats({
  stats,
  answerText,
  chosenText,
}: {
  stats?: QuestionStatsData | null
  answerText?: string
  chosenText?: string | null
}) {
  if (!stats || !stats.picks.length) return null
  const percent = (share: number) => Math.round(share * 100)
  const accuracy = stats.accuracy == null ? null : Math.round(stats.accuracy * 100)

  return (
    <section aria-label="How others answered" className="mt-3 rounded-[10px] border border-hairline bg-paper p-3">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <strong className="text-sm">How others answered</strong>
        <p className="text-xs text-muted">
          {accuracy == null ? null : <>{accuracy}% answered correctly · </>}
          {stats.attempts} {stats.attempts === 1 ? 'answer' : 'answers'} from {stats.learners}{' '}
          {stats.learners === 1 ? 'learner' : 'learners'}
        </p>
      </div>
      <ul className="mt-2 space-y-1.5">
        {stats.picks.map((pick) => {
          const isAnswer = answerText != null && pick.text === answerText
          const isYours = chosenText != null && pick.text === chosenText
          const labels = [isAnswer ? 'correct answer' : null, isYours ? 'your pick' : null].filter(Boolean)
          return (
            <li key={pick.text}>
              <div className="flex flex-wrap items-baseline justify-between gap-x-2 text-xs">
                <span className="min-w-0 flex-1 truncate">
                  <SourceQuestionText text={pick.text} />
                  {labels.length > 0 && (
                    <span className="ml-2 font-semibold text-secondary">({labels.join(' · ')})</span>
                  )}
                </span>
                <span className="font-mono text-muted">{percent(pick.share)}%</span>
              </div>
              <div
                className="mt-0.5 h-1.5 overflow-hidden rounded-pill bg-canvas"
                role="img"
                aria-label={`${percent(pick.share)} percent picked this option${
                  labels.length ? ' — ' + labels.join(' and ') : ''
                }`}
              >
                <div
                  className={'h-full rounded-pill ' + (isAnswer ? 'bg-correct-dark' : 'bg-hairline2')}
                  style={{ width: Math.max(pick.share * 100, pick.picks > 0 ? 2 : 0) + '%' }}
                />
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
