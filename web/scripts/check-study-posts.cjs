// Render study-note authoring/readers with private reads delayed across accounts.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]})),router=wr('react-router-dom');
const events=new Map(),requests=[],cache=new Map();global.crypto||=require('node:crypto').webcrypto;
global.localStorage=new(class{getItem(k){return Object.hasOwn(this,k)?this[k]:null}setItem(k,v){this[k]=String(v)}removeItem(k){delete this[k]}})();
global.window={location:{origin:'https://fixture.test'},addEventListener(n,f){if(!events.has(n))events.set(n,new Set());events.get(n).add(f)},removeEventListener(n,f){events.get(n)?.delete(f)}};
function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};cache.set(file,mod.exports);
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(mod,mod.exports,id=>{
  if(id.endsWith('/review'))return {reviewSession:async()=>({user_id:'synthetic-account'}),reviewRequest:(path,body,key)=>new Promise((resolve,reject)=>requests.push({path,body,key,resolve,reject}))};
  if(id.endsWith('/AvatarArt'))return {UserAvatar:()=>null};
  if(id==='react-router-dom')return router;
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(base+(fs.existsSync(base+'.tsx')?'.tsx':'.ts'))}return wr(id);
 });return mod.exports;
}
const {StudyComposer,StudyPostDetail}=load(root+'/web/src/components/StudyPosts.tsx'),{parseStudyReference}=load(root+'/web/src/lib/communityPosts.ts');
const policy={registered:true,can_create:true,old_enough:true,scored_attempts:50,weighted_helpful:0,needs_approval:true,post_limit:5,posts_remaining:5,reply_limit:30,replies_remaining:30,subjects:[{id:'english',label:'English'}]};
const post=(id,body)=>({id,body,author:'Synthetic author',created_at:'2026-11-17T10:00:00Z',is_author:false,needs_approval:false,topic_label:'English',reference:null,registered:true,helpful:0,voted:false});
let tree,saved=[];const text=n=>typeof n==='string'?n:(n?.children||[]).map(text).join(''),json=()=>JSON.stringify(tree.toJSON());
const button=label=>tree.root.findAllByType('button').find(n=>text(n)===label);
const wrap=element=>React.createElement(router.MemoryRouter,null,element);
async function mount(Component,props={}){await act(async()=>{tree?.unmount();tree=create(wrap(React.createElement(Component,{onClose(){},onSaved:id=>saved.push(id),...props})))})}
async function answer(value){const req=requests.shift();assert.ok(req,'Expected private request');await act(async()=>req.resolve(value));return req}
async function auth(){await act(async()=>{for(const fn of events.get('ism-auth-change')||[])fn()})}
async function type(body){await act(async()=>tree.root.findByType('textarea').props.onChange({target:{value:body}}))}
async function submit(){await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}))}
(async()=>{
 for(const [url,expected]of [
  ['/bank/cq_one?paper=source#discussion',{kind:'question',id:'cq_one'}],
  ['https://study.hawayu.in/materials/m_one',{kind:'material',id:'m_one'}],
  ['/exams/udc',{kind:'exam',id:'udc'}],
  ['/exams/udc/paper?paper=Old_Questions%2Fpaper.pdf',{kind:'paper',id:'Old_Questions/paper.pdf'}],
  ['/papers/source/Old_Questions/test%20paper.pdf',{kind:'paper',id:'Old_Questions/test paper.pdf'}]
 ])assert.deepEqual(parseStudyReference(url,'https://fixture.test'),expected);
 for(const url of ['https://example.test/bank/cq','//example.test/exams/udc','javascript:alert(1)','/creators/author','/bank/%ZZ'])assert.throws(()=>parseStudyReference(url,'https://fixture.test'));
 assert.equal(parseStudyReference(' ','https://fixture.test'),null);
 await mount(StudyComposer);await answer({...policy,can_create:false,scored_attempts:49});assert.ok(button('Post study note').props.disabled);assert.ok(json().includes('49'));assert.ok(json().includes('3 days and 50 scored attempts'));
 await mount(StudyComposer);await answer({...policy,registered:false});assert.equal(tree.root.findAllByType('form').length,0);assert.ok(json().includes('Sign in to write a note'));
 await mount(StudyComposer);await answer(policy);const draft='Synthetic draft retained for a safe retry.';await type(draft);
 const input=tree.root.findByType('input');await act(async()=>input.props.onChange({target:{value:'https://example.test/bank/cq'}}));await submit();assert.equal(requests.length,0);assert.ok(json().includes('Use a link to an item on Finna'));assert.ok(json().includes(draft));
 await act(async()=>input.props.onChange({target:{value:'/bank/cq_one'}}));await submit();let write=requests.shift();assert.deepEqual(write.body.reference,{kind:'question',id:'cq_one'});assert.equal(write.path,'/community/study-posts');const key=write.key;
 await act(async()=>write.reject(Error('Synthetic network failure')));assert.ok(json().includes(draft));await submit();write=requests.shift();assert.equal(write.key,key);await act(async()=>write.resolve({id:7}));assert.deepEqual(saved,[7]);
 // Late successful writes cannot navigate the newly signed-in account.
 await type('A second synthetic note for an account change.');await submit();const oldWrite=requests.shift();await auth();await act(async()=>oldWrite.resolve({id:8}));assert.deepEqual(saved,[7]);await answer({...policy,registered:false});assert.ok(!json().includes('A second synthetic note'));
 // Old policy reads and detail reads are also discarded.
 await mount(StudyComposer);const oldPolicy=requests.shift();await auth();await act(async()=>oldPolicy.resolve(policy));assert.equal(tree.root.findAllByType('form').length,0);await answer({...policy,registered:false});
 await mount(StudyPostDetail,{id:1});const first=requests.shift();await act(async()=>tree.update(wrap(React.createElement(StudyPostDetail,{id:2,onClose(){}}))));await act(async()=>first.resolve(post(1,'Previous note private text')));assert.ok(!json().includes('Previous note private text'));await answer(post(2,'Current visible study note'));assert.ok(json().includes('Current visible study note'));
 await act(async()=>button('Helpful').props.onClick());const reaction=requests.shift();assert.equal(reaction.path,'/community/study-posts/2/helpful');await act(async()=>reaction.reject(Error('Linked question is now protected')));assert.ok(!json().includes('Current visible study note'));assert.ok(json().includes('Linked question is now protected'));
 await mount(StudyPostDetail,{id:3});await answer(post(3,'Public synthetic reportable note'));
 await act(async()=>button('Report note').props.onClick());await type('Synthetic conduct details for the moderator.');await submit();let report=requests.shift();assert.equal(report.body.reason,'spam');await act(async()=>report.resolve({reported:true}));assert.ok(json().includes('Report saved for moderation'));
 await auth();assert.ok(!json().includes('Public synthetic reportable note'));await answer({...post(3,'Current public note'),registered:false});assert.ok(!button('Helpful'));assert.ok(json().includes('Sign in to vote or report'));
 await mount(StudyComposer,{kind:'material-share'});await answer(policy);assert.ok(json().includes('Share a reviewed material'));
 await type('Synthetic material recommendation retained on failure.');
 const materialInput=tree.root.findByType('input');assert.ok(materialInput.props.required);
 await act(async()=>materialInput.props.onChange({target:{value:'/bank/cq_one'}}));await submit();assert.equal(requests.length,0);assert.ok(json().includes('already-published Finna material'));
 await act(async()=>materialInput.props.onChange({target:{value:'/materials/m_one'}}));await submit();let shared=requests.shift();assert.equal(shared.body.kind,'material-share');assert.deepEqual(shared.body.reference,{kind:'material',id:'m_one'});const shareKey=shared.key;
 await act(async()=>shared.reject(Error('Publication no longer available')));assert.ok(json().includes('recommendation retained'));await submit();shared=requests.shift();assert.equal(shared.key,shareKey);await act(async()=>shared.resolve({id:9}));assert.deepEqual(saved,[7,9]);
 await mount(StudyPostDetail,{id:9});await answer({...post(9,'Synthetic public material recommendation'),kind:'material-share',reference:{kind:'material',id:'m_one',url:'/materials/m_one',label:'Reviewed synthetic guide'}});
 assert.ok(json().includes('Material share'));assert.ok(json().includes('Reviewed synthetic guide'));assert.ok(button('Report share'));assert.ok(!button('Report note'));
 await auth();assert.ok(!json().includes('Reviewed synthetic guide'));await answer({...post(9,'Owned synthetic share'),kind:'material-share',is_author:true});assert.ok(button('Withdraw share'));
 // A reload after an uncertain write restores both fields and the retry key.
 await mount(StudyComposer);await answer(policy);await type('Synthetic reload-safe formatted **study note**.');await submit();let uncertain=requests.shift(),reloadKey=uncertain.key;await act(async()=>uncertain.reject(Error('Uncertain write before reload')));
 await mount(StudyComposer);await answer(policy);assert.ok(json().includes('Synthetic reload-safe'));await submit();uncertain=requests.shift();assert.equal(uncertain.key,reloadKey);await act(async()=>uncertain.resolve({id:10}));assert.ok(!Object.keys(localStorage).some(k=>k.endsWith('post%3Astudy')));
 // An owned editor and its reply panel must retain distinct React identities.
 const warnings=[],originalError=console.error;console.error=(...args)=>{warnings.push(args.map(String).join(' '));originalError(...args)};
 await mount(StudyPostDetail,{id:9});await answer({...post(9,'An owned synthetic note.'),is_author:true});
 assert.equal(tree.root.findAllByType('button').filter(n=>text(n)==='Edit post').length,1);
 await act(async()=>button('Edit post').props.onClick());await type('A synthetic own edit stays in its one editor.');assert.equal(tree.root.findAllByType('textarea').length,1);
 console.error=originalError;assert.ok(!warnings.some(n=>n.includes('same key')),'An editor must not collide with the conversation panel key');
 await act(async()=>tree.unmount());assert.equal([...(events.get('ism-auth-change')||[])].length,0);assert.equal(requests.length,0);
 console.log('Study posts passed: owned entity links; maturity/guest controls; stable retry keys; retained error drafts; stale policy/write/detail rejection; protected-content clearing; report and signed-out actions.');
})().catch(e=>{console.error(e);process.exitCode=1});
