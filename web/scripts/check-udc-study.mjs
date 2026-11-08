import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
const require = createRequire(new URL('../package.json', import.meta.url))
const ts = require('typescript')
function load(path) {
  const mod = { exports: {} }
  const js = ts.transpileModule(readFileSync(new URL(path, import.meta.url), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText
  new Function('require', 'module', 'exports', js)(id => id==='./studySetLinks'?load('../src/lib/studySetLinks.ts'):require(id), mod, mod.exports)
  return mod.exports
}
const { groupUdcBooklets } = load('../src/lib/udcBooklets.ts')
const { practiceJourneyLink } = load('../src/lib/examJourney.ts')
const booklet = (role, series, extra = {}) => ({
  id: `Old_Questions/Direct_NG_2024-2027/Assistant, UDC Paper-${role} Series ${series}..pdf`,
  year: 2025, paper_number: role, title: 'Assistant / UDC', ...extra,
})
const eight = ['I', 'II'].flatMap(role => ['A', 'B', 'C', 'D'].map(series => booklet(role, series)))
const before = JSON.stringify(eight)
const groups = groupUdcBooklets(eight)
assert.equal(groups.length, 2)
assert.deepEqual(groups.map(group => group.papers.length), [4, 4])
assert.deepEqual(groups.flatMap(group => group.papers.map(p => p.id)), eight.map(p => p.id))
assert.equal(JSON.stringify(eight), before, 'must not mutate source records')
const unrelated = [
  booklet('I', 'A', { id: 'Taxation/UDC Paper-I Series A.pdf' }),
  booklet('I', 'B', { id: 'Fisheries/UDC Paper-I Series B.pdf' }),
  booklet('I', 'C', { year: null }),
  booklet('I', 'D', { paper_number: null }),
  booklet('II', 'A', { year: 2024 }),
]
assert.equal(groupUdcBooklets(unrelated).length, 5, 'unknown/different sittings remain separate')
assert.equal(groupUdcBooklets([eight[2]])[0].papers[0].id, eight[2].id, 'filtered series stays selected')
const base = { checkpoint: null, last_practice: null }
assert.equal(practiceJourneyLink('udc', base), '/exams/udc?view=practice#exam-question-browser')
const resumed = new URL(practiceJourneyLink('udc', { ...base, checkpoint: { state: {
  paper: eight[0].id, subject_id: 'english', offset: 12, pool: 'practice',
  view: 'browse', collection_id: 'group-b-non-gazetted',
} } }), 'https://study.hawayu.in')
assert.equal(resumed.pathname, '/exams/udc')
assert.equal(resumed.searchParams.get('view'), 'practice')
assert.equal(resumed.searchParams.get('paper'), eight[0].id)
assert.equal(resumed.searchParams.get('offset'), '12')
assert.equal(resumed.searchParams.has('collection_id'), false)
const fallback = new URL(practiceJourneyLink('udc', { ...base, last_practice: { paper_id: eight[4].id, section_path: 'past-papers' } }), 'https://study.hawayu.in')
assert.equal(fallback.searchParams.get('paper'), eight[4].id)
const {studySetFilters,studySetLink,nextStudySetLink}=load('../src/lib/studySetLinks.ts')
assert.equal(studySetLink('saved-id'), '/exams/udc?view=practice&session=saved-id#exam-question-browser')
const focused=studySetFilters(new URLSearchParams('subject_id=english&paper=source.pdf&status=wrong&offset=2&collection_id=other&pool=all'))
assert.equal(focused.paper_id,'source.pdf');assert.equal(focused.pool,'practice');assert.equal(focused.study_status,'wrong')
assert.equal(focused.collection_id,undefined)
assert.equal(new URL(nextStudySetLink(focused,10),'https://study.hawayu.in').searchParams.get('offset'),'2')
assert.equal(new URL(nextStudySetLink({...focused,study_status:'all'},10),'https://study.hawayu.in').searchParams.get('offset'),'12')
assert.equal(practiceJourneyLink('udc',{...base,active_study_session:{id:'saved-id'}}),studySetLink('saved-id'))
console.log('UDC study checks passed: booklet identity, department/unknown isolation, filtered series, and collection-scoped resume.')
