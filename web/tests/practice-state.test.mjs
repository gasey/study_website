import {test} from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import ts from 'typescript'
const source=await fs.readFile(new URL('../src/lib/practiceState.ts',import.meta.url),'utf8')
function harness(load){
 let scope='mizoram-recruitment',generation=1
 const modules={'./api':{loadPracticeStates:load},'./examScope':{currentExamScope:()=>scope},'./accountContext':{accountGeneration:()=>generation}}
 const output=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText
 const module={exports:{}}
 new Function('require','module','exports',output)(name=>modules[name],module,module.exports)
 return {...module.exports,change:()=>generation++,focus:()=>scope='all'}
}
const response=items=>({items:items.map(i=>({...i,viewed:false,answer:null}))})
test('visible cards share a bounded private read with exact paper mapping and no persistent cache',async()=>{
 const calls=[]
 const h=harness(async items=>{calls.push(items);return response(items)})
 const requests=Array.from({length:105},(_,i)=>({question_id:'q'+i,paper_id:'p'+i}))
 const states=await Promise.all(requests.map(i=>h.getPracticeState(i.question_id,i.paper_id)))
 assert.deepEqual(calls.map(c=>c.length),[100,5])
 assert.deepEqual(states.map(s=>s.paper_id),requests.map(s=>s.paper_id))
 await h.getPracticeState('q0','p0');assert.equal(calls.length,3)
})
test('identity changes reject private reads both before dispatch and during the response',async()=>{
 let resolve,called=0
 const h=harness(items=>{called++;return new Promise(r=>resolve=()=>r(response(items)))})
 const first=h.getPracticeState('q');h.change()
 await assert.rejects(first,/changed/);assert.equal(called,0)
 const second=h.getPracticeState('q');await Promise.resolve();h.change();resolve()
 await assert.rejects(second,/changed/)
})
test('scope changes cannot return a result from a prior focus and failures reject every waiting card',async()=>{
 const h=harness(async()=>{throw new Error('Read unavailable')})
 const first=h.getPracticeState('q');h.focus();await assert.rejects(first,/changed/)
 const reads=[h.getPracticeState('q1'),h.getPracticeState('q2')]
 const result=await Promise.allSettled(reads)
 assert.ok(result.every(r=>r.status==='rejected'&&r.reason.message==='Read unavailable'))
})

test('a reveal-triggered restoration gets a fresh generation and always settles reading mode',async()=>{
 // Exercise the component's actual async restore callback with its state/API
 // boundaries stubbed. A reused effect token left this flow loading forever.
 const file=await fs.readFile(new URL('../src/components/PracticeAnswerPanel.tsx',import.meta.url),'utf8')
 const ast=ts.createSourceFile('panel.tsx',file,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX)
 let restore
 function find(node){if(ts.isFunctionDeclaration(node)&&node.name?.text==='restore')restore=node;ts.forEachChild(node,find)}
 find(ast);assert.ok(restore)
 const body=ts.transpileModule(restore.getText(ast),{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.None}}).outputText
 const generation={current:1},events=[]
 const callbacks={current:{onViewed:v=>events.push(['viewed',v]),onBusy:v=>events.push(['busy',v])}}
 const names=['generation','callbacks','getPracticeState','qid','paperId','live','run','setRestoring','setViewed','setRestricted','setError','setDeadline','setNow']
 let calls=0
 const fn=new Function(...names,body+';return restore')(
  generation,callbacks,async()=>{calls++;return {viewed:true,answer:{answer_text:'Example'},retry_after_seconds:120}},'q','p',true,1,
  value=>events.push(['restoring',value]),value=>events.push(['answer',value]),()=>{},()=>{},()=>{},()=>{})
 await fn()
 generation.current++ // Show answer invalidates the initial read generation.
 await fn() // Its refresh event must not reuse the original effect's token.
 assert.equal(calls,2)
 assert.equal(events.filter(([key,value])=>key==='restoring'&&value===false).length,2)
 assert.equal(events.filter(([key,value])=>key==='viewed'&&value===true).length,2)
 assert.deepEqual(events.at(-1),['busy',false])
})
