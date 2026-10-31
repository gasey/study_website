import {test} from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import ts from 'typescript'
const source=await fs.readFile(new URL('../src/lib/adminReviewFlow.ts',import.meta.url),'utf8')
const output=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText
const {nextReviewTarget,adminReadCanCoalesce,ADMIN_TAXONOMY_TABS}=await import('data:text/javascript;base64,'+Buffer.from(output).toString('base64'))
test('review advances within the page and across its boundary without skipping a question',()=>{
 const rows=Array.from({length:20},(_,i)=>({id:String(i)}))
 assert.deepEqual(nextReviewTarget(rows,25,0,'18'),{kind:'question',question:rows[19]})
 assert.deepEqual(nextReviewTarget(rows,25,0,'19'),{kind:'page',offset:20})
 assert.equal(nextReviewTarget([{id:'24'}],25,24,'24'),null)
 assert.equal(nextReviewTarget(rows,25,0,'unknown'),null)
 assert.equal(nextReviewTarget([],25,0,'0'),null)
})
test('only matching admin reads can coalesce; unrelated private reads stay independent',()=>{
 for(const p of ['/admin/bank/questions?q=test','/admin/bank/work','/review/session','/review/taxonomy'])assert.equal(adminReadCanCoalesce(p),true)
 for(const p of ['/auth/session','/review/queue','/me','/questions','/admin/bank-other'])assert.equal(adminReadCanCoalesce(p),false)
})
test('taxonomy is deferred on home and work queue but required for classification and grants',()=>{
 for(const tab of ['overview','workflow','reports','publications','exams'])assert.ok(!ADMIN_TAXONOMY_TABS.includes(tab))
 for(const tab of ['questions','retag','review','people','taxonomy'])assert.ok(ADMIN_TAXONOMY_TABS.includes(tab))
})
