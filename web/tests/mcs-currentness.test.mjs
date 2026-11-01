import {test} from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import ts from 'typescript'
import {build} from 'esbuild'
import {createRequire} from 'node:module'

const require=createRequire(import.meta.url)

async function load(name){
 const source=await fs.readFile(new URL('../src/lib/'+name+'.ts',import.meta.url),'utf8')
 const output=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText
 return import('data:text/javascript;base64,'+Buffer.from(output).toString('base64'))
}

const {revisionNoteFor,questionCurrentness,revisionNotes}=await load('questionCurrentness')
const cases=[
 ['rail','Consider the following statements regarding the new railway line in Mizoram: it connects Bairabi with Sairang.',2025,'mcs-bairabi-sairang-2025'],
 ['healthcare','Consider the following statements regarding the Mizoram Universal HealthCare Scheme (MUHCS).',2025,'mcs-muhcs-policy-2025'],
 ['sdg','Which district in Mizoram ranked highest in NITI Aayog second edition of the North Eastern Region District SDG Index 2023-24?',2025,'mcs-ner-sdg-index-2025'],
 ['ullas','Mizoram was recently declared India’s first fully literate state under the ULLAS initiative.',2025,'mcs-ullas-literacy-2025'],
 ['unfpa',"What is the core message of the United Nations Population Fund's State of World Population Report 2025?",2025,'mcs-unfpa-swp-2025'],
 ['football','Which city hosted 2023 Hero Tri-Nation International Football Tournament?',2023,'mcs-hero-trination-imphal-2023'],
]

test('MCS current-affairs notes match only their bounded question and exam year',()=>{
 for(const [,question,year,id] of cases){
  const note=revisionNoteFor(question,year,'2026-11-01')
  assert.equal(note?.id,id)
  assert.equal(questionCurrentness(question,'General Studies',year)?.update?.id,id)
 }
})

test('nearby topics and wrong exam years do not inherit an MCS revision note',()=>{
 for(const [,question,year] of cases)assert.equal(revisionNoteFor(question,year+1,'2026-11-01'),null)
 assert.equal(revisionNoteFor('New railway line in Mizoram connects Bairabi with Hortoki.',2025,'2026-11-01'),null)
 assert.equal(revisionNoteFor('Which district ranked highest in a Mizoram SDG index?',2025,'2026-11-01'),null)
 assert.equal(revisionNoteFor('Mizoram was declared fully literate under ULLAS.',2025,'2026-11-01'),null)
 assert.equal(revisionNoteFor('Which of the following best describes Operation Black Forest carried out in 2025?',2025,'2026-11-01'),null)
})

test('MCS notes stay hidden before source check and expire as dated editorial material',()=>{
 for(const [,question,year,id] of cases){
  const note=revisionNoteFor(question,year,'2026-10-31')
  assert.equal(note,null,id)
  assert.equal(revisionNoteFor(question,year,'2027-02-01')?.stale,true,id)
 }
})

test('MCS notes contain dated references and no answer or scoring fields',()=>{
 const ids=new Set(cases.map(([, , ,id])=>id))
 const notes=revisionNotes.filter(note=>ids.has(note.id))
 assert.equal(notes.length,cases.length)
 for(const note of notes){
  assert.equal(note.checkedOn,'2026-11-01')
  assert.match(note.effectiveOn,/^\d{4}-\d{2}-\d{2}$/)
  assert.equal(note.reviewBy,'2027-02-01')
  assert.match(note.reference.url,/^https:\/\//)
  assert.ok(note.note.length>=80 && note.note.length<=650)
  assert.ok(note.revisionHint.length<=150)
  for(const field of ['answer_index','answerIndex','answerSource','verified','scorable'])assert.equal(field in note,false)
 }
})

const built=await build({stdin:{contents:`import React from 'react';import {renderToStaticMarkup} from 'react-dom/server';import Currentness from './components/QuestionCurrentness';export const render=(props)=>renderToStaticMarkup(React.createElement(Currentness,props));`,resolveDir:new URL('../src/',import.meta.url).pathname,loader:'tsx'},bundle:true,platform:'node',format:'cjs',jsx:'automatic',write:false,logLevel:'silent'})
const compiled={exports:{}}
new Function('require','module','exports',built.outputFiles[0].text)(require,compiled,compiled.exports)
const {render}=compiled.exports

test('MCS source-backed note contents remain behind the answer reveal gate',()=>{
 for(const [,question,year,id] of cases){
  const update=revisionNotes.find(note=>note.id===id)
  const hidden=render({question,year,topic:'General Studies'})
  assert.match(hidden,/Check or show the answer/)
  const sourceUrl=update.reference.url.split('?')[0]
  const sourcePath=new RegExp(sourceUrl.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'))
  assert.doesNotMatch(hidden,sourcePath)
  assert.doesNotMatch(hidden,new RegExp(update.note.slice(0,25).replace(/[.*+?^${}()|[\]\\]/g,'\\$&')))
  const shown=render({question,year,topic:'General Studies',revealed:true})
  assert.match(shown,new RegExp(update.note.slice(0,25).replace(/[.*+?^${}()|[\]\\]/g,'\\$&')))
  assert.match(shown,sourcePath)
  assert.match(shown,/does not verify or replace the stored answer/)
 }
})
