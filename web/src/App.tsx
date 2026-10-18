import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import Footer from './components/Footer'
import Header from './components/Header'
import { Card } from './components/ui'
import Bank from './screens/Bank'
import ExamPage from './screens/ExamPage'
import Exams from './screens/Exams'
import QuestionDetail from './screens/QuestionDetail'

/** Routes the shell links to but that are not built yet. Named explicitly
 *  rather than caught by `*`, so the page can say which phase owns it
 *  instead of pretending to be a 404. docs/PLAN.md has the order. */
const PLANNED: Record<string, { title: string; phase: string }> = {
  '/mistakes': { title: 'Mistakes', phase: 'Phase 2' },
  '/scoring': { title: 'How scoring works', phase: 'Phase 2' },
  '/profile': { title: 'Profile', phase: 'Phase 3' },
  '/feed': { title: 'Feed', phase: 'Phase 4' },
  '/create': { title: 'Create', phase: 'Phase 4' },
  '/desk': { title: 'Study desks', phase: 'Phase 4' },
  '/inbox': { title: 'Inbox', phase: 'Phase 4' },
  '/news': { title: 'News', phase: 'Phase 4' },
  '/calendar': { title: 'Exam calendar', phase: 'Phase 4' },
  '/games': { title: 'Games', phase: 'Phase 5' },
  '/duel': { title: 'Duel', phase: 'Phase 5' },
  '/board': { title: 'Leaderboard', phase: 'Phase 5' },
}

function Planned() {
  const { pathname } = useLocation()
  const p = PLANNED[pathname]
  return (
    <div className="mx-auto max-w-shell px-6 py-16">
      <Card className="max-w-xl p-8">
        <div className="font-mono text-[11px] uppercase tracking-[0.1em] text-muted">
          {p ? p.phase : 'Not found'}
        </div>
        <h1 className="mt-2 font-display text-[28px] font-semibold">
          {p ? p.title : 'No such page'}
        </h1>
        <p className="mt-2 text-[15px] leading-relaxed text-secondary">
          {p
            ? 'Designed, not built yet. The build order is in docs/PLAN.md.'
            : 'That route does not exist.'}
        </p>
      </Card>
    </div>
  )
}

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Navigate to="/bank" replace />} />
          <Route path="/bank" element={<Bank />} />
          <Route path="/bank/:id" element={<QuestionDetail />} />
          <Route path="/exams" element={<Exams />} />
          <Route path="/exams/:id" element={<ExamPage />} />
          <Route path="/exams/:id/*" element={<Planned />} />
          {Object.keys(PLANNED).map((path) => (
            <Route key={path} path={path} element={<Planned />} />
          ))}
          <Route path="*" element={<Planned />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
