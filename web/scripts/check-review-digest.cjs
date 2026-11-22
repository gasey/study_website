// Exercise the actual preference and signed-out unsubscribe components.
const assert=require('node:assert/strict'),fs=require('node:fs'),root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
let reads=[],writes=[],listeners=new Map(),requests=[],replaced=[];
global.window={addEventListener(n,f){if(!listeners.has(n))listeners.set(n,new Set());listeners.get(n).add(f)},removeEventListener(n,f){listeners.get(n)?.delete(f)}};
global.location={hash:''};global.history={replaceState(...a){replaced.push(a)}};
global.fetch=(...args)=>new Promise((resolve,reject)=>requests.push({args,resolve,reject}));
const Link=({to,children,...props})=>React.createElement('a',{href:to,...props},children);
function load(file,extra={}){const mod={exports:{}};const code=ts.transpileModule(fs.readFileSync(root+'/web/src/'+file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(mod,mod.exports,id=>id.endsWith('/review')?{reviewRequest:(...args)=>new Promise((resolve,reject)=>(args.length>1?writes:reads).push({args,resolve,reject}))}:id==='react-router-dom'?{Link}:extra[id]||wr(id));return mod.exports.default;}
const Preference=load('components/ReviewDigestPreference.tsx');
const Screen=load('screens/EmailPreferences.tsx',{'../components/ReviewDigestPreference':{__esModule:true,default:Preference}});
const pref={user_id:'user-a',enabled:false,verified:true,available:true,version:0};let tree;
const json=()=>JSON.stringify(tree.toJSON()),button=t=>tree.root.findAllByType('button').find(b=>b.children.join('')===t);
async function reply(queue,value,error=false){assert.ok(queue.length);await act(async()=>{const r=queue.shift();error?r.reject(Error(value)):r.resolve(value)})}
async function click(text){const b=button(text);assert.ok(b,text);await act(async()=>void b.props.onClick())}
async function auth(){await act(async()=>{for(const f of [...listeners.get('ism-auth-change')||[]])f()})}
(async()=>{
 await act(async()=>tree=create(React.createElement(Preference)));assert.ok(json().includes('Loading email preferences'));
 await reply(reads,pref);assert.ok(json().includes('Off'));await click('Turn evening reminders on');
 assert.deepEqual(writes[0].args,['/review-digest/preferences',{user_id:'user-a',expected_version:0,enabled:true}]);
 assert.ok(button('Saving…').props.disabled);await reply(writes,{...pref,enabled:true,version:1});assert.ok(json().includes('Evening reminders are on'));
 await click('Turn reminders off');await auth();await reply(reads,{...pref,user_id:'user-b',available:false});await reply(writes,{...pref,enabled:false,version:2});
 assert.ok(!json().includes('Review reminders are off.'),'Prior account save must not update new identity');assert.ok(button('Turn evening reminders on').props.disabled);
 await auth();const stale=reads.shift();await auth();await reply(reads,{...pref,user_id:'user-c',enabled:true,available:false,version:4});await act(async()=>stale.resolve(pref));
 assert.ok(!button('Turn reminders off').props.disabled,'Opt-out stays available when delivery is paused');await click('Turn reminders off');assert.equal(writes[0].args[1].user_id,'user-c');
 await reply(writes,'Preferences changed; reload',true);assert.ok(json().includes('Preferences changed; reload'));await click('Reload preferences');await reply(reads,{...pref,verified:false});assert.ok(button('Turn evening reminders on').props.disabled);
 await act(async()=>tree.unmount());assert.equal(listeners.get('ism-auth-change').size,0);
 location.hash='#unsubscribe=synthetic-private-capability';await act(async()=>tree=create(React.createElement(Screen)));
 assert.equal(requests.length,0,'Opening a link/prefetch must not unsubscribe');assert.equal(reads.length,0,'Signed-out unsubscribe must not request private preferences');
 assert.ok(!json().includes('synthetic-private-capability'));await click('Unsubscribe');assert.equal(requests[0].args[1].credentials,'omit');assert.equal(requests[0].args[1].method,'POST');
 await reply(requests,{ok:false});assert.ok(json().includes('could not be used'));await click('Unsubscribe');await reply(requests,{ok:true});
 assert.ok(json().includes('Review reminders are off'));assert.equal(replaced[0][2],'/account/email-preferences');assert.equal(button('Unsubscribe'),undefined);
 await act(async()=>tree.unmount());assert.equal(requests.length,0);console.log('Actual digest preference/unsubscribe components pass: default off, explicit consent, version/account binding, stale response isolation, withdrawal during pause, verified gating, signed-out no-cookie POST, inert link opening, error/retry and fragment clearing.');
})().catch(e=>{console.error(e);process.exitCode=1});
