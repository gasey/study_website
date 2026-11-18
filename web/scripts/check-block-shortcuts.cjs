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
  if(id.endsWith('/api'))return {getCommunityFeed:(...args)=>new Promise(resolve=>feeds.push({args,resolve}))};
  if(id.endsWith('/review'))return {reviewSession:async()=>({user_id:'synthetic-account'}),reviewRequest:(...args)=>args[0]==='/community/guides'?Promise.resolve({week_start:'2026-11-16',week_end:'2026-11-22',as_of:'2026-11-17T00:00:00Z',items:[]}):new Promise((resolve,reject)=>writes.push({args,resolve,reject}))};
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
const {StudyPostDetail}=load(root+'/web/src/components/StudyPosts.tsx'),StudyReplies=load(root+'/web/src/components/StudyReplies.tsx').default,BlockAuthor=load(root+'/web/src/components/BlockAuthor.tsx').default;
async function click(label){await act(async()=>button(label).props.onClick())}
async function settle(body={blocked:true}){const w=writes.shift();assert.ok(w,'Expected request');await act(async()=>w.resolve(body));return w}
const detail=(extra={})=>({id:4,author_id:'author/private',body:'A synthetic note from a private-profile author.',author:'Synthetic author',is_author:false,created_at:'2026-11-17T10:00:00Z',needs_approval:false,registered:true,reference:null,helpful:0,voted:false,...extra});
(async()=>{
 await mount(Discussion);await resolveRead(page());assert.ok(button('Block this author'),'Block is available without a report form');assert.equal(tree.root.findAllByType('form').length,1);await click('Block this author');assert.ok(button('Blocking…').props.disabled);let w=writes.shift();assert.equal(w.args[0],'/creators/synthetic-author/block');assert.deepEqual(w.args[1],{enabled:true});await act(async()=>w.resolve({blocked:true}));assert.ok(!json().includes('An existing synthetic'));assert.ok(json().includes('Author blocked.'));await resolveRead(page([]));assert.equal(tree.root.findAllByType('a').some(a=>a.props.href==='/creators/settings#blocked-users'),true);
 // Failure is uncertain: refresh the privacy-bound snapshot and retain feedback.
 await mount(StudyPostDetail,'/community?study=4',{id:4,onClose(){}});await settle(detail());await click('Block this author');w=writes.shift();assert.equal(w.args[0],'/creators/author%2Fprivate/block');await act(async()=>w.reject(Error('Synthetic lost response')));assert.ok(!json().includes('A synthetic note'));assert.ok(json().includes('Blocking was not confirmed'));assert.equal(writes[0].args[0],'/community/study-posts/4');await settle(detail());assert.ok(json().includes('Blocking was not confirmed'));
 // Sharing a reviewed material uses exactly the same block, without requiring report text.
 await mount(StudyPostDetail,'/community?study=4',{id:4,onClose(){}});await settle(detail({kind:'material-share'}));await click('Block this author');await settle();w=writes.shift();assert.ok(w.args[0].includes('/study-posts/4'));await act(async()=>w.reject(Error('Study note not found')));assert.ok(!json().includes('A synthetic note'));
 await mount(StudyPostDetail,'/community?study=4',{id:4,onClose(){}});await settle(detail({is_author:true}));assert.ok(!button('Block this author'));
 await mount(StudyPostDetail,'/community?study=4',{id:4,onClose(){}});await settle(detail({registered:false}));assert.ok(!button('Block this author'));
 // An owned root can contain a different author's reply. Block removes the
 // whole private page and invalidates concurrent pagination from that reader.
 await mount(StudyPostDetail,'/community?study=4',{id:4,onClose(){}});await settle(detail({is_author:true}));await click('Show replies');await settle({items:[{...detail({id:5,author_id:'reply-author'}),parent_id:4}],has_more:true,registered:true,can_reply:true,replies_remaining:30,reply_limit:30});await click('Block this author');const block=writes.shift();assert.equal(block.args[0],'/creators/reply-author/block');await click('Load more replies');const late=writes.shift();await act(async()=>block.resolve({blocked:true}));assert.ok(!json().includes('reply-author'));await act(async()=>late.resolve({items:[detail({id:6,body:'Late blocked reply must stay hidden'})],has_more:false,registered:true,can_reply:true,replies_remaining:30,reply_limit:30}));assert.ok(!json().includes('Late blocked reply'));await settle(detail({is_author:true}));assert.ok(button('Show replies'));
 // Feed snapshots and outstanding pagination clear when the account block settles.
 function Together(){return React.createElement(React.Fragment,null,React.createElement(Feed),React.createElement(BlockAuthor,{authorId:'feed-author'}))}
 await mount(Together,'/community?tab=following');const feedRow={...post(),source_context:null,accepted_answer:null,author_role:'Learner',question_id:'current',question:'A blocked feed question'};await act(async()=>feeds.shift().resolve({tab:'following',available:true,items:[feedRow],has_more:true}));assert.ok(json().includes('A blocked feed question'));await click('Load more');const lateFeed=feeds.shift();await click('Block this author');await settle();assert.ok(!json().includes('A blocked feed question'));await act(async()=>lateFeed.resolve({tab:'following',available:true,items:[{...feedRow,id:8,question:'Late blocked feed question'}],has_more:false}));assert.ok(!json().includes('Late blocked feed question'));await act(async()=>feeds.shift().resolve({tab:'following',available:true,items:[],has_more:false}));
 // Account expiry and unmount discard old block outcomes and their messages.
 await mount(BlockAuthor,'/',{authorId:'old-account-target'});await click('Block this author');w=writes.shift();await act(async()=>{for(const fn of events.get('ism-auth-expired')||[])fn(new Event('ism-auth-expired'))});let changed=0;const watch=()=>changed++;window.addEventListener('ism-community-change',watch);await act(async()=>w.resolve({blocked:true}));assert.equal(changed,0);window.removeEventListener('ism-community-change',watch);
 await click('Block this author');w=writes.shift();await act(async()=>tree.unmount());await act(async()=>w.resolve({blocked:true}));assert.equal(writes.length,0);
 console.log('Block shortcuts passed: direct canonical/note/share/reply controls, private-profile and escaped IDs, own/guest exclusion, one account block, success/uncertain privacy invalidation, surviving feedback/unblock link, late pagination and expired/unmounted outcome rejection.');
})().catch(e=>{console.error(e);process.exitCode=1});
