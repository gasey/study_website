import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { moduleHref, type Collection, type ExamProgressSummary } from '../lib/api'
import { examPresentation } from '../lib/examPresentation'
import { choosePreferredExam } from '../lib/preferredExam'
import { addLocalTrackedExam } from '../lib/trackedExams'

interface PanelVisual {
  shortTitle: string
  tagline: string
  image: string
  accent: string
}

const PANEL_VISUALS: Record<string, PanelVisual> = {
  udc: {
    shortTitle: 'UDC',
    tagline: 'Upper Division Clerk · past papers, GK, English & arithmetic drills',
    image: '/images/discover/guides.jpg',
    accent: '#0A7D8C',
  },
  ldc: {
    shortTitle: 'LDC',
    tagline: 'Lower Division Clerk · objective sets, clerical English & speed practice',
    image: '/images/discover/calendar.jpg',
    accent: '#1F4BE0',
  },
  'combined-prelims': {
    shortTitle: 'MCS Prelims',
    tagline: 'Mizoram Civil Services · Paper I General Studies & Paper II Aptitude',
    image: '/images/discover/stats.jpg',
    accent: '#4338CA',
  },
  'group-b-gazetted': {
    shortTitle: 'Group B Gazetted',
    tagline: 'Common General Studies, English & departmental technical papers',
    image: '/images/discover/chronicle.jpg',
    accent: '#7C3AED',
  },
  'group-b-non-gazetted': {
    shortTitle: 'Group B Non-Gaz.',
    tagline: 'Non-Gazetted recruitment papers, GK, aptitude & office subjects',
    image: '/images/discover/atlas.jpg',
    accent: '#059669',
  },
  mes: {
    shortTitle: 'MES',
    tagline: 'Mizoram Engineering Service · branch papers, syllabus & regulations',
    image: '/images/discover/games.jpg',
    accent: '#B45309',
  },
}

const PREFERRED_ORDER = [
  'udc',
  'ldc',
  'combined-prelims',
  'group-b-gazetted',
  'mes',
  'group-b-non-gazetted',
]

export default function FlagshipExamPanels({
  exams,
  progress,
  bookmarks,
  onToggleBookmark,
  busyBookmark,
}: {
  exams: Collection[]
  progress: Record<string, ExamProgressSummary>
  bookmarks: string[]
  onToggleBookmark: (c: Collection) => void
  busyBookmark: string | null
}) {
  const featured = useMemo(() => {
    const out: Collection[] = []
    for (const id of PREFERRED_ORDER) {
      const match = exams.find((e) => e.id === id)
      if (match) out.push(match)
      if (out.length >= 5) break
    }
    return out
  }, [exams])

  const [activeId, setActiveId] = useState<string>('')
  const resolvedActive = featured.some((e) => e.id === activeId)
    ? activeId
    : featured[0]?.id || ''

  if (featured.length < 3) return null

  return (
    <section className="exp-panels-wrap" aria-labelledby="flagship-spotlight-title">
      <div className="exp-panels-head">
        <div>
          <span className="cr-eyebrow">Flagship MPSC exams · Quick launch</span>
          <h2 id="flagship-spotlight-title">Most-studied recruitment exams</h2>
        </div>
        <span className="text-xs font-semibold text-secondary">
          Tap or hover any exam card to expand
        </span>
      </div>

      <div className="exp-panels" role="list">
        {featured.map((c) => {
          const isExpanded = c.id === resolvedActive
          const vis = PANEL_VISUALS[c.id] || {
            shortTitle: c.title,
            tagline: examPresentation(c.id, c.title).category,
            image: '/images/discover/guides.jpg',
            accent: '#1F4BE0',
          }
          const pres = examPresentation(c.id, c.title)
          const prog = progress[c.id]
          const pct =
            prog && c.questions > 0
              ? Math.min(100, Math.round((prog.unique_questions / c.questions) * 100))
              : 0
          const saved = bookmarks.includes(c.id)
          const href = moduleHref(c)

          return (
            <article
              key={c.id}
              role="listitem"
              className={`exp-panel${isExpanded ? ' is-open' : ''}`}
              style={{ ['--exp-accent' as string]: vis.accent }}
              onMouseEnter={() => setActiveId(c.id)}
              onFocus={() => setActiveId(c.id)}
              onClick={() => {
                if (!isExpanded) setActiveId(c.id)
              }}
            >
              <img
                src={vis.image}
                alt=""
                aria-hidden="true"
                loading="lazy"
                decoding="async"
                className="exp-panel-bg"
              />
              <div className="exp-panel-scrim" aria-hidden="true" />

              <div className="exp-panel-content">
                <div className="exp-panel-top">
                  <span className="exp-panel-stamp">{pres.short}</span>
                  {isExpanded && (
                    <button
                      type="button"
                      className={`exp-panel-save${saved ? ' is-saved' : ''}`}
                      disabled={busyBookmark !== null}
                      onClick={(e) => {
                        e.stopPropagation()
                        onToggleBookmark(c)
                      }}
                      aria-pressed={saved}
                    >
                      {saved ? '★ Tracked' : '+ Track'}
                    </button>
                  )}
                </div>

                {/* Vertical rail label when collapsed on desktop */}
                {!isExpanded && (
                  <div className="exp-panel-collapsed-label" aria-hidden="true">
                    <strong>{vis.shortTitle}</strong>
                    <span>{c.questions.toLocaleString('en-IN')} Q</span>
                  </div>
                )}

                {/* Full rich editorial details when expanded */}
                <div className="exp-panel-details">
                  <span className="exp-panel-cat">{pres.category}</span>
                  <h3>{vis.shortTitle}</h3>
                  <p>{vis.tagline}</p>

                  <div className="exp-panel-stats">
                    <span>
                      <strong>{c.questions.toLocaleString('en-IN')}</strong> questions
                    </span>
                    <span>
                      <strong>{c.scorable.toLocaleString('en-IN')}</strong> official key
                    </span>
                    <span>
                      <strong>{pct}%</strong> covered
                    </span>
                  </div>

                  <div className="exp-panel-actions">
                    <Link
                      to={href}
                      className="exp-panel-cta"
                      onClick={() => {
                        choosePreferredExam(c.id)
                        addLocalTrackedExam(c.id)
                      }}
                    >
                      Open booklet →
                    </Link>
                    <Link
                      to={'/practice?exam=' + encodeURIComponent(c.id)}
                      className="exp-panel-ghost"
                      onClick={() => {
                        choosePreferredExam(c.id)
                        addLocalTrackedExam(c.id)
                      }}
                    >
                      Practice
                    </Link>
                  </div>
                </div>
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}
