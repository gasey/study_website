import { Link, useLocation, useNavigate } from 'react-router-dom'
import { focusedSession } from '../lib/navigation'

interface Crumb {
  label: string
  to?: string
}

const EXAM_LABELS: Record<string, string> = {
  udc: 'UDC',
  ldc: 'LDC',
  assistant: 'Assistant Grade',
  'combined-prelims': 'MCS Prelims',
  'group-b-gazetted': 'Group B Gazetted',
  'group-b-non-gazetted': 'Group B Non-Gazetted',
  mes: 'MES',
  'iti-instructor': 'ITI Instructor',
  'subject-gk-gs': 'General Knowledge & Studies',
  'subject-english': 'English',
  'subject-mathematics': 'Mathematics & Arithmetic',
  'subject-reasoning': 'Reasoning & Aptitude',
  'subject-mizo': 'Mizo',
  'gk-gs': 'General Knowledge & Studies',
  english: 'English',
  mathematics: 'Mathematics & Arithmetic',
  reasoning: 'Reasoning & Aptitude',
  mizo: 'Mizo',
}

const VIEW_LABELS: Record<string, string> = {
  browse: 'Browse',
  topics: 'Subjects & Topics',
  papers: 'Past Papers',
  practice: 'Practice',
  progress: 'Progress',
}

