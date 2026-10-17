import { useParams } from 'react-router-dom'

export default function QuestionDetail() {
  const { id } = useParams()
  return (
    <div className="mx-auto max-w-shell px-6 py-10">
      <div className="label">Question</div>
      <h1 className="mt-1 font-display text-[28px] font-semibold">{id}</h1>
    </div>
  )
}
