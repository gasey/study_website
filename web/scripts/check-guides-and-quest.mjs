#!/usr/bin/env node
import fs from 'node:fs'
import path from 'node:path'

const webRoot = path.resolve(import.meta.dirname, '..')
const seedPath = path.join(webRoot, 'src/data/guides-seed.json')
const linkPath = path.join(webRoot, 'src/lib/questionGuideLink.ts')

const seed = JSON.parse(fs.readFileSync(seedPath, 'utf8'))
const valid = new Map()
const strayLatex = []

for (const g of seed) {
  const anchors = new Set()
  for (const ch of g.chapters || []) {
    anchors.add(ch.anchor)
    if (/\\(frac|sqrt|Delta|theta|infty|pm|times|text)\b/.test(ch.body_markdown || '')) {
      strayLatex.push(`${g.slug}#${ch.anchor}`)
    }
  }
  valid.set(g.slug, anchors)
}

if (strayLatex.length) {
  console.error('check-guides-and-quest: FAIL — stray LaTeX in guides-seed.json:', strayLatex)
  process.exit(1)
}

const linkSrc = fs.readFileSync(linkPath, 'utf8')
const matches = [...linkSrc.matchAll(/makeMatch\(\s*['"]([a-z0-9-]+)['"]\s*,\s*(?:['"]([a-z0-9-]+)['"]|null)/g)]
const broken = []
for (const [, slug, anchor] of matches) {
  if (!valid.has(slug) || (anchor && !valid.get(slug).has(anchor))) {
    broken.push(`${slug}#${anchor || ''}`)
  }
}

if (broken.length) {
  console.error('check-guides-and-quest: FAIL — broken guide chapter links:', broken)
  process.exit(1)
}

const auditedScreens = [
  'src/screens/Guides.tsx',
  'src/screens/GuidesStudio.tsx',
  'src/screens/QuestGame.tsx',
  'src/screens/Practice.tsx',
  'src/screens/AnswerConflictsAdmin.tsx',
]
for (const rel of auditedScreens) {
  const src = fs.readFileSync(path.join(webRoot, rel), 'utf8')
  const stripped = src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '')
  if (stripped.includes('dangerouslySetInnerHTML')) {
    console.error(`check-guides-and-quest: FAIL — dangerouslySetInnerHTML found in ${rel}`)
    process.exit(1)
  }
}

console.log(
  `check-guides-and-quest: OK — ${seed.length} guides, ${matches.length} chapter routes verified, 0 stray LaTeX, 0 raw HTML.`,
)
