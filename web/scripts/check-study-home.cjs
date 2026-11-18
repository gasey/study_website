// Offline checks for continuation, retries and account-bound Home data.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rendererRoot=process.argv[2]||root+'/../india-study-map/web';
const reactPath=require.resolve('react',{paths:[rendererRoot]});require.cache[reactPath]={id:reactPath,filename:reactPath,loaded:true,exports:React};
const {act,create}=require(require.resolve('react-test-renderer',{paths:[rendererRoot]}));
const listeners=new Map();
global.window={addEventListener(name,fn){if(!listeners.has(name))listeners.set(name,new Set());listeners.get(name).add(fn)},removeEventListener(name,fn){listeners.get(name)?.delete(fn)}};
const emit=()=>{for(const fn of listeners.get('ism-auth-change')||[])fn()};
let params=new URLSearchParams(),tree,failed=false,activeMock=null,reads=0,mockGate=null,overviewGate=null;
let resume={kind:'reading',title:'Saved revision A',detail:'A source paper',url:'/exams/mes?branch=computer&view=topics',updated_at:null};
let overview={activity:{answered:8,correct:4,completed_mocks:1},exams:[{id:'ldc',title:'Account A exam'}]};
const api={getProgress:async()=>({subjects:[],daily_activity:[],current_streak:0,unique_questions:0}),isLaterExamCollection:()=>false,listCollections:async()=>[{id:'udc',title:'UDC',kind:'exam',questions:100,scorable:30,sections:2}],getProgressSummary:async()=>({subjects:[],daily_activity:[],current_streak:0}),getExamProgress:async()=>[],getExamBookmarks:async()=>({collection_ids:[]}),currentMock:async()=>{reads++;if(failed)throw Error('offline');return mockGate?mockGate.promise:activeMock},listMocks:async()=>[]};
const cache=new Map();
function load(file){
 file=path.resolve(file);if(cache.has(file))return cache.get(file);
 const mod={exports:{}};cache.set(file,mod.exports);
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(mod,mod.exports,id=>{
  if(id==='react-router-dom')return {Link:({children,...props})=>React.createElement('a',props,children),Navigate:props=>React.createElement('redirect',props),useSearchParams:()=>[params]};
  if(id.endsWith('/api'))return api;
  if(id.endsWith('/accountContext'))return {accountContext:async()=>({authenticated:true})};
  if(id.endsWith('/examScope'))return {useExamScope:()=> 'all'};
  if(id.endsWith('/review'))return {reviewSession:async()=>({user_id:'test-user'}),reviewRequest:async()=>{if(failed)throw Error('offline');return overviewGate?overviewGate.promise:overview}};
  if(id.endsWith('/learning'))return {learningRequest:async()=>{if(failed)throw Error('offline');return {items:[resume],checkpoint_version:1}}};
  if(id.endsWith('/learningCatalog'))return {catalog:async()=>({items:[],today:'2026-11-12'})};
  if(['/QuickStudy','/QuestionDiscovery','/StudyDashboardPanels','/Feed','/TodayCard','/MasteryMap'].some(s=>id.endsWith(s)))return {default:()=>null};
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(base+(fs.existsSync(base+'.tsx')?'.tsx':'.ts'))}
  return wr(id);
 });cache.set(file,mod.exports);return mod.exports;
}
const Home=load(root+'/web/src/screens/StudyHome.tsx').default;
const Dashboard=load(root+'/web/src/components/StudyDashboardPanels.tsx').default;
const json=()=>JSON.stringify(tree.toJSON()),links=()=>tree.root.findAllByType('a');
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve}};
async function mount(Component){await act(async()=>{tree?.unmount();tree=create(React.createElement(Component))})}
const retryButton=()=>tree.root.findAllByType('button').find(b=>b.children.join('')==='Try again');
(async()=>{
 activeMock={collection_id:'ldc',paper_id:'source-paper',section_path:null,answer_mode:'official',paper_mode:'full',learning_test_id:'shared-test',questions:[],seconds_remaining:300};
 await mount(Home);
 assert.equal(links().find(a=>a.children.join('').includes('Resume test')).props.to,'/tests/shared-test/take','Shared tests resume through the real test route');
 activeMock={...activeMock,learning_test_id:null};await mount(Home);
 const full=new URL(links().find(a=>a.children.join('').includes('Resume test')).props.to,'https://test');
 assert.equal(full.searchParams.get('paper'),'source-paper');assert.equal(full.searchParams.get('simulation'),'full','A full-paper test retains its simulation mode');
 activeMock=null;resume={...resume,url:'/tests/another-test/take'};await mount(Home);
 assert.ok(links().some(a=>a.props.to==='/tests/another-test/take'),'Saved shared-test continuations remain available');
 resume={...resume,kind:'desk'};await mount(Home);assert.ok(!json().includes('Saved revision A'),'Retired self-reported Desk tasks never replace Today');resume={...resume,kind:'reading'};
 failed=true;await mount(Home);assert.ok(json().includes('Some study information couldn’t load'));assert.ok(retryButton());
 const before=reads;failed=false;await act(async()=>retryButton().props.onClick());assert.ok(reads>before);assert.ok(json().includes('Saved revision A'));
 mockGate=deferred();const oldMock=mockGate;await mount(Home);
 mockGate=null;resume={...resume,title:'Saved revision B',url:'/exams/udc?view=topics'};
 await act(async()=>emit());assert.ok(json().includes('Saved revision B'));assert.ok(!json().includes('Saved revision A'));
 await act(async()=>oldMock.resolve({...activeMock,collection_id:'ldc',learning_test_id:'old-account-test',questions:[],seconds_remaining:300}));
 assert.ok(!links().some(a=>a.props.to?.includes('old-account-test')),'Late account A test responses cannot replace account B continuation');
 failed=true;await mount(Dashboard);assert.ok(json().includes('Weekly activity is unavailable'));assert.ok(json().includes('Your saved exams couldn’t load'));assert.ok(!json().includes('Follow an exam to keep'));
 failed=false;await act(async()=>retryButton().props.onClick());assert.ok(json().includes('Account A exam'));
 overviewGate=deferred();const oldOverview=overviewGate;await mount(Dashboard);
 overviewGate=null;overview={activity:{answered:2,correct:1,completed_mocks:0},exams:[{id:'udc',title:'Account B exam'}]};
 await act(async()=>emit());assert.ok(json().includes('Account B exam'));
 await act(async()=>oldOverview.resolve({activity:{answered:999,correct:999,completed_mocks:99},exams:[{id:'ldc',title:'Old private exam'}]}));
 assert.ok(!json().includes('Old private exam'));assert.ok(!json().includes('999'),'Late account data cannot leak into the overview');
 await act(async()=>tree.unmount());assert.equal(listeners.get('ism-auth-change')?.size||0,0);
 console.log('Study Home passed: correct shared/full-test resume routes, saved test continuation, retry recovery, account refresh, stale-response isolation and listener cleanup.');
})().catch(e=>{console.error(e);process.exitCode=1});
