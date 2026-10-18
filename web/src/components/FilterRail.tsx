import type { AnswerSource } from '../lib/api'
import { Card, Checkbox, GroupTitle, NotYet } from './ui'

/** Filter rail, ported from markup line 390: white card, 14px radius, 16px
 *  padding, flex 1 1 220px capped at 260px, groups 22px apart. */

export interface Filters {
  sources: AnswerSource[]
  yearFrom: string
  yearTo: string
}

const SOURCES: { key: AnswerSource; label: string }[] = [
  { key: 'official', label: 'Official key' },
  { key: 'key', label: 'Transcribed key' },
  { key: 'derived', label: 'Derived answer' },
  { key: 'inferred', label: 'Unverified' },
]

export default function FilterRail({
  value,
  pool,
  onChange,
}: {
  value: Filters
  pool: 'scorable' | 'practice'
  onChange: (f: Filters) => void
}) {
  const toggle = (s: AnswerSource) =>
    onChange({
      ...value,
      sources: value.sources.includes(s)
        ? value.sources.filter((x) => x !== s)
        : [...value.sources, s],
    })

  return (
    <Card
      as="aside"
      aria-label="Filters"
      className="flex w-full max-w-full flex-col gap-[22px] p-4 sm:max-w-[260px] sm:flex-[1_1_220px]"
    >
      <div>
        <GroupTitle>Answer source</GroupTitle>
        {SOURCES.map((s) => (
          <Checkbox
            key={s.key}
            on={value.sources.includes(s.key)}
            label={s.label}
            onClick={() => toggle(s.key)}
            disabled={pool === 'scorable' && s.key !== 'official' && s.key !== 'key'}
          />
        ))}
        {pool === 'scorable' && (
          <NotYet>Choose All answered to include derived and unverified answers.</NotYet>
        )}
        {pool === 'practice' && (
          <NotYet>Questions without a usable answer are not in either pool yet.</NotYet>
        )}
      </div>

      <div>
        <GroupTitle>Exam year</GroupTitle>
        <div className="grid grid-cols-2 gap-2">
          {(['yearFrom', 'yearTo'] as const).map((key) => (
            <label key={key} className="flex flex-col gap-1 font-mono text-[10px] uppercase tracking-[0.06em] text-muted">
              {key === 'yearFrom' ? 'From' : 'To'}
              <input
                aria-label={key === 'yearFrom' ? 'From exam year' : 'To exam year'}
                type="number"
                min={1900}
                max={2100}
                placeholder="Any"
                value={value[key]}
                onChange={(e) => onChange({ ...value, [key]: e.target.value })}
                className="h-10 w-full rounded-[6px] border border-hairline2 bg-[#FBF8F1] px-2 font-sans text-[14px] normal-case tracking-normal text-ink placeholder:text-placeholder focus:border-ink focus:outline-none"
              />
            </label>
          ))}
        </div>
      </div>

      {/* Wired and correct, but matches nothing: every canonical question has
          exactly one appearance because the dedupe job has not run, and
          merging duplicate printings is what creates a repeat. Measured
          max(times_asked) = 1. Shown disabled rather than silently empty. */}
      <div>
        <GroupTitle>Repeats</GroupTitle>
        <Checkbox on={false} label="Asked 2+ times" disabled />
        <NotYet>
          No repeats yet — duplicate printings are merged by the dedupe job,
          which hasn’t run.
        </NotYet>
      </div>

      <div>
        <GroupTitle>Topic</GroupTitle>
        <NotYet>
          Not classified yet. 69,757 of 77,751 questions carry a placeholder
          subject, so topic filters would be meaningless.
        </NotYet>
      </div>
    </Card>
  )
}
