import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { getHome, submitAnswer, type AnswerResult, type HomeData } from '../lib/api'

const AREAS = [
  ['Practice', '#2D5BD0'], ['Learn', '#7B45B8'], ['Map', '#0E8287'],
  ['Community', '#B23A9A'], ['Exams', '#B26B00'], ['Rewards', '#8A8A12'],
] as const

const COMMUNITY = [
  { color: '#B23A9A', bg: '#F5E1F0', ink: '#86226F', title: 'Questions and doubts', body: 'Ask about a confusing question or share an MCQ. Community posting is coming soon.' },
  { color: '#2D5BD0', bg: '#E3E9F8', ink: '#1F44A6', title: 'Challenges', body: 'Topic duels, speed rounds, and a weekly cup built around the question bank.', soon: true },
  { color: '#8A8A12', bg: '#ECEDCF', ink: '#545A06', title: 'Leaderboard', body: 'A fair view of study activity and contributions, with clear weekly resets.', soon: true },
  { color: '#7B45B8', bg: '#EEE6F7', ink: '#5E2F98', title: 'Study materials', body: 'Learner-made notes and revision resources, with source and review details.', soon: true },
]

export default function Home() {
  const [libraryOpen, setLibraryOpen] = useState(false)
  const libraryNavRef = useRef<HTMLDivElement>(null)
  const [data, setData] = useState<HomeData | null>(null)
  const [loadError, setLoadError] = useState(false)
  const [pick, setPick] = useState<number | null>(null)
  const [answer, setAnswer] = useState<AnswerResult | null>(null)
  const [answerError, setAnswerError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const exam = useMemo(() => data?.collections.find((c) => c.kind === 'exam'), [data])
  useEffect(() => {
    if (!libraryOpen) return
    const dismiss = (event: MouseEvent) => { if (!libraryNavRef.current?.contains(event.target as Node)) setLibraryOpen(false) }
    const escape = (event: KeyboardEvent) => { if (event.key === 'Escape') setLibraryOpen(false) }
    document.addEventListener('mousedown', dismiss)
    document.addEventListener('keydown', escape)
    return () => { document.removeEventListener('mousedown', dismiss); document.removeEventListener('keydown', escape) }
  }, [libraryOpen])

  const load = () => {
    setLoadError(false)
    getHome().then((result) => setData(result)).catch(() => setLoadError(true))
  }
  useEffect(load, [])

  const question = data?.featured_question
  const sendAnswer = async (index: number) => {
    if (!question || submitting || answer) return
    setPick(index)
    setSubmitting(true)
    setAnswerError('')
    try {
      setAnswer(await submitAnswer(question.id, index, 'practice'))
    } catch {
      setAnswerError('Could not check that answer right now. Try again.')
      setPick(null)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-paper">
      <header className="bg-[#14130F] text-paper">
        <div className="mx-auto flex max-w-shell flex-wrap items-center justify-between gap-3 px-6 py-4">
          <Link to="/" className="flex items-center gap-2.5 font-display text-[22px] font-semibold -tracking-[0.01em] text-white">
            <span className="grid grid-cols-3 gap-[2px]" aria-hidden="true">{AREAS.map(([name, color]) => <span key={name} className="h-[7px] w-[7px] rounded-[2px]" style={{ backgroundColor: color }} />)}</span>
            India Study Map
          </Link>
          <nav aria-label="Main navigation" className="flex items-center gap-2">
            <Link to="/plans" className="hidden min-h-11 rounded-pill px-3 py-2.5 text-[13px] font-medium text-[#F4EFE4] sm:inline-flex">Plans</Link>
            <Link to="/login" className="min-h-11 rounded-pill px-3 py-2.5 text-[13px] font-medium text-[#F4EFE4] hover:bg-white/10">Log in</Link>
            <Link to="/join" className="min-h-11 rounded-pill border border-paper/70 px-3 py-2.5 text-[13px] font-semibold text-paper hover:bg-white/10">Join free</Link>
            <Link to="/feed" className="min-h-11 rounded-pill px-3 py-2.5 text-[13px] font-medium text-[#F4EFE4] hover:bg-white/10">Community</Link>
            <Link to="/desk" className="min-h-11 rounded-pill px-3 py-2.5 text-[13px] font-medium text-[#F4EFE4] hover:bg-white/10">Study desk</Link>
            <Link to="/exams" className="min-h-11 rounded-pill px-3 py-2.5 text-[13px] font-medium text-[#F4EFE4] hover:bg-white/10">Exams</Link>
            <div ref={libraryNavRef} className="relative">
              <button type="button" onClick={() => setLibraryOpen((open) => !open)} aria-expanded={libraryOpen} aria-controls="home-library-nav" className="min-h-11 rounded-pill bg-paper px-4 py-2.5 text-[13px] font-semibold text-ink hover:bg-white">Study library ▾</button>
              {libraryOpen && <div id="home-library-nav" className="absolute right-0 top-full z-50 mt-2 w-[290px] max-h-[min(70vh,520px)] overflow-y-auto rounded-[12px] border border-hairline bg-card p-2 text-ink shadow-[0_18px_40px_rgba(0,0,0,.25)]">
                {[['All subjects & tools', '/library'], ['Interactive Atlas', '/atlas'], ['Arithmetic', '/arithmetic'], ['Reasoning', '/arithmetic?subject=reasoning-and-aptitude&view=practice'], ['General Knowledge', '/library/subjects/general-knowledge'], ['Mizo', '/mizo'], ['English', '/english'], ['Vocabulary helper', '/vocabulary'], ['Essay writing', '/essay']].map(([label, href]) => <Link key={href} to={href} onClick={() => setLibraryOpen(false)} className="block rounded-[8px] px-3 py-2.5 font-display text-[17px] hover:bg-paper focus-visible:bg-paper focus-visible:outline focus-visible:outline-2 focus-visible:outline-link">{label}</Link>)}
              </div>}
            </div>
          </nav>
        </div>
        <div className="mx-auto grid max-w-shell items-center gap-10 px-6 pb-8 pt-9 sm:pb-12 sm:pt-14 lg:grid-cols-[minmax(0,1.45fr)_minmax(340px,.9fr)] lg:gap-12 lg:pb-14">
          <div>
            <span className="inline-flex rounded-pill bg-practice px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.08em] text-white">Start here · MPSC exam prep</span>
            <h1 className="mt-5 max-w-[760px] font-display text-[clamp(38px,5.4vw,64px)] font-medium leading-[1.04] -tracking-[0.025em] text-white [text-wrap:balance]">Practise every MPSC paper, then talk it through with the people sitting it with you.</h1>
            <p className="mt-5 max-w-[620px] text-[16px] leading-relaxed text-[#CFC7B8] sm:text-[18px]">Past-paper questions from UDC, LDC, Assistant Grade, Combined Prelims, and technical posts. Answers show where the key came from, so you know what you can trust.</p>
            <div className="mt-6 flex flex-wrap items-center gap-3">
              {exam ? <Link to={exam.route ?? `/exams/${exam.id}`} className="inline-flex min-h-12 items-center rounded-pill bg-practice px-5 py-3 text-[14px] font-semibold text-white hover:brightness-110">Start with {exam.title} →</Link> : <Link to="/exams" className="inline-flex min-h-12 items-center rounded-pill bg-practice px-5 py-3 text-[14px] font-semibold text-white">Explore exams →</Link>}
              <Link to="/library" className="inline-flex min-h-12 items-center rounded-pill border border-paper/70 px-5 py-3 text-[14px] font-semibold text-paper hover:bg-white/10">Explore the study library</Link>
              <a href="#exams" className="inline-flex min-h-11 items-center px-2 py-2 text-[14px] font-semibold text-paper">All exams ↓</a>
            </div>
            {data && <div className="mt-6 flex flex-wrap gap-x-5 gap-y-2 font-mono text-[11px] text-[#CFC7B8]"><span>{data.total_questions.toLocaleString('en-IN')} questions</span><span>{data.scorable_questions.toLocaleString('en-IN')} scorable for timed mocks</span></div>}
          </div>

          <section aria-labelledby="try-question-title" className="overflow-hidden rounded-[14px] bg-card text-ink shadow-[0_24px_60px_rgba(0,0,0,.35)]">
            <div className="flex justify-between gap-2 bg-practice-soft px-5 py-3 font-mono text-[10px] uppercase tracking-[0.08em] text-practice-dark"><span id="try-question-title">Try one · Practice</span><span>{question?.taxonomy_subject ?? question?.subject ?? 'From the bank'}</span></div>
            {loadError ? <div className="p-6"><p className="text-[14px] text-secondary">The sample question couldn’t load.</p><button type="button" onClick={load} className="mt-3 min-h-11 rounded-pill border border-ink px-4 py-2 text-[13px] font-semibold">Try again</button></div> : !question ? <div className="grid min-h-64 place-items-center p-6 text-center"><p className="text-[14px] text-secondary">Loading a question from the live bank…</p></div> : <div className="p-5 sm:p-6">
              <p className="font-display text-[20px] leading-[1.4] sm:text-[21px]">{question.question}</p>
              <div className="mt-4 grid gap-2">
                {question.options.map((option, index) => {
                  const correctIndex = answer?.answer_index
                  const chosen = pick === index
                  let palette = 'border-[#DCD3C2] bg-[#FBF8F1] text-ink hover:border-ink'
                  if (answer && index === correctIndex) palette = 'border-keyed bg-keyed-soft text-ink'
                  else if (answer && chosen && !answer.correct) palette = 'border-mypick bg-mypick-soft text-ink'
                  else if (answer) palette = 'border-[#DCD3C2] bg-[#FBF8F1] text-muted'
                  return <button key={`${index}-${option ?? 'missing'}`} type="button" disabled={submitting || !!answer || !option} onClick={() => sendAnswer(index)} className={`flex min-h-11 items-center gap-3 rounded-[8px] border px-3.5 py-2.5 text-left text-[14px] disabled:cursor-default ${palette}`}><span className="w-4 shrink-0 font-mono text-[12px]">{String.fromCharCode(65 + index)}</span><span className="flex-1">{option || 'Option unavailable in the source'}</span>{answer && index === correctIndex && <span className="font-mono text-[10px]">{chosen ? 'Correct' : 'Answer'}</span>}{answer && chosen && !answer.correct && <span className="font-mono text-[10px]">Your pick</span>}{submitting && chosen && <span className="font-mono text-[10px]">Checking…</span>}</button>
                })}
              </div>
              {answerError && <p role="alert" className="mt-3 text-[13px] text-wrong-dark">{answerError}</p>}
              {answer && <div aria-live="polite" className="mt-4 rounded-panel bg-paper p-3.5"><p className="font-semibold text-[14px]">{answer.correct ? 'That’s right.' : 'Not quite — the keyed answer is shown above.'}</p><p className="mt-1 text-[12px] leading-relaxed text-secondary">{answer.verified ? 'This key is published or transcribed from a paper.' : 'This answer is unverified.'}{answer.explanation ? ` ${answer.explanation}` : ''}</p></div>}
              <div className="mt-4 border-t border-hairline pt-3 font-mono text-[10px] leading-relaxed text-muted">{data?.featured_source ?? 'Question bank'} · {question.answer_source === 'official' ? 'Official key' : 'Transcribed key'} · Choosing records practice on this device</div>
              <Link to={`/bank/${question.id}`} className="mt-3 inline-flex min-h-10 items-center text-[12px] font-semibold text-link">See question details →</Link>
            </div>}
          </section>
        </div>
        <div className="mx-auto flex max-w-shell flex-wrap gap-2 px-6 pb-6 lg:pb-7" aria-label="Study areas">{AREAS.map(([name, color]) => <span key={name} className="inline-flex items-center gap-2 rounded-pill bg-[#25231E] px-3 py-1.5 text-[12px] text-[#E6DFD2]"><span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />{name}</span>)}</div>
      </header>

      <main className="mx-auto max-w-shell px-6 pb-16">
        <section aria-label="How it works" className="grid gap-4 pt-10 sm:grid-cols-3 sm:pt-12">
          {[
            { n: '1', area: 'Exams', color: '#B26B00', ink: '#7E4A00', bg: '#F7EAD0', title: 'Pick your exam', body: 'Choose a live exam collection and work through its papers and subject sections.' },
            { n: '2', area: 'Library', color: '#2D5BD0', ink: '#1F44A6', bg: '#E3E9F8', title: 'Learn by subject', body: 'Open Arithmetic, English, General Knowledge and other modules. Questions and progress stay in the subject flow.' },
            { n: '3', area: 'Community', color: '#B23A9A', ink: '#86226F', bg: '#F5E1F0', title: 'Bring a doubt to the community', body: 'Community features are being built. Your practice and study desk work now without an account.' },
          ].map((step) => <article key={step.n} className="rounded-[14px] p-6" style={{ backgroundColor: step.bg }}><div className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-full font-display text-[21px] text-white" style={{ backgroundColor: step.color }}>{step.n}</span><span className="font-mono text-[10px] uppercase tracking-[0.08em]" style={{ color: step.ink }}>{step.area}</span></div><h2 className="mt-4 font-display text-[24px] font-medium">{step.title}</h2><p className="mt-2 text-[14px] leading-relaxed text-[#2E2A24]">{step.body}</p></article>)}
        </section>

        <section className="pt-14 sm:pt-16" aria-labelledby="library-title"><div className="flex flex-wrap items-baseline justify-between gap-2 pb-4"><h2 id="library-title" className="font-display text-[36px] font-medium">Study library</h2><Link to="/library" className="text-[13px] font-semibold text-link underline">All subjects and tools →</Link></div><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{[['Arithmetic & reasoning','/arithmetic','Concepts, worked methods and inline practice'],['English & vocabulary','/english','Grammar, papers, writing and spaced recall'],['General Knowledge','/library/subjects/general-knowledge','Browse topics and practise past-paper questions'],['Interactive Atlas','/atlas','Explore geography, places and historical maps']].map(([title,href,description]) => <Link key={href} to={href} className="rounded-[12px] border border-hairline bg-card p-5 transition hover:border-ink"><h3 className="font-display text-[22px] font-medium">{title}</h3><p className="mt-2 text-[13px] text-secondary">{description}</p><span className="mt-4 inline-block text-[13px] font-semibold text-link">Open module →</span></Link>)}</div></section>

        <section id="exams" className="scroll-mt-6 pt-14 sm:pt-16" aria-labelledby="exams-title">
          <div className="flex flex-wrap items-baseline justify-between gap-2 pb-4"><h2 id="exams-title" className="font-display text-[36px] font-medium">Exams</h2><p className="text-[13px] text-secondary">Live collections and question counts from the bank.</p></div>
          {!data && !loadError && <p className="text-[14px] text-secondary">Loading live exam collections…</p>}
          {data?.collections.filter((collection) => collection.kind === 'exam').length === 0 && <p className="rounded-[12px] border border-hairline bg-card p-5 text-[14px] text-secondary">No public exams are available right now. Explore the study library for subject practice.</p>}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{data?.collections.filter((collection) => collection.kind === 'exam').map((collection, index) => {
            return <Link key={collection.id} to={collection.route ?? `/exams/${collection.id}`} className="flex min-h-52 flex-col gap-3 rounded-[12px] border bg-card p-5 shadow-[0_1px_2px_rgba(29,27,24,.06)] transition hover:-translate-y-0.5 hover:shadow-[0_8px_24px_rgba(29,27,24,.12)]" style={{ borderColor: index === 0 ? '#B26B00' : '#E4DBC9' }}><span className="self-start rounded-pill bg-exams-soft px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.08em] text-exams-dark">Exam collection</span><span className="font-display text-[21px] font-medium leading-tight">{collection.title}</span><span className="flex-1 text-[13px] leading-relaxed text-secondary">{collection.sections} sections · built from reviewed bank questions</span><span className="text-[13px] font-semibold text-exams-dark">Open →</span></Link>
          })}</div>
        </section>

        <section className="flex flex-wrap items-start gap-8 pt-16" aria-labelledby="community-title">
          <div className="flex-1 basis-[270px]"><div className="font-mono text-[10px] uppercase tracking-[0.08em] text-community-dark">Community</div><h2 id="community-title" className="mt-2 font-display text-[36px] font-medium leading-tight">Then the community.</h2><p className="mt-3 max-w-[420px] text-[14px] leading-relaxed text-secondary">Practice comes first. Community tools are planned for sharing questions, tackling challenges, and learning together.</p></div>
          <div className="grid flex-[2] basis-[520px] gap-3 sm:grid-cols-2">{COMMUNITY.map((item) => <article key={item.title} className="rounded-[12px] p-5" style={{ backgroundColor: item.bg }}><span className="block h-1 w-7 rounded-sm" style={{ backgroundColor: item.color }} /><div className="mt-2 flex flex-wrap items-center gap-2"><h3 className="font-display text-[20px] font-medium" style={{ color: item.ink }}>{item.title}</h3><span className="rounded-pill bg-white/70 px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.06em] text-secondary">{item.soon ? 'Planned' : 'In progress'}</span></div><p className="mt-2 text-[13px] leading-relaxed text-[#2E2A24]">{item.body}</p></article>)}</div>
        </section>
      </main>

      <footer className="bg-[#14130F] text-[#CFC7B8]"><div className="mx-auto flex max-w-shell flex-wrap justify-between gap-3 px-6 py-[22px] font-mono text-[10px] leading-relaxed sm:text-[12px]"><span>India Study Map · Aizawl</span><span>Questions sourced from MPSC papers · Answers labelled by provenance</span></div></footer>
    </div>
  )
}
