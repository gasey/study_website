// Actual React components with synthetic transports; no provider calls.
const assert=require('node:assert/strict'),fs=require('node:fs'),root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
let statuses=[],declarations=[],reads=[],writes=[],listeners=new Map();
global.window={addEventListener(n,f){if(!listeners.has(n))listeners.set(n,new Set());listeners.get(n).add(f)},removeEventListener(n,f){listeners.get(n)?.delete(f)}};
const Link=({to,children,...props})=>React.createElement('a',{href:to,...props},children);
function load(file,extra={}){const mod={exports:{}};const code=ts.transpileModule(fs.readFileSync(root+'/web/src/'+file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(mod,mod.exports,id=>extra[id]||id.endsWith('/privacy')?extra[id]||{privacyStatus:()=>new Promise((resolve,reject)=>statuses.push({resolve,reject})),declareAge:(...args)=>new Promise((resolve,reject)=>declarations.push({args,resolve,reject}))}:id.endsWith('/review')?{reviewRequest:(...args)=>new Promise((resolve,reject)=>(args.length>1?writes:reads).push({args,resolve,reject}))}:id==='react-router-dom'?{Link,useParams:()=>({page:'refunds'})}:wr(id));return mod.exports;}
const ageModule=load('components/AgeCategoryCheck.tsx'),Age=ageModule.default,AudienceNotice=ageModule.AudienceNotice;
const Page=load('screens/AccountPrivacy.tsx',{'../components/AgeCategoryCheck':{__esModule:true,default:()=>null}}).default;
let policyPage='refunds';
const Policies=load('screens/PolicyPages.tsx',{'react-router-dom':{Link,useParams:()=>({page:policyPage})}}).default;
const status={user_id:null,category:null,version:0,browser_category:null,age_check_enabled:true,guardian_enrollment_available:false,support_email:'hruaitluangasailo20@gmail.com'};
let tree;const json=()=>JSON.stringify(tree.toJSON()),button=text=>tree.root.findAllByType('button').find(x=>x.children.join('')===text);
async function reply(queue,value,fail=false){assert.ok(queue.length,'expected request');await act(async()=>{const item=queue.shift();fail?item.reject(Error(value)):item.resolve(value)})}
async function click(text){const b=button(text);assert.ok(b,text);await act(async()=>void b.props.onClick())}
async function auth(){await act(async()=>{for(const fn of [...listeners.get('ism-auth-change')||[]])fn()})}
(async()=>{
 const ready=[];const onReady=x=>ready.push(x);
 await act(async()=>tree=create(React.createElement(Age,{onReady})));assert.equal(ready.at(-1),false);
 await reply(statuses,status);await click('I am under 18');assert.deepEqual(declarations[0].args,[status,'under18']);
 await reply(declarations,{});await reply(statuses,{...status,browser_category:'under18'});assert.equal(ready.at(-1),false);assert.ok(json().includes('no new learner account was created'));assert.ok(json().includes('Under-18 enrollment is not supported'));assert.ok(!json().includes('being prepared'));
 await click('I am 18 or over');await auth();await reply(declarations,{});await reply(statuses,{...status,user_id:'other',category:'under18',version:1});await reply(statuses,{...status,browser_category:'adult'});
 assert.equal(ready.at(-1),false,'stale adult response cannot unlock another account');assert.ok(button('I am 18 or over').props.disabled);assert.ok(json().includes('existing account and data'));assert.ok(!json().includes('no new learner account was created'));
 await auth();await reply(statuses,{...status,age_check_enabled:false});assert.equal(tree.toJSON(),null);assert.equal(ready.at(-1),true);await act(async()=>tree.unmount());
 await act(async()=>tree=create(React.createElement(AudienceNotice)));await reply(statuses,{...status,user_id:'minor',category:'under18'});assert.ok(json().includes('Under-18 study access is not supported'));assert.ok(!json().includes('waiting for guardian'));await act(async()=>tree.unmount());
 statuses=[];reads=[];writes=[];
 await act(async()=>tree=create(React.createElement(Page)));await reply(statuses,{...status,user_id:'user-a'});await reply(reads,{user_id:'user-a',items:[]});
 assert.ok(!tree.root.findAllByType('option').some(x=>x.props.value==='guardian'),'new guardian requests are not offered');
 async function submit(){await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}))}
 await submit();const first=writes[0].args[1];assert.equal(first.user_id,'user-a');assert.equal(first.kind,'access');assert.ok(first.request_key);
 await reply(writes,'Connection interrupted',true);await submit();assert.equal(writes[0].args[1].request_key,first.request_key,'retry preserves idempotency key');
 await reply(writes,{id:'request-a'});await reply(reads,{user_id:'user-a',items:[{id:'request-a',kind:'access',state:'received',version:1,created_at:'2026-11-20T00:00:00Z'}]});
 assert.ok(json().includes('does not automatically export or erase data'));await click('Withdraw request');assert.deepEqual(writes[0].args[1],{user_id:'user-a',expected_version:1,state:'withdrawn'});
 await auth();await reply(writes,{});await reply(statuses,{...status,user_id:'user-b'});await reply(reads,{user_id:'user-a',items:[{id:'OLD_PRIVATE_REFERENCE',kind:'erasure',state:'withdrawn',version:2,created_at:'2026-11-20T00:00:00Z'}]});await reply(reads,{user_id:'user-b',items:[]});
 assert.ok(!json().includes('OLD_PRIVATE_REFERENCE'));assert.ok(json().includes('No requests to show'));await act(async()=>tree.unmount());
 await act(async()=>tree=create(React.createElement(Policies)));assert.ok(json().includes('any reason within seven days'));assert.ok(json().includes('no publication effective date'));assert.ok(json().includes('does not promise a fixed support response deadline'));await act(async()=>tree.unmount());
 policyPage='terms';await act(async()=>tree=create(React.createElement(Policies)));assert.ok(json().includes('Finna is for people aged 18 or over'));assert.ok(json().includes('Guardian enrollment is not offered'));await act(async()=>tree.unmount());
 policyPage='privacy';await act(async()=>tree=create(React.createElement(Policies)));assert.ok(json().includes('Under-18 enrollment and study access are not supported'));await act(async()=>tree.unmount());
 assert.equal(listeners.get('ism-auth-change').size,0);
 console.log('Privacy components pass: adult-only age boundary/notices/policy previews, no new guardian requests, disabled gate compatibility, stale-account isolation, declaration binding, request retry key, withdrawal/version binding, response isolation and cleanup.');
})().catch(e=>{console.error(e);process.exitCode=1});
