import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import guidesSeed from '../data/guides-seed.json'
import { reviewRequest } from '../lib/review'

interface StudioChapter {
  ord: number
  anchor: string
  heading: string
  body_markdown: string
  question_ids: string[]
}

interface StudioGuideSummary {
  slug: string
  title: string
  subject_id?: string | null
  topic_id?: string | null
  exam_scope?: string[]
  summary: string
  reading_minutes: number
  status?: string
  version?: number
  chapter_count?: number
  question_count?: number
  updated_at?: string
  inDb: boolean
  hasSeed: boolean
}

interface SeedGuide {
  slug: string
  title: string
  subject_id?: string | null
  topic_id?: string | null
  exam_scope?: string[]
  summary: string
  reading_minutes: number
  status?: string
  chapters: {
    ord: number
    anchor: string
    heading: string
    body_markdown: string
    question_ids?: string[]
  }[]
}

const SEED_GUIDES = guidesSeed as SeedGuide[]

const SUBJECT_PRESETS = [
  ['', 'General / Platform (no subject)'],
  ['english', 'English'],
  ['mathematics', 'Mathematics & Arithmetic'],
  ['gk-gs', 'GK & General Studies (Polity / Geography / History)'],
  ['reasoning', 'Reasoning & Aptitude'],
  ['mizo', 'Mizo'],
  ['general-knowledge', 'General Knowledge (legacy alias)'],
  ['general-studies', 'General Studies (legacy alias)'],
] as const

const TOPIC_HINTS = [
  'mathematics/arithmetic',
  'mathematics/algebra',
  'mathematics/mensuration',
  'mathematics/geometry',
  'gk-gs:indian-polity',
  'gk-gs:geography',
  'gk-gs:indian-history',
  'gk-gs:world-history',
  'gk-gs:indian-economy',
  'gk-gs:mizoram',
  'gk-gs:environment',
  'english/grammar',
  'english/vocabulary',
  'mizo/grammar',
] as const

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80)
}

function emptyChapter(ord: number): StudioChapter {
  return {
    ord,
    anchor: `chapter-${ord}`,
    heading: `${ord}. New Chapter`,
    body_markdown: 'Write concise concept points here.\n\n- Key rule or formula\n- Exam trap to watch for',
    question_ids: [],
  }
}

