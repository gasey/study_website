import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getCollection, listCollections, type CollectionDetail } from '../lib/api'

/** "Exams & tools", ported from markup line 526. The prototype hard-codes
 *  MPSC Combined Prelims as the flagship; we show whichever collection is
 *  first by position, which today is the only one that exists. */
export default function Exams() {
  const [flagship, setFlagship] = useState<CollectionDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    listCollections()
      .then((cs) => (cs.length ? getCollection(cs[0].id) : null))
      .then((d) => !cancelled && setFlagship(d))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [])

  const general = flagship?.section_list.filter((s) => s.path.startsWith('general/')) ?? []
  const technical = flagship?.section_list.filter((s) => s.path.startsWith('technical/')) ?? []

  return (
    <div className="mx-auto max-w-shell px-6 pb-24 pt-9">
      <div className="font-mono text-[11px] uppercase tracking-[0.1em] text-exams-dark">Library</div>
      <h1 className="mt-2 font-display text-[clamp(36px,5vw,52px)] font-medium -tracking-[0.02em]">
        Exams &amp; tools
      </h1>
      <p className="mt-3 max-w-[720px] text-[17px] leading-relaxed text-secondary [text-wrap:pretty]">
        Each exam page takes the right questions from the bank for one exam or subject and puts
        them in order, with mocks around them.
      </p>

      {/* The prototype's two orientation cards: where you are, and the bank. */}
      <div className="mt-5 grid gap-3.5 [grid-template-columns:repeat(auto-fit,minmax(280px,1fr))]">
        <div className="rounded-[14px] bg-exams-soft px-5 py-[18px]">
          <div className="text-[13px] font-semibold text-exams-dark">Exams · you are here</div>
          <div className="mt-1.5 font-display text-[21px] font-medium">
            Premade, in order, finite
          </div>
          <div className="mt-1.5 text-[13.5px] leading-[1.55] text-[#4A3205]">
            Start at the top and work down; you always know what’s left.
          </div>
        </div>
        <Link
          to="/bank"
          className="block rounded-[14px] border border-hairline bg-card px-5 py-[18px] shadow-[0_1px_2px_rgba(29,27,24,.05)]"
        >
          <div className="flex items-center gap-2 text-[13px] font-semibold text-practice-dark">
            <span className="h-2 w-2 rounded-full bg-practice" />
            Question bank
          </div>
          <div className="mt-1.5 font-display text-[21px] font-medium">
            Everything, unsorted until you filter
          </div>
          <div className="mt-1.5 text-[13.5px] leading-[1.55] text-secondary">
            Every question from every paper. Search, filter and build your own sets. Open the bank →
          </div>
        </Link>
      </div>

      {loading && <p className="label mt-10">Loading…</p>}
      {error && (
        <div className="mt-6 rounded-[14px] border border-mypick bg-mypick-soft p-4 text-mypick">
          <span className="font-mono text-[11px] uppercase tracking-[0.06em]">Error</span>
          <p className="mt-1 text-[14px]">{error}</p>
        </div>
      )}

      {flagship && (
        <>
          {/* Flagship panel: near-black with a stats rail, markup line 540. */}
          <section className="mt-7 flex flex-wrap overflow-hidden rounded-[14px] bg-[#14130F] text-paper">
            <div className="min-w-0 flex-[3_1_460px] px-8 py-[30px]">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-pill bg-practice px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.08em] text-white">
                  Start here
                </span>
                <span className="font-mono text-[11px] text-[#BDB3A0]">
                  Mizoram PSC · official answer keys only
                </span>
              </div>
              <h2 className="mt-3.5 font-display text-[clamp(34px,4.6vw,52px)] font-medium leading-[1.05] -tracking-[0.02em]">
                {flagship.title}
              </h2>
              <p className="mt-3 max-w-[560px] text-[16px] leading-relaxed text-[#D9D0BF]">
                Past papers with official keys, grouped by paper and trade. Every question here has
                a published answer — nothing in this exam is scored against a guess.
              </p>
              <div className="mt-4 flex flex-wrap gap-1.5">
                {flagship.section_list.slice(0, 6).map((s) => (
                  <span
                    key={s.path}
                    className="rounded-pill border border-[#5A544A] px-2.5 py-1 text-[12.5px] text-canvas"
                  >
                    {s.title}
                  </span>
                ))}
              </div>
              <div className="mt-[22px] flex flex-wrap gap-2.5">
                <Link
                  to={`/exams/${flagship.id}`}
                  className="rounded-pill bg-paper px-[22px] py-3 text-[15px] font-semibold text-ink"
                >
                  Open the exam
                </Link>
                <Link
                  to="/bank"
                  className="rounded-pill border border-paper px-[21px] py-[11px] text-[15px] font-semibold text-paper"
                >
                  Browse the bank instead
                </Link>
              </div>
            </div>
            <div className="grid flex-[1_1_260px] content-center gap-[18px] bg-[#2A2723] px-7 py-[26px] [grid-template-columns:1fr_1fr]">
              {[
                { v: flagship.scorable.toLocaleString('en-IN'), k: 'keyed questions', c: 'text-paper' },
                { v: String(flagship.sections), k: 'sections', c: 'text-paper' },
                { v: String(technical.length), k: 'trades', c: 'text-paper' },
                { v: '2026', k: 'exam year', c: 'text-paper' },
              ].map((s) => (
                <div key={s.k}>
                  <div className={`font-display text-[34px] leading-none ${s.c}`}>{s.v}</div>
                  <div className="mt-1 text-[12.5px] text-[#BDB3A0]">{s.k}</div>
                </div>
              ))}
            </div>
          </section>

          <SectionGroup
            title="General papers"
            desc="Taken by every candidate"
            items={general}
            examId={flagship.id}
          />
          <SectionGroup
            title="By trade"
            desc="Technical Paper-I and II"
            items={technical}
            examId={flagship.id}
          />
        </>
      )}
    </div>
  )
}

function SectionGroup({
  title,
  desc,
  items,
  examId,
}: {
  title: string
  desc: string
  items: { path: string; title: string; papers: number; scorable: number }[]
  examId: string
}) {
  if (!items.length) return null
  return (
    <section className="mt-10">
      <div className="flex flex-wrap items-baseline justify-between gap-2.5 pb-1">
        <h2 className="font-display text-[30px] font-medium">{title}</h2>
        <span className="text-[14px] text-secondary">{desc}</span>
      </div>
      <div className="mt-3.5 grid gap-3 [grid-template-columns:repeat(auto-fill,minmax(260px,1fr))]">
        {items.map((s) => (
          <Link
            key={s.path}
            to={`/exams/${examId}/${s.path}`}
            className="flex flex-col gap-2 rounded-[14px] border border-hairline bg-card p-5 shadow-[0_1px_2px_rgba(29,27,24,.05)] transition-shadow hover:shadow-[0_8px_24px_rgba(29,27,24,.12)]"
          >
            <span className="flex items-center gap-2 text-[12.5px] font-semibold">
              <span className="h-2 w-2 rounded-full bg-exams" />
              {s.papers} paper{s.papers === 1 ? '' : 's'}
            </span>
            <div className="font-display text-[21px] font-medium leading-tight">{s.title}</div>
            <div className="flex-1 text-[14px] leading-[1.55] text-[#2E2A24]">
              {s.scorable.toLocaleString('en-IN')} questions with an official key.
            </div>
            <span className="text-[12px] font-semibold">Open →</span>
          </Link>
        ))}
      </div>
    </section>
  )
}
