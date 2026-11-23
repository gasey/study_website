import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { Link, useLocation } from 'react-router-dom'
import { focusedSession } from '../lib/navigation'

interface RouteTip {
  title: string
  steps: string[]
}

function tipsForRoute(pathname: string): RouteTip {
  if (pathname.startsWith('/practice') || pathname.startsWith('/bank')) {
    return {
      title: 'Practice & Question Bank',
      steps: [
        'Filter by exam, subject, year or your previous status (unseen, wrong, or saved).',
        'Toggle Timed run when you want a full exam countdown; untimed mode reveals explanations right away.',
        'Save tricky questions so they appear in your Revision queue across devices.',
      ],
    }
  }
  if (pathname.startsWith('/exams')) {
    return {
      title: 'Exam Workspaces',
      steps: [
        'Each exam groups its past papers, subject sections and timed mocks in one place.',
        'Set your primary exam to personalise your Home dashboard and Today plan.',
        'Use Papers to browse sitting-by-sitting, or jump straight into Practice.',
      ],
    }
  }
  if (pathname.startsWith('/results')) {
    return {
      title: 'Test Results & Mistake Review',
      steps: [
        'Use "Review mistakes" to step through only the questions you missed with their explanations.',
        'Search inside your results without losing original paper question numbers (Q1, Q2…).',
        'Click any topic card to filter down to that topic’s questions.',
      ],
    }
  }
  if (pathname.startsWith('/desk')) {
    return {
      title: 'Study Desk',
      steps: [
        'Keep your personal study notes, bookmarks and Pomodoro focus timer in one quiet workspace.',
        'Invite up to 6 study companions into a private group room for shared weekly goals.',
      ],
    }
  }
  return {
    title: 'Your Finna Study Home',
    steps: [
      'Start from the Return block at the top to resume your last paper, due reviews or repeated mistakes.',
      'Check the right-rail calendar for upcoming official exam dates and your recent practice days.',
      'Press Ctrl K (or /) anytime to jump directly to any exam, subject, past paper or guide.',
    ],
  }
}

const SHORTCUTS: [string, string][] = [
  ['Ctrl K  or  /', 'Open Quick Find (jump to any exam, paper or guide)'],
  ['?', 'Open or close this Help & Shortcuts drawer'],
  ['Esc', 'Close any open modal, menu or drawer'],
  ['↑  ↓  Enter', 'Navigate Quick Find results or mistake review'],
]

/**
 * Route-aware Help & Keyboard Shortcuts drawer.
 * Ported from ShikshaCom's TourProvider `?` shortcut + HelpPanel (§VII.19.3).
 * Suppressed during focused exam/mock sessions so it never interrupts a timer.
 */
export default function HelpDrawer() {
  const { pathname, search } = useLocation()
  const [open, setOpen] = useState(false)
  const isFocused = focusedSession(pathname, search)

  useEffect(() => {
    setOpen(false)
  }, [pathname])

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (isFocused) return
      if (e.key === 'Escape' && open) {
        setOpen(false)
        return
      }
      if (e.key !== '?' || e.ctrlKey || e.metaKey || e.altKey || e.repeat) return
      const el = document.activeElement as HTMLElement | null
      const typing =
        el && (/INPUT|TEXTAREA|SELECT/.test(el.tagName) || el.isContentEditable)
      if (typing) return
      if (!open && document.querySelector('dialog[open], [role="dialog"]')) return
      e.preventDefault()
      setOpen((v) => !v)
    }
    const onOpenEvent = () => {
      if (!isFocused) setOpen(true)
    }
    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('finna-open-help', onOpenEvent)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('finna-open-help', onOpenEvent)
    }
  }, [open, isFocused])

  if (!open || isFocused) return null
  const tips = tipsForRoute(pathname)

  return createPortal(
    <div
      className="finna-modal-backdrop"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) setOpen(false)
      }}
    >
      <div
        className="finna-help-sheet"
        role="dialog"
        aria-modal="true"
        aria-labelledby="finna-help-title"
      >
        <div className="finna-help-head">
          <div>
            <div className="finna-eyebrow">Quick guide</div>
            <h2 id="finna-help-title">{tips.title}</h2>
          </div>
          <button
            type="button"
            className="finna-btn finna-btn-quiet"
            onClick={() => setOpen(false)}
            aria-label="Close help"
          >
            Close
          </button>
        </div>

        <ol className="finna-help-steps">
          {tips.steps.map((step, i) => (
            <li key={i}>
              <span className="finna-help-num">{i + 1}</span>
              <span>{step}</span>
            </li>
          ))}
        </ol>

        <div className="finna-help-section">
          <h3>Keyboard shortcuts</h3>
          <ul className="finna-help-keys">
            {SHORTCUTS.map(([keys, desc]) => (
              <li key={keys}>
                <kbd>{keys}</kbd>
                <span>{desc}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="finna-help-foot">
          <Link to="/guides/using-finna" className="finna-btn" onClick={() => setOpen(false)}>
            Read Using Finna guide →
          </Link>
          <Link to="/index" className="finna-btn finna-btn-quiet" onClick={() => setOpen(false)}>
            All pages (/index)
          </Link>
        </div>
      </div>
    </div>,
    document.body,
  )
}
