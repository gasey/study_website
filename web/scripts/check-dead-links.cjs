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
  let p = target.split('?')[0].split('#')[0]
  if (p.endsWith('.html')) return fs.existsSync(path.join(PUBLIC, p))
  if (p !== '/') p = p.replace(/\/$/, '')
  return p === '/' || matchers.some((m) => m.test(p))
}

// `to="/x"`, `to={'/x'}`, `navigate('/x')`. A match followed by `+` is a
// template prefix (`navigate('/results/'+id)`) and is checked as its route.
const LINK = /(?:to|href)="(\/[^"{}]*)"|(?:to|href)=\{'(\/[^'{}]*)'\}|navigate\('(\/[^'{}]*)'/g

const dead = []
for (const file of walk(SRC)) {
  const rel = path.relative(SRC, file)
  fs.readFileSync(file, 'utf8')
    .split('\n')
    .forEach((line, i) => {
      for (const m of line.matchAll(LINK)) {
        const target = m[1] || m[2] || m[3]
        if (line[m.index + m[0].length] === '+' || target.endsWith('/')) continue
        if (!live(target)) dead.push(`${rel}:${i + 1}  ${target}`)
      }
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
