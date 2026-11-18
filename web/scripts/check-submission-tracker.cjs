// Actual tracker with delayed identity, pagination, account and expiry responses.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]})),router=wr('react-router-dom');
const events=new Map(),identities=[],reads=[];
global.window={addEventListener(n,f){if(!events.has(n))events.set(n,new Set());events.get(n).add(f)},removeEventListener(n,f){events.get(n)?.delete(f)}};
const cache=new Map();function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};cache.set(file,mod.exports);
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(mod,mod.exports,id=>{
  if(id.endsWith('/accountContext'))return {accountContext:()=>new Promise(resolve=>identities.push(resolve))};
  if(id.endsWith('/review'))return {reviewRequest:url=>new Promise((resolve,reject)=>reads.push({url,resolve,reject})),kindLabel:kind=>kind};
  if(id.endsWith('/ContributorStanding'))return {TierFlair:({tier})=>tier?React.createElement('span',null,tier):null};
  if(id==='react-router-dom')return router;
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(base+(fs.existsSync(base+'.tsx')?'.tsx':'.ts'))}return wr(id);
 });return mod.exports}
const Tracker=load(root+'/web/src/components/SubmissionTracker.tsx').default;
let tree;const text=n=>typeof n==='string'?n:(n?.children||[]).map(text).join(''),json=()=>JSON.stringify(tree.toJSON()),button=label=>tree.root.findAllByType('button').find(n=>text(n)===label);
const row=(extra={})=>({pipeline:'material',id:'a/b?',title:'Synthetic material',kind:'material',state:'changes_requested',revision:3,updated_at:'2026-11-18T00:00:00Z',published_revision:1,locked:false,queue_position:null,feedback:{note:'<script>literal return text</script>',revision:2,created_at:'2026-11-17T00:00:00Z'},...extra});
const page=(items=[row()],extra={})=>({items,offset:0,has_more:true,as_of:'2026-11-18T00:00:00Z',queue_scope:'Snapshot ordering; not FIFO.',standing:{display_tier:'Guide',tier:null,can_create:false,privileges_restricted:true,mentor_eligible:false,post_limit:5,reply_limit:30,posts_remaining:2,replies_remaining:12},review_times:[{pipeline:'bank',sample_count:0,median_seconds:null},{pipeline:'material',sample_count:3,median_seconds:172800},{pipeline:'collection',sample_count:0,median_seconds:null}],...extra});
async function mount(){await act(async()=>{tree?.unmount();tree=create(React.createElement(router.MemoryRouter,null,React.createElement(Tracker)))})}
async function identity(authenticated=true){assert.ok(identities.length);await act(async()=>identities.shift()({authenticated}))}
async function resolve(body){assert.ok(reads.length);const r=reads.shift();await act(async()=>r.resolve(body));return r}
async function emit(n){await act(async()=>{for(const fn of [...(events.get(n)||[])])fn()})}
(async()=>{
 await mount();assert.ok(json().includes('Loading your submissions'));
 await identity(false);assert.ok(json().includes('Sign in to see'));assert.equal(reads.length,0);
 await emit('ism-auth-change');await identity();await resolve(page());
 assert.ok(json().includes('Returned for changes'));assert.ok(json().includes('Latest return note'));assert.ok(json().includes('<script>literal return text</script>'));assert.equal(tree.root.findAllByType('script').length,0);
 assert.ok(json().includes('No recent paired'));assert.ok(json().includes('2.0 days'));assert.ok(json().includes('Guide'));assert.ok(json().includes('paused'));assert.ok(json().includes('does not assign a role'));
 assert.ok(tree.root.findAllByType('a').some(n=>n.props.href==='/studio/a%2Fb%3F'));
 await act(async()=>button('Next submissions').props.onClick());assert.ok(!json().includes('Synthetic material'));await identity();assert.ok(reads[0].url.endsWith('offset=20'));
 const late=reads.shift();await emit('ism-community-change');await act(async()=>late.resolve(page([row({title:'Blocked late draft'})])));assert.ok(!json().includes('Blocked late draft'));
 await identity();await resolve(page([row({pipeline:'bank',locked:true,title:'Linked question details are locked',feedback:null,queue_position:2})]));assert.ok(json().includes('Queue position'));assert.ok(json().includes('Cup closes'));assert.ok(!tree.root.findAllByType('a').some(n=>String(n.props.href).startsWith('/contributions/')));
 await emit('ism-content-change');await identity();const expiryLate=reads.shift();await emit('ism-auth-expired');await act(async()=>expiryLate.resolve(page([row({title:'Expired private draft'})])));assert.ok(json().includes('Sign in to see'));assert.ok(!json().includes('Expired private draft'));
 await emit('ism-auth-change');await identity();await act(async()=>reads.shift().reject(new Error('Synthetic outage')));assert.ok(json().includes('Could not load submissions'));assert.ok(!json().includes('No submissions on this page'));
 await act(async()=>button('Retry submissions').props.onClick());await identity();await resolve(page([],{has_more:false}));assert.ok(json().includes('No submissions on this page'));assert.ok(button('Next submissions').props.disabled);
 await act(async()=>button('Refresh submissions').props.onClick());const previousIdentity=identities.shift();await emit('ism-auth-change');await act(async()=>previousIdentity({authenticated:true}));assert.equal(reads.length,0);
 await identity();await resolve(page([row({pipeline:'collection',id:'same-thread'})]));assert.ok(tree.root.findAllByType('a').some(n=>n.props.href==='/learning/manage?entry=same-thread'));
 await act(async()=>tree.unmount());assert.ok([...events.values()].every(v=>v.size===0));
 console.log('Submission tracker passed: actual states, private/guest/error/empty reads, raw return text, honest medians, queue context, escaped same-thread links, assessment redaction, current privilege/retained label distinction, pagination and stale identity/block/expiry/content-response rejection.');
})().catch(e=>{console.error(e);process.exitCode=1});
