import type { AnswerSource } from '../lib/api'

/** Filter rail, ported from `India Study Map v3.dc.html` line 390.
 *  White card, 14px radius, 16px padding; groups separated by a mono label
 *  with a 1px ink underline; 14px checkbox squares at 3px radius that fill
 *  solid ink when on. See docs/DESIGN-FIDELITY.md. */

export interface Filters {
  sources: AnswerSource[]
  repeatsOnly: boolean
}

const SOURCES: { key: AnswerSource; label: string }[] = [
  { key: 'official', label: 'Official key' },
  { key: 'key', label: 'Transcribed key' },
  { key: 'derived', label: 'Derived answer' },
  { key: 'inferred', label: 'Unverified' },
  { key: 'none', label: 'No published key' },
]

function Group({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-1.5 border-b border-ink pb-1.5 font-mono text-[11px] uppercase tracking-[0.1em] text-muted">
        {title}
      </div>
      {children}
    </div>
  )
}

function Check({
  on,
  label,
  onClick,
}: {
  on: boolean
  label: string
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      aria-pressed={on}
      className="flex w-full cursor-pointer items-center gap-2.5 py-1.5 text-left text-[14px]"
    >
      <span
        className={`h-[14px] w-[14px] shrink-0 rounded-[3px] border border-ink ${
          on ? 'bg-ink' : 'bg-transparent'
        }`}
      />
      <span>{label}</span>
    </button>
  )
}

export default function FilterRail({
  value,
  onChange,
}: {
  value: Filters
  onChange: (f: Filters) => void
}) {
  const toggleSource = (s: AnswerSource) =>
    onChange({
      ...value,
      sources: value.sources.includes(s)
        ? value.sources.filter((x) => x !== s)
        : [...value.sources, s],
    })

  return (
    <aside className="flex max-w-[260px] flex-[1_1_220px] flex-col gap-[22px] rounded-[14px] border border-hairline bg-card p-4 shadow-[0_1px_2px_rgba(29,27,24,.05)]">
      <Group title="Answer key">
        {SOURCES.map((s) => (
          <Check
            key={s.key}
            on={value.sources.includes(s.key)}
            label={s.label}
            onClick={() => toggleSource(s.key)}
          />
        ))}
      </Group>

      {/* "Asked 2+ times" is wired and correct, but matches nothing today:
          every canonical question has exactly one appearance because the
          dedupe job has not run, and merging duplicate printings is what
          creates a repeat. Measured on the live DB: max(times_asked) = 1.
          Disabled rather than silently returning an empty list. */}
      <Group title="Repeats">
        <div className="flex items-center gap-2.5 py-1.5 text-[14px] text-muted">
          <span className="h-[14px] w-[14px] shrink-0 rounded-[3px] border border-hairline2" />
          <span>Asked 2+ times</span>
        </div>
        <p className="text-[13px] leading-snug text-muted">
          No repeats found yet — duplicate printings are merged by the dedupe
          job, which hasn’t run.
        </p>
      </Group>

      {/* The prototype filters by topic (Current affairs, Polity, Science…).
          Our `subject` and `topic` are NULL on every row by design until
          classification runs — see CLAUDE.md rule 5. Showing the group empty
          is honest; inventing placeholder topics would not be. */}
      <Group title="Topic">
        <p className="py-1.5 text-[13px] leading-snug text-muted">
          Not classified yet. 69,757 of 77,751 questions carry a placeholder
          subject, so topic filters would be meaningless until that work runs.
        </p>
      </Group>
    </aside>
  )
}
