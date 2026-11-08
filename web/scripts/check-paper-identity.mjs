import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {createRequire} from 'node:module'
const require=createRequire(new URL('../package.json',import.meta.url)),ts=require('typescript'),mod={exports:{}}
new Function('module','exports',ts.transpileModule(readFileSync(new URL('../src/lib/paperIdentity.ts',import.meta.url),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText)(mod,mod.exports)
const {paperIdentity}=mod.exports
const paper={id:'archive/General English Paper-I 2026..pdf',title:'Common Competitive Examination · 2026',exam:"Common Competitive Examination for Group B Non-Gazetted (Technical)",paper_label:'Paper I · General English'}
assert.deepEqual(paperIdentity(paper),{title:'Paper I · General English',exam:paper.exam,filename:'General English Paper-I 2026'})
assert.equal(paperIdentity({...paper,paper_label:null}).exam,paper.exam,'generic filename must never hide the exam')
assert.equal(paperIdentity({...paper,paper_label:null}).title,'General English Paper-I 2026')
assert.equal(paperIdentity({...paper,exam:null}).exam,paper.title)
assert.equal(paperIdentity({id:'paper',title:'Paper',exam:'Paper',paper_label:'Paper'}).exam,'','avoid identical headings')
console.log('Paper identity checks passed: printed heading, visible exam identity, filename fallback, no invented exam and duplicate suppression.')
