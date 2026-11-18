const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path')
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript')
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React}
const {act,create}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}))
const saved=new Map(),events={},docEvents={};let user='student-a',params=new URLSearchParams(),setParams,tree,result,scrolls=[],cardTop=160
const storage={getItem:k=>saved.get(k)||null,setItem:(k,v)=>saved.set(k,v)}
global.localStorage=storage
global.window={setTimeout,clearTimeout,cancelAnimationFrame:clearTimeout,scrollY:1000,innerHeight:800,addEventListener:(n,f)=>events[n]=f,removeEventListener:(n,f)=>{if(events[n]===f)delete events[n]},scrollTo:p=>scrolls.push(p),matchMedia:()=>({matches:false})}
global.requestAnimationFrame=f=>setTimeout(f,0)
global.document={visibilityState:'visible',getElementById:id=>id==='question-q60'?{getBoundingClientRect:()=>({top:cardTop,bottom:cardTop+300})}:id==='exam-question-browser'?{scrollIntoView:()=>scrolls.push('browser')}:null,addEventListener:(n,f)=>docEvents[n]=f,removeEventListener:(n,f)=>{if(docEvents[n]===f)delete docEvents[n]}}
const cache=new Map()
function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};new Function('module','exports','require',ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText)(mod,mod.exports,id=>{
 if(id==='react-router-dom')return {useSearchParams:()=>[params,fn=>setParams(fn)]}
 if(id==='../lib/api')return {getAccountSession:async()=>({authenticated:user!=='guest'})}
 if(id==='../lib/device')return {deviceId:()=> 'this-browser'}
 if(id==='../lib/review')return {reviewSession:async()=>({user_id:user})}
 if(id==='../lib/examScope')return {currentExamScope:()=> 'mizoram-recruitment'}
 if(id.startsWith('.'))return load(path.resolve(path.dirname(file),id)+'.ts')
 return wr(id)
});cache.set(file,mod.exports);return mod.exports}
const memory=load(root+'/web/src/lib/browsePosition.ts'),{useBrowsePosition}=load(root+'/web/src/hooks/useBrowsePosition.ts')
const key=memory.browseStoreKey(user,'udc','mizoram-recruitment')
const query=memory.browseQuery(new URLSearchParams('paper=source.pdf&subject_id=english&offset=50&seed=stable&url=https://evil&answer=secret'))
assert.ok(!query.includes('secret'));assert.ok(!query.includes('evil'))
const position={query,questionId:'q60',top:140,savedAt:Date.now()}
memory.writeBrowsePosition(key,position)
assert.equal(memory.readBrowsePosition(key,new URLSearchParams('view=browse')).questionId,'q60')
assert.equal(memory.readBrowsePosition(key,new URLSearchParams('view=browse&pool=all&order=mixed&seed=new')).questionId,'q60','Default filters or a generated seed do not hide the last reading context')
assert.equal(memory.readBrowsePosition(key,new URLSearchParams('paper=other.pdf')),null)
assert.equal(memory.readBrowsePosition(memory.browseStoreKey('student-b','udc','mizoram-recruitment'),new URLSearchParams()),null)
assert.equal(memory.readBrowsePosition(memory.browseStoreKey(user,'ldc','mizoram-recruitment'),new URLSearchParams()),null)
assert.equal(memory.readBrowsePosition(memory.browseStoreKey(user,'udc','all'),new URLSearchParams()),null)
for(let i=0;i<45;i++)memory.writeBrowsePosition('bounded',{query:'paper='+i,questionId:null,top:0,savedAt:Date.now()+i})
assert.equal(Object.keys(JSON.parse(saved.get('bounded')).entries).length,40)
saved.set('corrupt','{invalid');assert.equal(memory.readBrowsePosition('corrupt',new URLSearchParams()),null)
saved.set('corrupt',JSON.stringify({entries:{bad:null},last:'bad'}));assert.doesNotThrow(()=>memory.writeBrowsePosition('corrupt',position))
const link=new URL(memory.paperBrowseLink('group-b-gazetted','source / I.pdf'),'https://study.hawayu.in')
assert.equal(link.pathname,'/group-b');assert.equal(link.searchParams.get('collection'),'group-b-gazetted');assert.equal(link.searchParams.get('paper'),'source / I.pdf')
assert.equal(link.searchParams.get('order'),'paper','Paper entry explicitly requests source order')
assert.equal(new URLSearchParams(query).get('order'),'paper','Saved paper reading normalizes old mixed URLs to source order')
function Harness({pending,ids=['q60']}){
 const [route,setRoute]=React.useState(params);params=route
 setParams=fn=>setRoute(typeof fn==='function'?fn(params):new URLSearchParams(fn))
 result=useBrowsePosition('udc',true,pending,ids)
 return React.createElement('p',null,result.message)
}
async function mount(pending=true){await act(async()=>{tree?.unmount();tree=create(React.createElement(Harness,{pending}))})}
async function render(pending=false){await act(async()=>tree.update(React.createElement(Harness,{pending})))}
;(async()=>{
 params=new URLSearchParams('view=browse');await mount()
 assert.equal(params.get('offset'),'50');assert.equal(params.get('seed'),'stable');assert.equal(params.get('paper'),'source.pdf');assert.equal(scrolls.length,0,'Wait for fetched matching questions')
 await render();await act(async()=>new Promise(r=>setTimeout(r,10)))
 assert.equal(scrolls.at(-1).top,1020,'Restore the actual question at its saved viewport offset')
 cardTop=190;await act(async()=>events.pagehide())
 assert.equal(memory.readBrowsePosition(key,params).top,190)
 await act(async()=>tree.unmount());tree=null
 params=new URLSearchParams('view=browse');scrolls=[];await mount();await render();await act(async()=>new Promise(r=>setTimeout(r,10)))
 assert.equal(scrolls.at(-1).top,1000,'Reload/re-entry restores the last saved question rather than only the page')
 saved.set('exam-attempts','keep scores')
 await act(async()=>result.startAgain());await render();await act(async()=>new Promise(r=>setTimeout(r,10)))
 assert.equal(params.has('offset'),false);assert.equal(params.has('fresh'),false,'Reset marker is one-shot, future visits can resume')
 assert.equal(saved.get('exam-attempts'),'keep scores')
 assert.equal(params.get('subject_id'),'english','Restart retains the chosen subject and paper')
 await act(async()=>tree.unmount());tree=null
 user='student-b';params=new URLSearchParams('view=browse');await mount()
 assert.equal(params.has('paper'),false,'Another account does not inherit the reader position')
 await act(async()=>tree.unmount());tree=null
 user='guest';params=new URLSearchParams('view=browse');await mount();await render();await act(async()=>events.pagehide());assert.ok([...saved.keys()].some(k=>k.includes('guest-this-browser')),'Guest browsing also saves a place without sign-in');await act(async()=>tree.unmount());tree=null
 storage.setItem=()=>{throw Error('Storage disabled')};assert.equal(memory.writeBrowsePosition(key,position),false)
 console.log('Browse position passed: reload/re-entry, exact question anchor, stable seed, exam/account/scope isolation, one-shot restart, retained scores, bounded/corrupt/unavailable storage and same-module paper links.')
})().catch(e=>{console.error(e);process.exitCode=1})
