#!/usr/bin/env node
/** Phase V.15 (§VII.5) Guide extractor — converts the owner-confirmed first
 *  batch from `india-study-map/public/` into clean, structured markdown JSON
 *  (zero raw embedded HTML) at `web/src/data/guides-seed.json` and
 *  `api/app/data/guides-seed.json`.
 *
 *  Confirmed batch (§VII.17 #2):
 *   1. `/guides/using-finna` (§VII.12.2)
 *   2. `/guides/polity-codex` (21 topics from `public/codex/index.html`)
 *   3. `/guides/quick-revision` (15 paper revision outlines from `public/quick-practice/quick-revision/data.js`)
 *   4. `/guides/tenses-and-voice` (12 tenses + voice table from `public/quick-practice/tenses-and-voice.html`)
 */

const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')

const ISM_PUBLIC = '/home/hruaia/workspace/projects/personal/india-study-map/public'
const FINNA_ROOT = path.resolve(__dirname, '..')

function extractConst(src, name) {
  const idx = src.indexOf('const ' + name + ' =')
  if (idx < 0) throw new Error(`Could not find const ${name}`)
  let i = src.indexOf('=', idx) + 1
  while (/\s/.test(src[i])) i++
  const open = src[i]
  const close = open === '[' ? ']' : '}'
  let depth = 0
  let inStr = null
  let esc = false
  for (let j = i; j < src.length; j++) {
    const ch = src[j]
    if (inStr) {
      if (esc) esc = false
      else if (ch === '\\') esc = true
      else if (ch === inStr) inStr = null
    } else {
      if (ch === '"' || ch === "'" || ch === '`') inStr = ch
      else if (ch === open) depth++
      else if (ch === close) {
        depth--
        if (depth === 0) return vm.runInNewContext('(' + src.slice(i, j + 1) + ')')
      }
    }
  }
  throw new Error(`Unterminated const ${name}`)
}

