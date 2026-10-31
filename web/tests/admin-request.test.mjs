import {test} from 'node:test'
import assert from 'node:assert/strict'
import {createServer} from 'vite'
test('admin reads coalesce only while pending and invalidate on writes, content and account changes',async()=>{
 globalThis.window=new EventTarget();const storage=new Map()
 globalThis.localStorage={getItem:k=>storage.get(k)??null,setItem:(k,v)=>storage.set(k,v)}
 const server=await createServer({root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true},appType:'custom'})
 let count=0;const requests=[]
 globalThis.fetch=async(path,options)=>{
  if(path==='/api/auth/session')return Response.json({authenticated:true})
  if(path==='/api/review/session')return Response.json({user_id:'test',csrf:'test',grants:[]})
  if(options.method==='POST')return Response.json({saved:true})
  count++;return new Promise(resolve=>requests.push(()=>resolve(Response.json({count}))))
 }
 try{
  const {reviewRequest}=await server.ssrLoadModule('/src/lib/review.ts')
  const settle=()=>new Promise(resolve=>setImmediate(resolve))
  const a=reviewRequest('/admin/bank/questions'),b=reviewRequest('/admin/bank/questions');await settle();assert.equal(count,1);requests.shift()();await Promise.all([a,b])
  const c=reviewRequest('/admin/bank/questions');await settle();assert.equal(count,2);requests.shift()();await c
  const old=reviewRequest('/admin/bank/questions');await settle()
  await reviewRequest('/admin/bank/anything',{test:true})
  const fresh=reviewRequest('/admin/bank/questions');await settle();assert.equal(count,4);requests.shift()();requests.shift()();await Promise.all([old,fresh])
  const before=reviewRequest('/admin/bank/questions');await settle();window.dispatchEvent(new Event('ism-content-change'))
  const after=reviewRequest('/admin/bank/questions');await settle();assert.equal(count,6);requests.shift()();requests.shift()();await Promise.all([before,after])
  const prior=reviewRequest('/admin/bank/questions');const rejection=assert.rejects(prior,/account changed/);await settle();window.dispatchEvent(new Event('ism-auth-change'))
  const next=reviewRequest('/admin/bank/questions');await settle();assert.equal(count,8);requests.shift()();requests.shift()();await rejection;await next
 }finally{await server.close()}
})
