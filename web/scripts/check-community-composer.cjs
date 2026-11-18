// Real hook/storage/rendering with private identity resolution delayed across accounts.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]})),{renderToStaticMarkup}=wr('react-dom/server');
const events=new Map(),sessions=[],cache=new Map();let storageFails=false,reloads=0;
global.crypto||=require('node:crypto').webcrypto;
class Storage{getItem(k){if(storageFails)throw Error('Storage disabled');return Object.hasOwn(this,k)?this[k]:null}setItem(k,v){if(storageFails)throw Error('Storage disabled');this[k]=String(v)}removeItem(k){if(storageFails)throw Error('Storage disabled');delete this[k]}}
global.localStorage=new Storage();global.window={location:{origin:'https://fixture.test',reload(){reloads++}},addEventListener(n,f){if(!events.has(n))events.set(n,new Set());events.get(n).add(f)},removeEventListener(n,f){events.get(n)?.delete(f)}};
function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};cache.set(file,mod.exports);
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(mod,mod.exports,id=>{
  if(id.endsWith('/review'))return {reviewSession:()=>new Promise((resolve,reject)=>sessions.push({resolve,reject}))};
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(base+(fs.existsSync(base+'.tsx')?'.tsx':'.ts'))}return wr(id);
 });return mod.exports;
}
const {useComposerDraft}=load(root+'/web/src/lib/useComposerDraft.ts'),storage=load(root+'/web/src/lib/communityDrafts.ts'),{default:CommunityText}=load(root+'/web/src/components/CommunityText.tsx');
let tree,draft;function Harness({scope='post:study',enabled=true}){draft=useComposerDraft(scope,enabled);return React.createElement('textarea',{value:draft.fields.body,onChange:e=>draft.update({body:e.target.value})})}
async function mount(props={}){await act(async()=>{tree?.unmount();tree=create(React.createElement(Harness,props))})}
async function identity(user='account-A'){const next=sessions.shift();assert.ok(next);await act(async()=>next.resolve({user_id:user,csrf:'NEVER_STORE_CSRF'}))}
async function update(fields){await act(async()=>draft.update(fields))}
async function event(name,arg){await act(async()=>{for(const fn of events.get(name)||[])fn(arg)})}
const keys=()=>Object.keys(localStorage).filter(n=>n.startsWith(storage.DRAFT_PREFIX));
(async()=>{
 const html=renderToStaticMarkup(React.createElement(CommunityText,{body:'**Read carefully**\n- First item\n- Second item\n\n3. Third item\n4. Fourth item\n\n`<img src=x onerror=alert(1)>`\n<script>alert(1)</script>\n[Link](javascript:alert(1))'}));
 assert.ok(html.includes('<strong>Read carefully</strong>'));assert.ok(html.includes('<ul'));assert.ok(html.includes('<ol start="3"'));assert.ok(html.includes('<code'));assert.ok(!html.includes('<script'));assert.ok(!html.includes('<img'));assert.ok(!html.includes('<a '));assert.ok(html.includes('&lt;script&gt;'));assert.ok(html.includes('[Link](javascript:alert(1))'));
 const literal=renderToStaticMarkup(React.createElement(CommunityText,{body:'No unmatched ** marker or ` code is lost.\nLine two'}));assert.ok(literal.includes('unmatched ** marker'));assert.ok(literal.includes('Line two'));
 await mount();assert.equal(draft.status,'checking');await identity();await update({body:'**Synthetic saved note**',subject:'english',link:'/bank/cq_fixture'});assert.equal(draft.status,'saved');let key;await act(async()=>{key=draft.requestKey('synthetic exact payload')});assert.equal(keys().length,1);assert.ok(!JSON.stringify(localStorage).includes('NEVER_STORE_CSRF'));
 await mount();await identity();assert.equal(draft.status,'restored');assert.equal(draft.fields.body,'**Synthetic saved note**');assert.equal(draft.fields.subject,'english');assert.equal(draft.fields.link,'/bank/cq_fixture');await act(async()=>assert.equal(draft.requestKey('synthetic exact payload'),key));
 // Separate post kinds, parent threads and authoritative account identities.
 await mount({scope:'post:material-share'});await identity();assert.equal(draft.fields.body,'');await update({body:'Synthetic material recommendation',link:'/materials/reviewed'});
 await mount({scope:'reply:1'});await identity();assert.equal(draft.fields.body,'');await update({body:'Synthetic reply for parent one'});
 await mount({scope:'reply:2'});await identity();assert.equal(draft.fields.body,'');
 await mount();await identity('account-B');assert.equal(draft.fields.body,'');await update({body:'Account B synthetic draft'});
 await mount();await identity();assert.equal(draft.fields.body,'**Synthetic saved note**');await act(async()=>draft.clear());assert.equal(draft.fields.body,'');assert.equal(storage.readComposerDraft('account-A','post:study'),null);assert.ok(storage.readComposerDraft('account-B','post:study'));
 // Input typed while identity is loading takes precedence over an older draft.
 await mount({scope:'reply:1'});await update({body:'New synthetic text typed during identity lookup'});await identity();assert.equal(draft.fields.body,'New synthetic text typed during identity lookup');
 // Account transitions synchronously clear all stored composer drafts and cancel old reads.
 await mount();const late=sessions.shift();await event('ism-auth-change');assert.equal(keys().length,0);await act(async()=>late.resolve({user_id:'account-A'}));assert.equal(draft.fields.body,'');assert.equal(keys().length,0);
 await mount();await identity();await update({body:'Synthetic draft before expiry'});await event('ism-auth-expired');assert.equal(draft.fields.body,'');assert.equal(keys().length,0);
 await mount({enabled:false});assert.equal(sessions.length,0);await update({body:'Unsaved guest input'});assert.equal(keys().length,0);
 // Broken storage cannot erase input or prevent the composer from posting.
 storageFails=true;await mount();await identity();await update({body:'Synthetic in-memory fallback draft'});assert.equal(draft.status,'unavailable');assert.equal(draft.fields.body,'Synthetic in-memory fallback draft');storageFails=false;
 const saved={version:1,owner:'account-A',scope:'post:study',updated:Date.now(),fields:{body:'Synthetic record',subject:'',link:''},retry:{payload:'',key:crypto.randomUUID()}};
 localStorage.setItem(storage.draftKey('account-A','post:study'),JSON.stringify({...saved,owner:'other-account'}));assert.equal(storage.readComposerDraft('account-A','post:study'),null);
 localStorage.setItem(storage.draftKey('account-A','post:study'),JSON.stringify({...saved,updated:Date.now()-8*86400000}));assert.equal(storage.readComposerDraft('account-A','post:study'),null);
 localStorage.setItem(storage.draftKey('account-A','post:study'),'{bad json');assert.equal(storage.readComposerDraft('account-A','post:study'),null);
 const discussion={kind:'explanation',sources:[{url:'https://example.test/source',note:'Own synthetic citation'}]};
 storage.writeComposerDraft({...saved,scope:'question:synthetic',fields:{...saved.fields,discussion},retry:{payload:JSON.stringify({body:'"'.repeat(5000),sources:Array(5).fill({url:'https://example.test/'+'x'.repeat(1900),note:'"'.repeat(1000)})}),key:saved.retry.key}});assert.deepEqual(storage.readComposerDraft('account-A','question:synthetic').fields.discussion,discussion);
 for(const invalid of [{kind:'reply',sources:[]},{kind:'doubt',sources:Array(6).fill({url:'',note:''})},{kind:'doubt',sources:[{url:42,note:''}]},{kind:'doubt',sources:[{url:'',note:'x'.repeat(1001)}]}]){
  localStorage.setItem(storage.draftKey('account-A','question:synthetic'),JSON.stringify({...saved,scope:'question:synthetic',fields:{...saved.fields,discussion:invalid}}));assert.equal(storage.readComposerDraft('account-A','question:synthetic'),null);
 }
 storage.writeComposerDraft({...saved,scope:'question:source-only',fields:{...storage.emptyComposerFields(),discussion:{kind:'doubt',sources:[{url:'',note:''}]}}});assert.ok(storage.readComposerDraft('account-A','question:source-only'),'Incomplete own citation inputs survive reload');
 for(let i=0;i<40;i++)storage.writeComposerDraft({...saved,scope:'reply:'+i});assert.equal(keys().length,32);
 await act(async()=>tree.unmount());load(root+'/web/src/lib/accountContext.ts');localStorage.setItem('unrelated-preference','keep');await event('ism-auth-change');assert.equal(keys().length,0);assert.equal(localStorage.getItem('unrelated-preference'),'keep');
 storage.writeComposerDraft(saved);await event('storage',{key:'ism.account-change'});assert.equal(keys().length,0);assert.equal(reloads,1);
 console.log('Composer checks passed: semantic safe markdown, literal HTML/URLs, bounded draft records, expiry/malformed rejection, private account/kind/parent isolation, reload restoration, retry-key continuity, discard/success clearing, late-identity protection, sign-out/expiry/cross-tab purge and storage-denied fallback.');
})().catch(e=>{console.error(e);process.exitCode=1});
