import {learnerExplanation} from '../lib/answerStatus'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getHome, submitAnswer, type AnswerResult, type HomeData } from '../lib/api'
import { STUDY_THEMES, useStudyTheme } from '../lib/theme'

const AREAS = [
  ['Practice', '#2D5BD0'], ['Learn', '#7B45B8'], ['Map', '#0E8287'],
  ['Community', '#B23A9A'], ['Exams', '#B26B00'], ['Rewards', '#8A8A12'],
] as const

const COMMUNITY = [
  {color:'#B23A9A',softClass:'bg-community-soft',inkClass:'text-community-dark',title:'Questions & doubts',body:'Discuss the questions you are working through and learn from other explanations.',to:'/community?tab=questions'},
  {color:'#2D5BD0',softClass:'bg-practice-soft',inkClass:'text-practice-dark',title:'Website question bank',body:'Practise reviewed learner contributions, kept separate from the MPSC paper bank.',to:'/website-bank'},
  {color:'#B26B00',softClass:'bg-exams-soft',inkClass:'text-exams-dark',title:'Important Days',body:'Connect verified dates and annual themes to relevant practice questions.',to:'/important-days'},
  {color:'#7B45B8',softClass:'bg-learn-soft',inkClass:'text-learn-dark',title:'Notes & lessons',body:'Read shared study materials and save useful resources for later.',to:'/library?library_view=reading'},
]

