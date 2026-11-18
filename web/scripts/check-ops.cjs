// Render the real ops component: unknown/error states and account transitions.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]})),router=wr('react-router-dom');
const events=new Map();let epoch=0,calls=[];
global.window={addEventListener(n,f){if(!events.has(n))events.set(n,new Set());events.get(n).add(f)},removeEventListener(n,f){events.get(n)?.delete(f)}};
const code=ts.transpileModule(fs.readFileSync(root+'/web/src/components/OpsDashboard.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
const mod={exports:{}};
new Function('module','exports','require',code)(mod,mod.exports,id=>id==='./SiteNoticeAdmin'?{default:()=>null}:id.endsWith('/review')?{reviewRequest:(...args)=>new Promise((resolve,reject)=>calls.push({args,resolve,reject}))}:id.endsWith('/accountContext')?{accountGeneration:()=>epoch}:id==='react-router-dom'?router:wr(id));
const Ops=mod.exports.default;
const beat={id:'x',label:'Uninstrumented worker',last_beat:null,last_ok:null,note:null,state:'unknown',stale_after_seconds:60};
const data={observed_at:'2026-11-18T08:00:00Z',read_only:true,workers:[beat],timers:[{...beat,id:'timer:x',label:'Backup timer'}],probes:{api:'responding',database:'query succeeded',pool:{size:2,available:1,waiting:0,max:6},pool_scope:'Current process.',disk:{state:'healthy',note:'Measured available host space',free_bytes:14*1024**3,total_bytes:96*1024**3,last_beat:'2026-11-18T08:00:00Z',last_ok:'2026-11-18T08:00:00Z'},backup:{state:'healthy',note:'Verified paired backup',last_beat:'2026-11-18T08:00:00Z',last_ok:'2026-11-17T20:00:00Z'},webhooks:{state:'disabled',count_24h:null}},economy:{day:'2026-11-17',minted_points:10,minted_xp:100,receipts:4,redemptions:0,redeemed_points:0,cap_accounts:1,cap_streaks:[{user_id:'PRIVATE_OLD_OWNER_RESULT',days:7}],cap_streaks_more:false,new_account_velocity:[],new_account_velocity_more:false,velocity_rule:'Review only',cap_rule:'Recorded cap',mint_rule:'Positive amounts'},moderation:[{queue:'questions',open:0,median_hours:null,over_48h:0}]};
let tree;const json=()=>JSON.stringify(tree.toJSON()),text=n=>typeof n==='string'?n:(n?.children||[]).map(text).join('');
const button=()=>tree.root.findByType('button');
async function resolve(value){await act(async()=>calls.shift().resolve(value))}
(async()=>{
 await act(async()=>{tree=create(React.createElement(router.MemoryRouter,null,React.createElement(Ops)))});
 assert.equal(calls[0].args[0],'/admin/ops');assert.ok(json().includes('Reading live operational records'));
 await resolve(data);assert.ok(json().includes('Unknown'));assert.ok(json().includes('14.0'));assert.ok(json().includes('Checksum verification is separate from a restore rehearsal'));assert.ok(json().includes('No open reports'));assert.ok(json().includes('PRIVATE_OLD_OWNER_RESULT'));assert.ok(json().includes('Checkout disabled; no live metric'));
 const links=tree.root.findAllByType('a');for(const a of links)assert.ok(a.props.href.startsWith('/'));
 await act(async()=>button().props.onClick());assert.ok(!json().includes('PRIVATE_OLD_OWNER_RESULT'),'Refresh clears stale snapshot');
 await act(async()=>calls.shift().reject(Error('Database unavailable')));assert.ok(json().includes('Snapshot unavailable: '));assert.ok(json().includes('Database unavailable'));assert.ok(!json().includes('No accounts match'));
 await act(async()=>button().props.onClick());epoch++;await act(async()=>{for(const fn of events.get('ism-auth-change'))fn()});
 assert.equal(calls.length,2);await resolve(data);assert.ok(!json().includes('PRIVATE_OLD_OWNER_RESULT'),'Old account response must not appear');
 await act(async()=>calls.shift().reject(Error('Permission required')));assert.ok(json().includes('Permission required'));
 await act(async()=>tree.unmount());console.log('Ops real component passed: unknown vs zero, actual probes, runbook links, refresh/outage, account-switch stale-response suppression.');
})().catch(e=>{console.error(e);process.exitCode=1});
