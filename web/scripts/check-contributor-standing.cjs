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
window.dispatchEvent=e=>{for(const fn of [...(events.get(e.type)||[])])fn(e)};
global.document={getElementById(){return null}};
global.fetch=(url)=>new Promise(resolve=>reads.push({url,resolve:body=>resolve({ok:!body.error,json:async()=>body.error?{detail:body.error}:body})}));
const widget=()=>null,cache=new Map();
function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};cache.set(file,mod.exports);
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(mod,mod.exports,id=>{
  if(id.endsWith('/BioModeration'))return {default:widget};
  if(id.endsWith('/materials'))return {contentRequest:(url)=>url.startsWith('/materials?')?Promise.resolve({items:[],total:0}):new Promise((resolve,reject)=>writes.push({args:[url],resolve,reject}))};
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

const {ContributorName,TierFlair,OwnCommunityStanding,GuideStrip}=load(root+'/web/src/components/ContributorStanding.tsx'),Profile=load(root+'/web/src/screens/Creators.tsx').default;
const week={week_start:'2026-11-16',week_end:'2026-11-22',as_of:'2026-11-17T10:00:00Z',items:[]};
const visible=()=>text(tree.toJSON());
const reputation={display_tier:'Guide',helpful_count:157,accepted_answers:3,weekly_helpful:7,counts_scope:'Published posts visible to you'};
async function click(label){await act(async()=>button(label).props.onClick())}
async function answer(value){const req=writes.shift();assert.ok(req,'Expected standing read');await act(async()=>req.resolve(value));return req}
async function event(name){await act(async()=>window.dispatchEvent(new Event(name)))}
(async()=>{
 await mount(ContributorName,'/',{author:'Synthetic learner',author_tier:'Helper'});assert.ok(!json().includes('Highest earned'));assert.equal(tree.root.findAllByType('a').length,0);
 await mount(ContributorName,'/',{author:'Synthetic learner',author_tier:'Regular',author_profile_id:'private/id'});assert.ok(json().includes('Regular'));assert.equal(tree.root.findByType('a').props.href,'/creators/private%2Fid');
 await mount(GuideStrip);assert.equal(writes[0].args[0],'/community/guides');await answer(week);assert.ok(json().includes('No eligible Guides'));assert.ok(json().includes('16 Nov'));assert.ok(json().includes('22 Nov'));
 await event('ism-community-standing-change');await answer({...week,items:[{...reputation,id:'guide/id',handle:'Synthetic Guide'}]});assert.ok(json().includes('Synthetic Guide'));assert.ok(visible().includes('7 Helpful this week'));assert.equal(tree.root.findByType('a').props.href,'/creators/guide%2Fid');
 await event('ism-community-change');assert.ok(!json().includes('Synthetic Guide'));const late=writes.shift();await event('ism-auth-expired');await act(async()=>late.resolve({...week,items:[{...reputation,id:'old',handle:'Private previous account Guide'}]}));assert.ok(!json().includes('Private previous account'));await answer(week);
 await event('ism-community-standing-change');const failed=writes.shift();await act(async()=>failed.reject(Error('Synthetic network failure')));assert.ok(button('Retry Guides'));await click('Retry Guides');await answer(week);
 await mount(OwnCommunityStanding);await answer({...reputation,weighted_helpful:24,tier:'Helper',privileges_restricted:true,mentor_eligible:false,post_limit:5,reply_limit:30,creator_public:false,board_public:false});assert.ok(json().includes('Guide'));assert.ok(visible().includes('24 weighted Helpful'));assert.ok(json().includes('paused'));assert.ok(json().includes('Highest earned tiers'));assert.ok(!json().includes('You are eligible for a reviewer'));
 await event('ism-community-standing-change');await answer({...reputation,weighted_helpful:150,tier:'Guide',privileges_restricted:false,mentor_eligible:true,post_limit:10,reply_limit:60,creator_public:true,board_public:true});assert.ok(json().includes('eligible for a reviewer'));assert.ok(json().includes('does not grant access automatically'));assert.ok(visible().includes('157 visible Helpful votes'));
 await event('ism-auth-change');assert.ok(!visible().includes('157 visible'));const oldOwn=writes.shift();await act(async()=>tree.unmount());await act(async()=>oldOwn.resolve({...reputation,weighted_helpful:150}));
 // The actual public creator profile renders raw counts and drops a late read
 // across an auth transition, using the shared synchronous generation guard.
 function PublicRoute(){return React.createElement(router.Routes,null,React.createElement(router.Route,{path:'/creators/:id',element:React.createElement(Profile)}))}
 const creator={id:'author',handle:'Synthetic public author',public:true,bio:'Own reviewed bio',materials:0,following:false,followers:0,is_self:false,contributions:[],has_more_contributions:false,community:reputation};
 await mount(PublicRoute,'/creators/author');await answer(creator);assert.ok(json().includes('157'));assert.ok(json().includes('Accepted replies'));assert.ok(json().includes('Guide'));
 await event('ism-community-change');const oldProfile=writes.shift();await event('ism-auth-change');await act(async()=>oldProfile.resolve({...creator,handle:'Stale private profile'}));assert.ok(!json().includes('Stale private profile'));await answer({...creator,community:{...reputation,helpful_count:0,accepted_answers:0}});assert.ok(!json().includes('157'));
 await act(async()=>tree.unmount());assert.equal(writes.length,0);console.log('Contributor standing passed: consented author links, Regular+ flair, dated empty/real Guide strip, retry and auth/block/vote invalidation, immutable display/current privilege distinction, raw counts, explicit invitation boundary, and actual creator-profile stale-response rejection.');
})().catch(e=>{console.error(e);process.exitCode=1});
