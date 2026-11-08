import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {createRequire} from 'node:module'
const require=createRequire(new URL('../package.json',import.meta.url)),ts=require('typescript'),mod={exports:{}}
new Function('module','exports',ts.transpileModule(readFileSync(new URL('../src/lib/paperArchive.ts',import.meta.url),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText)(mod,mod.exports)
const {sortArchivePapers, paperOrder}=mod.exports
const rows=[{id:'unknown',year:null,exam:'A'},{id:'2026b',year:2026,exam:'B'},{id:'2024a',year:2024,exam:'A'},{id:'2026a',year:2026,exam:'A'}]
const before=JSON.stringify(rows)
assert.deepEqual(sortArchivePapers(rows,'newest').map(p=>p.id),['2026a','2026b','2024a','unknown'])
assert.deepEqual(sortArchivePapers(rows,'oldest').map(p=>p.id),['2024a','2026a','2026b','unknown'])
assert.deepEqual(sortArchivePapers(rows,'exam-asc').map(p=>p.id),['2026a','2024a','unknown','2026b'])
assert.equal(sortArchivePapers(rows,'exam-desc')[0].id,'2026b')
assert.equal(JSON.stringify(rows),before)
assert.equal(paperOrder('invalid'),'newest')
console.log('Archive ordering passed: chronological/name directions, unknown years last, stable ties and immutable input.')
