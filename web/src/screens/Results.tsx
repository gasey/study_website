import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import MockResultView from '../components/MockResultView'
import { getMockResult, type MockResult } from '../lib/api'

/** A finished paper, revisited. The prototype's `results` screen (1582).
 *  Everything needed is already in mock_sessions + attempts, so this is a
 *  read — nothing is recomputed and nothing is stored twice. */
export default function Results() {
  const { mockId = '' } = useParams()
  const [result, setResult] = useState<MockResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setResult(null)
    setError(null)
    getMockResult(mockId).then(setResult).catch((e) => setError(e.message))
  }, [mockId])

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-12">
        <div className="rounded-[14px] border border-mypick bg-mypick-soft p-5 text-mypick">
          <span className="font-mono text-[11px] uppercase tracking-[0.06em]">Error</span>
          <p className="mt-1">{error}</p>
        </div>
        <Link to="/exams" className="label mt-4 inline-block underline">← Exams</Link>
      </div>
    )
  }
  if (!result) return <div className="mx-auto max-w-shell px-6 py-12 label">Loading…</div>
  return <MockResultView result={result} backTo="/exams" backLabel="← Exams" />
}
