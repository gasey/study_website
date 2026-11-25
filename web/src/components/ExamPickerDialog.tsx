import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  EXAM_CATEGORIES,
  FLAGSHIP_EXAM_IDS,
  examCategory,
  examPresentation,
  type ExamCategoryId,
} from '../lib/examPresentation'
import type { Collection, ExamProgressSummary } from '../lib/api'

const FLAGSHIP_SET = new Set<string>(FLAGSHIP_EXAM_IDS)

interface ExamPickerProps {
  exams: Collection[]
  trackedIds: string[]
  activeExamId: string | null
  examProgress: ExamProgressSummary[]
  busyId?: string | null
  onToggleTrack: (examId: string) => void
  onSetPrimary: (examId: string) => void
  /** When provided, renders inside an accessible modal `<dialog>`. */
  open?: boolean
  onClose?: () => void
  /** Render inline inside the My Exams tab instead of a modal dialog. */
  inline?: boolean
}

function PickerBody({
  exams,
  trackedIds,
  activeExamId,
  examProgress,
  busyId,
  onToggleTrack,
  onSetPrimary,
  onClose,
  inline,
}: ExamPickerProps) {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<ExamCategoryId | 'flagship'>('all')

  const progressById = useMemo(
    () => new Map(examProgress.map((p) => [p.collection_id, p])),
    [examProgress],
  )

  const sortedExams = useMemo(() => {
    const flagshipOrder = [...FLAGSHIP_EXAM_IDS]
    const rank = (c: Collection) => {
      const idx = flagshipOrder.indexOf(c.id as (typeof FLAGSHIP_EXAM_IDS)[number])
      return idx >= 0 ? idx : 100
    }
    return [...exams].sort((a, b) => {
      const aTracked = trackedIds.includes(a.id) || a.id === activeExamId ? 0 : 1
      const bTracked = trackedIds.includes(b.id) || b.id === activeExamId ? 0 : 1
      if (aTracked !== bTracked) return aTracked - bTracked
      const ra = rank(a)
      const rb = rank(b)
      if (ra !== rb) return ra - rb
      return b.questions - a.questions || a.title.localeCompare(b.title)
    })
  }, [exams, trackedIds, activeExamId])

  const availableCategories = useMemo(() => {
    const present = new Set<ExamCategoryId>()
    for (const e of exams) present.add(examCategory(e.id, e.title))
    return EXAM_CATEGORIES.filter((c) => c.id === 'all' || present.has(c.id))
  }, [exams])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return sortedExams.filter((e) => {
      if (category === 'flagship' && !FLAGSHIP_SET.has(e.id)) return false
      if (category !== 'all' && category !== 'flagship' && examCategory(e.id, e.title) !== category) {
        return false
      }
      if (!q) return true
      const pres = examPresentation(e.id, e.title)
      return `${e.id} ${e.title} ${pres.short} ${pres.category}`.toLowerCase().includes(q)
    })
  }, [sortedExams, query, category])

  const effectiveTracked = useMemo(() => {
    const set = new Set(trackedIds)
    if (activeExamId) set.add(activeExamId)
    return set
  }, [trackedIds, activeExamId])

  const activeExam = exams.find((e) => e.id === activeExamId)

  return (
    <div className="finna-exam-picker">
      <div className="finna-exam-picker-head">
        <div>
          <h2 id="exam-picker-title" className="font-display text-xl font-bold text-ink">
            {inline ? 'Add or switch exams' : 'Choose your exams'}
          </h2>
          <p className="mt-1 text-sm text-secondary">
            Track as many exams as you are preparing for. Mark one as <strong>Primary</strong> to drive Today’s plan.
          </p>
        </div>
        {!inline && onClose && (
          <button
            type="button"
            className="finna-btn finna-btn-quiet"
            onClick={onClose}
            aria-label="Close exam selector"
          >
            Done
          </button>
        )}
      </div>

      <div className="finna-exam-picker-controls">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search UDC, LDC, Prelims, Group B, JE…"
          aria-label="Search exams"
          className="finna-exam-picker-search"
        />
        <div className="finna-exam-picker-cats" role="group" aria-label="Filter exams by category">
          <button
            type="button"
            aria-pressed={category === 'all'}
            onClick={() => setCategory('all')}
            className="finna-picker-cat-pill"
          >
            All ({exams.length})
          </button>
          <button
            type="button"
            aria-pressed={category === 'flagship'}
            onClick={() => setCategory('flagship')}
            className="finna-picker-cat-pill"
          >
            Popular MPSC
          </button>
          {availableCategories
            .filter((c) => c.id !== 'all')
            .map((c) => (
              <button
                key={c.id}
                type="button"
                aria-pressed={category === c.id}
                onClick={() => setCategory(c.id)}
                className="finna-picker-cat-pill"
              >
                {c.label}
              </button>
            ))}
        </div>
      </div>

      <div className="finna-exam-picker-list" role="list">
        {filtered.length === 0 ? (
          <p className="py-6 text-center text-sm text-secondary">
            No matching exams found.{' '}
            <button
              type="button"
              className="font-bold text-link underline"
              onClick={() => {
                setQuery('')
                setCategory('all')
              }}
            >
              Reset filters
            </button>
          </p>
        ) : (
          filtered.map((item) => {
            const isTracked = effectiveTracked.has(item.id)
            const isPrimary = item.id === activeExamId
            const pres = examPresentation(item.id, item.title)
            const prog = progressById.get(item.id)
            const pct =
              prog && item.questions > 0
                ? Math.min(100, Math.round((prog.unique_questions / item.questions) * 100))
                : null
            const isBusy = busyId === item.id

            return (
              <div
                key={item.id}
                role="listitem"
                className={`finna-exam-picker-row${isTracked ? ' is-tracked' : ''}${isPrimary ? ' is-primary' : ''}`}
              >
                <label className="finna-exam-picker-check">
                  <input
                    type="checkbox"
                    checked={isTracked}
                    disabled={isBusy || (isTracked && effectiveTracked.size <= 1)}
                    onChange={() => onToggleTrack(item.id)}
                    aria-label={`Track ${item.title}`}
                  />
                  <span className="finna-exam-stamp" aria-hidden="true">
                    {pres.short}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="finna-exam-picker-name">{item.title}</span>
                    <span className="finna-exam-picker-meta">
                      {item.questions.toLocaleString('en-IN')} Q · {pres.category}
                      {pct !== null && pct > 0 ? ` · ${pct}% covered` : ''}
                    </span>
                  </span>
                </label>

                <div className="finna-exam-picker-row-actions">
                  {isPrimary ? (
                    <span className="finna-primary-badge">★ Primary</span>
                  ) : (
                    <button
                      type="button"
                      disabled={isBusy}
                      onClick={() => onSetPrimary(item.id)}
                      className="finna-set-primary-btn"
                      title={`Make ${item.title} your primary exam`}
                    >
                      Set primary
                    </button>
                  )}
                </div>
              </div>
            )
          })
        )}
      </div>

      <div className="finna-exam-picker-foot">
        <span className="text-xs text-secondary">
          <strong>{effectiveTracked.size}</strong> {effectiveTracked.size === 1 ? 'exam' : 'exams'} tracked
          {activeExam ? ` · Primary: ${activeExam.title}` : ''}
        </span>
        <div className="flex items-center gap-3">
          <Link to="/exams" className="text-xs font-bold text-link hover:underline" onClick={onClose}>
            Full exam directory →
          </Link>
          {!inline && onClose && (
            <button type="button" className="finna-btn" onClick={onClose}>
              Save & close
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default function ExamPickerDialog(props: ExamPickerProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    if (props.inline) return
    const dialog = dialogRef.current
    if (!dialog) return
    if (props.open && !dialog.open) {
      dialog.showModal()
    } else if (!props.open && dialog.open) {
      dialog.close()
    }
  }, [props.open, props.inline])

  if (props.inline) {
    return (
      <section className="finna-card" aria-labelledby="exam-picker-title">
        <PickerBody {...props} />
      </section>
    )
  }

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby="exam-picker-title"
      onCancel={(e) => {
        e.preventDefault()
        props.onClose?.()
      }}
      onClick={(e) => {
        if (e.target === dialogRef.current) props.onClose?.()
      }}
      className="finna-exam-dialog"
    >
      {props.open && <PickerBody {...props} />}
    </dialog>
  )
}
