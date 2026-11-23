import VocabularyCardRead from './VocabularyCardRead'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { type ContentBlock } from '../lib/materials'
import { getQuestion, type Question } from '../lib/api'
import QuestionCard from './QuestionCard'
import { SourceQuestionText } from './SourceQuestionText'

function BankQuestion({ id, interactive }: { id: string; interactive: boolean }) {
  const [question, setQuestion] = useState<Question | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let live = true
    if (interactive) {
      getQuestion(id)
        .then(q => {
          if (live) setQuestion(q)
        })
        .catch(e => {
          if (live) setError(e.message)
        })
    }
    return () => {
      live = false
    }
  }, [id, interactive])
  return (
    <section className="mt-block-question">
      <div className="mt-block-eyebrow">Practise a past-paper question</div>
      {!interactive ? (
        <p className="text-sm">Bank question: {id || 'Choose an ID in the editor'}</p>
      ) : error ? (
        <p className="text-sm">{error}</p>
      ) : question ? (
        <QuestionCard q={question} />
      ) : (
        <p className="text-sm">Loading question…</p>
      )}
      {id && (
        <Link to={'/bank/' + encodeURIComponent(id)} className="mt-inline-link">
          Open question source →
        </Link>
      )}
    </section>
  )
}

function safeLink(value?: string) {
  try {
    const url = new URL(value || '')
    return url.protocol === 'https:' && !url.username && !url.password ? url.href : null
  } catch {
    return null
  }
}

export default function MaterialBody({
  blocks,
  interactive = true,
}: {
  blocks: ContentBlock[]
  interactive?: boolean
}) {
  return (
    <div className="mt-body">
      {blocks.map((b, i) => {
        const url = safeLink(b.url)
        return (
          <div key={b.id || i} className="min-w-0 break-words">
            {b.type === 'heading' ? (
              <h2 className="mt-body-h2">
                <SourceQuestionText text={b.text || 'Section heading'} />
              </h2>
            ) : b.type === 'paragraph' ? (
              <p className="mt-body-p">
                <SourceQuestionText text={b.text || ''} />
              </p>
            ) : b.type === 'quote' ? (
              <blockquote className="mt-body-quote">
                <SourceQuestionText text={b.text || ''} />
              </blockquote>
            ) : b.type === 'callout' ? (
              <aside className="mt-body-callout">
                <SourceQuestionText text={b.text || ''} />
              </aside>
            ) : b.type === 'list' ? (
              <ul className="mt-body-list">
                {b.items?.map((s, j) => (
                  <li key={j}>
                    <SourceQuestionText text={s} />
                  </li>
                ))}
              </ul>
            ) : b.type === 'table' ? (
              <div className="mt-body-table-wrap">
                <table className="mt-body-table">
                  <tbody>
                    {b.rows?.map((row, r) => (
                      <tr key={r} className={r === 0 ? 'is-head' : ''}>
                        {row.map((cell, c) =>
                          r === 0 ? (
                            <th scope="col" key={c}>
                              <SourceQuestionText text={cell} />
                            </th>
                          ) : (
                            <td key={c}>
                              <SourceQuestionText text={cell} />
                            </td>
                          ),
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : b.type === 'image' ? (
              url ? (
                <figure className="mt-body-fig">
                  <img
                    src={url}
                    alt={b.alt || ''}
                    referrerPolicy="no-referrer"
                    loading="lazy"
                    className="mt-body-img"
                  />
                  {b.text && <figcaption className="mt-body-cap">{b.text}</figcaption>}
                </figure>
              ) : (
                <p className="text-sm text-muted">Add an HTTPS image URL.</p>
              )
            ) : b.type === 'link' ? (
              url ? (
                <a href={url} target="_blank" rel="noreferrer" className="mt-inline-link">
                  {b.text || url} ↗
                </a>
              ) : (
                <p className="text-sm text-muted">Add an HTTPS reference link.</p>
              )
            ) : b.type === 'vocabulary' ? (
              b.vocabulary ? (
                <VocabularyCardRead card={b.vocabulary} />
              ) : (
                <p className="text-sm text-muted">Vocabulary card not entered.</p>
              )
            ) : b.type === 'question' ? (
              <BankQuestion id={b.question_id || ''} interactive={interactive} />
            ) : (
              <p className="text-xs text-muted">This older block format is unavailable in this reader.</p>
            )}
          </div>
        )
      })}
    </div>
  )
}
