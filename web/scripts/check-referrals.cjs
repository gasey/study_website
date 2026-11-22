// Actual React components, synthetic requests only.
const assert=require('node:assert/strict'),fs=require('node:fs'),root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
let reads=[],writes=[],listeners=new Map(),requests=[];
global.window={location:{origin:'https://example.test'},addEventListener(n,f){if(!listeners.has(n))listeners.set(n,new Set());listeners.get(n).add(f)},removeEventListener(n,f){listeners.get(n)?.delete(f)}};
global.fetch=(...args)=>new Promise((resolve,reject)=>requests.push({args,resolve,reject}));
const Link=({to,children,...props})=>React.createElement('a',{href:to,...props},children);
function load(file,extra={}){const mod={exports:{}};const code=ts.transpileModule(fs.readFileSync(root+'/web/src/'+file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(mod,mod.exports,id=>id.endsWith('/review')?{reviewRequest:(...args)=>new Promise((resolve,reject)=>(args.length>1?writes:reads).push({args,resolve,reject}))}:id==='react-router-dom'?{Link}:extra[id]||wr(id));return mod.exports;}
const {default:Panel,SignupReferral}=load('components/ReferralPanel.tsx');
const initial={user_id:'user-a',available:true,verified:true,code:null,credited_this_rolling_year:0,signup_referral:null};let tree;
const json=()=>JSON.stringify(tree.toJSON()),button=t=>tree.root.findAllByType('button').find(b=>b.children.join('')===t);
async function reply(queue,value,error=false){assert.ok(queue.length);await act(async()=>{const r=queue.shift();error?r.reject(Error(value)):r.resolve(value)})}
async function click(text){const b=button(text);assert.ok(b,text);await act(async()=>void b.props.onClick())}
async function auth(){await act(async()=>{for(const f of [...listeners.get('ism-auth-change')||[]])f()})}
(async()=>{
 await act(async()=>tree=create(React.createElement(Panel)));assert.ok(json().includes('Loading invitations'));
 await reply(reads,{...initial,available:false});assert.ok(button('Create invitation link').props.disabled);assert.ok(json().includes('after paid plans launch'));
 await auth();await reply(reads,initial);await click('Create invitation link');assert.deepEqual(writes[0].args,['/referrals/code',{user_id:'user-a',expected_version:0,enabled:true}]);
 const code={code:'A'.repeat(24),version:1,enabled:true};await reply(writes,{...initial,code});assert.equal(tree.root.findByProps({'aria-label':'Your invitation link'}).props.value,'https://example.test/join?ref='+code.code);
 await click('Turn invitation link off');await auth();await reply(reads,{...initial,user_id:'user-b',code,available:false});await reply(writes,{...initial,code:{...code,enabled:false}});
 assert.ok(button('Turn invitation link off'),'Prior account reply must not change current account');assert.ok(!button('Turn invitation link off').props.disabled);
 await click('Turn invitation link off');assert.equal(writes[0].args[1].user_id,'user-b');await reply(writes,'Conflict; reload',true);assert.ok(json().includes('Conflict; reload'));
 await click('Reload invitations');await reply(reads,{...initial,verified:false});assert.ok(button('Create invitation link').props.disabled);assert.ok(json().includes('Verify your email'));
 await auth();const stale=reads.shift();await auth();await reply(reads,{...initial,signup_referral:{state:'credited',scored_attempts:10}});await act(async()=>stale.resolve({...initial,code}));assert.ok(!json().includes('Your invitation link'));assert.ok(json().includes('added 7 Pro days'));
 assert.ok(tree.root.findAllByType('a').some(a=>a.props.href==='/billing'));await act(async()=>tree.unmount());assert.equal(listeners.get('ism-auth-change').size,0);
 let removed=0;await act(async()=>tree=create(React.createElement(SignupReferral,{code:'A'.repeat(24),onRemove:()=>removed++})));
 assert.equal(requests[0].args[1].credentials,'omit');assert.equal(writes.length,0);const first=requests.shift();
 await act(async()=>tree.update(React.createElement(SignupReferral,{code:'B'.repeat(24),onRemove:()=>removed++})));
 await reply(requests,{ok:true,json:async()=>({available:false})});await act(async()=>first.resolve({ok:true,json:async()=>({available:true})}));assert.ok(json().includes('unavailable for this link'));
 await click('Remove invitation');assert.equal(removed,1);
 await act(async()=>tree.update(React.createElement(SignupReferral,{code:'B'.repeat(24),disabled:true,onRemove:()=>removed++})));assert.ok(button('Remove invitation').props.disabled);await act(async()=>tree.unmount());
 const Google=load('components/GoogleSignIn.tsx',{'../lib/accountContext':{accountContext:async()=>({csrf:'synthetic'})},'../lib/mobileReturn':{mobileReturn:()=>null}}).default;
 let assigned=[],busy=[];window.location.assign=url=>assigned.push(url);global.sessionStorage={setItem(){},removeItem(){}};
 await act(async()=>tree=create(React.createElement(Google,{referralCode:'A'.repeat(24),onBusyChange:v=>busy.push(v)})));
 await reply(requests,{ok:true,json:async()=>({enabled:true})});await click('Continue with Google');assert.ok(button('Opening Google…').props.disabled);assert.deepEqual(busy,[true]);
 assert.deepEqual(JSON.parse(requests[0].args[1].body),{action:'login',referral_code:'A'.repeat(24)});
 await act(async()=>tree.update(React.createElement(Google,{referralCode:'B'.repeat(24),onBusyChange:v=>busy.push(v)})));
 await reply(requests,{ok:false,json:async()=>({detail:'Synthetic sign-in failure'})});assert.deepEqual(busy,[true,false]);assert.ok(json().includes('Synthetic sign-in failure'));
 await click('Continue with Google');assert.equal(JSON.parse(requests[0].args[1].body).referral_code,'B'.repeat(24));await reply(requests,{ok:true,json:async()=>({url:'https://accounts.google.com/synthetic'})});assert.deepEqual(assigned,['https://accounts.google.com/synthetic']);await act(async()=>tree.unmount());
 await act(async()=>tree=create(React.createElement(Google,{link:true,referralCode:'B'.repeat(24)})));await reply(requests,{ok:true,json:async()=>({enabled:true})});await click('Link Google to this account');assert.deepEqual(JSON.parse(requests[0].args[1].body),{action:'link'});await reply(requests,{ok:true,json:async()=>({url:'https://accounts.google.com/synthetic-link'})});await act(async()=>tree.unmount());
 console.log('Three actual referral/signup/Google components pass: launch and verification gates, explicit creation/withdrawal, CAS/account binding, paused withdrawal, stale request isolation, optional signup removal locked during submission, Google code forwarding/retry/busy state and omission when linking, no implicit writes.');
})().catch(e=>{console.error(e);process.exitCode=1});
