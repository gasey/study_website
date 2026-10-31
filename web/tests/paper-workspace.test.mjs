import {test} from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import ts from 'typescript'
const source=await fs.readFile(new URL('../src/lib/paperWorkspace.ts',import.meta.url),'utf8')
const output=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText
const {sourcePageUrl,printedQuestionLabel,matchesPaperSearch,loadPaperWorkspace,paperLearningSubjects}=await import('data:text/javascript;base64,'+Buffer.from(output).toString('base64'))
const q={qnum:'73',question:'Who led Jharkhand?',direction:'Choose one option.',passage:'A shared passage about statehood.',options:['Odisha','Jharkhand',null]}
test('paper search covers printed numbers, options, instructions and passages without changing source',()=>{
 for(const term of ['Q73','#73','Question 73','jharkhand','one option','statehood','73'])assert.equal(matchesPaperSearch(q,term),true)
 for(const term of ['Q7','Q730','no matching phrase'])assert.equal(matchesPaperSearch(q,term),false)
 assert.equal(matchesPaperSearch({...q,qnum:'12(a)'},'Q12(a)'),true)
 assert.equal(matchesPaperSearch({...q,qnum:null},'Q1'),false)
 assert.equal(printedQuestionLabel({qnum:null},4),'Item 5')
 assert.equal(printedQuestionLabel({qnum:'12(a)'},4),'Q12(a)')
})
test('PDF links replace old fragments and never invent missing page mapping',()=>{
 assert.equal(sourcePageUrl('/source.pdf#page=9',3),'/source.pdf#page=3')
 for(const page of [null,0,-2,1.5])assert.equal(sourcePageUrl('/source.pdf#page=9',page),'/source.pdf')
})
test('progressive loading preserves every printed appearance even when canonical totals undercount',async()=>{
 const calls=[],updates=[]
 await loadPaperWorkspace(async offset=>{calls.push(offset);return {items:offset===0?['a','b']:offset===2?['c','d']:[],total:3,practice_count:2}},(rows,total)=>updates.push({rows,total}),()=>true,2)
 assert.deepEqual(calls,[0,2,4]);assert.deepEqual(updates.at(-1),{rows:['a','b','c','d'],total:4})
})
test('leaving the paper prevents late publication and additional requests',async()=>{
 let active=true,calls=0,published=false
 await loadPaperWorkspace(async()=>{calls++;active=false;return {items:['a','b'],total:5,practice_count:2}},()=>{published=true},()=>active,2)
 assert.equal(calls,1);assert.equal(published,false)
})
test('a later page failure retains earlier progress and surfaces an error',async()=>{
 const published=[]
 await assert.rejects(loadPaperWorkspace(async offset=>{if(offset)throw Error('offline');return {items:['a','b'],total:3,practice_count:2}},rows=>published.push(rows),()=>true,2),/offline/)
 assert.deepEqual(published,[['a','b']])
})

test('clerical GK combines legacy GK/GS and includes Science while retaining a Science filter',()=>{
 const gs={taxonomy_subject_id:'general-studies',taxonomy_subject:'General Studies',taxonomy_topic:null}
 for(const exam of ['udc','ldc','assistant'])assert.deepEqual(paperLearningSubjects(gs,exam),[{id:'gk-gs',label:'General Knowledge'}])
 assert.deepEqual(paperLearningSubjects(gs,'group-b'),[{id:'gk-gs',label:'GK/GS'}])
 assert.deepEqual(paperLearningSubjects({...gs,taxonomy_subject_id:'science'},'udc'),[{id:'gk-gs',label:'General Knowledge'},{id:'science',label:'Science'}])
 assert.deepEqual(paperLearningSubjects({...gs,taxonomy_topic:'Science in the news'},'ldc'),[{id:'gk-gs',label:'General Knowledge'},{id:'science',label:'Science'}])
 assert.equal(gs.taxonomy_subject_id,'general-studies')
})

test('MCS uses General Studies with nested Science while clerical GK stays distinct',()=>{
 const science={taxonomy_subject_id:'science',taxonomy_subject:'Science',taxonomy_topic:'Physics'}
 assert.deepEqual(paperLearningSubjects(science,'combined-prelims'),[{id:'gk-gs',label:'General Studies'},{id:'science',label:'Science'}])
 assert.deepEqual(paperLearningSubjects(science,'udc'),[{id:'gk-gs',label:'General Knowledge'},{id:'science',label:'Science'}])
})