function prettySlug(slug: string): string {
  const decoded = decodeURIComponent(slug).replace(/^subject-/, '')
  if (EXAM_LABELS[decoded]) return EXAM_LABELS[decoded]
  return decoded
    .split(/[-_]+/)
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

function buildTrail(pathname: string, search: string): { crumbs: Crumb[]; fallbackTo: string } {
  const params = new URLSearchParams(search)
  const parts = pathname.split('/').filter(Boolean)
  const root = parts[0] || ''

  const home: Crumb = { label: 'Home', to: '/home' }

  if (root === 'exams') {
    if (parts.length === 1) return { crumbs: [home, { label: 'Exams' }], fallbackTo: '/home' }
    const examId = parts[1]
    const examLabel = prettySlug(examId)
    const sub = parts[2]
    const view = params.get('view')
    if (sub === 'paper') {
      return {
        crumbs: [home, { label: 'Exams', to: '/exams' }, { label: examLabel, to: `/exams/${examId}` }, { label: 'Paper viewer' }],
        fallbackTo: `/exams/${examId}`,
      }
    }
    if (view && VIEW_LABELS[view]) {
      return {
        crumbs: [home, { label: 'Exams', to: '/exams' }, { label: examLabel, to: `/exams/${examId}` }, { label: VIEW_LABELS[view] }],
        fallbackTo: '/exams',
      }
    }
    return {
      crumbs: [home, { label: 'Exams', to: '/exams' }, { label: examLabel }],
      fallbackTo: '/exams',
    }
  }

  if (root === 'subjects') {
    if (parts.length === 1) return { crumbs: [home, { label: 'Subjects' }], fallbackTo: '/home' }
    const subjectId = parts[1]
    const subjectLabel = prettySlug(subjectId)
    const view = params.get('view')
    if (view && VIEW_LABELS[view] && view !== 'browse') {
      return {
        crumbs: [home, { label: 'Subjects', to: '/library' }, { label: subjectLabel, to: `/subjects/${subjectId}` }, { label: VIEW_LABELS[view] }],
        fallbackTo: '/library',
      }
    }
    return {
      crumbs: [home, { label: 'Subjects', to: '/library' }, { label: subjectLabel }],
      fallbackTo: '/library',
    }
  }

  if (root === 'library') {
    if (parts.length === 1) return { crumbs: [home, { label: 'Subjects' }], fallbackTo: '/home' }
    return {
      crumbs: [home, { label: 'Subjects', to: '/library' }, { label: prettySlug(parts[parts.length - 1]) }],
      fallbackTo: '/library',
    }
  }

  if (root === 'past-papers') {
    return { crumbs: [home, { label: 'Exams', to: '/exams' }, { label: 'Past papers' }], fallbackTo: '/exams' }
  }

  if (root === 'calendar') {
    return { crumbs: [home, { label: 'Exams', to: '/exams' }, { label: 'Exam calendar' }], fallbackTo: '/exams' }
  }

  if (root === 'practice') {
    if (parts[1] === 'build') {
      return { crumbs: [home, { label: 'Practice', to: '/practice' }, { label: 'Build a test' }], fallbackTo: '/practice' }
    }
    return { crumbs: [home, { label: 'Practice' }], fallbackTo: '/home' }
  }

  if (root === 'revise') {
    return { crumbs: [home, { label: 'Practice', to: '/practice' }, { label: 'Revise' }], fallbackTo: '/home' }
  }

  if (root === 'bank') {
    if (parts[1]) {
      return { crumbs: [home, { label: 'Question bank', to: '/bank' }, { label: 'Question' }], fallbackTo: '/bank' }
    }
    return { crumbs: [home, { label: 'Practice', to: '/practice' }, { label: 'Question bank' }], fallbackTo: '/practice' }
  }

  if (root === 'tests') {
    if (parts[1]) {
      return { crumbs: [home, { label: 'Shared tests', to: '/tests' }, { label: 'Test details' }], fallbackTo: '/tests' }
    }
    return { crumbs: [home, { label: 'Practice', to: '/practice' }, { label: 'Shared tests' }], fallbackTo: '/practice' }
  }

  if (root === 'results') {
    return { crumbs: [home, { label: 'Practice', to: '/practice' }, { label: 'Test result' }], fallbackTo: '/practice' }
  }

  if (root === 'games') {
    if (parts[1] === 'quest') {
      return {
        crumbs: [home, { label: 'Play & Games', to: '/games' }, { label: 'Finna Quest RPG' }],
        fallbackTo: '/games',
      }
    }
    return { crumbs: [home, { label: 'Practice', to: '/practice' }, { label: 'Play & Games' }], fallbackTo: '/practice' }
  }

  if (root === 'guides') {
    if (parts[1]) {
      return { crumbs: [home, { label: 'Concept Guides', to: '/guides' }, { label: prettySlug(parts[1]) }], fallbackTo: '/guides' }
    }
    return { crumbs: [home, { label: 'Concept Guides' }], fallbackTo: '/home' }
  }

  if (root === 'atlas') {
    return { crumbs: [home, { label: 'Tools & Guides', to: '/guides' }, { label: 'Interactive Atlas' }], fallbackTo: '/guides' }
  }

  if (root === 'chronicle') {
    return { crumbs: [home, { label: 'Tools & Guides', to: '/guides' }, { label: 'History Chronicle' }], fallbackTo: '/guides' }
  }

  if (root === 'stats') {
    if (parts.length > 1) {
      return { crumbs: [home, { label: 'India & Global Stats', to: '/stats' }, { label: prettySlug(parts[parts.length - 1]) }], fallbackTo: '/stats' }
    }
    return { crumbs: [home, { label: 'Tools & Guides', to: '/guides' }, { label: 'India & Global Stats' }], fallbackTo: '/guides' }
  }

  if (root === 'desk') {
    if (parts[1]) {
      return { crumbs: [home, { label: 'Study Desk', to: '/desk' }, { label: 'Study room' }], fallbackTo: '/desk' }
    }
    return { crumbs: [home, { label: 'Study Desk' }], fallbackTo: '/home' }
  }

  if (root === 'vault') {
    return { crumbs: [home, { label: 'Personal Vault' }], fallbackTo: '/home' }
  }

  if (root === 'community') {
    if (parts[1] === 'questions') {
      return { crumbs: [home, { label: 'Community', to: '/community' }, { label: 'Community questions' }], fallbackTo: '/community' }
    }
    return { crumbs: [home, { label: 'Community' }], fallbackTo: '/home' }
  }

  if (root === 'materials') {
    if (parts[1]) {
      return { crumbs: [home, { label: 'Study materials', to: '/materials' }, { label: 'Reader' }], fallbackTo: '/materials' }
    }
    return { crumbs: [home, { label: 'Community', to: '/community' }, { label: 'Study materials' }], fallbackTo: '/community' }
  }

  if (root === 'creators') {
    if (parts[1]) {
      return { crumbs: [home, { label: 'Creators', to: '/creators' }, { label: parts[1] === 'settings' ? 'Settings' : 'Profile' }], fallbackTo: '/creators' }
    }
    return { crumbs: [home, { label: 'Community', to: '/community' }, { label: 'Creators' }], fallbackTo: '/community' }
  }

  if (root === 'create') {
    if (parts[1]) {
      return { crumbs: [home, { label: 'Create', to: '/create' }, { label: parts[1] === 'new' ? 'Editor' : 'Submissions' }], fallbackTo: '/create' }
    }
    return { crumbs: [home, { label: 'Create' }], fallbackTo: '/home' }
  }

  if (root === 'contributions') {
    return { crumbs: [home, { label: 'Submissions', to: '/create/submissions' }, { label: parts[2] === 'edit' ? 'Edit proposal' : 'Proposal' }], fallbackTo: '/create/submissions' }
  }

  if (root === 'studio') {
    if (parts[1]) {
      return { crumbs: [home, { label: 'Content Studio', to: '/studio' }, { label: 'Editor' }], fallbackTo: '/studio' }
    }
    return { crumbs: [home, { label: 'Create', to: '/create' }, { label: 'Content Studio' }], fallbackTo: '/create' }
  }

  if (root === 'profile') {
    if (parts[1]) {
      return { crumbs: [home, { label: 'Profile', to: '/profile' }, { label: prettySlug(parts[1]) }], fallbackTo: '/profile' }
    }
    return { crumbs: [home, { label: 'Profile' }], fallbackTo: '/home' }
  }

  if (root === 'account') {
    return { crumbs: [home, { label: 'Profile', to: '/profile' }, { label: 'Account settings' }], fallbackTo: '/profile' }
  }

  if (root === 'inbox') return { crumbs: [home, { label: 'Inbox' }], fallbackTo: '/home' }
  if (root === 'search') return { crumbs: [home, { label: 'Search' }], fallbackTo: '/home' }
  if (root === 'index') return { crumbs: [home, { label: 'All pages' }], fallbackTo: '/home' }
  if (root === 'plans' || root === 'billing') return { crumbs: [home, { label: prettySlug(root) }], fallbackTo: '/home' }
  if (root === 'policies') return { crumbs: [home, { label: 'Policies' }], fallbackTo: '/home' }

  return { crumbs: [home, { label: prettySlug(root || 'Page') }], fallbackTo: '/home' }
}

const HIDDEN_ROOTS = new Set(['', 'home', 'login', 'join', 'google', 'onboarding', 'admin'])

/** Slim global Back + Breadcrumb strip so learners always have a reliable way back. */
export default function RouteBackBar() {
  const { pathname, search } = useLocation()
  const navigate = useNavigate()
  const firstSegment = pathname.split('/').filter(Boolean)[0] || ''

  if (HIDDEN_ROOTS.has(firstSegment) || focusedSession(pathname, search)) {
    return null
  }

  const { crumbs, fallbackTo } = buildTrail(pathname, search)
  const canStepBack =
    typeof window !== 'undefined' &&
    window.history.state &&
    typeof window.history.state.idx === 'number' &&
    window.history.state.idx > 0

  function handleBack() {
    if (canStepBack) navigate(-1)
    else navigate(fallbackTo)
  }

  return (
    <div className="finna-backbar">
      <div className="finna-wrap finna-backbar-row">
        <button
          type="button"
          className="finna-back-btn"
          onClick={handleBack}
          aria-label="Go back to previous page"
        >
          <span aria-hidden="true">←</span>
          <span>Back</span>
        </button>

        <nav aria-label="Breadcrumb" className="finna-crumbs">
          {crumbs.map((crumb, idx) => {
            const isLast = idx === crumbs.length - 1
            return (
              <span key={`${crumb.label}-${idx}`} className="finna-crumb-item">
                {idx > 0 && <span className="finna-crumb-sep" aria-hidden="true">›</span>}
                {crumb.to && !isLast ? (
                  <Link to={crumb.to} className="finna-crumb-link">
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="finna-crumb-current" aria-current={isLast ? 'page' : undefined}>
                    {crumb.label}
                  </span>
                )}
              </span>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
