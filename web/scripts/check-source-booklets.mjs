import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {createRequire} from 'node:module'
const require=createRequire(new URL('../package.json',import.meta.url)),ts=require('typescript'),mod={exports:{}}
new Function('module','exports',ts.transpileModule(readFileSync(new URL('../src/lib/sourceBooklets.ts',import.meta.url),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText)(mod,mod.exports)
const {groupSourceBooklets,representativeBooklet,sourceBookletIdentity}=mod.exports
const row=(series,extra={})=>({id:`Archive/Exam Paper-I Booklet ${series}..pdf`,year:2025,paper_number:'I',title:'Exam Paper-I',questions:100,...extra})
const papers=['A','B','C','D'].map(s=>row(s)),before=JSON.stringify(papers)
assert.equal(groupSourceBooklets(papers).length,1)
assert.equal(representativeBooklet(groupSourceBooklets(papers)[0]).id,papers[0].id)
assert.equal(JSON.stringify(papers),before)
assert.equal(groupSourceBooklets([row('1'),row('2')]).length,1)
assert.equal(groupSourceBooklets([row('A'),row('B',{year:2024}),row('C',{paper_number:'II'}),row('D',{year:null})]).length,4)
assert.equal(groupSourceBooklets([row('A'),row('B',{id:'Different/Exam Paper-I Booklet B..pdf'})]).length,2)
assert.equal(sourceBookletIdentity(row('A',{id:'Archive/Exam Paper-I.pdf'})),null)
assert.equal(groupSourceBooklets([row('A',{id:'Archive/Exam Paper-I.pdf'}),row('B',{id:'Archive/Exam Paper-II.pdf'})]).length,2)
assert.equal(representativeBooklet(groupSourceBooklets([row('A',{questions:50}),row('B')])[0]).questions,100)
console.log('Booklet grouping passed: letter/numeric variants, intact sources, stable default, fuller-source fallback, separate papers/years/directories and unknown metadata.')
