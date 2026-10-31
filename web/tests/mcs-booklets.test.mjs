import {test} from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import ts from 'typescript'
const source=await fs.readFile(new URL('../src/lib/mcsBooklets.ts',import.meta.url),'utf8')
const output=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText
const {groupMcsBooklets,bookletLabel}=await import('data:text/javascript;base64,'+Buffer.from(output).toString('base64'))
const paper=(year,section_path,series)=>({id:`MCS Combined ${year} Preliminary Exam Paper-${section_path==='gs'?'I':'II'} Series '${series}'..pdf`,year,section_path,title:'Original source',questions:100,scorable:98})
test('groups year and source role while retaining every independent booklet',()=>{
 const papers=[paper(2023,'gs','B'),paper(2025,'aptitude','A'),paper(2025,'gs','D'),paper(2023,'gs','A')]
 const before=JSON.stringify(papers),groups=groupMcsBooklets(papers)
 assert.deepEqual(groups.map(g=>g.id),['2025:I','2025:II','2023:I'])
 assert.equal(groups[2].papers.length,2)
 assert.equal(bookletLabel(groups[2].papers[0]),'Series A')
 assert.equal(groups.flatMap(g=>g.papers).length,papers.length)
 assert.equal(JSON.stringify(papers),before)
})
test('unidentified source roles and missing years are never grouped by assumption',()=>{
 const a={...paper(2025,'gs','A'),section_path:null},b={...paper(2025,'gs','B'),section_path:null}
 assert.equal(groupMcsBooklets([a,b]).length,2)
 assert.equal(groupMcsBooklets([{...a,year:null},{...b,year:null}]).length,2)
 assert.equal(bookletLabel({...a,id:'Recovered Series-A Chase copy.pdf'}),'Series A')
 assert.deepEqual(groupMcsBooklets([]),[])
})
