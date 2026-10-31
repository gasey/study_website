import {test} from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import ts from 'typescript'
const source=await fs.readFile(new URL('../src/lib/adminNavigation.ts',import.meta.url),'utf8')
const output=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText
const {ADMIN_SECTIONS,adminNavigation,canOpenAdminTab,adminTabHref}=await import('data:text/javascript;base64,'+Buffer.from(output).toString('base64'))
test('owner has five everyday destinations and every legacy tab remains reachable',()=>{
 const n=adminNavigation([{role:'owner',subject_id:null}])
 assert.deepEqual(n.primary.map(s=>s[0]),['overview','questions','retag','workflow','exams'])
 const ids=[...n.primary,...n.more].map(s=>s[0]);assert.equal(new Set(ids).size,21)
 for(const tab of ['papers','intake','publications','review','database','audit','quality','modules'])assert.ok(ids.includes(tab))
 assert.equal(new Set(ADMIN_SECTIONS.map(s=>s[0])).size,ADMIN_SECTIONS.length)
})
test('subject reviewers keep scoped work and do not see global inventory or owner controls',()=>{
 const grants=[{role:'reviewer',subject_id:'english'}],n=adminNavigation(grants)
 assert.deepEqual(n.primary.map(s=>s[0]),['overview','questions','review'])
 for(const id of ['people','rewards','workflow','retag','intake','exams'])assert.equal(canOpenAdminTab(id,grants),false)
 assert.ok(n.more.some(s=>s[0]==='reports'))
 assert.equal(canOpenAdminTab('not-a-tab',grants),false)
 assert.deepEqual(adminNavigation([]),{primary:[],more:[]})
})
test('global inventory reviewers get existing inventory access without owner settings',()=>{
 const grants=[{role:'reviewer',subject_id:null}]
 assert.equal(canOpenAdminTab('retag',grants),true);assert.equal(canOpenAdminTab('exams',grants),true)
 assert.equal(canOpenAdminTab('people',grants),false)
 const url=new URL(adminTabHref('questions'),'https://study.hawayu.in')
 assert.equal(url.pathname,'/admin/bank');assert.equal(url.searchParams.get('answer_status'),'needs-review')
})
