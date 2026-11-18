// Actual new screens and saved-player mode with deterministic API adapters.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]})),router=wr('react-router-dom');
const events=new Map();let epoch=0,reads=[],starts=[],saves=[],summaries=[],focuses=[],sets=[];
global.window={location:{origin:'https://fixture.test',search:''},dispatchEvent(e){for(const f of events.get(e.type)||[])f(e)},addEventListener(n,f){if(!events.has(n))events.set(n,new Set());events.get(n).add(f)},removeEventListener(n,f){events.get(n)?.delete(f)}};
global.crypto||=require('node:crypto').webcrypto;global.requestAnimationFrame=()=>1;global.cancelAnimationFrame=()=>{};
const deferred=queue=>(...args)=>new Promise((resolve,reject)=>queue.push({args,resolve,reject}));
const api={getOnboarding:deferred(reads),startOnboarding:deferred(starts),getOnboardingSummary:deferred(summaries),getFocusSubjects:deferred(focuses),saveFocusSubjects:deferred(saves),getStudySet:deferred(sets)};
const stub=()=>null,cache=new Map();function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};cache.set(file,mod.exports);
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(mod,mod.exports,id=>{
  if(id.endsWith('/api'))return api;
  if(id.endsWith('/accountContext'))return {accountGeneration:()=>epoch};
  if(id.endsWith('/StudyQuestionCard'))return {default:p=>React.createElement('div',{'data-collection':p.collectionId},p.q.question)};
  if(id.endsWith('/CuratedWordQuestion')||id.endsWith('/QuestionStudyControls'))return {default:stub};
  if(id.endsWith('/AnswerLayout'))return {AnswerLayoutControl:stub};
  if(id.endsWith('/pagination'))return {scrollToResults:()=>{}};
  if(id.endsWith('/answerStatus'))return {answerFeedbackLabel:()=> 'Checked'};
  if(id.endsWith('/questionBrowse'))return {newQuestionSeed:()=> 'seed'};
  if(id.endsWith('/studySetLinks'))return {studySetFilters:()=>({}),studySetLink:id=>'/exams/udc?session='+id,nextStudySetLink:()=>'/exams/udc'};
  if(id==='react-router-dom')return router;
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(base+(fs.existsSync(base+'.tsx')?'.tsx':'.ts'))}return wr(id);
 });return mod.exports}
const Screen=load(root+'/web/src/screens/Onboarding.tsx').default,Suggestions=load(root+'/web/src/components/OnboardingSuggestions.tsx').default,Player=load(root+'/web/src/components/UdcStudySessions.tsx').default;
let tree;const text=n=>typeof n==='string'?n:(n?.children||[]).map(text).join(''),json=()=>JSON.stringify(tree.toJSON()),button=label=>tree.root.findAllByType('button').find(n=>text(n)===label);
const status={exam:{id:'exam1',title:'Synthetic exam'},session:null,available:true,reason:null},focus={items:[{subject_id:'mizo',label:'Mizo'}],available:[{id:'english',label:'English'},{id:'mizo',label:'Mizo'}],limit:5};
const summary={finished:true,subjects:[{subject_id:'english',label:'English',checked:5,correct:1}],suggested_subject_ids:['english'],basis:'Synthetic checked sample'};
const withRouter=el=>React.createElement(router.MemoryRouter,{initialEntries:['/onboarding']},el);
async function emit(n){if(n==='ism-auth-change')epoch++;await act(async()=>window.dispatchEvent(new Event(n)))}
async function resolve(queue,value){assert.ok(queue.length);await act(async()=>queue.shift().resolve(value))}
(async()=>{
 await act(async()=>{tree=create(withRouter(React.createElement(Screen)))});await resolve(reads,status);
 const oldStart=button('Start 10 questions →').props.onClick;await emit('ism-auth-change');await act(async()=>oldStart());assert.equal(starts.length,0);
 await resolve(reads,{...status,exam:{id:'exam2',title:'New exam'}});await act(async()=>button('Start 10 questions →').props.onClick());assert.equal(starts[0].args[0],'exam2');const key=starts[0].args[1];
 await act(async()=>starts.shift().reject(Error('Temporary failure')));await act(async()=>button('Start 10 questions →').props.onClick());assert.equal(starts[0].args[1],key,'An uncertain retry retains its request key');await emit('ism-auth-change');await resolve(starts,{id:'OLD_PRIVATE_SESSION'});assert.ok(!json().includes('OLD_PRIVATE_SESSION'));await resolve(reads,{...status,available:false,reason:'No eligible pool'});assert.ok(!button('Start 10 questions →')&&json().includes('No eligible pool'));
 await act(async()=>{tree.unmount();tree=create(React.createElement(Suggestions,{sid:'s1'}))});await resolve(summaries,summary);await resolve(focuses,focus);
 assert.equal(saves.length,0,'Suggestions never auto-apply');let boxes=tree.root.findAllByType('input');assert.equal(boxes[0].props.checked,false);assert.equal(boxes[1].props.checked,true);
 await act(async()=>boxes[0].props.onChange({target:{checked:true}}));await act(async()=>button('Save selected focus subjects').props.onClick());assert.deepEqual(saves[0].args[0],['mizo','english']);await resolve(saves,{});assert.ok(json().includes('Your selected focus subjects are saved.'));
 const staleSave=button('Save selected focus subjects').props.onClick;await emit('ism-auth-change');await act(async()=>staleSave());assert.equal(saves.length,0);assert.ok(!json().includes('English'));
 await resolve(summaries,{...summary,subjects:[],suggested_subject_ids:[]});await resolve(focuses,{items:[],available:[],limit:5});assert.ok(json().includes('No currently eligible checked answers'));assert.ok(button('Save selected focus subjects').props.disabled);
 const session={id:'s',kind:'practice',collection_id:'actual-exam',position:0,version:1,total:1,requested_size:10,finished_at:null,filters:{onboarding_version:1,exam_title:'Actual synthetic exam'},question_ids:['q'],items:[{id:'q',question:'Synthetic check-in item',options:['A','B']}],results:{},viewed_ids:[],summary:{correct:0,wrong:0,viewed:0,skipped:1,total:1,unofficial:0}};
 await act(async()=>{tree.unmount();tree=create(React.createElement(router.MemoryRouter,{initialEntries:['/onboarding?session=s']},React.createElement(Player,{papers:[],onboarding:true})))});await resolve(sets,session);assert.equal(tree.root.findByProps({'data-collection':'actual-exam'}).children[0],'Synthetic check-in item');assert.ok(json().includes('Actual synthetic exam')&&!json().includes('UDC practice'));
 await act(async()=>tree.unmount());console.log('Onboarding real screen/suggestions/player passed: optional/empty/resume binding, durable start retry, stale account outcomes, preserved explicit focus, true exam context.');
})().catch(e=>{console.error(e);process.exitCode=1});
