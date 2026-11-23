#!/usr/bin/env node
/** Phase V.22 verification checks (§VIII.6) — the admin console's navigation truth.
 *
 *  Before V.22, `AdminNavigation.tsx` kept its own hardcoded group list against the
 *  manifest in `lib/adminNavigation.ts`. The two drifted, and eleven of thirty-seven
 *  sections became unreachable from the sidebar — including `edit`, the keyboard
 *  authoring console. Nothing failed; the sections simply could not be found.
 *
 *  These checks make that regression loud:
 *   1. The sidebar derives its groups from ADMIN_GROUPS, not from a local list
 *   2. Every section's group is a declared group (or `start`)
 *   3. Every declared group contains at least one section
 *   4. Every section id is dispatched by BankAdmin.tsx
 *   5. One addressing scheme: adminTabHref never emits /admin/ops or /admin/users
 *   6. No dead /admin/<section> links anywhere in web/src
 *   7. The dead `adminNavigation()` helper and the `papers` twin stay deleted
 */

const fs = require('node:fs')
const path = require('node:path')
const assert = require('node:assert/strict')

const root = path.resolve(__dirname, '..')
const read = (p) => fs.readFileSync(path.join(root, p), 'utf8')

const manifest = read('src/lib/adminNavigation.ts')
const sidebar = read('src/components/AdminNavigation.tsx')
const console_ = read('src/screens/BankAdmin.tsx')

const sections = [...manifest.matchAll(/^ \['([a-z0-9-]+)','([^']+)','([a-z]+)','([a-z]+)'/gm)]
  .map(([, id, label, group, minRole]) => ({ id, label, group, minRole }))
// Parse inside the ADMIN_GROUPS block only: a group id and a section id may coincide.
const groupsBlock = manifest.slice(
  manifest.indexOf('export const ADMIN_GROUPS'),
  manifest.indexOf('export const ADMIN_SECTIONS'),
)
const groups = [...groupsBlock.matchAll(/\['([a-z-]+)','([^']+)'\]/g)].map(([, id]) => id)

assert.ok(sections.length >= 30, `expected the full section manifest, parsed ${sections.length}`)
assert.ok(groups.length === 4, `expected four job groups, parsed ${groups.length}: ${groups}`)

// 1. The sidebar must not reintroduce a local group list.
assert.match(sidebar, /ADMIN_GROUPS/, 'AdminNavigation.tsx must derive groups from ADMIN_GROUPS')
assert.doesNotMatch(
  sidebar,
  /const GROUPS\s*:/,
  'AdminNavigation.tsx declares its own GROUPS again — that is the V.22 regression',
)

// 2 & 3. Groups and sections must agree in both directions.
const known = new Set([...groups, 'start'])
const orphans = sections.filter((s) => !known.has(s.group))
assert.equal(orphans.length, 0, `sections in no declared group: ${orphans.map((s) => s.id)}`)
const empty = groups.filter((g) => !sections.some((s) => s.group === g))
assert.equal(empty.length, 0, `declared groups with no sections: ${empty}`)

// 4. Every section must actually render.
const undispatched = sections.filter((s) => !console_.includes(`'${s.id}'`))
assert.equal(undispatched.length, 0, `sections the console never renders: ${undispatched.map((s) => s.id)}`)

// 5. One addressing scheme.
const href = manifest.slice(manifest.indexOf('export function adminTabHref'))
assert.doesNotMatch(href, /'\/admin\/'\+tab/, 'adminTabHref must not emit the legacy /admin/<tab> aliases')

// 6. No dead /admin/<section> links: only /admin/bank is a real path.
const dead = []
for (const file of walk(path.join(root, 'src'))) {
  const text = fs.readFileSync(file, 'utf8')
  for (const [, target] of text.matchAll(/to="(\/admin\/[a-z-]+)"/g)) {
    if (target !== '/admin/bank') dead.push(`${path.relative(root, file)} -> ${target}`)
  }
}
assert.equal(dead.length, 0, `dead admin links (only /admin/bank is routed):\n  ${dead.join('\n  ')}`)

// 7. Deletions stay deleted.
assert.doesNotMatch(manifest, /export function adminNavigation\b/, 'the dead adminNavigation() helper is back')
assert.equal(sections.filter((s) => s.id === 'papers').length, 0, 'the `papers` twin of `exams` is back')

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) return walk(full)
    return /\.tsx?$/.test(entry.name) ? [full] : []
  })
}

console.log(
  `check-admin-nav: OK — ${sections.length} sections across ${groups.length} job groups, all reachable and dispatched.`,
)
