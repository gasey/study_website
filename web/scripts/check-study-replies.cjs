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
const StudyReplies=load(root+'/web/src/components/StudyReplies.tsx').default;
const policy={registered:true,can_create:true,old_enough:true,scored_attempts:50,weighted_helpful:0,needs_approval:true,post_limit:5,posts_remaining:5,reply_limit:30,replies_remaining:30,subjects:[{id:'english',label:'English'}]};
const post=(id,body)=>({id,body,author:'Synthetic author',created_at:'2026-11-17T10:00:00Z',is_author:false,needs_approval:false,topic_label:'English',reference:null,registered:true,helpful:0,voted:false});
let tree,saved=[],unavailable=[];const text=n=>typeof n==='string'?n:(n?.children||[]).map(text).join(''),json=()=>JSON.stringify(tree.toJSON());
const button=label=>tree.root.findAllByType('button').find(n=>text(n)===label);
const wrap=element=>React.createElement(router.MemoryRouter,null,element);
async function mount(Component,props={}){await act(async()=>{tree?.unmount();tree=create(wrap(React.createElement(Component,{id:1,onUnavailable:message=>unavailable.push(message),onClose(){},onSaved:id=>saved.push(id),...props})))})}
async function answer(value){const req=requests.shift();assert.ok(req,'Expected private request');await act(async()=>req.resolve(value));return req}
async function auth(){await act(async()=>{for(const fn of events.get('ism-auth-change')||[])fn()})}
async function type(body){await act(async()=>tree.root.findByType('textarea').props.onChange({target:{value:body}}))}
async function submit(){await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}))}
const page=(items=[],more=false)=>({items,has_more:more,registered:true,can_reply:true,replies_remaining:30,reply_limit:30});
const row=(id,body='Synthetic visible reply')=>({id,body,author:'Synthetic respondent',created_at:'2026-11-17T10:00:00Z',is_author:false,needs_approval:false,helpful:0,voted:false});
async function open(){await act(async()=>button('Show replies').props.onClick())}
(async()=>{
 await mount(StudyReplies);assert.equal(requests.length,0);await open();assert.equal(requests[0].path,'/community/study-posts/1/replies?offset=0');await answer(page());assert.ok(json().includes('No visible replies'));assert.ok(button('Post reply'));
 await type('Synthetic draft retained across an uncertain reply request.');await submit();let write=requests.shift();const key=write.key;assert.equal(write.path,'/community/study-posts/1/replies');await act(async()=>write.reject(Error('Synthetic network failure')));await answer(page());assert.ok(json().includes('Synthetic draft retained'));await submit();write=requests.shift();assert.equal(write.key,key);await act(async()=>write.resolve({id:2,needs_approval:true}));await answer(page([{...row(2,'Pending synthetic response'),is_author:true,needs_approval:true}]));assert.ok(json().includes('awaiting moderation'));assert.ok(button('Withdraw reply'));
 await act(async()=>button('Withdraw reply').props.onClick());assert.equal(requests[0].path,'/community/study-posts/2/withdraw');await answer({withdrawn:true});await answer(page());
 // Pagination appends chronological results and removes duplicates.
 await mount(StudyReplies);await open();await answer(page([row(3)],true));await act(async()=>button('Load more replies').props.onClick());assert.ok(requests[0].path.endsWith('offset=20'));await answer(page([row(3),row(4)]));assert.equal(tree.root.findAllByType('article').length,2);
 await act(async()=>tree.root.findAllByType('button').find(n=>text(n)==='Helpful reply').props.onClick());const vote=requests.shift();assert.equal(vote.path,'/community/study-posts/3/helpful');await act(async()=>vote.reject(Error('Parent question became protected')));assert.deepEqual(unavailable,['Parent question became protected']);assert.ok(!json().includes('Synthetic visible reply'));
 // Old reads and successful writes cannot carry a draft or content to another account.
 await mount(StudyReplies);await open();const oldRead=requests.shift();await auth();await act(async()=>oldRead.resolve(page([row(5,'Previous account private reply')])));assert.ok(!json().includes('Previous account private reply'));assert.ok(button('Show replies'));
 await open();await answer(page());await type('Previous account private draft');await submit();const oldWrite=requests.shift();await auth();await act(async()=>oldWrite.resolve({id:8,needs_approval:false}));assert.ok(!json().includes('Previous account private draft'));assert.equal(requests.length,0);
 await open();await answer({...page(),registered:false,can_reply:false});assert.equal(tree.root.findAllByType('form').length,0);assert.ok(json().includes('Sign in to reply'));
 await mount(StudyReplies);await open();await answer({...page(),can_reply:false});assert.ok(button('Post reply').props.disabled);assert.ok(json().includes('restricted'));
 await mount(StudyReplies);await open();await answer({...page(),replies_remaining:0});assert.ok(button('Post reply').props.disabled);
 await mount(StudyReplies);await open();await answer(page([row(6)]));await act(async()=>button('Report reply').props.onClick());await act(async()=>tree.root.findAllByType('textarea')[0].props.onChange({target:{value:'Synthetic reply conduct report details.'}}));await act(async()=>tree.root.findAllByType('form')[0].props.onSubmit({preventDefault(){}}));assert.equal(requests[0].path,'/community/study-posts/6/report');assert.equal(requests[0].body.reason,'spam');await answer({reported:true});await answer(page([row(6)]));assert.ok(json().includes('Reply report saved'));
 // The reply draft and retry key survive a page remount as one record.
 await type('Synthetic **reply** survives an uncertain network write.');await submit();let uncertain=requests.shift(),reloadKey=uncertain.key;await act(async()=>uncertain.reject(Error('Uncertain reply before reload')));await answer(page([row(6)]));
 await mount(StudyReplies);await open();await answer(page([row(6)]));assert.ok(json().includes('survives an uncertain'));await submit();uncertain=requests.shift();assert.equal(uncertain.key,reloadKey);await act(async()=>uncertain.resolve({id:11,needs_approval:false}));await answer(page([row(6)]));assert.ok(!Object.keys(localStorage).some(k=>k.endsWith('reply%3A1')));
 await act(async()=>tree.unmount());assert.equal(requests.length,0);assert.equal([...(events.get('ism-auth-change')||[])].length,0);
 console.log('Study replies passed: on-demand private reads, shared budget/guest/sanction controls, chronological pagination/dedup, retry drafts/keys, moderation/withdraw/report, stale reads/writes/account clearing and privacy-failure removal.');
})().catch(e=>{console.error(e);process.exitCode=1});
