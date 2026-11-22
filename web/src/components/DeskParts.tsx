import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import type { DeskOverview } from '../lib/studyDesks'

export const DESK_BTN = 'desk-v3-button'
export const DESK_INPUT = 'desk-v3-input'

export function DeskModal({
  title,
  onClose,
  children,
}: {
  title: string
  onClose: () => void
  children: React.ReactNode
}) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    ref.current?.showModal()
    return () => ref.current?.close()
  }, [])
  return (
    <dialog
      ref={ref}
      onCancel={(e) => {
        e.preventDefault()
        onClose()
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      aria-label={title}
      className="max-h-[90vh] w-[min(680px,calc(100%-32px))] overflow-y-auto rounded-[14px] border border-hairline bg-paper p-6 text-ink backdrop:bg-ink/50"
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <h2 className="font-display text-2xl">{title}</h2>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close dialog"
          className={DESK_BTN}
        >
          Close
        </button>
      </div>
      {children}
    </dialog>
  )
}

export function DeskEmpty({ children }: { children: React.ReactNode }) {
  return <div className="desk-v3-empty">{children}</div>
}

export function DeskRecentQuestions({
  questions,
  recentIds,
}: {
  questions: DeskOverview['questions']
  recentIds: string[]
}) {
  const recent = questions.filter((q) => recentIds.includes(q.id)).slice(0, 4)
  if (!recent.length) return null
  return (
    <section>
      <h3 className="desk-v3-label border-b border-hairline pb-2">
        Pick up where you left off
      </h3>
      {recent.map((q) => (
        <Link
          key={q.id}
          to={'/bank/' + q.id}
          className="mt-2 block border-b border-hairline pb-2 text-sm text-link hover:underline"
        >
          {q.question}
        </Link>
      ))}
    </section>
  )
}
