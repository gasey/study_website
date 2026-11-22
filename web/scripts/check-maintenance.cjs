// Actual public announcement and owner editor components with deferred requests.
const assert=require('node:assert/strict'),fs=require('node:fs'),root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]})),router=wr('react-router-dom');
let events=new Map(),timers=new Map(),intervals=new Map(),next=0,epoch=0,fetches=[],requests=[],fakeNow=Date.now(),announcements=0;
const add=(n,f)=>{if(!events.has(n))events.set(n,new Set());events.get(n).add(f)},remove=(n,f)=>events.get(n)?.delete(f);
global.window={addEventListener:add,removeEventListener:remove,dispatchEvent(e){if(e.type==='ism-site-notice-change')announcements++;for(const fn of [...events.get(e.type)||[]])fn(e);return true},setTimeout(f,ms){const id=++next;timers.set(id,{f,ms});return id},clearTimeout(id){timers.delete(id)},setInterval(f,ms){const id=++next;intervals.set(id,{f,ms});return id},clearInterval(id){intervals.delete(id)}};
global.document={visibilityState:'visible',addEventListener:add,removeEventListener:remove};
global.fetch=(...args)=>new Promise((resolve,reject)=>fetches.push({args,resolve,reject}));
const originalNow=Date.now;Date.now=()=>fakeNow;
function load(name){const m={exports:{}};const code=ts.transpileModule(fs.readFileSync(root+'/web/src/components/'+name+'.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;new Function('module','exports','require',code)(m,m.exports,id=>id.endsWith('/review')?{reviewRequest:(...args)=>new Promise((resolve,reject)=>requests.push({args,resolve,reject}))}:id.endsWith('/accountContext')?{accountGeneration:()=>epoch}:id==='react-router-dom'?router:wr(id));return m.exports.default}
const Public=load('SiteNotice'),Admin=load('SiteNoticeAdmin');let tree;
const json=()=>JSON.stringify(tree.toJSON()),button=t=>tree.root.findAllByType('button').find(b=>(b.children||[]).join('')===t);
async function publicReply(item,data){await act(async()=>item.resolve({ok:true,json:async()=>data}))}
async function adminReply(value,error=false){await act(async()=>{const item=requests.shift();error?item.reject(Error(value)):item.resolve(value)})}
(async()=>{
 await act(async()=>tree=create(React.createElement(Public)));assert.equal(fetches[0].args[0],'/api/site-notice');assert.equal(tree.toJSON(),null);
 await publicReply(fetches.shift(),{message:'<script>Plain announcement</script>',expires_at:null,version:1});assert.ok(json().includes('Plain announcement'));assert.equal(tree.root.findAllByType('script').length,0);
 await act(async()=>window.dispatchEvent(new Event('ism-site-notice-change')));const older=fetches.shift(),oldTimer=[...timers.values()][0];
 await act(async()=>window.dispatchEvent(new Event('ism-site-notice-change')));const newer=fetches.shift();oldTimer.f();assert.ok(!newer.args[1].signal.aborted,'Old timeout must not abort a newer request');
 await publicReply(newer,{message:'Latest notice',expires_at:null,version:3});await publicReply(older,{message:'Stale response',expires_at:null,version:2});assert.ok(json().includes('Latest notice'));assert.ok(!json().includes('Stale response'));
 await act(async()=>window.dispatchEvent(new Event('ism-site-notice-change')));await publicReply(fetches.shift(),{message:'Expires soon',expires_at:new Date(fakeNow+5000).toISOString(),version:4});assert.ok(json().includes('Expires soon'));
 fakeNow+=6000;await act(async()=>{for(const t of [...timers.values()])if(t.ms===5000)t.f()});assert.equal(tree.toJSON(),null,'Expired announcement disappears without navigation');
 await act(async()=>tree.unmount());assert.equal(intervals.size,0);
 await act(async()=>tree=create(React.createElement(router.MemoryRouter,null,React.createElement(Admin))));assert.equal(requests[0].args[0],'/admin/ops/notice');
 const setting={message:'',expires_at:null,version:2,updated_at:'2026-11-18T00:00:00Z'};await adminReply(setting);
 await act(async()=>tree.root.findByType('textarea').props.onChange({target:{value:'Maintenance tonight'}}));
 await act(async()=>tree.root.findByType('input').props.onInput({currentTarget:{value:'2030-01-01T02:00'}}));
 await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}));assert.deepEqual(requests[0].args[1],{message:'Maintenance tonight',expires_at:'2029-12-31T20:30:00.000Z',expected_version:2});
 await adminReply({...setting,message:'Maintenance tonight',expires_at:'2029-12-31T20:30:00.000Z',version:3});assert.ok(json().includes('Site notice saved.'));assert.ok(button('Clear notice'));
 await act(async()=>button('Clear notice').props.onClick());assert.deepEqual(requests[0].args[1],{message:'',expires_at:null,expected_version:3});await adminReply({...setting,version:4});assert.ok(json().includes('Site notice cleared.'));
 await act(async()=>tree.root.findByType('textarea').props.onChange({target:{value:'PRIVATE_UNSAVED_OWNER_DRAFT'}}));assert.ok(!json().includes('Site notice cleared.'),'Editing clears a prior saved confirmation');
 await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}));const before=announcements;epoch++;await act(async()=>window.dispatchEvent(new Event('ism-auth-change')));assert.ok(!json().includes('PRIVATE_UNSAVED_OWNER_DRAFT'));
 await adminReply({...setting,message:'PRIVATE_UNSAVED_OWNER_DRAFT',version:5});assert.ok(!json().includes('PRIVATE_UNSAVED_OWNER_DRAFT'));assert.equal(announcements,before,'Old authenticated save response cannot emit a refresh');await adminReply('Permission required',true);assert.ok(json().includes('Permission required'));
 await act(async()=>button('Reload notice setting').props.onClick());await adminReply({...setting,version:8});await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}));await adminReply('Site notice changed. Reload before saving',true);assert.ok(json().includes('Reload before saving'));assert.ok(!json().includes('Site notice saved.'));
 await act(async()=>tree.unmount());Date.now=originalNow;
 console.log('Maintenance components passed: public plain text, late-response/timeout isolation, exact expiry, versioned save/clear, refresh events, conflict handling and auth draft/save suppression.');
})().catch(e=>{Date.now=originalNow;console.error(e);process.exitCode=1});
