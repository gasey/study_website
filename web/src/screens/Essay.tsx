import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getAccountSession, getEssayDraft, listQuestions, saveEssayDraft, type Question, type QuestionPage } from '../lib/api'
import { SourceQuestionText } from '../components/SourceQuestionText'

const PAGE = 10
const browserDraftKey = (id: string) => `ism-essay-draft:${id}`

export default function Essay() {
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const [page, setPage] = useState<QuestionPage | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState<Question | null>(null)
  const [draft, setDraft] = useState('')
  const [draftLoading, setDraftLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [dirty, setDirty] = useState(false)
  const [saveMessage, setSaveMessage] = useState('')
  const [signedIn, setSignedIn] = useState(false)
  const [sessionLoading, setSessionLoading] = useState(true)

  useEffect(() => {
    getAccountSession().then((session) => setSignedIn(session.authenticated))
      .catch(() => setSignedIn(false)).finally(() => setSessionLoading(false))
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => { setSearch(query.trim()); setOffset(0) }, 250)
    return () => window.clearTimeout(timer)
  }, [query])
  useEffect(() => {
    let live = true
    setLoading(true); setError('')
    listQuestions({ essay_kind: 'essay', pool: 'all', q: search.length >= 2 ? search : undefined, limit: PAGE, offset })
      .then((result) => { if (live) setPage(result) })
      .catch((e) => { if (live) setError(e.message || 'Essay prompts could not be loaded.') })
      .finally(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [search, offset])
  useEffect(() => {
    if (!selected || sessionLoading) return
    let live = true
    setDraft(''); setDirty(false); setSaveMessage(''); setDraftLoading(true)
    const browserDraft = window.localStorage.getItem(browserDraftKey(selected.id)) || ''
    const load = signedIn ? getEssayDraft(selected.id) : Promise.resolve({ body: browserDraft })
    load.then((result) => {
      if (!live) return
      if (signedIn && !result.body && browserDraft) {
        setDraft(browserDraft); setDirty(true)
        setSaveMessage('Browser draft ready — save it to your account')
      } else setDraft(result.body)
    })
      .catch((e) => { if (live) setSaveMessage(e.message || 'Draft could not be loaded.') })
      .finally(() => { if (live) setDraftLoading(false) })
    return () => { live = false }
  }, [selected?.id, signedIn, sessionLoading])
  useEffect(() => {
    if (!dirty) return
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = '' }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty])

  const wordCount = useMemo(() => draft.trim() ? draft.trim().split(/\s+/).length : 0, [draft])
  const pages = Math.max(1, Math.ceil((page?.total ?? 0) / PAGE))
  async function save() {
    if (!selected || saving || draftLoading) return
    setSaving(true); setSaveMessage('')
    try {
      const result = signedIn ? await saveEssayDraft(selected.id, draft) : (() => {
        window.localStorage.setItem(browserDraftKey(selected.id), draft)
        return { updated_at: new Date().toISOString() }
      })()
      if (signedIn) window.localStorage.removeItem(browserDraftKey(selected.id))
      setDirty(false)
      setSaveMessage(`${signedIn ? 'Saved to your account' : 'Saved in this browser'} · ${new Date(result.updated_at || Date.now()).toLocaleString()}`)
    } catch (e) {
      setSaveMessage(e instanceof Error ? e.message : 'Could not save draft. Please try again.')
    } finally { setSaving(false) }
  }
  function choose(prompt: Question) {
    if (selected?.id === prompt.id) return
    if (dirty && !window.confirm('Your draft has unsaved changes. Switch prompts anyway?')) return
    setSelected(prompt)
  }

  return <div className="mx-auto max-w-shell px-6 pb-24 pt-9">
    <Link to="/library" className="text-[13px] font-semibold text-link">← Study library</Link>
    <header className="mt-5 rounded-[18px] bg-[#F3EAD9] px-6 py-8 sm:px-9"><div className="font-mono text-[11px] uppercase tracking-[.12em] text-[#8C5C16]">Write · revise · return</div><h1 className="mt-2 font-display text-[clamp(38px,5vw,56px)] font-medium">Essay practice</h1><p className="mt-3 max-w-[760px] text-[16px] leading-relaxed text-[#604B30]">Choose a real paper prompt, draft an answer, and save it privately. Descriptive writing is not marked as an MCQ or given an automatic score.</p></header>
    <div className="mt-8 grid gap-7 lg:grid-cols-[minmax(280px,.9fr)_minmax(0,1.2fr)]">
      <section aria-labelledby="essay-prompts-heading"><div className="flex items-end justify-between"><h2 id="essay-prompts-heading" className="font-display text-[27px]">Past-paper prompts</h2><span className="font-mono text-[11px] text-muted">{(page?.total ?? 0).toLocaleString('en-IN')} prompts</span></div><input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Find an essay topic" aria-label="Search essay prompts" className="mt-3 h-11 w-full rounded-pill border border-hairline bg-card px-4 text-[14px] placeholder:text-placeholder focus:border-ink focus:outline-none" />
        {error && <p role="alert" className="mt-3 text-[13px] text-mypick">{error}</p>}
        {loading ? <p className="mt-4 text-[13px] text-muted">Loading prompts…</p> : <div className="mt-3 grid gap-2">{page?.items.map((prompt) => {
          const source = prompt.source_appearance
          return <button key={prompt.id} type="button" onClick={() => choose(prompt)} aria-pressed={selected?.id === prompt.id} className={`rounded-[12px] border p-4 text-left ${selected?.id === prompt.id ? 'border-[#8C5C16] bg-[#FFF7E8]' : 'border-hairline bg-card hover:border-ink'}`}><span className="line-clamp-3 font-display text-[18px] leading-snug"><SourceQuestionText text={prompt.question_markup ?? prompt.question} /></span><span className="mt-2 block text-[11px] text-muted">{source?.exam || source?.paper_id.split('/').pop() || 'MPSC paper'}{source?.year ? ` · ${source.year}` : ''}</span></button>
        })}</div>}
        {!loading && !error && !page?.items.length && <p className="mt-4 text-[13px] text-secondary">No essay prompts match that search.</p>}
        {!loading && pages > 1 && <nav aria-label="Essay prompt pages" className="mt-4 flex items-center justify-between"><button type="button" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))} className="min-h-11 rounded-pill border border-hairline px-3 text-[12px] disabled:opacity-40">← Previous</button><span className="font-mono text-[11px] text-muted">Page {Math.floor(offset / PAGE) + 1} of {pages}</span><button type="button" disabled={offset + PAGE >= (page?.total ?? 0)} onClick={() => setOffset(offset + PAGE)} className="min-h-11 rounded-pill border border-hairline px-3 text-[12px] disabled:opacity-40">Next →</button></nav>}
      </section>
      <section aria-labelledby="essay-editor-heading" className="self-start rounded-[15px] border border-hairline bg-card p-5 lg:sticky lg:top-20"><div className="font-mono text-[10px] uppercase tracking-[.1em] text-[#8C5C16]">Your private workspace</div><h2 id="essay-editor-heading" className="mt-1 font-display text-[27px]">Draft an answer</h2>
        {!selected ? <p className="mt-4 text-[14px] text-secondary">Select a prompt to begin or continue a draft.</p> : <><div className="mt-4 rounded-[10px] bg-paper p-4"><div className="font-display text-[18px] leading-relaxed"><SourceQuestionText text={selected.question_markup ?? selected.question} /></div>{selected.source_appearance && <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-secondary"><span>Source: {selected.source_appearance.exam || selected.source_appearance.paper_id.split('/').pop()}{selected.source_appearance.year ? ` · ${selected.source_appearance.year}` : ''}{selected.source_appearance.qnum ? ` · Q${selected.source_appearance.qnum}` : ''}</span>{selected.source_appearance.source_pdf_url && <a href={`${selected.source_appearance.source_pdf_url}${selected.source_appearance.page ? `#page=${selected.source_appearance.page}` : ''}`} target="_blank" rel="noreferrer" className="font-semibold text-link underline">Source PDF ↗</a>}</div>}</div>
          <label htmlFor="essay-draft" className="mt-5 block text-[13px] font-semibold">Your response</label><textarea id="essay-draft" value={draft} onChange={(e) => { setDraft(e.target.value); setDirty(true); setSaveMessage('Unsaved changes') }} disabled={draftLoading || saving || sessionLoading} maxLength={30000} rows={16} placeholder="Plan your argument, then write here…" className="mt-2 w-full resize-y rounded-[10px] border border-hairline bg-white p-4 text-[15px] leading-relaxed focus:border-ink focus:outline-none disabled:opacity-50" /><div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-[12px] text-muted"><span>{wordCount} words · {draft.length.toLocaleString('en-IN')}/30,000 characters</span><span role="status">{draftLoading || sessionLoading ? 'Loading saved draft…' : saveMessage}</span></div><button type="button" onClick={save} disabled={draftLoading || saving || sessionLoading} className="mt-4 min-h-11 rounded-pill bg-ink px-5 text-[13px] font-semibold text-paper disabled:opacity-50">{saving ? 'Saving…' : 'Save draft'}</button><p className="mt-3 text-[12px] leading-relaxed text-muted">{signedIn ? 'Drafts save privately to your account and follow you across devices.' : 'Guest drafts save only in this browser. Sign in and save again to keep them across devices.'} No automatic grade is assigned.</p>
        </>}
      </section>
    </div>
  </div>
}
