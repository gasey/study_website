import { useEffect, useMemo, useState } from 'react'
import type { Collection } from '../lib/api'
import { FLAGSHIP_EXAM_IDS, examPresentation } from '../lib/examPresentation'
import { MAX_FOCUS_SUBJECTS, shortExamLabel } from '../lib/trackedExams'
import {
  HOME_WIDGET_CATALOG,
  PRESET_DETAILS,
  PRESET_HIDDEN,
  type HomePreferences,
  type HomePreset,
  type HomeWidgetId,
} from '../lib/homePrefs'

export type WizardStep = 1 | 2 | 3

export interface SubjectChoice {
  id: string
  label: string
  questions: number
}

interface HomeSetupWizardProps {
  open: boolean
  initialStep?: WizardStep
  isFirstTime?: boolean
  exams: Collection[]
  trackedExamIds: string[]
  primaryExamId: string | null
  subjectChoices: SubjectChoice[]
  focusSubjectIds: string[]
  prefs: HomePreferences
  onClose: () => void
  onSkip: () => void
  onApply: (payload: {
    examIds: string[]
    primaryExamId: string | null
    subjectIds: string[]
    prefs: HomePreferences
  }) => Promise<void> | void
}

const GROUP_LABELS: Record<'top' | 'left' | 'community' | 'right', string> = {
  top: 'Top & Centre workspace',
  left: 'Left column (Exam, Plan & Games)',
  community: 'Discover & Live Standings column',
  right: 'Right column (Quests, Shortcuts & Tools)',
}

