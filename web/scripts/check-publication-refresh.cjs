// Disposable renderer: terminal publication refreshes lists without resetting an open editor.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const{create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
const listeners=new Map(),timers=new Map();let timerId=0,events=0;
global.CustomEvent=class{constructor(type,init){this.type=type;this.detail=init?.detail}};
global.window={setTimeout(fn){timers.set(++timerId,fn);return timerId},clearTimeout(id){timers.delete(id)},matchMedia:()=>({matches:true}),addEventListener(n,f){if(!listeners.has(n))listeners.set(n,new Set());listeners.get(n).add(f)},removeEventListener(n,f){listeners.get(n)?.delete(f)},dispatchEvent(e){events++;for(const fn of listeners.get(e.type)||[])fn(e)}};
global.document={visibilityState:'visible'};global.crypto=require('node:crypto').webcrypto;
let lastListURL='',refreshWorkbench=()=>{},pulseMode=false,pulseRevision='one',pulsePending=1,pulseCalls=0;
let pub='exported',verification='matched',answerStatus='verified',listCalls=0,inspectCalls=0;
let params=new URLSearchParams({tab:'questions',answer_status:'needs-review',question:'q1',appearance:'a1'});
const row={id:'q1',type:'mcq',question:'Example',answer_status:'needs-review',status:'live',subject_id:'english'};
const snapshot={record:{id:'a1',paperId:'p1',type:'mcq',question:'Example',options:['A','B'],answerIndex:0,answerSource:'derived'},paper:{id:'p1',title:'Example'}};
async function request(url){
 if(url==='/contributions/c1')return{state:pub==='applied'?'published':'publishing',publications:[{id:'pub1',state:pub,error:pub==='failed'?'Bank snapshot changed since review export':null}]};
 if(url==='/admin/bank/publication-pulse'){pulseCalls++;return{revision:pulseRevision,pending:pulsePending}};
 if(url.includes('/verification'))return{status:verification,differences:[],checked_at:new Date().toISOString(),question_state:'live',answer_status:answerStatus};
 if(url.includes('/inventory/exams'))return{items:[]};
 if(url.startsWith('/admin/bank/questions?')){lastListURL=url;listCalls++;return{items:pub==='applied'&&answerStatus==='verified'?[]:[row],total:pub==='applied'&&answerStatus==='verified'?0:1,task_counts:{publishing:pulseMode?pulsePending:0}}};
 if(url.includes('/inspect?')){inspectCalls++;return{canonical:row,snapshot,appearances:[],appearance_total:1,appearance_offset:0,proposals:[],luna_draft:null}};
 throw Error('Unexpected request '+url);
}
const cache=new Map();function load(file){if(cache.has(file))return cache.get(file);const m={exports:{}};const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(m,m.exports,id=>{
  if(id==='react-router-dom')return{Link:({children,...p})=>React.createElement('a',p,children),useSearchParams:()=>[params,next=>{params=typeof next==='function'?next(params):next;refreshWorkbench()}]};
  if(id==='../lib/review')return{reviewRequest:request,stateLabel:s=>s};
  if(id==='./AdminAnswerDecision'||id==='./InlineQuestionCorrection')return{default:()=>React.createElement('textarea',{'aria-label':'Open draft',defaultValue:'Unsaved working text'})};
  if(id==='./SourceQuestionText')return{SourceQuestionText:({text})=>React.createElement('span',null,text),SourceQuestionContext:()=>null};
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(fs.existsSync(base+'.tsx')?base+'.tsx':base+'.ts')}
  return wr(id);
 });cache.set(file,m.exports);return m.exports;
}
const Progress=load(root+'/web/src/components/AdminReviewProgress.tsx').default,Workbench=load(root+'/web/src/components/AdminQuestionWorkbench.tsx').default;
const receipt={state:'publishing',contribution_id:'c1',publication_id:'pub1',questionId:'q1',label:'Decision'};
let tree,progress;const text=()=>JSON.stringify(progress.toJSON());
async function tick(){const fn=[...timers.values()].at(-1);timers.clear();await act(async()=>{await fn?.()})}
(async()=>{
 await act(async()=>{tree=create(React.createElement(Workbench,{taxonomy:[],grants:[{role:'owner',subject_id:null}],onHold(){}}))});
 refreshWorkbench=()=>tree.update(React.createElement(Workbench,{taxonomy:[],grants:[{role:'owner',subject_id:null}],onHold(){}}));
 const draft=tree.root.findAllByType('textarea')[0];assert.ok(draft);assert.equal(listCalls,1);assert.equal(inspectCalls,1);
 await act(async()=>{progress=create(React.createElement(Progress,{receipt}))});assert.equal(events,0);assert.ok(text().includes('waiting for bank publication'));
 pub='applied';await tick();assert.equal(events,1);assert.equal(listCalls,2);assert.equal(inspectCalls,1);assert.equal(tree.root.findAllByType('textarea')[0],draft);assert.ok(JSON.stringify(tree.toJSON()).includes('No questions match'));
 const recheck=progress.root.findAllByType('button').find(b=>b.children.join('').includes('Recheck'));
 await act(async()=>{recheck.props.onClick()});assert.equal(events,1,'Rechecking same publication must not loop-refresh');
 await act(async()=>progress.unmount());pub='failed';await act(async()=>{progress=create(React.createElement(Progress,{receipt}))});assert.equal(events,1);assert.ok(text().includes('save a fresh decision'));
 await act(async()=>progress.unmount());pub='applied';answerStatus='needs-review';await act(async()=>{progress=create(React.createElement(Progress,{receipt}))});assert.ok(text().includes('answer still needs review'));
 const sourceTask=tree.root.findAllByType('button').find(b=>b.findAllByType('span').some(s=>s.children.join('')==='Source / scoring problems'));
 await act(async()=>sourceTask.props.onClick());assert.equal(params.get('review_task'),'source');assert.ok(lastListURL.includes('review_task=source'));assert.equal(params.has('question'),false);
 await act(async()=>{progress.unmount();tree.unmount()});assert.equal(listeners.get('ism-content-change')?.size,0);
 pub='exported';pulseMode=true;params=new URLSearchParams({tab:'questions',question:'q1',appearance:'a1'});
 await act(async()=>{tree=create(React.createElement(Workbench,{taxonomy:[],grants:[{role:'owner',subject_id:null}],onHold(){}}))});
 const pulseDraft=tree.root.findAllByType('textarea')[0],beforeLists=listCalls,beforeInspects=inspectCalls;
 await tick();assert.equal(pulseCalls,1);assert.equal(listCalls,beforeLists);
 await tick();assert.equal(pulseCalls,2);assert.equal(listCalls,beforeLists,'Unchanged lightweight pulse must not run the bank list query');
 pulseRevision='two';pulsePending=0;await tick();assert.equal(listCalls,beforeLists+1);assert.equal(inspectCalls,beforeInspects);assert.equal(tree.root.findAllByType('textarea')[0],pulseDraft);
 await act(async()=>tree.unmount());
 console.log('Publication refresh checks passed: pending/applied/failed, one-time notification, actual answer state, list count and editor preservation.');
})().catch(e=>{console.error(e);process.exitCode=1});