export default function Home() {
  const [theme, , cycleTheme] = useStudyTheme()
  const activeTheme = STUDY_THEMES.find((t) => t.id === theme) || STUDY_THEMES[0]
  const [data, setData] = useState<HomeData | null>(null)
  const [loadError, setLoadError] = useState(false)
  const [pick, setPick] = useState<number | null>(null)
  const [answer, setAnswer] = useState<AnswerResult | null>(null)
  const [answerError, setAnswerError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const exam = useMemo(() => data?.collections.find((c) => c.kind === 'exam'), [data])

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
    <div className="min-h-screen bg-paper"><a href="#landing-content" className="sr-only focus:not-sr-only focus:absolute focus:z-[80] focus:rounded-lg focus:bg-paper focus:p-3 focus:text-ink">Skip to content</a>
      <header
        className="relative overflow-hidden bg-[#12131A] text-[#F5F0E6]"
        style={{
          backgroundImage:
            'radial-gradient(ellipse 70% 55% at 80% 20%, rgba(37, 87, 214, 0.24), transparent), radial-gradient(ellipse 50% 45% at 15% 85%, rgba(184, 107, 0, 0.14), transparent)',
        }}
      >
        <div className="mx-auto flex max-w-shell flex-wrap items-center justify-between gap-3 px-6 py-4">
          <Link to="/" className="group flex items-center gap-2.5 font-display text-[22px] font-semibold -tracking-[0.01em] text-white">
            <span className="grid grid-cols-3 gap-[2px] transition-transform duration-200 group-hover:scale-110" aria-hidden="true">{AREAS.map(([name, color]) => <span key={name} className="h-[7px] w-[7px] rounded-[2px]" style={{ backgroundColor: color }} />)}</span>
            India Study Map
          </Link>
          <nav aria-label="Main navigation" className="flex flex-wrap items-center gap-1 sm:gap-2">
            <button
              type="button"
              onClick={cycleTheme}
              aria-label={`Study theme: ${activeTheme.label}. Activate to switch theme.`}
              title={`Theme: ${activeTheme.label} — tap to switch`}
              className="ism-tactile-btn inline-flex min-h-11 items-center gap-1.5 rounded-pill border border-white/15 bg-white/5 px-3 text-[12px] text-[#E6DFD2] hover:bg-white/15"
            >
              <span aria-hidden="true">{activeTheme.icon}</span>
              <span className="font-mono text-[11px] uppercase tracking-wider">{activeTheme.shortLabel}</span>
            </button>
            <Link to="/exams" className="inline-flex min-h-11 items-center rounded-pill px-3 text-[13px] text-[#F5F0E6] transition-colors hover:bg-white/10">Exams</Link>
            <Link to="/library" className="inline-flex min-h-11 items-center rounded-pill px-3 text-[13px] text-[#F5F0E6] transition-colors hover:bg-white/10">Library</Link>
            <Link to="/login" className="inline-flex min-h-11 items-center rounded-pill px-3 text-[13px] text-[#F5F0E6] transition-colors hover:bg-white/10">Sign in</Link>
            <Link to="/feed" className="ism-tactile-btn inline-flex min-h-11 items-center rounded-pill bg-[#F5F0E6] px-4 text-[13px] font-semibold text-[#12131A] shadow-sm hover:bg-white">Start learning →</Link>
          </nav>
        </div>
        <div className="mx-auto grid max-w-shell items-center gap-10 px-6 pb-8 pt-9 sm:pb-12 sm:pt-14 lg:grid-cols-[minmax(0,1.45fr)_minmax(340px,.9fr)] lg:gap-12 lg:pb-14">
          <div>
            <span className="inline-flex items-center gap-2 rounded-pill bg-[#2557D6] px-3.5 py-1.5 font-mono text-[10px] uppercase tracking-[0.08em] text-white shadow-sm"><span className="h-1.5 w-1.5 rounded-full bg-[#93C5FD]" aria-hidden="true" />Start here · MPSC exam prep</span>
            <h1 className="mt-5 max-w-[760px] font-display text-[clamp(38px,5.4vw,64px)] font-medium leading-[1.04] -tracking-[0.025em] text-white [text-wrap:balance]">A clearer path to your next exam.</h1>
            <p className="mt-5 max-w-[620px] text-[16px] leading-relaxed text-[#CFC7B8] sm:text-[18px]">Prepare with past papers, focused subject practice and a community that learns together. Every question keeps its source and answer labels in view.</p>
            <div className="mt-6 flex flex-wrap items-center gap-3">
              {exam ? <Link to={exam.route ?? `/exams/${exam.id}`} className="ism-tactile-btn inline-flex min-h-12 items-center rounded-pill bg-[#2557D6] px-5 py-3 text-[14px] font-semibold text-white shadow-[0_4px_14px_rgba(37,87,214,.4)] hover:brightness-110">Start with {exam.title} →</Link> : <Link to="/exams" className="ism-tactile-btn inline-flex min-h-12 items-center rounded-pill bg-[#2557D6] px-5 py-3 text-[14px] font-semibold text-white shadow-[0_4px_14px_rgba(37,87,214,.4)]">Explore exams →</Link>}
              <Link to="/library" className="ism-tactile-btn inline-flex min-h-12 items-center rounded-pill border border-white/30 bg-white/5 px-5 py-3 text-[14px] font-semibold text-white hover:bg-white/15">Explore the study library</Link>
            </div>
            {data && <div className="mt-6 flex flex-wrap gap-x-5 gap-y-2 font-mono text-[11px] text-[#CFC7B8]"><span className="inline-flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-[#34D399]" aria-hidden="true" />{data.total_questions.toLocaleString('en-IN')} questions</span><span className="inline-flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-[#FBBF24]" aria-hidden="true" />{data.scorable_questions.toLocaleString('en-IN')} ready for timed tests</span></div>}
          </div>

          <section aria-labelledby="try-question-title" className="overflow-hidden rounded-[16px] border border-white/10 bg-card text-ink shadow-[0_24px_60px_rgba(0,0,0,.4)]">
            <div className="flex justify-between gap-2 bg-practice-soft px-5 py-3 font-mono text-[10px] uppercase tracking-[0.08em] text-practice-dark"><span id="try-question-title">Try one · Practice</span><span>{question?.taxonomy_subject ?? question?.subject ?? 'From the bank'}</span></div>
            {loadError ? <div className="p-6"><p className="text-[14px] text-secondary">The sample question couldn’t load.</p><button type="button" onClick={load} className="mt-3 min-h-11 rounded-pill border border-ink px-4 py-2 text-[13px] font-semibold">Try again</button></div> : !question ? <div className="grid min-h-64 place-items-center p-6 text-center"><p className="text-[14px] text-secondary">Loading a question from the live bank…</p></div> : <div className="p-5 sm:p-6">
              <p className="font-display text-[20px] leading-[1.4] sm:text-[21px]">{question.question}</p>
              <div className="answer-options mt-4 grid gap-2" data-layout="list">
                {question.options.map((option, index) => {
                  const correctIndex = answer?.answer_index
                  const chosen = pick === index
                  const isCorrect = answer && index === correctIndex
                  const isWrong = answer && chosen && !answer.correct
                  let palette = 'border-opt-border bg-opt-bg text-ink'
                  if (isCorrect) palette = 'border-keyed bg-keyed-soft text-ink'
                  else if (isWrong) palette = 'border-mypick bg-mypick-soft text-ink'
                  else if (answer) palette = 'border-opt-border bg-opt-bg text-muted'
                  return <button key={`${index}-${option ?? 'missing'}`} type="button" disabled={submitting || !!answer || !option} onClick={() => sendAnswer(index)} data-answer-state={isCorrect ? 'correct' : isWrong ? 'wrong' : chosen ? 'selected' : 'neutral'} className={`answer-option flex min-h-11 items-center gap-3 rounded-[9px] border px-3.5 py-2.5 text-left text-[14px] disabled:cursor-default ${palette}`}><span className="w-4 shrink-0 font-mono text-[12px]">{String.fromCharCode(65 + index)}</span><span className="flex-1">{option || 'Option unavailable in the source'}</span>{isCorrect && <span className="font-mono text-[10px] font-semibold">{chosen ? 'Correct' : 'Answer'}</span>}{isWrong && <span className="font-mono text-[10px] font-semibold">Your pick</span>}{submitting && chosen && <span className="font-mono text-[10px]">Checking…</span>}</button>
                })}
              </div>
              {answerError && <p role="alert" className="mt-3 text-[13px] text-wrong-dark">{answerError}</p>}
              {answer && <div aria-live="polite" className="mt-4 rounded-panel border border-hairline bg-paper p-3.5"><p className="font-semibold text-[14px]">{answer.correct ? 'That’s right.' : 'Not quite — the keyed answer is shown above.'}</p><p className="mt-1 text-[12px] leading-relaxed text-secondary">{answer.verified ? 'This key is published or transcribed from a paper.' : 'This answer is unverified.'}{answer.explanation ? ` ${learnerExplanation(answer.explanation)}` : ''}</p></div>}
              <div className="mt-4 border-t border-hairline pt-3 font-mono text-[10px] leading-relaxed text-muted">{data?.featured_source ?? 'Question bank'} · {question.answer_source === 'official' ? 'Official key' : 'Transcribed key'} · Choosing records practice on this device</div>
              <Link to={`/bank/${question.id}`} className="mt-3 inline-flex min-h-10 items-center text-[12px] font-semibold text-link hover:underline">See question details →</Link>
            </div>}
          </section>
        </div>
        <div className="mx-auto flex max-w-shell flex-wrap gap-2 px-6 pb-6 lg:pb-7" aria-label="Study areas">{AREAS.map(([name, color]) => <span key={name} className="inline-flex items-center gap-2 rounded-pill border border-white/10 bg-white/5 px-3 py-1.5 text-[12px] text-[#E6DFD2]"><span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />{name}</span>)}</div>
      </header>

      <div id="landing-content" tabIndex={-1} className="mx-auto max-w-shell px-6 pb-16 focus:outline-none">
        <section aria-label="How it works" className="grid gap-4 pt-10 sm:grid-cols-3 sm:pt-12">
          {[
            { n: '1', area: 'Exams', color: '#B26B00', softClass: 'bg-exams-soft', inkClass: 'text-exams-dark', title: 'Pick your exam', body: 'Choose a live exam collection and work through its papers and subject sections.' },
            { n: '2', area: 'Library', color: '#2D5BD0', softClass: 'bg-practice-soft', inkClass: 'text-practice-dark', title: 'Learn by subject', body: 'Open Arithmetic, English, General Knowledge and other modules. Questions and progress stay in the subject flow.' },
            { n: '3', area: 'Community', color: '#B23A9A', softClass: 'bg-community-soft', inkClass: 'text-community-dark', title: 'Bring a doubt to the community', body: 'Discuss a question, read a shared note or contribute an explanation with its sources.' },
          ].map((step) => <article key={step.n} className={`ism-card-surface rounded-[16px] border border-hairline p-6 ${step.softClass}`}><div className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-full font-display text-[21px] text-white shadow-sm" style={{ backgroundColor: step.color }}>{step.n}</span><span className={`font-mono text-[10px] uppercase tracking-[0.08em] font-semibold ${step.inkClass}`}>{step.area}</span></div><h2 className="mt-4 font-display text-[24px] font-medium text-ink">{step.title}</h2><p className="mt-2 text-[14px] leading-relaxed text-secondary">{step.body}</p></article>)}
        </section>

        <section className="pt-14 sm:pt-16" aria-labelledby="library-title"><div className="flex flex-wrap items-baseline justify-between gap-2 pb-4"><h2 id="library-title" className="font-display text-[36px] font-medium">Study library</h2><Link to="/library" className="text-[13px] font-semibold text-link underline">All subjects and tools →</Link></div><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{[['Arithmetic & reasoning','/arithmetic','Concepts, worked methods and inline practice','bg-practice'],['English & vocabulary','/english','Grammar, papers, writing and spaced recall','bg-learn'],['General Knowledge','/library/subjects/gk-gs','Browse topics and practise past-paper questions','bg-exams'],['Interactive Atlas','/atlas','Explore geography, places and historical maps','bg-map']].map(([title,href,description,accent]) => <Link key={href} to={href} className="ism-card-surface group flex flex-col rounded-[14px] border border-hairline bg-card p-5 hover:border-practice"><span className={`mb-3 h-1.5 w-8 rounded-pill ${accent}`} aria-hidden="true" /><h3 className="font-display text-[22px] font-medium group-hover:text-link">{title}</h3><p className="mt-2 flex-1 text-[13px] text-secondary">{description}</p><span className="mt-4 inline-flex items-center gap-1 text-[13px] font-semibold text-link">Open module <span aria-hidden="true" className="transition-transform duration-150 group-hover:translate-x-1">→</span></span></Link>)}</div></section>

        <section id="exams" className="scroll-mt-6 pt-14 sm:pt-16" aria-labelledby="exams-title">
          <div className="flex flex-wrap items-baseline justify-between gap-2 pb-4"><h2 id="exams-title" className="font-display text-[36px] font-medium">Exams</h2><Link to="/exams" className="inline-flex min-h-11 items-center text-[13px] font-semibold text-link">Browse all exams →</Link></div>
          {!data && !loadError && <p className="text-[14px] text-secondary">Loading live exam collections…</p>}
          {data?.collections.filter((collection) => collection.kind === 'exam').length === 0 && <p className="rounded-[12px] border border-hairline bg-card p-5 text-[14px] text-secondary">No public exams are available right now. Explore the study library for subject practice.</p>}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{data?.collections.filter((collection) => collection.kind === 'exam').slice(0,6).map((collection, index) => {
            return <Link key={collection.id} to={collection.route ?? `/exams/${collection.id}`} className={`ism-card-surface group flex min-h-52 flex-col gap-3 rounded-[14px] border bg-card p-5 ${index === 0 ? 'border-exams' : 'border-hairline'}`}><span className="self-start rounded-pill bg-exams-soft px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.08em] text-exams-dark">Exam collection</span><span className="font-display text-[21px] font-medium leading-tight group-hover:text-exams-dark">{collection.title}</span><span className="flex-1 text-[13px] leading-relaxed text-secondary">{collection.sections} sections · built from reviewed bank questions</span><span className="inline-flex items-center gap-1 text-[13px] font-semibold text-exams-dark">Open <span aria-hidden="true" className="transition-transform duration-150 group-hover:translate-x-1">→</span></span></Link>
          })}</div>
        </section>

        <section className="flex flex-wrap items-start gap-8 pt-16" aria-labelledby="community-title">
          <div className="flex-1 basis-[270px]"><div className="font-mono text-[10px] uppercase tracking-[0.08em] text-community-dark">Community</div><h2 id="community-title" className="mt-2 font-display text-[36px] font-medium leading-tight">Better, together.</h2><p className="mt-3 max-w-[420px] text-[14px] leading-relaxed text-secondary">Share what helps you learn. Questions, useful notes and reviewed collections each have a place.</p></div>
          <div className="grid flex-[2] basis-[520px] gap-3 sm:grid-cols-2">{COMMUNITY.map((item) => <Link to={item.to} key={item.title} className={`ism-card-surface group rounded-[14px] border border-hairline p-5 ${item.softClass}`}><span className="block h-1.5 w-8 rounded-pill" style={{ backgroundColor: item.color }} /><div className="mt-2.5 flex flex-wrap items-center gap-2"><h3 className={`font-display text-[20px] font-medium ${item.inkClass}`}>{item.title}</h3></div><p className="mt-2 text-[13px] leading-relaxed text-secondary">{item.body}</p><span className="mt-3 inline-flex min-h-11 items-center gap-1 text-[13px] font-semibold text-link">Explore <span aria-hidden="true" className="transition-transform duration-150 group-hover:translate-x-1">→</span></span></Link>)}</div>
        </section>
      </div>

      <footer className="bg-[#12131A] text-[#CFC7B8]"><div className="mx-auto flex max-w-shell flex-wrap justify-between gap-3 px-6 py-[22px] font-mono text-[10px] leading-relaxed sm:text-[12px]"><span>India Study Map · Aizawl</span><span>Past MPSC questions · Clearly labelled answer sources</span></div></footer>
    </div>
  )
}
