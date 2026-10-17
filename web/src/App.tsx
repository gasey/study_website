import { Navigate, Route, Routes } from 'react-router-dom'
import Header from './components/Header'
import Bank from './screens/Bank'
import QuestionDetail from './screens/QuestionDetail'

function Placeholder({ title }: { title: string }) {
  return (
    <div className="mx-auto max-w-shell px-6 py-16">
      <h1 className="font-display text-[32px] font-semibold">{title}</h1>
      <p className="mt-2 text-muted">Not built yet — see docs/PLAN.md.</p>
    </div>
  )
}

export default function App() {
  return (
    <>
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<Navigate to="/bank" replace />} />
          <Route path="/bank" element={<Bank />} />
          <Route path="/bank/:id" element={<QuestionDetail />} />
          <Route path="/exams" element={<Placeholder title="Exams & tools" />} />
          <Route path="/feed" element={<Placeholder title="Community" />} />
          <Route path="*" element={<Placeholder title="Not found" />} />
        </Routes>
      </main>
    </>
  )
}
