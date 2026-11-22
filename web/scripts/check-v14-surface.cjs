#!/usr/bin/env node
/** Phase V.14 verification checks (§VII.15).
 *  Verifies:
 *   1. Route count <= 40 in web/src/App.tsx
 *   2. Every §VII.14 Cut route is absent from App.tsx
 *   3. Zero Google Fonts links in web/index.html; self-hosted woff2 fonts exist
 *   4. Single CSS file declaring font-family (web/src/styles/finna.css)
 *   5. Zero text-[Npx] arbitrary font-size classes in web/src
 *   6. tailwind.config.js fontSize has exactly 8 keys
 *   7. Zero `pool=practice` links remaining in web/src
 *   8. Header.tsx / BottomBar.tsx / quickAccess.ts read from siteMap.ts
 *   9. answerStatus.ts handles provisional key -> trusted:false and disputed -> "Answer disputed"
 *  10. api/app/routers/me.py allows essay, letter, precis and comprehension drafts
 */

const fs = require('node:fs')
const path = require('node:path')
const assert = require('node:assert/strict')

const root = path.resolve(__dirname, '../..')
const webSrc = path.join(root, 'web/src')

function walk(dir, exts) {
  const out = []
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) out.push(...walk(full, exts))
    else if (exts.some((ext) => entry.name.endsWith(ext))) out.push(full)
  }
  return out
}

// 1 & 2. Route count <= 40 and Cut routes removed
const appTsx = fs.readFileSync(path.join(webSrc, 'App.tsx'), 'utf8')
const routeCount = (appTsx.match(/<Route\s/g) || []).length
assert.ok(routeCount <= 40, `Expected <= 40 routes, got ${routeCount}`)
const cutRoutes = [
  '"/duel"', '"/important-days"', '"/notifications"', '"/contribute/notifications"',
  '"/revision"', '"/mistakes"', '"/vocabulary"', '"/review"', '"/website-bank"',
  '"/more"', '"/scoring"', '"/tests/make"', '"/exams/:id/*"',
]
for (const cut of cutRoutes) {
  assert.ok(!appTsx.includes(`path=${cut}`), `Cut route ${cut} still declared in App.tsx`)
}

// 3. Self-hosted fonts, no Google Fonts
const indexHtml = fs.readFileSync(path.join(root, 'web/index.html'), 'utf8')
assert.ok(!indexHtml.includes('fonts.googleapis.com'), 'index.html still references fonts.googleapis.com')
assert.ok(!indexHtml.includes('fonts.gstatic.com'), 'index.html still references fonts.gstatic.com')
assert.ok(indexHtml.includes('/fonts/figtree-latin-wght.woff2'), 'index.html missing preload for Figtree woff2')
for (const fontFile of [
  'figtree-latin-wght.woff2',
  'newsreader-latin-wght.woff2',
  'newsreader-latin-wght-italic.woff2',
  'ibm-plex-mono-400.woff2',
  'ibm-plex-mono-500.woff2',
]) {
  const p = path.join(root, 'web/public/fonts', fontFile)
  assert.ok(fs.existsSync(p) && fs.statSync(p).size > 1000, `Missing font file: ${fontFile}`)
}

// 4. Single CSS file declaring font-family
const cssFilesWithFontFamily = []
for (const file of walk(webSrc, ['.css'])) {
  const txt = fs.readFileSync(file, 'utf8')
  if (/\bfont-family\s*:/.test(txt)) {
    cssFilesWithFontFamily.push(path.relative(webSrc, file))
  }
}
assert.deepEqual(cssFilesWithFontFamily, ['styles/finna.css'], `Unexpected font-family files: ${cssFilesWithFontFamily.join(', ')}`)

// 5. Zero text-[Npx] arbitrary font-size classes
const pxOffenders = []
for (const file of walk(webSrc, ['.ts', '.tsx', '.css'])) {
  const txt = fs.readFileSync(file, 'utf8')
  if (/text-\[\d+(?:\.\d+)?px\]/.test(txt)) {
    pxOffenders.push(path.relative(webSrc, file))
  }
}
assert.deepEqual(pxOffenders, [], `Found text-[Npx] in: ${pxOffenders.join(', ')}`)

// 6. Tailwind fontSize has exactly 8 keys
const twCfg = fs.readFileSync(path.join(root, 'web/tailwind.config.js'), 'utf8')
const fontSizeBlock = twCfg.match(/fontSize\s*:\s*\{([\s\S]*?)\n\s*\}/)
assert.ok(fontSizeBlock, 'tailwind.config.js missing theme.fontSize')
const fontSizeKeys = [...fontSizeBlock[1].matchAll(/^\s*['"]?([a-z0-9-]+)['"]?\s*:/gm)].map((m) => m[1])
assert.equal(fontSizeKeys.length, 8, `Expected 8 fontSize keys, got ${fontSizeKeys.length}: ${fontSizeKeys.join(', ')}`)

// 7. Zero pool=practice in web/src
const poolPracticeFiles = []
for (const file of walk(webSrc, ['.ts', '.tsx'])) {
  const txt = fs.readFileSync(file, 'utf8')
  if (txt.includes('pool=practice')) poolPracticeFiles.push(path.relative(webSrc, file))
}
assert.deepEqual(poolPracticeFiles, [], `Found pool=practice in: ${poolPracticeFiles.join(', ')}`)

// 8. Navigation surfaces import from siteMap.ts
for (const navFile of ['components/Header.tsx', 'lib/navigation.ts', 'lib/quickAccess.ts', 'components/Footer.tsx']) {
  const txt = fs.readFileSync(path.join(webSrc, navFile), 'utf8')
  assert.ok(txt.includes('siteMap'), `${navFile} does not import from siteMap`)
}

// 9. answerStatus.ts provenance contract
const answerStatusTs = fs.readFileSync(path.join(webSrc, 'lib/answerStatus.ts'), 'utf8')
assert.ok(answerStatusTs.includes("keyStatus==='provisional'"), 'answerStatus.ts missing provisional key check')
assert.ok(answerStatusTs.includes("label:'Answer disputed'"), 'answerStatus.ts missing Answer disputed state')
assert.ok(!answerStatusTs.includes('#8CB89A'), 'answerStatus.ts still has hardcoded hex colours')

// 10. API essay draft guard widened to all 4 descriptive kinds
const mePy = fs.readFileSync(path.join(root, 'api/app/routers/me.py'), 'utf8')
assert.ok(
  mePy.includes("a.essay_kind IN ('essay','letter','precis','comprehension')"),
  'api/app/routers/me.py essay_kind guard not widened to all four kinds',
)

console.log(
  JSON.stringify(
    {
      ok: true,
      routeCount,
      fontSizeKeys,
      cssFilesWithFontFamily,
      checks: 10,
    },
    null,
    2,
  ),
)
