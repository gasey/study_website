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
const {explanationPresentation}=await load('answerStatus')
const {questionCurrentness,revisionNoteFor,revisionNotes}=await load('questionCurrentness')
test('key provenance and explanation availability remain independent',()=>{
 assert.equal(explanationPresentation(null,'official').status,'missing')
 assert.equal(explanationPresentation('   ','derived',{reviewed:true}).status,'missing')
 assert.equal(explanationPresentation('The source supports this answer.','official',{reviewed:true}).status,'available')
 assert.equal(explanationPresentation('Some working','derived').status,'needs-review')
 assert.equal(explanationPresentation('Checked working','derived',{reviewed:true}).status,'reviewed-solution')
 for(const context of [{disputed:true},{defect:'unresolved-source'},{statusOverride:'needs-review'}])assert.equal(explanationPresentation('Working','derived',{reviewed:true,...context}).status,'needs-review')
})
test('dated notes require context, expire honestly and never provide scoring fields',()=>{
 const q='Shibu Soren who recently passed away in August this year had been Chief Minister of which state?'
 assert.equal(revisionNoteFor(q,2024,'2026-11-01'),null)
 assert.equal(revisionNoteFor(q,null,'2026-11-01'),null)
 assert.equal(revisionNoteFor(q,2025,'2026-10-31'),null)
 assert.equal(revisionNoteFor(q,2025,'2026-11-01').stale,false)
 assert.equal(revisionNoteFor(q,2025,'2027-02-01').stale,true)
 assert.match(questionCurrentness(q,'Current Affairs',2025).reference.url,/newsonair/)
 assert.equal(questionCurrentness('The present perfect tense','English'),null)
 assert.equal(questionCurrentness('Who is the current Chief Minister of Assam?').reference,null)
 for(const note of revisionNotes){
  assert.ok(note.checkedOn<=note.reviewBy)
  assert.match(note.effectiveOn,/^\d{4}-\d{2}-\d{2}$/)
  assert.match(note.reference.url,/^https:\/\//)
  for(const field of ['answer_index','answerIndex','answerSource','verified','scorable'])assert.equal(field in note,false)
 }
})
const built=await build({stdin:{contents:`import React from 'react';import {renderToStaticMarkup} from 'react-dom/server';import Currentness from './components/QuestionCurrentness';import Explanation from './components/QuestionExplanation';export const note=(props)=>renderToStaticMarkup(<Currentness {...props}/>);export const explanation=(props)=>renderToStaticMarkup(<Explanation {...props}/>);`,resolveDir:new URL('../src/',import.meta.url).pathname,loader:'tsx'},bundle:true,platform:'node',format:'cjs',jsx:'automatic',write:false,logLevel:'silent'})
const compiled={exports:{}};new Function('require','module','exports',built.outputFiles[0].text)(require,compiled,compiled.exports)
const {note,explanation}=compiled.exports
test('revision sources and answers are absent from markup before reveal',()=>{
 const props={question:'Shibu Soren who recently passed away in August this year had been Chief Minister of which state?',year:2025,topic:'Current Affairs'}
 const hidden=note(props)
 assert.doesNotMatch(hidden,/Jharkhand|newsonair\.gov|4 August 2025/)
 assert.match(hidden,/Check or show the answer/)
 assert.doesNotMatch(hidden,/<button/)
 const shown=note({...props,revealed:true})
 assert.match(shown,/Jharkhand/);assert.match(shown,/2025-08-04/);assert.match(shown,/2026-11-01/)
 assert.match(shown,/does not verify or replace/)
 const fallback=note({question:'Who is the current governor?',revealed:true})
 assert.match(fallback,/No question-specific dated update/)
})
test('explanation rendering preserves working without claiming an official explanation review',()=>{
 assert.match(explanation({source:'official'}),/Explanation not yet available/)
 const text=explanation({source:'official',explanation:'First step.\nSecond step.'})
 assert.match(text,/First step/);assert.match(text,/Separate review of this explanation is not recorded/)
 assert.doesNotMatch(text,/Reviewed solution working/)
 assert.match(explanation({source:'derived',explanation:'Working',context:{reviewed:true}}),/Reviewed solution working/)
})
test('MCS revision notes stay tied to the original year and distinguish dated references from current claims',()=>{
 const stand='What is the main aim of Stand up India plan recently announced by the Prime Minister?'
 assert.equal(revisionNoteFor(stand,2015),null)
 assert.match(questionCurrentness(stand,'General Studies',2016).update.note,/22 July 2025/)
 const lang='How many languages were initially included in the Indian Constitution?'
 assert.match(questionCurrentness(lang,'Indian Polity',2015).update.note,/original 14/)
 assert.equal(revisionNoteFor(lang,2025),null)
 const bio='The number of Biodiversity Hotspots in the world is'
 assert.match(questionCurrentness(bio,'Environment',2017).update.note,/Not Updated/)
 assert.equal(revisionNoteFor(bio,2018),null)
})
