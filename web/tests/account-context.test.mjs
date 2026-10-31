import {test} from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import ts from 'typescript'
const events=new EventTarget()
globalThis.window=events
globalThis.location={origin:'https://study.hawayu.in'}
globalThis.localStorage={setItem(){}}
let calls=0
globalThis.fetch=async()=>{calls++;return {ok:true,json:async()=>({authenticated:false,state:'guest'})}}
const source=await fs.readFile(new URL('../src/lib/accountContext.ts',import.meta.url),'utf8')
const output=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText
const m=await import('data:text/javascript;base64,'+Buffer.from(output).toString('base64'))
test('return path preserves exam filters and rejects external destinations and auth loops',()=>{
 assert.equal(m.safeReturnPath('/exams/udc?subject_id=gk-gs#q1'),'/exams/udc?subject_id=gk-gs#q1')
 for(const value of ['https://evil.test','//evil.test','/\\evil.test','/login?next=/join','/join','/path\n',''])assert.equal(m.safeReturnPath(value),'/profile')
})
test('initial session request coalesces and account changes invalidate its generation',async()=>{
 await Promise.all([m.accountContext(),m.accountContext()]);assert.equal(calls,1)
 const before=m.accountGeneration();window.dispatchEvent(new Event('ism-auth-change'))
 assert.equal(m.accountGeneration(),before+1)
 await m.accountContext();assert.equal(calls,2)
})
test('guest and offline responses do not announce session expiry',async()=>{
 let expired=0;window.addEventListener('ism-auth-expired',()=>expired++)
 await m.checkSessionRejected({authenticated:false,state:'guest'});assert.equal(expired,0)
 const previous=globalThis.fetch;globalThis.fetch=async()=>{throw Error('offline')}
 await m.checkSessionRejected({authenticated:true});assert.equal(expired,0)
 globalThis.fetch=async()=>({ok:true,json:async()=>({authenticated:false})})
 await m.checkSessionRejected({authenticated:true});assert.equal(expired,1)
 globalThis.fetch=previous
})
