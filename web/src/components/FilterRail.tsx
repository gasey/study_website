import type { AnswerSource } from '../lib/api'
import { Card, Checkbox, GroupTitle, NotYet } from './ui'
import type { TaxonomyFacet } from '../lib/api'

/** Filter rail, ported from markup line 390: white card, 14px radius, 16px
 *  padding, flex 1 1 220px capped at 260px, groups 22px apart. */

export interface Filters {
  sources: AnswerSource[]
  yearFrom: string
  yearTo: string
  subjectId: string
  topicId: string
}

const SOURCES: { key: AnswerSource; label: string }[] = [
  { key: 'official', label: 'Official key' },
  { key: 'key', label: 'Transcribed key' },
  { key: 'derived', label: 'Worked solution' },
  { key: 'inferred', label: 'Suggested answer' },
  { key: 'none', label: 'No recorded answer' },
]

export default function FilterRail({
  value,
  pool,
  taxonomy,
  onChange,
}: {
  value: Filters
  pool: 'all' | 'scorable' | 'practice'
  taxonomy: TaxonomyFacet[]
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
        <details><summary className="min-h-11 cursor-pointer py-3 font-semibold text-[13px]">Source details</summary><p className="mb-2 text-[12px] text-muted">Source and verification are separate. Worked solutions may be verified or still need review.</p>
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
          <NotYet>Choose All answered to include worked solutions and answers awaiting review.</NotYet>
        )}
        {pool === 'practice' && (
          <NotYet>Questions without a usable answer are not in either pool yet.</NotYet>
        )}
        {pool === 'all' && (
          <NotYet>Choose “No recorded answer” to find questions that are browse-only.</NotYet>
        )}
        </details>
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
        {taxonomy.length ? (
          <div className="flex flex-col gap-2">
            <label className="sr-only" htmlFor="bank-subject">Subject</label>
            <select
              id="bank-subject"
              aria-label="Filter by subject"
              value={value.subjectId}
              onChange={(e) => onChange({ ...value, subjectId: e.target.value, topicId: '' })}
              className="h-10 rounded-[6px] border border-hairline2 bg-[#FBF8F1] px-2 text-[13px] text-ink focus:border-ink focus:outline-none"
            >
              <option value="">All subjects</option>
              {['general-knowledge','general-studies'].includes(value.subjectId)&&<option value={value.subjectId}>GK/GS · original {value.subjectId==='general-knowledge'?'GK':'GS'} tags</option>}
              {[...new Map(taxonomy.map((f) => [f.subject_id, f.subject])).entries()].map(([id, label]) => (
                <option key={id} value={id}>{label}</option>
              ))}
            </select>
            <label className="sr-only" htmlFor="bank-topic">Topic</label>
            <select
              id="bank-topic"
              aria-label="Filter by topic"
              value={value.topicId}
              disabled={!value.subjectId}
              onChange={(e) => onChange({ ...value, topicId: e.target.value })}
              className="h-10 rounded-[6px] border border-hairline2 bg-[#FBF8F1] px-2 text-[13px] text-ink focus:border-ink focus:outline-none disabled:opacity-50"
            >
              <option value="">All topics</option>
              {value.topicId&&!taxonomy.some(f=>f.topic_id===value.topicId)&&<option value={value.topicId}>Original topic selection</option>}
              {taxonomy.filter((f) => f.subject_id === value.subjectId && f.topic_id).map((f) => (
                <option key={f.topic_id} value={f.topic_id!}>{f.topic} ({f.questions})</option>
              ))}
            </select>
            <p className="text-[11px] leading-snug text-muted">GK and GS share learning topics. Original paper wording appears on each question’s source.</p>
          </div>
        ) : (
          <NotYet>Reviewed subject and topic tags will appear here as they are added.</NotYet>
        )}
      </div>
    </Card>
  )
}
