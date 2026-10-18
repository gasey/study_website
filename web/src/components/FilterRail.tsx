import type { AnswerSource } from '../lib/api'
import { Card, Checkbox, GroupTitle, NotYet } from './ui'

/** Filter rail, ported from markup line 390: white card, 14px radius, 16px
 *  padding, flex 1 1 220px capped at 260px, groups 22px apart. */

export interface Filters {
  sources: AnswerSource[]
}

const SOURCES: { key: AnswerSource; label: string }[] = [
  { key: 'official', label: 'Official key' },
  { key: 'key', label: 'Transcribed key' },
  { key: 'derived', label: 'Derived answer' },
  { key: 'inferred', label: 'Unverified' },
  { key: 'none', label: 'No published key' },
]

export default function FilterRail({
  value,
  onChange,
}: {
  value: Filters
  onChange: (f: Filters) => void
}) {
  const toggle = (s: AnswerSource) =>
    onChange({
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
        <GroupTitle>Answer key</GroupTitle>
        {SOURCES.map((s) => (
          <Checkbox
            key={s.key}
            on={value.sources.includes(s.key)}
            label={s.label}
            onClick={() => toggle(s.key)}
          />
        ))}
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
