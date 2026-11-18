// Render the real feed and discussion UI with delayed private reads and writes.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]})),router=wr('react-router-dom');
const events=new Map(),reads=[],feeds=[],writes=[];let failures=false;
global.crypto||=require('node:crypto').webcrypto;
class Storage{getItem(k){return Object.hasOwn(this,k)?this[k]:null}setItem(k,v){this[k]=String(v)}removeItem(k){delete this[k]}}
global.localStorage=new Storage();
global.window={location:{search:'',origin:'https://fixture.test'},addEventListener(n,f){if(!events.has(n))events.set(n,new Set());events.get(n).add(f)},removeEventListener(n,f){events.get(n)?.delete(f)}};
global.document={getElementById(){return null}};
global.fetch=(url)=>new Promise(resolve=>reads.push({url,resolve:body=>resolve({ok:!body.error,json:async()=>body.error?{detail:body.error}:body})}));
const widget=()=>null,cache=new Map();
function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};cache.set(file,mod.exports);
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(mod,mod.exports,id=>{
  if(id.endsWith('/api'))return {getCommunityFeed:(...args)=>new Promise(resolve=>feeds.push({args,resolve}))};
  if(id.endsWith('/review'))return {reviewSession:async()=>({user_id:'synthetic-account'}),reviewRequest:(...args)=>new Promise((resolve,reject)=>writes.push({args,resolve,reject}))};
  if(id.endsWith('/device'))return {deviceId:()=> 'synthetic-device'};
  if(id.endsWith('/useQuestionStaff'))return {useQuestionStaff:()=>false};
  if(id.endsWith('/examScope'))return {scopeLink:link=>link};
  if(id.endsWith('/AvatarArt'))return {UserAvatar:widget};
  if(id.endsWith('/MaterialDiscovery')||id.endsWith('/QuestionReport'))return {default:widget};
  if(id.endsWith('/Creators'))return {FollowingMaterials:widget};
  if(id.endsWith('/Materials')||id.endsWith('/CommunityQuestions'))return {default:widget};
  if(id==='react-router-dom')return router;
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(base+(fs.existsSync(base+'.tsx')?'.tsx':'.ts'))}return wr(id);
 });return mod.exports;
}
const Discussion=load(root+'/web/src/components/QuestionDiscussion.tsx').default,Feed=load(root+'/web/src/screens/Feed.tsx').default;
const post=(id=1,extra={})=>({id,canonical_id:'cq_synthetic',parent_id:null,kind:'doubt',body:'An existing synthetic question about this wording.',author:'Synthetic author',author_id:'synthetic-author',is_author:false,needs_approval:false,pinned:false,accepted:false,voted:false,helpful:0,created_at:'2026-11-17T10:00:00Z',source_links:[],source_context:{},...extra});
const page=(items=[post()],extra={})=>({items,has_more:false,allowed:true,registered:true,locked:false,can_disclose:false,lock_reason:null,...extra});
let tree;const text=n=>typeof n==='string'?n:(n?.children||[]).map(text).join(''),json=()=>JSON.stringify(tree.toJSON());
const button=label=>tree.root.findAllByType('button').find(n=>text(n).includes(label));
async function mount(Component,url='/bank/cq_synthetic',props={}){
 await act(async()=>{tree?.unmount();tree=create(React.createElement(router.MemoryRouter,{initialEntries:[url]},React.createElement(Component,{qid:'cq_synthetic',context:{},...props})),{createNodeMock:node=>node.type==='article'?{querySelector:()=>({focus(){}})}:node.type==='form'?{reportValidity:()=>true}:null})});
}
async function resolveRead(body){const r=reads.shift();assert.ok(r,'Expected private read');await act(async()=>r.resolve(body));return r}
async function type(body){const input=tree.root.findAllByType('textarea').find(n=>n.props.placeholder);await act(async()=>input.props.onChange({target:{value:body}}))}
async function submit(){const form=tree.root.findAllByType('form')[0];await act(async()=>form.props.onSubmit({preventDefault(){}}))}
async function authChange(){await act(async()=>{for(const fn of events.get('ism-auth-change')||[])fn()})}
const Nudge=load(root+'/web/src/components/AcceptanceNudge.tsx').default;
async function click(label){await act(async()=>button(label).props.onClick())}
async function write(prompt){const w=writes.shift();assert.ok(w,'Expected prompt claim');assert.ok(w.args[0].endsWith('/acceptance-nudge'));await act(async()=>w.resolve({prompt}));return w}
(async()=>{
 await mount(Nudge,'/',{postId:123});assert.ok(!json().includes('Did one'));await write(true);assert.ok(json().includes('Did one of these solve it?'));await click('Not now');assert.ok(!json().includes('Did one'));
 await mount(Nudge,'/',{postId:123});await write(false);assert.ok(!json().includes('Did one'),'A new device/reload obeys the server once-only decision');
 await mount(Nudge,'/',{postId:123});const late=writes.shift();await act(async()=>tree.unmount());await act(async()=>late.resolve({prompt:true}));assert.equal(tree.toJSON(),null);
 await mount(Nudge,'/',{postId:123});const failed=writes.shift();await act(async()=>failed.reject(Error('Uncertain optional claim')));assert.ok(!json().includes('Did one'));assert.equal(writes.length,0);
 const own=post(1,{is_author:true}),other=post(2,{kind:'reply',parent_id:1});
 async function thread(extra={},replies=[other]){await mount(Discussion);await resolveRead(page([post(1,{...own,...extra})]));assert.equal(writes.length,0,'Closed topics never claim prompts');await click('Replies / Reply');await resolveRead({items:replies,has_more:false})}
 await thread();assert.equal(writes.length,1);await write(true);assert.ok(json().includes('Did one'));assert.ok(button('Accept reply'));await click('Hide replies');assert.ok(!json().includes('Did one'));await click('Replies / Reply');await resolveRead({items:[other],has_more:false});await write(false);assert.ok(!json().includes('Did one'));
 await thread();const expired=writes.shift();await authChange();await act(async()=>expired.resolve({prompt:true}));assert.ok(!json().includes('Did one'));await resolveRead(page([]));
 await thread({},[]);assert.equal(writes.length,0);await thread({},[{...other,is_author:true}]);assert.equal(writes.length,0);await thread({},[{...other,needs_approval:true}]);assert.equal(writes.length,0);await thread({},[{...other,accepted:true}]);assert.equal(writes.length,0);await thread({is_author:false});assert.equal(writes.length,0);await thread({kind:'explanation'});assert.equal(writes.length,0);
 await act(async()=>tree.unmount());console.log('Acceptance nudge passed: actual thread eligibility, open-only author prompt, dismissal, reload/server refusal, hidden on collapse/acceptance, no automatic acceptance, uncertain-response silence and late unmount/account response rejection.');
})().catch(e=>{console.error(e);process.exitCode=1});