/** Safe markdown preview — never emits raw HTML. */
function SafePreview({ markdown }: { markdown: string }) {
  const blocks = markdown.split(/\n{2,}/)
  return (
    <div className="space-y-3 font-reading text-sm leading-relaxed text-ink">
      {blocks.map((block, i) => {
        const lines = block.split('\n').filter(Boolean)
        if (!lines.length) return null
        if (lines[0].startsWith('### ')) {
          return (
            <h4 key={i} className="font-display text-base font-bold text-ink">
              {lines[0].slice(4)}
            </h4>
          )
        }
        if (lines.every((l) => l.trim().startsWith('|') && l.trim().endsWith('|')) && lines.length >= 2) {
          const rows = lines
            .filter((l) => !/^\|[\s:-]+\|$/.test(l.trim().replace(/\|/g, '|')))
            .map((l) =>
              l
                .trim()
                .slice(1, -1)
                .split('|')
                .map((c) => c.trim()),
            )
          const [head, ...body] = rows
          if (head?.length) {
            return (
              <div key={i} className="overflow-x-auto rounded-lg border border-hairline">
                <table className="w-full border-collapse text-left text-xs">
                  <thead>
                    <tr className="bg-canvas">
                      {head.map((c, ci) => (
                        <th key={ci} className="border-b border-hairline px-2.5 py-1.5 font-bold">
                          {c}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {body.map((r, ri) => (
                      <tr key={ri} className="border-b border-hairline/60 last:border-b-0">
                        {r.map((c, ci) => (
                          <td key={ci} className="px-2.5 py-1.5">
                            {c}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          }
        }
        if (lines.every((l) => l.startsWith('- '))) {
          return (
            <ul key={i} className="list-disc space-y-1 pl-5">
              {lines.map((l, li) => (
                <li key={li}>{l.slice(2)}</li>
              ))}
            </ul>
          )
        }
        return (
          <p key={i} className="whitespace-pre-wrap">
            {block}
          </p>
        )
      })}
    </div>
  )
}

export default function GuidesStudio() {
  const [dbGuides, setDbGuides] = useState<StudioGuideSummary[]>([])
  const [loadingList, setLoadingList] = useState(true)
  const [listNote, setListNote] = useState('')

  const [selectedSlug, setSelectedSlug] = useState<string | null>(null)
  const [isNew, setIsNew] = useState(false)
  const [slug, setSlug] = useState('')
  const [title, setTitle] = useState('')
  const [subjectId, setSubjectId] = useState('')
  const [topicId, setTopicId] = useState('')
  const [examScopeText, setExamScopeText] = useState('')
  const [summary, setSummary] = useState('')
  const [readingMinutes, setReadingMinutes] = useState(8)
  const [status, setStatus] = useState<'draft' | 'published' | 'archived'>('published')
  const [chapters, setChapters] = useState<StudioChapter[]>([emptyChapter(1)])
  const [activeChapterIdx, setActiveChapterIdx] = useState(0)
  const [previewMode, setPreviewMode] = useState(false)

  const [loadingDoc, setLoadingDoc] = useState(false)
  const [saving, setSaving] = useState(false)
  const [syncingAll, setSyncingAll] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  async function refreshCatalog() {
    setLoadingList(true)
    setListNote('')
    try {
      let items: Record<string, unknown>[] = []
      try {
        const res = await reviewRequest<{ items: Record<string, unknown>[] }>('/guides/admin')
        items = res.items || []
      } catch {
        // Graceful fallback if API hasn't been restarted with GET /guides/admin yet.
        const r = await fetch('/api/guides')
        if (r.ok) {
          const payload = (await r.json()) as { items?: Record<string, unknown>[] }
          items = payload.items || []
          setListNote('Showing published guides from live API (draft listing activates after API restart).')
        }
      }
      const mapped: StudioGuideSummary[] = items.map((g) => ({
        slug: String(g.slug),
        title: String(g.title),
        subject_id: g.subject_id ? String(g.subject_id) : null,
        topic_id: g.topic_id ? String(g.topic_id) : null,
        exam_scope: Array.isArray(g.exam_scope) ? g.exam_scope.map(String) : [],
        summary: String(g.summary || ''),
        reading_minutes: Number(g.reading_minutes || 5),
        status: String(g.status || 'published'),
        version: Number(g.version || 1),
        chapter_count: Number(g.chapter_count || 0),
        question_count: Number(g.question_count || 0),
        updated_at: g.updated_at ? String(g.updated_at) : undefined,
        inDb: true,
        hasSeed: SEED_GUIDES.some((s) => s.slug === String(g.slug)),
      }))
      setDbGuides(mapped)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load guides catalog.')
    } finally {
      setLoadingList(false)
    }
  }

  useEffect(() => {
    void refreshCatalog()
  }, [])

  const catalog = useMemo(() => {
    const bySlug = new Map<string, StudioGuideSummary>()
    for (const g of dbGuides) bySlug.set(g.slug, g)
    for (const s of SEED_GUIDES) {
      if (!bySlug.has(s.slug)) {
        bySlug.set(s.slug, {
          slug: s.slug,
          title: s.title,
          subject_id: s.subject_id || null,
          topic_id: s.topic_id || null,
          exam_scope: s.exam_scope || [],
          summary: s.summary,
          reading_minutes: s.reading_minutes,
          status: 'seed',
          chapter_count: s.chapters.length,
          inDb: false,
          hasSeed: true,
        })
      }
    }
    return [...bySlug.values()]
  }, [dbGuides])

  function applyDocToEditor(doc: {
    slug: string
    title: string
    subject_id?: string | null
    topic_id?: string | null
    exam_scope?: string[]
    summary: string
    reading_minutes: number
    status?: string
    chapters: {
      ord: number
      anchor: string
      heading: string
      body_markdown: string
      question_ids?: string[]
    }[]
  }) {
    setSlug(doc.slug)
    setTitle(doc.title)
    setSubjectId(doc.subject_id || '')
    setTopicId(doc.topic_id || '')
    setExamScopeText((doc.exam_scope || []).join(', '))
    setSummary(doc.summary)
    setReadingMinutes(doc.reading_minutes || 5)
    setStatus(
      doc.status === 'draft' || doc.status === 'archived' ? doc.status : 'published',
    )
    const chs: StudioChapter[] = doc.chapters.length
      ? doc.chapters.map((c, idx) => ({
          ord: idx + 1,
          anchor: c.anchor || `chapter-${idx + 1}`,
          heading: c.heading,
          body_markdown: c.body_markdown,
          question_ids: c.question_ids || [],
        }))
      : [emptyChapter(1)]
    setChapters(chs)
    setActiveChapterIdx(0)
  }

  async function openGuide(targetSlug: string) {
    setSelectedSlug(targetSlug)
    setIsNew(false)
    setLoadingDoc(true)
    setError('')
    setNotice('')
    try {
      let loaded: SeedGuide | null = null
      try {
        loaded = await reviewRequest<SeedGuide>('/guides/admin/' + encodeURIComponent(targetSlug))
      } catch {
        const r = await fetch('/api/guides/' + encodeURIComponent(targetSlug))
        if (r.ok) loaded = (await r.json()) as SeedGuide
      }
      if (loaded && loaded.slug) {
        applyDocToEditor(loaded)
      } else {
        const seed = SEED_GUIDES.find((s) => s.slug === targetSlug)
        if (seed) {
          applyDocToEditor(seed)
          setNotice('Loaded from bundled seed. Click "Save & publish" to store it live in Postgres.')
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not open guide.')
    } finally {
      setLoadingDoc(false)
    }
  }

  function startNewGuide() {
    setSelectedSlug(null)
    setIsNew(true)
    setSlug('')
    setTitle('')
    setSubjectId('gk-gs')
    setTopicId('')
    setExamScopeText('udc, ldc, combined-prelims')
    setSummary('')
    setReadingMinutes(8)
    setStatus('draft')
    setChapters([emptyChapter(1)])
    setActiveChapterIdx(0)
    setError('')
    setNotice('')
  }

  function loadBundledVersion() {
    const seed = SEED_GUIDES.find((s) => s.slug === slug)
    if (!seed) return
    applyDocToEditor(seed)
    setNotice('Loaded the upgraded bundled chapters into the editor. Review and click "Save & publish" to update Postgres.')
  }

  function updateChapter(idx: number, patch: Partial<StudioChapter>) {
    setChapters((prev) =>
      prev.map((c, i) => (i === idx ? { ...c, ...patch } : c)),
    )
  }

  function addChapter() {
    const nextOrd = chapters.length + 1
    setChapters((prev) => [...prev, emptyChapter(nextOrd)])
    setActiveChapterIdx(chapters.length)
  }

  function moveChapter(idx: number, dir: -1 | 1) {
    const target = idx + dir
    if (target < 0 || target >= chapters.length) return
    setChapters((prev) => {
      const next = [...prev]
      const [item] = next.splice(idx, 1)
      next.splice(target, 0, item)
      return next.map((c, i) => ({ ...c, ord: i + 1 }))
    })
    setActiveChapterIdx(target)
  }

  function removeChapter(idx: number) {
    if (chapters.length <= 1) return
    setChapters((prev) =>
      prev.filter((_, i) => i !== idx).map((c, i) => ({ ...c, ord: i + 1 })),
    )
    setActiveChapterIdx((prev) => Math.max(0, Math.min(prev, chapters.length - 2)))
  }

  async function saveGuide(nextStatus: 'draft' | 'published' | 'archived') {
    setError('')
    setNotice('')
    const cleanSlug = slug.trim().toLowerCase()
    if (!/^[a-z0-9][a-z0-9-]{1,100}$/.test(cleanSlug)) {
      setError('Slug must be lowercase letters, numbers, and hyphens (e.g. maths-and-arithmetic).')
      return
    }
    if (title.trim().length < 2) {
      setError('Enter a guide title (at least 2 characters).')
      return
    }
    if (summary.trim().length < 10) {
      setError('Enter a clear summary (at least 10 characters).')
      return
    }
    const cleanChapters = chapters.map((c, idx) => ({
      ord: idx + 1,
      anchor: slugify(c.anchor || c.heading) || `chapter-${idx + 1}`,
      heading: c.heading.trim(),
      body_markdown: c.body_markdown.trim(),
      question_ids: c.question_ids.map((id) => id.trim()).filter(Boolean),
    }))
    const badCh = cleanChapters.find((c) => c.heading.length < 2 || c.body_markdown.length < 10)
    if (badCh) {
      setError(`Chapter ${badCh.ord} needs a heading (≥2 chars) and markdown body (≥10 chars).`)
      return
    }
    setSaving(true)
    try {
      const examScope = examScopeText
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)
      const res = await reviewRequest<{ id: string; slug: string; version: number; status: string }>(
        '/guides/admin',
        {
          slug: cleanSlug,
          title: title.trim(),
          subject_id: subjectId.trim() || null,
          topic_id: topicId.trim() || null,
          exam_scope: examScope,
          summary: summary.trim(),
          reading_minutes: Math.max(1, Math.min(240, Number(readingMinutes) || 5)),
          status: nextStatus,
          chapters: cleanChapters,
        },
      )
      setStatus(nextStatus)
      setSelectedSlug(res.slug)
      setIsNew(false)
      setNotice(`Saved "${title.trim()}" (v${res.version} · ${res.status}). Learners see published guides immediately on /guides and /subjects.`)
      await refreshCatalog()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save guide.')
    } finally {
      setSaving(false)
    }
  }

  async function syncAllBundledGuides() {
    if (!window.confirm(`Publish all ${SEED_GUIDES.length} bundled first-party guides (including Maths & Arithmetic, Geography, History, and upgraded Polity Codex) into live Postgres?`)) {
      return
    }
    setSyncingAll(true)
    setError('')
    setNotice('')
    let ok = 0
    try {
      for (const s of SEED_GUIDES) {
        await reviewRequest('/guides/admin', {
          slug: s.slug,
          title: s.title,
          subject_id: s.subject_id || null,
          topic_id: s.topic_id || null,
          exam_scope: s.exam_scope || [],
          summary: s.summary,
          reading_minutes: s.reading_minutes || 8,
          status: 'published',
          chapters: s.chapters.map((c, idx) => ({
            ord: idx + 1,
            anchor: slugify(c.anchor || c.heading) || `chapter-${idx + 1}`,
            heading: c.heading,
            body_markdown: c.body_markdown,
            question_ids: c.question_ids || [],
          })),
        })
        ok++
      }
      setNotice(`Synced ${ok} of ${SEED_GUIDES.length} concept guides cleanly to live Postgres.`)
      await refreshCatalog()
    } catch (e) {
      setError(`Synced ${ok}/${SEED_GUIDES.length} before error: ${e instanceof Error ? e.message : 'Save failed'}`)
    } finally {
      setSyncingAll(false)
    }
  }

  const activeChapter = chapters[activeChapterIdx] || chapters[0]
  const hasSeedMatch = !!SEED_GUIDES.find((s) => s.slug === slug)
  const INPUT =
    'min-h-10 w-full rounded-[8px] border border-hairline bg-canvas px-3 py-2 text-sm text-ink focus:border-ink focus:outline-none'

  return (
    <section className="mt-5 space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-[14px] border border-hairline bg-card p-4">
        <div>
          <h2 className="font-display text-xl font-semibold text-ink">Concept Guides Studio</h2>
          <p className="mt-0.5 text-xs text-secondary">
            Author, edit, and publish first-party study guides. Published guides appear automatically in{' '}
            <Link to="/guides" className="font-semibold text-link underline">/guides</Link> and on matching{' '}
            <Link to="/library" className="font-semibold text-link underline">Subject Topics</Link> pages.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={syncingAll}
            onClick={() => void syncAllBundledGuides()}
            className="min-h-10 rounded-pill border border-hairline bg-canvas px-4 text-xs font-bold text-ink hover:border-ink disabled:opacity-50"
          >
            {syncingAll ? 'Syncing…' : `↑ Sync ${SEED_GUIDES.length} bundled guides to DB`}
          </button>
          <button
            type="button"
            onClick={startNewGuide}
            className="min-h-10 rounded-pill bg-ink px-4 text-xs font-bold text-paper"
          >
            + New concept guide
          </button>
        </div>
      </div>

      {listNote && (
        <p className="rounded-[10px] border border-hairline bg-paper px-3.5 py-2 text-xs text-secondary">
          {listNote}
        </p>
      )}
      {error && (
        <p role="alert" className="rounded-[10px] border border-mypick bg-mypick-soft px-4 py-3 text-sm text-mypick">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="rounded-[10px] border border-correct bg-correct-soft px-4 py-3 text-sm text-ink">
          {notice}
        </p>
      )}

      <div className="grid gap-5 lg:grid-cols-[300px_minmax(0,1fr)]">
        {/* Left Guide Shelf List */}
        <aside className="space-y-2 rounded-[14px] border border-hairline bg-card p-3">
          <div className="flex items-center justify-between px-1 pb-1">
            <span className="font-mono text-[11px] font-bold uppercase tracking-[.08em] text-muted">
              All guides ({catalog.length})
            </span>
            <button
              type="button"
              onClick={() => void refreshCatalog()}
              className="text-xs font-semibold text-link underline"
            >
              Refresh
            </button>
          </div>
          {loadingList && <p className="p-2 text-xs text-muted">Loading guides…</p>}
          {catalog.map((g) => {
            const active = !isNew && selectedSlug === g.slug
            return (
              <button
                key={g.slug}
                type="button"
                onClick={() => void openGuide(g.slug)}
                className={`w-full rounded-[11px] border p-3 text-left transition ${
                  active
                    ? 'border-ink bg-paper'
                    : 'border-hairline bg-canvas hover:border-ink/60'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <strong className="truncate text-sm text-ink">{g.title}</strong>
                  <span
                    className={`shrink-0 rounded-pill px-2 py-0.5 font-mono text-[10px] font-bold uppercase ${
                      g.inDb
                        ? g.status === 'published'
                          ? 'bg-correct-soft text-correct'
                          : 'bg-paper text-secondary'
                        : 'bg-exams-soft text-exams-dark'
                    }`}
                  >
                    {g.inDb ? `${g.status || 'live'} v${g.version || 1}` : 'seed'}
                  </span>
                </div>
                <div className="mt-1 font-mono text-[11px] text-muted">
                  /{g.slug} · {g.subject_id || 'general'} · {g.chapter_count || 0} ch
                </div>
              </button>
            )
          })}
        </aside>

        {/* Right Editor Pane */}
        <div className="rounded-[14px] border border-hairline bg-card p-5">
          {!isNew && !selectedSlug ? (
            <div className="py-12 text-center text-sm text-secondary">
              Select a guide on the left to edit its chapters and linked questions, or click{' '}
              <button type="button" onClick={startNewGuide} className="font-bold text-link underline">
                + New concept guide
              </button>
              .
            </div>
          ) : loadingDoc ? (
            <p className="py-12 text-center text-sm text-muted">Loading guide chapters…</p>
          ) : (
            <div className="space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-hairline pb-3">
                <div>
                  <span className="font-mono text-[11px] font-bold uppercase tracking-[.08em] text-muted">
                    {isNew ? 'New Guide Draft' : `Editing /guides/${slug}`}
                  </span>
                  <h3 className="font-display text-lg font-semibold text-ink">
                    {title || 'Untitled Concept Guide'}
                  </h3>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {hasSeedMatch && (
                    <button
                      type="button"
                      onClick={loadBundledVersion}
                      className="min-h-9 rounded-pill border border-hairline bg-canvas px-3 text-xs font-semibold text-ink hover:border-ink"
                    >
                      Load upgraded seed
                    </button>
                  )}
                  {!isNew && slug && (
                    <Link
                      to={`/guides/${encodeURIComponent(slug)}`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex min-h-9 items-center rounded-pill border border-hairline px-3 text-xs font-semibold text-link hover:border-ink"
                    >
                      Open live page ↗
                    </Link>
                  )}
                </div>
              </div>

              {/* Metadata Fields */}
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="block text-xs font-semibold text-secondary">
                  Title
                  <input
                    value={title}
                    onChange={(e) => {
                      const val = e.target.value
                      setTitle(val)
                      if (isNew && !slug) setSlug(slugify(val))
                    }}
                    placeholder="e.g. Mathematics & Arithmetic Formula Handbook"
                    className={INPUT + ' mt-1'}
                  />
                </label>
                <label className="block text-xs font-semibold text-secondary">
                  Slug (URL path)
                  <input
                    value={slug}
                    onChange={(e) => setSlug(e.target.value)}
                    placeholder="e.g. maths-and-arithmetic"
                    className={INPUT + ' mt-1 font-mono'}
                  />
                </label>
                <label className="block text-xs font-semibold text-secondary">
                  Subject
                  <select
                    value={subjectId}
                    onChange={(e) => setSubjectId(e.target.value)}
                    className={INPUT + ' mt-1'}
                  >
                    {SUBJECT_PRESETS.map(([id, label]) => (
                      <option key={id} value={id}>
                        {label}
                      </option>
                    ))}
                    {subjectId && !SUBJECT_PRESETS.some(([id]) => id === subjectId) && (
                      <option value={subjectId}>{subjectId}</option>
                    )}
                  </select>
                </label>
                <label className="block text-xs font-semibold text-secondary">
                  Topic ID (optional — pins guide to that topic card)
                  <input
                    list="guides-studio-topics"
                    value={topicId}
                    onChange={(e) => setTopicId(e.target.value)}
                    placeholder="e.g. gk-gs:geography or mathematics/arithmetic"
                    className={INPUT + ' mt-1 font-mono'}
                  />
                  <datalist id="guides-studio-topics">
                    {TOPIC_HINTS.map((t) => (
                      <option key={t} value={t} />
                    ))}
                  </datalist>
                </label>
                <label className="block text-xs font-semibold text-secondary">
                  Exam scope (comma-separated collection IDs)
                  <input
                    value={examScopeText}
                    onChange={(e) => setExamScopeText(e.target.value)}
                    placeholder="udc, ldc, combined-prelims"
                    className={INPUT + ' mt-1 font-mono'}
                  />
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <label className="block text-xs font-semibold text-secondary">
                    Reading minutes
                    <input
                      type="number"
                      min={1}
                      max={240}
                      value={readingMinutes}
                      onChange={(e) => setReadingMinutes(Number(e.target.value) || 5)}
                      className={INPUT + ' mt-1'}
                    />
                  </label>
                  <label className="block text-xs font-semibold text-secondary">
                    Status
                    <select
                      value={status}
                      onChange={(e) =>
                        setStatus(e.target.value as 'draft' | 'published' | 'archived')
                      }
                      className={INPUT + ' mt-1'}
                    >
                      <option value="draft">Draft</option>
                      <option value="published">Published</option>
                      <option value="archived">Archived</option>
                    </select>
                  </label>
                </div>
              </div>

              <label className="block text-xs font-semibold text-secondary">
                Summary (shown on /guides and Subject Topics cards)
                <textarea
                  rows={2}
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                  placeholder="Concise description of what this concept guide covers…"
                  className={INPUT + ' mt-1'}
                />
              </label>

              {/* Chapter Strip + Active Chapter Editor */}
              <div className="rounded-[12px] border border-hairline bg-canvas p-3.5">
                <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5">
                  <span className="font-mono text-[11px] font-bold uppercase tracking-[.08em] text-muted">
                    Chapters ({chapters.length})
                  </span>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => setPreviewMode((v) => !v)}
                      className="min-h-8 rounded-pill border border-hairline bg-card px-3 text-xs font-semibold text-ink"
                    >
                      {previewMode ? 'Edit markdown' : 'Preview chapter'}
                    </button>
                    <button
                      type="button"
                      onClick={addChapter}
                      className="min-h-8 rounded-pill border border-ink bg-card px-3 text-xs font-bold text-ink"
                    >
                      + Add chapter
                    </button>
                  </div>
                </div>

                <div className="flex flex-wrap gap-1.5 pb-3">
                  {chapters.map((ch, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setActiveChapterIdx(idx)}
                      className={`min-h-8 rounded-pill border px-2.5 text-xs font-semibold ${
                        idx === activeChapterIdx
                          ? 'border-ink bg-ink text-paper'
                          : 'border-hairline bg-card text-ink hover:border-ink/50'
                      }`}
                    >
                      {String(idx + 1).padStart(2, '0')}. {ch.heading.replace(/^\d+\.\s*/, '').slice(0, 22)}
                    </button>
                  ))}
                </div>

                {activeChapter && (
                  <div className="space-y-3 border-t border-hairline pt-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-xs font-bold text-ink">
                        Chapter {activeChapterIdx + 1} of {chapters.length}
                      </span>
                      <div className="flex gap-1.5">
                        <button
                          type="button"
                          disabled={activeChapterIdx === 0}
                          onClick={() => moveChapter(activeChapterIdx, -1)}
                          className="min-h-8 rounded-lg border border-hairline bg-card px-2.5 text-xs font-bold disabled:opacity-35"
                        >
                          ↑ Up
                        </button>
                        <button
                          type="button"
                          disabled={activeChapterIdx >= chapters.length - 1}
                          onClick={() => moveChapter(activeChapterIdx, 1)}
                          className="min-h-8 rounded-lg border border-hairline bg-card px-2.5 text-xs font-bold disabled:opacity-35"
                        >
                          ↓ Down
                        </button>
                        <button
                          type="button"
                          disabled={chapters.length <= 1}
                          onClick={() => removeChapter(activeChapterIdx)}
                          className="min-h-8 rounded-lg border border-mypick/40 bg-card px-2.5 text-xs font-bold text-mypick disabled:opacity-35"
                        >
                          Delete
                        </button>
                      </div>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <label className="block text-xs font-semibold text-secondary">
                        Chapter heading
                        <input
                          value={activeChapter.heading}
                          onChange={(e) =>
                            updateChapter(activeChapterIdx, { heading: e.target.value })
                          }
                          className={INPUT + ' mt-1 bg-card'}
                        />
                      </label>
                      <label className="block text-xs font-semibold text-secondary">
                        URL anchor
                        <input
                          value={activeChapter.anchor}
                          onChange={(e) =>
                            updateChapter(activeChapterIdx, { anchor: e.target.value })
                          }
                          className={INPUT + ' mt-1 bg-card font-mono'}
                        />
                      </label>
                    </div>

                    {previewMode ? (
                      <div className="min-h-[200px] rounded-[10px] border border-hairline bg-card p-4">
                        <SafePreview markdown={activeChapter.body_markdown} />
                      </div>
                    ) : (
                      <label className="block text-xs font-semibold text-secondary">
                        Markdown body (supports **bold**, `formulas`, ### subheadings, bullet lists, and | tables |)
                        <textarea
                          rows={10}
                          value={activeChapter.body_markdown}
                          onChange={(e) =>
                            updateChapter(activeChapterIdx, { body_markdown: e.target.value })
                          }
                          className={INPUT + ' mt-1 bg-card font-mono text-xs leading-relaxed'}
                        />
                      </label>
                    )}

                    <label className="block text-xs font-semibold text-secondary">
                      Linked bank question IDs (optional, comma-separated `cq_...` — validated live)
                      <input
                        value={activeChapter.question_ids.join(', ')}
                        onChange={(e) =>
                          updateChapter(activeChapterIdx, {
                            question_ids: e.target.value
                              .split(/[\s,]+/)
                              .map((s) => s.trim())
                              .filter(Boolean),
                          })
                        }
                        placeholder="cq_000447f8e5cd82dd, cq_00bae67f3219434b"
                        className={INPUT + ' mt-1 bg-card font-mono text-xs'}
                      />
                    </label>
                  </div>
                )}
              </div>

              {/* Save Action Footer */}
              <div className="flex flex-wrap items-center justify-end gap-2 border-t border-hairline pt-4">
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => void saveGuide('draft')}
                  className="min-h-11 rounded-pill border border-hairline bg-canvas px-5 text-sm font-bold text-ink hover:border-ink disabled:opacity-50"
                >
                  Save as draft
                </button>
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => void saveGuide('published')}
                  className="min-h-11 rounded-pill bg-ink px-5 text-sm font-bold text-paper disabled:opacity-50"
                >
                  {saving ? 'Saving…' : 'Save & publish live →'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
