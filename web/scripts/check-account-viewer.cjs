// Render actual account viewer, using deferred responses across navigation/auth.
const assert=require('node:assert/strict'),fs=require('node:fs'),root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]})),router=wr('react-router-dom');
let calls=[],epoch=0,events=new Map(),navigate;
global.window={addEventListener(n,f){if(!events.has(n))events.set(n,new Set());events.get(n).add(f)},removeEventListener(n,f){events.get(n)?.delete(f)}};
const source=fs.readFileSync(root+'/web/src/components/AccountViewer.tsx','utf8'),code=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText,mod={exports:{}};
new Function('module','exports','require',code)(mod,mod.exports,id=>id.endsWith('/review')?{reviewRequest:(...args)=>new Promise((resolve,reject)=>calls.push({args,resolve,reject}))}:id.endsWith('/accountContext')?{accountGeneration:()=>epoch}:id==='react-router-dom'?router:wr(id));
const Viewer=mod.exports.default;
function Harness(){navigate=router.useNavigate();return React.createElement(Viewer)}
let tree;const json=()=>JSON.stringify(tree.toJSON()),button=t=>tree.root.findAllByType('button').find(b=>(b.children||[]).join('')===t);
const member={id:'member',email:'PRIVATE_PREVIOUS_ACCOUNT@example.test',handle:'member',role:'learner',created_at:'2026-11-01T00:00:00Z',email_verified_at:null,mfa_enabled:false,web_sessions:1,mobile_sessions:0,last_activity_at:null,roles:[]};
const data={observed_at:'2026-11-18T00:00:00Z',read_only:true,account:member,access:{has_pro:false,status:'free',amount_paise:5000,trial_ends_at:null,plan_ends_at:null,subscription_reference:null,grants:[],redemptions:[],grants_more:false,redemptions_more:false},study:{attempts:0,verified_correct:0,streak:{current_streak_days:0,longest_streak_days:0},mastery:[],exams:[],exams_more:false},economy:{points:0,xp:0,cap_days:0,ledger:[]},community:{posts:0,replies:0,helpful_received:0,weighted_helpful:0,display_tier:null,needs_approval:true,can_create:false,sanctioned:false,blocks_given:0,blocks_received:0,post_reports:0,material_reports:0,profile_reports:0}};
async function settle(value,error=false){await act(async()=>{const c=calls.shift();error?c.reject(Error(value)):c.resolve(value)})}
(async()=>{
 await act(async()=>{tree=create(React.createElement(router.MemoryRouter,{initialEntries:['/admin/users']},React.createElement(Harness)))});
 assert.equal(calls.length,0);assert.ok(button('Search accounts').props.disabled);
 await act(async()=>tree.root.findByType('input').props.onChange({target:{value:'member'}}));
 await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}));assert.equal(calls[0].args[0],'/admin/users?q=member');
 await settle({items:[member],more:true});assert.ok(json().includes('Enter more of the handle'));assert.ok(json().includes('PRIVATE_PREVIOUS_ACCOUNT'));
 await act(async()=>navigate('?user=member'));assert.equal(calls[0].args[0],'/admin/users/member');assert.ok(!json().includes('PRIVATE_PREVIOUS_ACCOUNT'));
 await settle(data);for(const label of ['Account · @','Access','Study','Economy','Community','Existing account tools','No ledger receipts','No saved or primary exam','None recorded'])assert.ok(json().includes(label),label);
 const paths=tree.root.findAllByType('a').map(a=>a.props.href);assert.ok(paths.includes('/admin/bank?tab=rewards'));assert.ok(paths.includes('/admin/bank?tab=workflow'));
 await act(async()=>button('Refresh account').props.onClick());assert.ok(!json().includes('PRIVATE_PREVIOUS_ACCOUNT'));
 await settle('Database unavailable',true);assert.ok(json().includes('Database unavailable'));assert.ok(!json().includes('No ledger receipts'));
 await act(async()=>button('Retry').props.onClick());
 await act(async()=>navigate('?user=other'));assert.equal(calls.length,2);
 await settle(data);assert.ok(!json().includes('PRIVATE_PREVIOUS_ACCOUNT'),'Earlier selected account response suppressed');
 epoch++;await act(async()=>{for(const fn of [...events.get('ism-auth-change')])fn()});await settle({...data,account:{...member,id:'other'}});assert.ok(!json().includes('PRIVATE_PREVIOUS_ACCOUNT'),'Old authenticated account response suppressed');assert.equal(calls.length,0);
 await act(async()=>tree.unmount());console.log('Account viewer component passed: explicit search, bounded results, direct account, truthful empty/outage states, tool links, refresh, navigation and auth stale-response suppression.');
})().catch(e=>{console.error(e);process.exitCode=1});
