#!/usr/bin/env node
/**
 * Every in-app link target must resolve to a declared route in App.tsx, and
 * every siteMap.ts destination must too.
 *
 * Phase V.14 consolidated the route table from ~88 paths to 37 without
 * retargeting the links pointing at the removed ones. That shipped 93 dead
 * references to production, including the whole desktop nav and the Topic
 * Trail creation flow. A manifest that *can* silently point at deleted routes
 * eventually will, so this is a check and not a convention.
 *
 * The first version of this script matched only `to="/x"`, `to={'/x'}` and a
 * literal `navigate('/x')`. It therefore passed while three dead navigations
 * survived in TopicTrail.tsx, because that file aliases the hook
 * (`const nav = useNavigate()`). A checker with a silent hole is worse than no
 * checker, so it now resolves the hook's local alias per file and reads string
 * literals out of arbitrary `to={...}` expressions.
 *
 * Pure static analysis — needs no renderer, no DOM and no argv. Run with:
 *   node scripts/check-dead-links.cjs
 */
const fs = require('fs')
const path = require('path')

const SRC = path.join(__dirname, '..', 'src')
const PUBLIC = path.join(__dirname, '..', 'public')

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const full = path.join(dir, e.name)
    return e.isDirectory() ? walk(full) : /\.tsx?$/.test(e.name) ? [full] : []
  })
}

const app = fs.readFileSync(path.join(SRC, 'App.tsx'), 'utf8')
const routes = [...app.matchAll(/path="([^"]*)"/g)].map((m) => m[1]).filter((r) => r !== '*')

const matchers = routes.map((r) => {
  const body = r
    .split('/')
    .filter(Boolean)
    .map((seg) =>
      // `/x/*` is a splat: it matches `/x` and anything below it.
      seg === '*' ? '(?:/.*)?' : seg.startsWith(':') ? (seg.endsWith('?') ? '(?:/[^/]+)?' : '/[^/]+') : '/' + seg.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'),
    )
    .join('')
  return new RegExp('^' + (body || '/') + '$')
})

function live(target) {
  const p = target.split('?')[0].split('#')[0]
  if (p.endsWith('.html')) return fs.existsSync(path.join(PUBLIC, p))
  // `/api/...` is the backend, not a client route.
  if (p === '/api' || p.startsWith('/api/')) return true
  if (p === '/') return true
  // A dynamic tail (`/bank/${id}`, `'/contributions/'+id`) ends in a slash;
  // substitute one segment so it is checked against the parameterised route
  // rather than against its own truncated prefix.
  const probe = p.endsWith('/') ? p + 'x' : p
  return matchers.some((m) => m.test(probe))
}

/** Local names bound to useNavigate() in this file, e.g. `const nav = useNavigate()`. */
function navigateAliases(src) {
  const names = new Set(['navigate'])
  // Any identifier assigned from the hook, including inside a destructuring
  // chain such as `const {id}=useParams(),nav=useNavigate()` — which a
  // `const\s+` anchor misses, and which is exactly where three dead
  // navigations survived the first sweep.
  for (const m of src.matchAll(/([A-Za-z_$][\w$]*)\s*=\s*useNavigate\s*\(/g)) names.add(m[1])
  return [...names]
}

/** String literals and template-literal static prefixes that look like routes. */
function targetsIn(expr) {
  const out = []
  for (const m of expr.matchAll(/'(\/[^'`]*)'|"(\/[^"`]*)"/g)) {
    const before = expr.slice(0, m.index).trimEnd()
    // `'/exams/' + id + '/mock?' + qs` — only the first piece is a target;
    // the rest are fragments. And a path compared, not navigated to
    // (`pathname.startsWith('/library/')`), is not a link either.
    if (before.endsWith('+')) continue
    if (/(?:startsWith|endsWith|includes|test|match|indexOf)\($/.test(before)) continue
    if (/[=!]==?$/.test(before)) continue
    out.push(m[1] || m[2])
  }
  // `` `/exams/${id}` `` -> check the static prefix `/exams/`. Only the first
  // template per expression: nested templates (a ternary inside an
  // interpolation) yield fragments like `/mock?`, not real targets.
  const tpl = expr.match(/`(\/[^`$]*)(?:\$\{|`)/)
  if (tpl && tpl[1]) out.push(tpl[1])
  return out
}

const dead = []
for (const file of walk(SRC)) {
  const rel = path.relative(SRC, file)
  const src = fs.readFileSync(file, 'utf8')
  const navCall = new RegExp('\\b(?:' + navigateAliases(src).join('|') + ')\\(\\s*([\'"`][^)]*)', 'g')
  src.split('\n').forEach((line, i) => {
    const found = []
    // to="/x" | to={ ...any expression... } | href=...
    for (const m of line.matchAll(/(?:to|href)="(\/[^"]*)"/g)) found.push(m[1])
    for (const m of line.matchAll(/(?:to|href)=\{([^}]*(?:\}[^}]*)??)\}/g)) found.push(...targetsIn(m[1]))
    for (const m of line.matchAll(navCall)) found.push(...targetsIn(m[1]))
    // Route strings held in label/path tuples — `[['Rewards','/rewards'], …]`
    // mapped to <Link to={href}>. The path never appears next to a `to=`, so
    // the scans above cannot see it; two dead links hid here.
    for (const m of line.matchAll(/\[\s*'[^']{2,60}'\s*,\s*'(\/[^']*)'\s*\]|\[\s*'(\/[^']*)'\s*,\s*'[^']{2,60}'\s*\]/g)) found.push(m[1] || m[2])
    for (const t of new Set(found)) if (!live(t)) dead.push(`${rel}:${i + 1}  ${t}`)
  })
}

const manifest = fs.readFileSync(path.join(SRC, 'lib', 'siteMap.ts'), 'utf8')
for (const m of manifest.matchAll(/path: '([^']+)'/g)) {
  if (!live(m[1])) dead.push(`lib/siteMap.ts  ${m[1]}  (manifest destination)`)
}

if (dead.length) {
  console.error(`check-dead-links: ${dead.length} link target(s) resolve to no route\n`)
  dead.forEach((d) => console.error('  ' + d))
  console.error(`\n${routes.length} routes declared in App.tsx.`)
  process.exit(1)
}
console.log(`check-dead-links: OK — every link resolves against ${routes.length} declared routes.`)