function stripHtml(text) {
  return String(text || '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(?:p|li|div|tr)>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

function slugify(text, fallback) {
  const s = String(text || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 70)
  return s || fallback
}

// 1. Using Finna (§VII.12.2)
const usingFinna = {
  slug: 'using-finna',
  title: 'Using Finna',
  subject_id: null,
  subject_label: 'Guide',
  exam_scope: ['udc', 'ldc', 'combined-prelims'],
  summary: 'How past papers, answer labels, the practice timer, scoring and the free allowance work.',
  reading_minutes: 4,
  status: 'published',
  chapters: [
    {
      ord: 1,
      anchor: 'browse-and-practice',
      heading: '1. Browse and make a test',
      body_markdown: [
        'Every past paper and every question in the Finna bank is free to browse without signing in. Use **Papers** to read original booklets by year, or open the **Question bank** to search across exams and subjects.',
        'When you are ready to test yourself, open **Practice**. Choose what you want to cover, choose how many questions, and toggle the timer on or off. Timer off checks each answer as you go; timer on runs a server-timed paper and scores at the end.',
      ].join('\n\n'),
      practice_query: '/practice',
    },
    {
      ord: 2,
      anchor: 'answer-labels',
      heading: '2. What the answer labels mean',
      body_markdown: [
        'Trusted answers (an uncontested official key or a reviewed worked solution) render cleanly without badge noise. The source line under every question always names the exam, year, paper and question number.',
        '- **Not verified** (amber): answer awaiting verification, unsolved, or a provisional key before the final key publishes.',
        '- **Answer disputed** (inline): the official key and our reviewed working disagree. Both sources are shown inline while we check it.',
      ].join('\n\n'),
      practice_query: '/bank',
    },
    {
      ord: 3,
      anchor: 'written-questions',
      heading: '3. Written, essay and LDE papers',
      body_markdown: [
        'Descriptive questions — essays, letters, précis, comprehension and LDE papers — are reading surfaces. Finna lists them clearly with printed directions, passages and marks, without auto-marking. Signed-in learners can save private practice drafts on any descriptive prompt.',
      ].join('\n\n'),
      practice_query: '/bank?mode=written',
    },
    {
      ord: 4,
      anchor: 'free-tier',
      heading: '4. Free allowance and scoring',
      body_markdown: [
        'Browsing past papers, reading guides and checking question sources are always free. Under the unified Practice surface, the free tier provides **1 timed run per month** and **50 untimed answers per day**, with timed runs saved as snapshots so your past results stay auditable.',
      ].join('\n\n'),
      practice_query: '/plans',
    },
  ],
}

// 2. Polity Codex (21 chapters from public/codex/index.html)
const codexHtml = fs.readFileSync(path.join(ISM_PUBLIC, 'codex/index.html'), 'utf8')
const TOPICS = extractConst(codexHtml, 'TOPICS')
const STUDY = extractConst(codexHtml, 'STUDY')
const topicById = Object.fromEntries(TOPICS.map((t) => [t.id, t]))

const polityCodex = {
  slug: 'polity-codex',
  title: 'Indian Polity Codex',
  subject_id: 'polity',
  subject_label: 'Indian Polity',
  exam_scope: ['combined-prelims', 'udc', 'ldc'],
  summary: 'Comprehensive 21-chapter constitutional reference covering the making of the Constitution, Fundamental Rights, Parliament, Federalism, Mizoram Sixth Schedule and local bodies.',
  reading_minutes: 35,
  status: 'published',
  chapters: STUDY.map((sec, idx) => {
    const t = topicById[sec.topic] || {}
    const heading = `${idx + 1}. ${stripHtml(t.name || sec.topic)}`
    const bullets = (sec.points || []).map((pt) => {
      if (typeof pt === 'string') return `- ${stripHtml(pt)}`
      const lead = pt.t || pt.title || pt.h || ''
      const body = pt.b || pt.body || pt.d || pt.text || ''
      return lead ? `- **${stripHtml(lead)}**: ${stripHtml(body)}` : `- ${stripHtml(body)}`
    })
    return {
      ord: idx + 1,
      anchor: slugify(sec.topic, `chapter-${idx + 1}`),
      heading,
      body_markdown: bullets.join('\n'),
      practice_query: `/practice?subject=polity&q=${encodeURIComponent(stripHtml(t.name || '').split(' ')[0] || '')}`,
    }
  }),
}

// 3. Quick Revision (15 paper revision outlines from public/quick-practice/quick-revision/data.js)
const qrJs = fs.readFileSync(path.join(ISM_PUBLIC, 'quick-practice/quick-revision/data.js'), 'utf8')
const qrCtx = { window: {} }
vm.runInNewContext(qrJs, qrCtx)
const qrPapers = qrCtx.window.QR_DATA.papers || []

const quickRevision = {
  slug: 'quick-revision',
  title: 'MPSC Quick Revision',
  subject_id: 'general-knowledge',
  subject_label: 'General Knowledge & Revision',
  exam_scope: ['udc', 'ldc', 'combined-prelims'],
  summary: 'High-yield rapid revision summaries extracted from 15 core MPSC papers and recurring exam themes.',
  reading_minutes: 25,
  status: 'published',
  chapters: qrPapers.map((paper, idx) => {
    const qs = (paper.questions || []).slice(0, 12)
    const lines = []
    if (paper.subtitle) lines.push(stripHtml(paper.subtitle))
    if (paper.note) lines.push(`> ${stripHtml(paper.note)}`)
    for (const q of qs) {
      const prompt = stripHtml(q.q || q.question || '')
      const ans =
        Array.isArray(q.o || q.options) && typeof (q.a ?? q.answer) === 'number'
          ? stripHtml((q.o || q.options)[q.a ?? q.answer])
          : stripHtml(q.answer_text || '')
      const exp = stripHtml(q.e || q.explanation || '')
      if (prompt) {
        lines.push(`- **${prompt}**${ans ? ` → *${ans}*` : ''}${exp ? ` — ${exp}` : ''}`)
      }
    }
    return {
      ord: idx + 1,
      anchor: slugify(paper.id || paper.title, `paper-${idx + 1}`),
      heading: `${idx + 1}. ${stripHtml(paper.title)}`,
      body_markdown: lines.join('\n\n') || stripHtml(paper.title),
      practice_query: `/practice?q=${encodeURIComponent(stripHtml(paper.title).split(' ')[0] || '')}`,
    }
  }),
}

// 4. Tenses & Voice (12 tenses + voice conversion table from public/quick-practice/tenses-and-voice.html)
const tvHtml = fs.readFileSync(path.join(ISM_PUBLIC, 'quick-practice/tenses-and-voice.html'), 'utf8')
const TENSES = extractConst(tvHtml, 'TENSES')
const VOICE_TABLE = extractConst(tvHtml, 'VOICE_TABLE')

const tensesChapters = [
  ...TENSES.map((t, idx) => {
    const lines = [
      `**Time & Aspect:** ${stripHtml(t.time)} · ${stripHtml(t.aspect)}`,
      `**Structure:** \`${stripHtml(t.formula)}\``,
      stripHtml(t.use),
    ]
    if (Array.isArray(t.signals) && t.signals.length) {
      lines.push(`**Signal words:** ${t.signals.map(stripHtml).join(', ')}`)
    }
    if (Array.isArray(t.examples) && t.examples.length) {
      lines.push('**Examples:**')
      for (const ex of t.examples) {
        lines.push(`- ${stripHtml(typeof ex === 'string' ? ex : ex.s || ex.text || JSON.stringify(ex))}`)
      }
    }
    return {
      ord: idx + 1,
      anchor: slugify(t.name, `tense-${idx + 1}`),
      heading: `${idx + 1}. ${stripHtml(t.name)}`,
      body_markdown: lines.join('\n\n'),
      practice_query: '/practice?subject=english&q=tense',
    }
  }),
  {
    ord: TENSES.length + 1,
    anchor: 'active-and-passive-voice',
    heading: `${TENSES.length + 1}. Active and Passive Voice Conversion Table`,
    body_markdown: [
      'Every tense transforms systematically between Active and Passive voice by inserting the matching form of *be* + past participle (V3):',
      ...VOICE_TABLE.map(
        (row) => `- **${stripHtml(row[0])}**: Active: \`${stripHtml(row[1])}\` → Passive: \`${stripHtml(row[2])}\``,
      ),
    ].join('\n\n'),
    practice_query: '/practice?subject=english&q=voice',
  },
]

const tensesAndVoice = {
  slug: 'tenses-and-voice',
  title: 'English Tenses & Voice',
  subject_id: 'english',
  subject_label: 'English Grammar',
  exam_scope: ['udc', 'ldc', 'combined-prelims'],
  summary: 'All twelve English tenses with structures, signal words and worked examples, plus the complete Active-to-Passive voice conversion table.',
  reading_minutes: 18,
  status: 'published',
  chapters: tensesChapters,
}

const allGuides = [usingFinna, polityCodex, quickRevision, tensesAndVoice]

// Verify zero raw HTML tags leaked into any body_markdown
for (const g of allGuides) {
  for (const ch of g.chapters) {
    if (/<(?:script|style|div|span|table|iframe|object)/i.test(ch.body_markdown)) {
      throw new Error(`Raw HTML detected in ${g.slug}#${ch.anchor}`)
    }
  }
}

const json = JSON.stringify(allGuides, null, 2) + '\n'
fs.mkdirSync(path.join(FINNA_ROOT, 'web/src/data'), { recursive: true })
fs.mkdirSync(path.join(FINNA_ROOT, 'api/app/data'), { recursive: true })
fs.writeFileSync(path.join(FINNA_ROOT, 'web/src/data/guides-seed.json'), json)
fs.writeFileSync(path.join(FINNA_ROOT, 'api/app/data/guides-seed.json'), json)

console.log(
  JSON.stringify(
    {
      ok: true,
      guides: allGuides.map((g) => ({
        slug: g.slug,
        title: g.title,
        chapters: g.chapters.length,
      })),
    },
    null,
    2,
  ),
)
