// Actual component: confirmation, network retry, active reservation and account/room isolation.
const assert=require('node:assert/strict'),fs=require('node:fs'),root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
let epoch=0,reads=[],writes=[],navigation=[],listeners=new Map(),intervals=new Map(),next=0;
global.window={addEventListener(n,f){if(!listeners.has(n))listeners.set(n,new Set());listeners.get(n).add(f)},removeEventListener(n,f){listeners.get(n)?.delete(f)},setInterval(f){const id=++next;intervals.set(id,f);return id},clearInterval(id){intervals.delete(id)}};
global.document={visibilityState:'visible'};global.crypto=require('node:crypto').webcrypto;
const mod={exports:{}};
const code=ts.transpileModule(fs.readFileSync(root+'/web/src/components/DeskPracticeSessions.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
new Function('module','exports','require',code)(mod,mod.exports,id=>id.endsWith('/desk')?{deskRead:(...args)=>new Promise((resolve,reject)=>reads.push({args,resolve,reject}))}:id.endsWith('/studyDesks')?{deskWrite:(...args)=>new Promise((resolve,reject)=>writes.push({args,resolve,reject}))}:id.endsWith('/accountContext')?{accountGeneration:()=>epoch}:id==='react-router-dom'?{Link:({to,children,...rest})=>React.createElement('a',{href:to,...rest},children),useNavigate:()=>url=>navigation.push(url)}:wr(id));
const Component=mod.exports.default;
const initial={preview:{context_hash:'a'.repeat(64),available:3,required:10,can_start:false,capacity:4,round_seconds:25,message:'3 shared questions with official keys are ready; a session needs 10.'},sessions:[],active_game:null};
const ready={...initial,preview:{...initial.preview,available:10,can_start:true,message:'10 shared questions with official keys are ready; a session needs 10.'}};
const session={id:'game_1',state:'waiting',players:2,capacity:4,context_hash:'b'.repeat(64),joined:false,can_join:true,questions:10,round_seconds:25};
let tree;const json=()=>JSON.stringify(tree.toJSON()),button=t=>tree.root.findAllByType('button').find(b=>b.children.join('')===t);
async function reply(queue,value,error=false){assert.ok(queue.length);await act(async()=>{const r=queue.shift();error?r.reject(Error(value)):r.resolve(value)})}
async function emit(name){await act(async()=>{for(const f of [...listeners.get(name)||[]])f()})}
async function click(label){await act(async()=>{void button(label).props.onClick()})}
(async()=>{
 await act(async()=>tree=create(React.createElement(Component,{deskId:'desk_1'})));
 assert.equal(reads[0].args[0],'/rooms/desk_1/practice');await reply(reads,initial);
 assert.ok(button('Confirm shared set · Create session').props.disabled);assert.ok(json().includes('No active room sessions'));
 await emit('focus');await reply(reads,ready);await click('Confirm shared set · Create session');
 assert.equal(writes[0].args[0],'/rooms/desk_1/practice');const body=writes[0].args[1];assert.equal(body.preview_hash,'a'.repeat(64));assert.ok(body.request_key.length>=16);
 await reply(writes,'Connection interrupted',true);assert.ok(json().includes('Refresh sessions to check'));assert.ok(!button('Confirm shared set · Create session'));
 await click('Refresh sessions');await reply(reads,ready);await click('Confirm shared set · Create session');assert.deepEqual(writes[0].args[1],body,'Retry retains exact start key');await reply(writes,{id:'game_created'});assert.deepEqual(navigation,['/games/game_created']);
 await emit('focus');await reply(reads,{...ready,sessions:[session]});await click('Confirm set · Join');assert.deepEqual(writes[0].args,['/rooms/desk_1/practice/game_1/join',{context_hash:'b'.repeat(64)}]);
 await reply(writes,{id:'game_1'});assert.equal(navigation.at(-1),'/games/game_1');
 await emit('focus');await reply(reads,{...ready,active_game:{id:'game_1',state:'waiting'},sessions:[{...session,joined:true}]});assert.ok(button('Confirm shared set · Create session').props.disabled);assert.ok(tree.root.findAllByType('a').some(a=>a.props.href==='/games/game_1'&&a.children.join('')==='Open session'));
 await emit('focus');const older=reads.shift();await emit('focus');await reply(reads,{...ready,sessions:[{...session,can_join:false,players:4}]});await act(async()=>older.resolve(initial));assert.ok(button('Session full').props.disabled);
 await emit('focus');const pending=reads.shift();epoch++;await emit('ism-auth-change');await act(async()=>pending.resolve(ready));assert.ok(!button('Confirm shared set · Create session'));
 await act(async()=>tree.unmount());assert.equal(intervals.size,0);
 await act(async()=>tree=create(React.createElement(Component,{deskId:'desk_1'})));await reply(reads,ready);await click('Confirm shared set · Create session');
 await act(async()=>tree.update(React.createElement(Component,{deskId:'desk_2'})));await reply(reads,initial);const count=navigation.length;await reply(writes,{id:'old_room'});assert.equal(navigation.length,count,'Late write cannot navigate from another room');
 await emit('focus');await reply(reads,'Membership has ended',true);assert.ok(json().includes('Membership has ended'));assert.ok(!button('Confirm shared set · Create session'));
 await act(async()=>tree.unmount());assert.equal(intervals.size,0);assert.equal(reads.length,0);assert.equal(writes.length,0);
 console.log('Desk practice actual component passed: honest eligibility/full/active states, explicit frozen confirmation, same-key retry, joins, response order, private outage, account/room navigation guards and cleanup.');
})().catch(e=>{console.error(e);process.exitCode=1});
