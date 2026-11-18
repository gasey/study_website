// Legacy bookmark and account-boundary checks for the V.9 surface consolidation.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]})),router=wr('react-router-dom');
const events=new Map();global.window={addEventListener(n,f){events.set(n,f)},removeEventListener(n){events.delete(n)}};
const requests=[];
const cache=new Map();function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};cache.set(file,mod.exports);
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(mod,mod.exports,id=>{
  if(id.endsWith('/api'))return {getMistakes:()=>new Promise(resolve=>requests.push(resolve))};
  if(id==='react-router-dom')return router;
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(base+(fs.existsSync(base+'.tsx')?'.tsx':'.ts'))}return wr(id);
 });return mod.exports;
}
const Redirect=load(root+'/web/src/components/ConsolidatedDestination.tsx').default;
const Mistakes=load(root+'/web/src/screens/Mistakes.tsx').default;
const paths=Array.from(fs.readFileSync(root+'/web/src/App.tsx','utf8').matchAll(/<Route path="([^"]+)"/g),m=>m[1]).filter(p=>p!=='*');
const legacy=['/mistakes','/revision','/vocabulary','/important-days','/notifications','/contribute/notifications','/duel'];
const cases=[
 ['/mistakes?exam_scope=all#source','/revise',{tab:'queue',exam_scope:'all'},'#source'],
 ['/revision?session=rev_ab12&exam_scope=all','/revise',{tab:'legacy',session:'rev_ab12',exam_scope:'all'}],
 ['/revision?exam_scope=all','/revise',{exam_scope:'all'}],
 ['/vocabulary?review=card_saved&question_id=q1&return_to=rev_ab12','/revise',{tab:'vocabulary',review:'card_saved',question_id:'q1',return_to:'rev_ab12'}],
 ['/important-days?event=date_abc&question_page=2&view=chronology#date-events','/chronicle',{event:'date_abc',question_page:'2',view:'chronology'},'#date-events'],
 ['/important-days?month=6&day=5','/chronicle',{view:'list',month:'6',day:'5'}],
 ['/important-days?entry=learn_saved','/chronicle',{view:'list',entry:'learn_saved'}],
 ['/notifications?tab=messages&thread=owned','/inbox',{tab:'messages',thread:'owned'}],
 ['/contribute/notifications?tab=updates','/inbox',{tab:'updates'}],
 ['/duel?join=EXAMPLE','/games',{mode:'duel',join:'EXAMPLE'}],
];
let tree;function Probe(){const l=router.useLocation();return React.createElement('output',{'data-location':l.pathname+l.search+l.hash})}
async function mount(element,url='/revise'){await act(async()=>{tree?.unmount();tree=create(React.createElement(router.MemoryRouter,{initialEntries:[url]},element))})}
const json=()=>JSON.stringify(tree.toJSON());
(async()=>{
 for(const [url,target,params,hash='']of cases){
  await mount(React.createElement(router.Routes,null,paths.map(p=>React.createElement(router.Route,{key:p,path:p,element:React.createElement(legacy.includes(p)?Redirect:Probe)}))),url);
  const actual=new URL(tree.root.findByType('output').props['data-location'],'https://fixture.test');
  assert.equal(actual.pathname,target);assert.equal(actual.hash,hash);for(const [k,v]of Object.entries(params))assert.equal(actual.searchParams.get(k),v);
 }
 // Every literal navigation destination in the changed shell/catalog has a real route.
 let checked=0;
 for(const file of ['components/Header.tsx','screens/More.tsx','screens/Library.tsx','lib/quickAccess.ts']){
  const text=fs.readFileSync(root+'/web/src/'+file,'utf8');
  for(const match of text.matchAll(/["'](\/[a-z][a-z0-9/?=&.-]*)(?:["'])/g)){
   const pathname=new URL(match[1],'https://fixture.test').pathname;
   if(pathname.endsWith('/')||['/inbox/unread'].includes(pathname)||pathname.startsWith('/editorial/'))continue; // Private API reads, not links.
   assert.ok(router.matchRoutes(paths.map(path=>({path})),pathname),'Orphan navigation: '+match[1]+' in '+file);checked++;
  }
 }
 await mount(React.createElement(Mistakes));assert.equal(requests.length,1);
 await act(async()=>events.get('ism-auth-change')());assert.equal(requests.length,2);
 const row=question=>({id:question,question,times_wrong:1,last_attempt:'2026-11-17T10:00:00Z',chosen_text:'A',answer_text:'B'});
 await act(async()=>requests[0]([row('Previous account private question')]));assert.ok(!json().includes('Previous account private question'));
 await act(async()=>requests[1]([row('Current account question')]));assert.ok(json().includes('Current account question'));
 await act(async()=>tree.unmount());assert.equal(events.size,0);
 console.log(`Consolidation passed: ${cases.length} actual-router redirects retain sessions, filters, source references and fragments; ${checked} navigation destinations resolve; delayed previous-account mistakes stay hidden.`);
})().catch(e=>{console.error(e);process.exitCode=1});
