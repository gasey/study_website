import { useEffect, useMemo, useState } from 'react'
import {
  getFocusSubjects,
  getMastery,
  type FocusSubjects,
  type MasterySnapshot,
  type TopicMastery,
} from '../lib/api'
import { FocusPicker } from './TodayCard'

const INITIAL_TOPIC_CAP = 9

function stateTone(t: TopicMastery): 'strong' | 'building' | 'rusty' | 'new' {
  if (t.rusty) return 'rusty'
  if (t.accuracy >= 75 || t.state === 'mastered' || t.state === 'proficient') return 'strong'
  if (t.accuracy >= 50 || t.state === 'practicing') return 'building'
  return 'new'
}

export default function MasteryMap() {
  const [data, setData] = useState<MasterySnapshot | null>(null)
  const [focus, setFocus] = useState<FocusSubjects | null>(null)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  const [activeSubject, setActiveSubject] = useState<string>('')
  const [showAllTopics, setShowAllTopics] = useState(false)
  const [focusOpen, setFocusOpen] = useState(false)

  useEffect(() => {
    let live = true
    setData(null)
    setFocus(null)
    setError('')
    Promise.all([getMastery(), getFocusSubjects()])
      .then(([m, f]) => {
        if (live) {
          setData(m)
          setFocus(f)
        }
      })
      .catch((e) => {
        if (live) setError(e instanceof Error ? e.message : 'Could not load mastery.')
      })
    const refresh = () => {
      setData(null)
      setFocus(null)
      setRetry((n) => n + 1)
    }
    window.addEventListener('ism-auth-change', refresh)
    window.addEventListener('ism-focus-change', refresh)
    return () => {
      live = false
      window.removeEventListener('ism-auth-change', refresh)
      window.removeEventListener('ism-focus-change', refresh)
    }
  }, [retry])

  const groups = useMemo(() => {
    if (!data?.items.length) return []
    const ids = [...new Set(data.items.map((i) => i.subject_id))]
    return ids
      .map((id) => {
        const items = data.items
          .filter((i) => i.subject_id === id)
          .sort((a, b) => Number(b.rusty) - Number(a.rusty) || b.distinct_attempted - a.distinct_attempted)
        return {
          id,
          label: items[0].subject_label,
          items,
          isFocus: Boolean(focus?.items.some((f) => f.subject_id === id)),
        }
      })
      .sort((a, b) => Number(b.isFocus) - Number(a.isFocus) || b.items.length - a.items.length)
  }, [data, focus])

  // Default cleanly to the top/focus subject so Mastery stays compact instead of dumping 50+ cards
  const resolvedSubject = useMemo(() => {
    if (activeSubject === '__all__') return '__all__'
    if (activeSubject && groups.some((g) => g.id === activeSubject)) return activeSubject
    return groups[0]?.id || '__all__'
  }, [activeSubject, groups])

  const summary = useMemo(() => {
    const all = data?.items || []
    let strong = 0
    let rusty = 0
    for (const item of all) {
      if (item.rusty) rusty++
      else if (item.accuracy >= 75 || item.state === 'mastered' || item.state === 'proficient') strong++
    }
    return { total: all.length, strong, rusty }
  }, [data])

  const visibleItems = useMemo(() => {
    if (resolvedSubject === '__all__') return data?.items || []
    return groups.find((g) => g.id === resolvedSubject)?.items || []
  }, [data, groups, resolvedSubject])

  const displayedItems = showAllTopics ? visibleItems : visibleItems.slice(0, INITIAL_TOPIC_CAP)
  const hiddenCount = Math.max(0, visibleItems.length - displayedItems.length)

  return (
    <section className="mm-card rounded-panel border border-hairline bg-card p-4 sm:p-5">
      <div className="mm-head">
        <div className="min-w-0">
          <div className="mm-title-row">
            <h2 className="font-display text-lg font-bold text-ink">Topic mastery</h2>
            {summary.total > 0 && (
              <div className="mm-stat-pills">
                <span className="mm-pill">{summary.total} topics</span>
                {summary.strong > 0 && <span className="mm-pill is-strong">{summary.strong} strong</span>}
                {summary.rusty > 0 && <span className="mm-pill is-rusty">◷ {summary.rusty} rusty</span>}
              </div>
            )}
          </div>
          <p className="mt-1 text-xs text-secondary">
            Verified-key accuracy by topic. Rusty = 45+ days idle (your earned tier stays).
          </p>
        </div>

        {focus && (
          <button
            type="button"
            onClick={() => setFocusOpen((v) => !v)}
            aria-expanded={focusOpen}
            className="mm-focus-toggle"
          >
            {focusOpen ? 'Hide focus subjects' : `Focus subjects (${focus.items.length}) ▾`}
          </button>
        )}
      </div>

      {focus && focusOpen && (
        <div className="mt-3 rounded-xl border border-hairline bg-canvas p-3">
          <FocusPicker focus={focus} onSaved={() => setRetry((n) => n + 1)} />
        </div>
      )}

      {error ? (
        <p role="alert" className="mt-3 text-sm text-wrong">
          {error}{' '}
          <button type="button" className="min-h-10 font-bold text-link underline" onClick={() => setRetry((n) => n + 1)}>
            Try again
          </button>
        </p>
      ) : !data ? (
        <p role="status" className="mt-3 text-xs text-secondary">
          Loading mastery…
        </p>
      ) : !groups.length ? (
        <p className="mt-3 text-sm text-secondary">
          Answer verified questions with approved topic tags to start building your mastery map.
        </p>
      ) : (
        <>
          <div className="mm-subj-tabs" role="tablist" aria-label="Mastery subjects">
            {groups.map((g) => (
              <button
                key={g.id}
                type="button"
                role="tab"
                aria-selected={resolvedSubject === g.id}
                onClick={() => {
                  setActiveSubject(g.id)
                  setShowAllTopics(false)
                }}
                className={`mm-subj-tab${resolvedSubject === g.id ? ' is-on' : ''}`}
              >
                <span>{g.isFocus ? '★ ' : ''}{g.label}</span>
                <small>{g.items.length}</small>
              </button>
            ))}
            {groups.length > 1 && (
              <button
                type="button"
                role="tab"
                aria-selected={resolvedSubject === '__all__'}
                onClick={() => {
                  setActiveSubject('__all__')
                  setShowAllTopics(false)
                }}
                className={`mm-subj-tab${resolvedSubject === '__all__' ? ' is-on' : ''}`}
              >
                <span>All</span>
                <small>{summary.total}</small>
              </button>
            )}
          </div>

          <div className="mm-grid">
            {displayedItems.map((t) => {
              const tone = stateTone(t)
              return (
                <div
                  key={t.topic}
                  className={`mm-tile is-${tone}`}
                  aria-label={`${t.topic_label}: ${t.rusty ? 'rusty, earned tier ' : ''}${t.state}, ${t.accuracy}% accuracy`}
                >
                  <div className="mm-tile-top">
                    <strong className="mm-tile-name" title={t.topic_label}>
                      {t.topic_label}
                    </strong>
                    <span className={`mm-tile-pct is-${tone}`}>{t.accuracy}%</span>
                  </div>
                  <div className="mm-tile-bar" aria-hidden="true">
                    <span style={{ width: `${Math.max(4, Math.min(100, t.accuracy))}%` }} />
                  </div>
                  <div className="mm-tile-meta">
                    <span>{t.distinct_attempted} Qs</span>
                    <span className="capitalize">
                      {t.rusty ? '◷ Rusty · ' : ''}
                      {t.state}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>

          {(hiddenCount > 0 || (showAllTopics && visibleItems.length > INITIAL_TOPIC_CAP)) && (
            <div className="mt-3 flex justify-center">
              <button
                type="button"
                onClick={() => setShowAllTopics((v) => !v)}
                className="mm-more-btn"
              >
                {showAllTopics
                  ? 'Show fewer topics'
                  : `Show all ${visibleItems.length} topics (+${hiddenCount} more)`}
              </button>
            </div>
          )}
        </>
      )}
    </section>
  )
}
