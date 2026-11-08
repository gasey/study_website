// Uses the disposable renderer install passed as the first argument.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),webRequire=require('node:module').createRequire(root+'/web/package.json'),React=webRequire('react'),ts=webRequire('typescript');
const reactPath=require.resolve('react',{paths:[process.argv[2]]});require.cache[reactPath]={id:reactPath,filename:reactPath,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
const listeners=new Map();global.window={addEventListener(n,f){if(!listeners.has(n))listeners.set(n,new Set());listeners.get(n).add(f)},removeEventListener(n,f){listeners.get(n)?.delete(f)}};
let account={authenticated:true},grants=[],assignments=[],pathname='/feed',sessionWait=null;
const cache=new Map();function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};const js=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',js)(mod,mod.exports,id=>{
  if(id.endsWith('.css'))return {};
  if(id==='react-router-dom')return {Link:({children,...p})=>React.createElement('a',p,children),useLocation:()=>({pathname,search:''}),useNavigate:()=>()=>{}};
  if(id==='../lib/api')return {getAccountSession:async()=>account};
  if(id==='../lib/review')return {reviewSession:()=>sessionWait||Promise.resolve({user_id:'test',grants}),reviewRequest:async(url)=>url==='/editorial/assignments'?{items:assignments}:{unread:0}};
  if(id==='../lib/examScope')return {useExamScope:()=> 'all',changeExamScope:()=>'/bank'};
  if(id==='./QuickFind')return {default:()=>null};
  if(id==='./ui')return {Avatar:()=>null};if(id==='./NavIcon')return {default:()=>null};
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(fs.existsSync(base+'.tsx')?base+'.tsx':base+'.ts')}
  return webRequire(id);
 });cache.set(file,mod.exports);return mod.exports;
}
const {reviewDestinations,moduleTagScope}=load(root+'/web/src/lib/reviewNavigation.ts');
assert.deepEqual(reviewDestinations({grants:[],assigned:false}),[]);
assert.deepEqual(reviewDestinations({grants:[],assigned:true}).map(x=>x.to),['/editorial']);
const owner=[{role:'owner',subject_id:null}];
assert.equal(reviewDestinations({grants:owner,assigned:false}).length,3);
const position=new URLSearchParams({assignment:'assigned',paper:'current-paper',question:'q1',appearance:'a1',offset:'25',tag_paper:'other',tag_bank:'website',tag_q:'old',tag_offset:'80',retag_batch:'old-batch',tab:'retag'});
const scoped=moduleTagScope(position,'future-module');assert.equal(scoped.get('tag_module'),'future-module');assert.equal(scoped.get('workspace'),'attention');assert.equal(scoped.get('queue'),'tags');
for(const key of ['assignment','paper','question','appearance','offset'])assert.equal(scoped.get(key),position.get(key));
for(const key of ['tag_paper','tag_bank','tag_q','tag_offset','retag_batch','tab'])assert.equal(scoped.has(key),false);
const Header=load(root+'/web/src/components/Header.tsx').default,More=load(root+'/web/src/screens/More.tsx').default,AdminNavigation=load(root+'/web/src/components/AdminNavigation.tsx').default,AdminHome=load(root+'/web/src/components/AdminHome.tsx').default;
let tree;const links=()=>tree.root.findAllByType('a').map(a=>a.props.to);
async function mount(Component,props={}){await act(async()=>{if(tree)tree.unmount();tree=create(React.createElement(Component,props))})}
async function event(name){await act(async()=>{for(const fn of listeners.get(name)||[])fn()})}
(async()=>{
 grants=owner;await mount(Header);assert.ok(links().includes('/editorial')&&links().includes('/admin/bank'));
 // Staff utility links do not enlarge the sticky header or the five-item primary nav.
 const workspace=tree.root.findByProps({'aria-label':'Workspaces'});assert.equal(workspace.findAllByType('a').length,2);
 assert.equal(tree.root.findByType('header').findAllByProps({'aria-label':'Workspaces'}).length,0);
 account={authenticated:false};await event('ism-auth-change');assert.ok(!links().includes('/editorial')&&!links().includes('/admin/bank'));
 account={authenticated:true};grants=[];assignments=[{state:'active'}];await mount(Header);assert.ok(links().includes('/editorial'));assert.ok(!links().includes('/admin/bank'));
 assignments=[];await mount(Header);assert.ok(!links().includes('/editorial'));
 pathname='/games/test';grants=owner;await mount(Header);assert.ok(!links().includes('/editorial'));pathname='/feed';
 let resolve;sessionWait=new Promise(r=>resolve=r);await mount(Header);account={authenticated:false};await event('ism-auth-change');await act(async()=>resolve({grants:owner,user_id:'old'}));sessionWait=null;assert.ok(!links().includes('/admin/bank'));
 account={authenticated:true};grants=owner;await mount(More);const work=tree.root.findByProps({'aria-label':'Your workspaces'});assert.equal(work.findAllByType('details').length,0);assert.ok(links().includes('/editorial?workspace=attention&queue=tags'));
 account={authenticated:false};await event('ism-auth-change');assert.equal(tree.root.findAllByProps({'aria-label':'Your workspaces'}).length,0);
 account={authenticated:true};grants=[];assignments=[{state:'pending'}];await mount(More);assert.ok(links().includes('/editorial'));assert.ok(!links().includes('/admin/bank'));
 await mount(AdminNavigation,{tab:'questions',grants:owner,onNavigate(){}});assert.ok(links().includes('/editorial')&&links().includes('/editorial?workspace=attention&queue=tags'));
 await mount(AdminNavigation,{tab:'overview',grants:[],onNavigate(){}});assert.ok(!links().includes('/editorial'));
 await mount(AdminHome,{health:{questions:0,missing_answers:0,keyed:0,defects:0,held:0,queue:[],sync:null},grants:owner,busy:false,onRetry(){}});assert.equal(links()[0],'/editorial');assert.ok(JSON.stringify(tree.toJSON()).includes('Across the bank'));
 await act(async()=>tree.unmount());console.log('Review navigation passed: owner/assigned/learner visibility, sign-out and stale-response isolation, focused sessions, admin entry points and module-scoped position preservation.');
})().catch(e=>{console.error(e);process.exitCode=1});
