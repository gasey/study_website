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
  if(id.endsWith('/review'))return {reviewSession:async()=>({user_id:'synthetic-account'}),reviewRequest:async(...args)=>{if(args[0]==='/community/guides')return {week_start:'2026-11-16',week_end:'2026-11-22',as_of:'2026-11-17T00:00:00Z',items:[]};writes.push(args);if(failures)throw Error('Synthetic network failure');return {needs_approval:false}}};
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
(async()=>{
 await mount(Discussion);await resolveRead(page());
 const draft='A different synthetic doubt draft stays intact.';await type(draft);await submit();
 assert.equal(writes.length,0,'Doubt must wait for a fresh thread read');
 await resolveRead(page([post(),post(2,{needs_approval:true,body:'Private pending content'})],{has_more:true}));
 assert.ok(json().includes('Discussions already exist'));assert.ok(json().includes('most recent discussions'));
 assert.equal(tree.root.findAllByType('button').filter(n=>text(n).startsWith('Join discussion by')).length,1,'Pending topics cannot be joined');
 await act(async()=>button('Join discussion by').props.onClick());assert.ok(reads[0].url.includes('/posts/1/replies'));
 await resolveRead({items:[],has_more:false});assert.ok(json().includes('Post reply'));assert.ok(json().includes(draft));assert.equal(writes.length,0);
 await act(async()=>button('My doubt is different').props.onClick());assert.equal(writes.length,1);assert.equal(writes[0][1].body,draft);
 await resolveRead(page());
 // Empty conversations do not add an unnecessary confirmation.
 await mount(Discussion);await resolveRead(page([]));await type(draft);await submit();await resolveRead(page([]));assert.equal(writes.length,2);await resolveRead(page());
 // A failed suggestion read or changed access must never silently publish.
 await mount(Discussion);await resolveRead(page());await type(draft);await submit();await resolveRead({error:'Synthetic unavailable threads'});assert.equal(writes.length,2);assert.ok(json().includes('Synthetic unavailable threads'));assert.ok(json().includes(draft));
 await submit();await resolveRead(page([],{allowed:false}));assert.equal(writes.length,2);assert.ok(json().includes('Reload this discussion'));
 // A late previous-account suggestion response cannot create a post.
 await submit();const old=reads.shift();await authChange();await act(async()=>old.resolve(page([])));assert.equal(writes.length,2);await resolveRead(page([],{registered:false}));assert.equal(tree.root.findAllByType('form').length,0);
 // Explanations bypass doubt deflection; write retry keeps its idempotency key.
 await mount(Discussion);await resolveRead(page([]));await act(async()=>tree.root.findByType('select').props.onChange({target:{value:'explanation'}}));await type(draft);failures=true;await submit();const key=writes.at(-1)[2];assert.equal(reads.length,0);failures=false;await submit();assert.equal(writes.at(-1)[2],key);await resolveRead(page());
 // A joined topic outside the original page and its suggestions disappear on a privacy refresh.
 await mount(Discussion);await resolveRead(page());await type(draft);await submit();
 await resolveRead(page([post(3,{body:'Hidden after block synthetic discussion.'})]));
 await act(async()=>button('Join discussion by').props.onClick());await resolveRead({items:[],has_more:false});
 const joined=tree.root.findAllByType('article').find(n=>n.props.id==='discussion-post-3');
 await act(async()=>joined.findAllByType('button').find(n=>text(n)==='Report post').props.onClick());
 await act(async()=>button('Block this author').props.onClick());await resolveRead(page([]));
 assert.ok(!json().includes('Hidden after block synthetic discussion.'));assert.ok(!json().includes('Discussions already exist'));assert.ok(json().includes(draft));
 // Canonical drafts restore their post kind, citations and exact uncertain-write key.
 await mount(Discussion);await resolveRead(page([]));
 await act(async()=>tree.root.findByType('select').props.onChange({target:{value:'explanation'}}));
 const formatted='**Synthetic method**\n- Compare the wording\n- Use `x = 2`';await type(formatted);
 await act(async()=>button('Add source').props.onClick());
 const citationUrl=()=>tree.root.findAllByType('input').find(n=>n.props.type==='url');
 const citationNote=()=>tree.root.findAllByType('input').find(n=>n.props.maxLength===1000);
 await act(async()=>citationUrl().props.onChange({target:{value:'https://example.test/reviewed-source'}}));
 await act(async()=>citationNote().props.onChange({target:{value:'Supports this synthetic method'}}));
 failures=true;await submit();const uncertain=writes.at(-1);failures=false;
 await mount(Discussion);await resolveRead(page([]));
 assert.equal(tree.root.findByType('select').props.value,'explanation');assert.equal(tree.root.findByType('textarea').props.value,formatted);
 assert.equal(citationUrl().props.value,'https://example.test/reviewed-source');assert.equal(citationNote().props.value,'Supports this synthetic method');assert.ok(json().includes('Draft restored'));
 assert.ok(tree.root.findAllByType('strong').some(n=>text(n)==='Synthetic method'));assert.ok(tree.root.findAllByType('code').some(n=>text(n)==='x = 2'));assert.equal(tree.root.findAllByType('a').filter(n=>n.props.href==='https://example.test/reviewed-source').length,0,'Own source inputs are not raw HTML preview anchors');
 // Same canonical question under another paper, and another question, use separate drafts.
 await mount(Discussion,undefined,{context:{paper_id:'another-paper'}});await resolveRead(page([]));assert.equal(tree.root.findByType('textarea').props.value,'');
 await mount(Discussion,undefined,{qid:'cq_other'});await resolveRead(page([]));assert.equal(tree.root.findByType('textarea').props.value,'');
 await mount(Discussion);await resolveRead(page([]));await submit();assert.deepEqual(writes.at(-1)[1],uncertain[1]);assert.equal(writes.at(-1)[2],uncertain[2]);await resolveRead(page([]));assert.equal(tree.root.findByType('textarea').props.value,'');
 await mount(Discussion);await resolveRead(page([]));assert.equal(tree.root.findByType('textarea').props.value,'');assert.equal(tree.root.findByType('select').props.value,'doubt');
 // Deflected doubts survive reload and still perform a fresh duplicate check.
 await type(draft);await submit();await resolveRead(page());await mount(Discussion);await resolveRead(page());assert.equal(tree.root.findByType('textarea').props.value,draft);
 const beforeReloadSubmit=writes.length;await submit();assert.equal(writes.length,beforeReloadSubmit);await resolveRead(page());assert.ok(json().includes('Discussions already exist'));
 await act(async()=>button('Join discussion by').props.onClick());await resolveRead({items:[],has_more:false});
 let replyForm=tree.root.findAllByType('form').find(n=>text(n).includes('Your reply'));
 await act(async()=>replyForm.findByType('textarea').props.onChange({target:{value:'**Synthetic reply** with a separate saved draft.'}}));
 failures=true;await act(async()=>replyForm.props.onSubmit({preventDefault(){}}));const uncertainReply=writes.at(-1);failures=false;
 await mount(Discussion);await resolveRead(page());await act(async()=>button('Replies').props.onClick());await resolveRead({items:[],has_more:false});
 replyForm=tree.root.findAllByType('form').find(n=>text(n).includes('Your reply'));assert.ok(replyForm.findByType('textarea').props.value.startsWith('**Synthetic reply**'));assert.equal(tree.root.findAllByType('textarea').at(-1).props.value,draft,'Question draft is separate from reply draft');
 await act(async()=>replyForm.props.onSubmit({preventDefault(){}}));assert.equal(writes.at(-1)[2],uncertainReply[2]);await resolveRead({items:[],has_more:false});assert.equal(replyForm.findByType('textarea').props.value,'');
 await act(async()=>button('Discard draft').props.onClick());assert.ok(!json().includes('Discussions already exist'));assert.equal(tree.root.findAllByType('textarea').at(-1).props.value,'');
 // Accepted content keeps its source citation and gets formatting without an edit control.
 await mount(Discussion);await resolveRead(page([post(8,{accepted:true,body:'**Accepted synthetic method**\n1. Compare `a`',source_links:[{url:'https://example.test/evidence',note:'Existing source evidence'}]})]));
 assert.ok(tree.root.findAllByType('strong').some(n=>text(n)==='Accepted synthetic method'));assert.equal(tree.root.findAllByType('button').filter(n=>/^Edit/.test(text(n))).length,0);assert.ok(tree.root.findAllByType('a').some(n=>n.props.href==='https://example.test/evidence'));
 // Expiry hides private content and prevents a late response from restoring it.
 await act(async()=>{for(const fn of events.get('ism-auth-expired')||[])fn()});assert.ok(!json().includes('Accepted synthetic method'));await resolveRead(page([],{registered:false}));assert.equal(tree.root.findAllByType('form').length,0);
 // Following uses the real discussion feed, and late account reads stay hidden.
 await mount(Feed,'/community?tab=following');assert.equal(feeds[0].args[0],'following');
 const prior=feeds.shift();await authChange();await act(async()=>prior.resolve({tab:'following',available:true,items:[{...post(),source_context:null,accepted_answer:null,author_role:'Learner',question_id:'old',question:'Previous account private question'}],has_more:false}));assert.ok(!json().includes('Previous account private question'));
 await act(async()=>feeds.shift().resolve({tab:'following',available:true,items:[{...post(),source_context:null,accepted_answer:null,author_role:'Learner',question_id:'current',question:'Current unlocked question',body:'**Formatted synthetic question**',accepted_answer:'**Formatted accepted reply**'}],has_more:true}));assert.ok(json().includes('Current unlocked question'));assert.ok(json().includes('From people you follow'));assert.ok(tree.root.findAllByType('strong').some(n=>text(n)==='Formatted synthetic question'));assert.ok(tree.root.findAllByType('strong').some(n=>text(n)==='Formatted accepted reply'));
 await act(async()=>button('Load more').props.onClick());const more=feeds.shift();assert.equal(more.args[1],20);await act(async()=>more.resolve({tab:'following',available:true,items:[{...post(),source_context:null,accepted_answer:null,author_role:'Learner',question_id:'current',question:'Current unlocked question',body:'**Formatted synthetic question**',accepted_answer:'**Formatted accepted reply**'}],has_more:false}));assert.equal(tree.root.findAllByType('article').length,1,'Pagination must not duplicate a card');
 await act(async()=>tree.unmount());assert.equal([...(events.get('ism-auth-change')||[])].length,0);
 console.log('Community v2 passed: fresh-thread deflection, one-tap replies, retained drafts, pending-post filtering, empty/error/access cases, account changes, idempotent retries chronological-feed pagination, canonical citation/type/context/parent drafts, reload retries, safe formatted readers and accepted/expiry guards.');
})().catch(e=>{console.error(e);process.exitCode=1});