export default function HomeSetupWizard({
  open,
  initialStep = 1,
  isFirstTime = false,
  exams,
  trackedExamIds,
  primaryExamId,
  subjectChoices,
  focusSubjectIds,
  prefs,
  onClose,
  onSkip,
  onApply,
}: HomeSetupWizardProps) {
  const [step, setStep] = useState<WizardStep>(initialStep)
  const [examSearch, setExamSearch] = useState('')
  const [draftExams, setDraftExams] = useState<string[]>(trackedExamIds)
  const [draftPrimary, setDraftPrimary] = useState<string | null>(primaryExamId)
  const [draftSubjects, setDraftSubjects] = useState<string[]>(focusSubjectIds)
  const [draftPreset, setDraftPreset] = useState<HomePreset>(prefs.preset)
  const [draftHidden, setDraftHidden] = useState<HomeWidgetId[]>(prefs.hidden)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    setStep(initialStep)
    setExamSearch('')
    setDraftExams(trackedExamIds.length ? [...trackedExamIds] : primaryExamId ? [primaryExamId] : [])
    setDraftPrimary(primaryExamId || trackedExamIds[0] || null)
    setDraftSubjects([...focusSubjectIds])
    setDraftPreset(prefs.preset)
    setDraftHidden([...prefs.hidden])
    setSaving(false)
  }, [open, initialStep, trackedExamIds, primaryExamId, focusSubjectIds, prefs.preset, prefs.hidden])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !saving) {
        if (isFirstTime) onSkip()
        else onClose()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, saving, isFirstTime, onSkip, onClose])

  const sortedExams = useMemo(() => {
    const q = examSearch.trim().toLowerCase()
    const flagshipRank = new Map<string, number>(FLAGSHIP_EXAM_IDS.map((id, i) => [id, i]))
    const list = exams.filter((e) => {
      if (!q) return true
      const pres = examPresentation(e.id, e.title)
      return (
        e.title.toLowerCase().includes(q) ||
        e.id.toLowerCase().includes(q) ||
        pres.short.toLowerCase().includes(q) ||
        pres.category.toLowerCase().includes(q)
      )
    })
    return [...list].sort((a, b) => {
      const aSelected = draftExams.includes(a.id) ? 0 : 1
      const bSelected = draftExams.includes(b.id) ? 0 : 1
      if (aSelected !== bSelected) return aSelected - bSelected
      const aFlag = flagshipRank.get(a.id) ?? 999
      const bFlag = flagshipRank.get(b.id) ?? 999
      if (aFlag !== bFlag) return aFlag - bFlag
      return b.questions - a.questions
    })
  }, [exams, examSearch, draftExams])

  if (!open) return null

  function toggleExam(id: string) {
    setDraftExams((prev) => {
      if (prev.includes(id)) {
        const next = prev.filter((x) => x !== id)
        if (draftPrimary === id) setDraftPrimary(next[0] || null)
        return next
      }
      const next = [...prev, id]
      if (!draftPrimary) setDraftPrimary(id)
      return next
    })
  }

  function makePrimary(id: string) {
    setDraftPrimary(id)
    setDraftExams((prev) => (prev.includes(id) ? prev : [id, ...prev]))
  }

  function toggleSubject(id: string) {
    setDraftSubjects((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id)
      if (prev.length >= MAX_FOCUS_SUBJECTS) return prev
      return [...prev, id]
    })
  }

  function selectPreset(preset: HomePreset) {
    setDraftPreset(preset)
    setDraftHidden([...PRESET_HIDDEN[preset]])
  }

  function toggleWidget(id: HomeWidgetId) {
    setDraftHidden((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  async function handleSave() {
    if (saving) return
    setSaving(true)
    try {
      const resolvedPrimary =
        draftPrimary && draftExams.includes(draftPrimary)
          ? draftPrimary
          : draftExams[0] || primaryExamId || null
      await onApply({
        examIds: draftExams,
        primaryExamId: resolvedPrimary,
        subjectIds: draftSubjects,
        prefs: {
          preset: draftPreset,
          hidden: draftHidden,
          onboarded: true,
        },
      })
    } finally {
      setSaving(false)
    }
  }

  const visibleCount = HOME_WIDGET_CATALOG.length - draftHidden.length

  return (
    <div
      className="hsw-backdrop"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget && !saving) {
          if (isFirstTime) onSkip()
          else onClose()
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="hsw-title"
        className="hsw-dialog"
      >
        <header className="hsw-head">
          <div className="min-w-0">
            <span className="hsw-eyebrow">
              {isFirstTime ? 'Welcome to Finna · Quick setup' : 'Personalise your front page'}
            </span>
            <h2 id="hsw-title" className="hsw-title">
              {step === 1
                ? 'Which exams are you preparing for?'
                : step === 2
                  ? 'Which subjects do you want to focus on?'
                  : 'Choose what to show on Home'}
            </h2>
          </div>
          <button
            type="button"
            className="hsw-close"
            aria-label="Close setup"
            disabled={saving}
            onClick={() => (isFirstTime ? onSkip() : onClose())}
          >
            ×
          </button>
        </header>

        <nav className="hsw-steps" aria-label="Setup steps">
          {(
            [
              [1, '1. Exams'],
              [2, '2. Focus subjects'],
              [3, '3. Home layout'],
            ] as const
          ).map(([n, label]) => (
            <button
              key={n}
              type="button"
              aria-current={step === n ? 'step' : undefined}
              onClick={() => setStep(n)}
              className={`hsw-step-pill${step === n ? ' is-active' : ''}`}
            >
              {label}
            </button>
          ))}
        </nav>

        <div className="hsw-body">
          {step === 1 && (
            <div className="hsw-pane">
              <p className="hsw-sub">
                Pick one or more exams to track on your front page. Star your main target so
                Today’s plan and practice shortcuts match it. You can change this anytime.
              </p>
              <input
                type="search"
                value={examSearch}
                onChange={(e) => setExamSearch(e.target.value)}
                placeholder="Search exams (UDC, LDC, MCS, Group B, MES, Staff Nurse…)"
                aria-label="Search exams"
                className="hsw-search"
              />
              <div className="hsw-exam-grid">
                {sortedExams.slice(0, examSearch.trim() ? 24 : 12).map((item) => {
                  const picked = draftExams.includes(item.id)
                  const isPrimary = draftPrimary === item.id && picked
                  const pres = examPresentation(item.id, item.title)
                  return (
                    <div
                      key={item.id}
                      className={`hsw-exam-chip${picked ? ' is-picked' : ''}${isPrimary ? ' is-primary' : ''}`}
                    >
                      <button
                        type="button"
                        aria-pressed={picked}
                        onClick={() => toggleExam(item.id)}
                        className="hsw-exam-main"
                      >
                        <span className="hsw-exam-short">{shortExamLabel(item)}</span>
                        <span className="hsw-exam-meta">
                          <strong>{item.title}</strong>
                          <small>
                            {item.questions.toLocaleString('en-IN')} Q · {pres.category}
                          </small>
                        </span>
                      </button>
                      {picked && (
                        <button
                          type="button"
                          onClick={() => makePrimary(item.id)}
                          aria-pressed={isPrimary}
                          className={`hsw-star-btn${isPrimary ? ' is-on' : ''}`}
                          title={isPrimary ? 'Primary exam' : 'Set as primary exam'}
                        >
                          {isPrimary ? '★ Primary' : '☆ Primary'}
                        </button>
                      )}
                    </div>
                  )
                })}
              </div>
              {!sortedExams.length && (
                <p className="text-sm text-secondary">No exams match “{examSearch}”.</p>
              )}
            </div>
          )}

          {step === 2 && (
            <div className="hsw-pane">
              <p className="hsw-sub">
                Pick up to {MAX_FOCUS_SUBJECTS} focus subjects ({draftSubjects.length}/
                {MAX_FOCUS_SUBJECTS} selected). We’ll highlight them first in your Home subject
                progress.
              </p>
              <div className="hsw-subject-grid">
                {subjectChoices.map((subj) => {
                  const picked = draftSubjects.includes(subj.id)
                  const atMax = !picked && draftSubjects.length >= MAX_FOCUS_SUBJECTS
                  return (
                    <button
                      key={subj.id}
                      type="button"
                      aria-pressed={picked}
                      disabled={atMax}
                      onClick={() => toggleSubject(subj.id)}
                      className={`hsw-subj-chip${picked ? ' is-picked' : ''}`}
                    >
                      <span className="hsw-subj-check" aria-hidden="true">
                        {picked ? '✓' : '+'}
                      </span>
                      <span className="hsw-subj-copy">
                        <strong>{subj.label}</strong>
                        <small>{subj.questions.toLocaleString('en-IN')} questions</small>
                      </span>
                    </button>
                  )
                })}
              </div>
              {draftSubjects.length > 0 && (
                <button
                  type="button"
                  onClick={() => setDraftSubjects([])}
                  className="mt-2 text-xs font-semibold text-link underline"
                >
                  Clear subject selection
                </button>
              )}
            </div>
          )}

          {step === 3 && (
            <div className="hsw-pane">
              <p className="hsw-sub">
                Start with a calm preset, then hide or show any individual card. You can also hide
                any card directly from the front page later.
              </p>

              <div className="hsw-preset-grid" role="group" aria-label="Home layout presets">
                {PRESET_DETAILS.map((p) => {
                  const active = draftPreset === p.id
                  return (
                    <button
                      key={p.id}
                      type="button"
                      aria-pressed={active}
                      onClick={() => selectPreset(p.id)}
                      className={`hsw-preset-card${active ? ' is-active' : ''}`}
                    >
                      <div className="hsw-preset-top">
                        <strong>{p.title}</strong>
                        {p.badge && <span className="hsw-preset-badge">{p.badge}</span>}
                      </div>
                      <small>{p.summary}</small>
                    </button>
                  )
                })}
              </div>

              <div className="hsw-widget-meta-bar">
                <span>
                  Showing <strong>{visibleCount}</strong> of {HOME_WIDGET_CATALOG.length} cards
                </span>
                {draftHidden.length > 0 && (
                  <button
                    type="button"
                    onClick={() => selectPreset('everything')}
                    className="text-xs font-semibold text-link underline"
                  >
                    Show all
                  </button>
                )}
              </div>

              <div className="hsw-toggle-groups">
                {(['top', 'left', 'community', 'right'] as const).map((group) => (
                  <div key={group} className="hsw-toggle-group">
                    <h3>{GROUP_LABELS[group]}</h3>
                    <div className="hsw-toggle-list">
                      {HOME_WIDGET_CATALOG.filter((w) => w.group === group).map((w) => {
                        const shown = !draftHidden.includes(w.id)
                        return (
                          <label key={w.id} className="hsw-toggle-row">
                            <span className="hsw-toggle-copy">
                              <strong>{w.label}</strong>
                              <small>{w.description}</small>
                            </span>
                            <button
                              type="button"
                              role="switch"
                              aria-checked={shown}
                              aria-label={`${shown ? 'Hide' : 'Show'} ${w.label}`}
                              onClick={() => toggleWidget(w.id)}
                              className={`finna-st-toggle${shown ? ' is-on' : ''}`}
                            >
                              <span className="finna-st-toggle-dot" />
                            </button>
                          </label>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <footer className="hsw-foot">
          <div className="hsw-foot-left">
            {isFirstTime ? (
              <button
                type="button"
                className="hsw-ghost-btn"
                disabled={saving}
                onClick={onSkip}
              >
                Skip for now
              </button>
            ) : (
              <button
                type="button"
                className="hsw-ghost-btn"
                disabled={saving}
                onClick={onClose}
              >
                Cancel
              </button>
            )}
          </div>
          <div className="hsw-foot-right">
            {step > 1 && (
              <button
                type="button"
                className="finna-btn finna-btn-quiet"
                disabled={saving}
                onClick={() => setStep((s) => (s === 3 ? 2 : 1))}
              >
                ← Back
              </button>
            )}
            {step < 3 ? (
              <button
                type="button"
                className="finna-btn"
                disabled={saving}
                onClick={() => setStep((s) => (s === 1 ? 2 : 3))}
              >
                Next →
              </button>
            ) : (
              <button
                type="button"
                className="finna-btn"
                disabled={saving}
                onClick={() => void handleSave()}
              >
                {saving ? 'Saving…' : 'Save my Home'}
              </button>
            )}
          </div>
        </footer>
      </section>
    </div>
  )
}
