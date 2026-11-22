const assert=require('node:assert/strict'),fs=require('node:fs'),root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
let epoch=0,writes=[],listeners=new Map(),changes=0;
global.window={addEventListener(n,f){if(!listeners.has(n))listeners.set(n,new Set());listeners.get(n).add(f)},removeEventListener(n,f){listeners.get(n)?.delete(f)}};
const mod={exports:{}};
const code=ts.transpileModule(fs.readFileSync(root+'/web/src/components/DeskDiscussionButton.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
new Function('module','exports','require',code)(mod,mod.exports,id=>id.endsWith('/studyDesks')?{deskWrite:(...args)=>new Promise((resolve,reject)=>writes.push({args,resolve,reject}))}:id.endsWith('/accountContext')?{accountGeneration:()=>epoch}:wr(id));
const Component=mod.exports.default;let tree;
const item={id:'item_1',version:1,discussion_state:'none'},changed=async()=>{changes++};
const button=()=>tree.root.findByType('button'),json=()=>JSON.stringify(tree.toJSON());
async function reply(value,error=false){await act(async()=>{const r=writes.shift();error?r.reject(Error(value)):r.resolve(value)})}
(async()=>{
 await act(async()=>tree=create(React.createElement(Component,{deskId:'desk_1',item,onChange:changed})));
 assert.ok(json().includes('Discuss this'));await act(async()=>button().props.onClick());
 assert.deepEqual(writes[0].args,['/rooms/desk_1/items/item_1/discussion',{expected_version:1,state:'needed'}]);assert.ok(button().props.disabled);await reply({version:2});assert.equal(changes,1);
 await act(async()=>tree.update(React.createElement(Component,{deskId:'desk_1',item:{...item,version:2,discussion_state:'needed'},onChange:changed})));
 assert.ok(json().includes('Mark discussion resolved'));await act(async()=>button().props.onClick());assert.equal(writes[0].args[1].state,'resolved');await reply('Shared question changed',true);assert.ok(json().includes('Refresh desk before trying again'));assert.equal(changes,1);
 await act(async()=>tree.update(React.createElement(Component,{deskId:'desk_1',item:{...item,version:3,discussion_state:'resolved'},onChange:changed})));
 assert.ok(json().includes('Reopen discussion'));const stale=button().props.onClick;epoch++;await act(async()=>{for(const f of [...listeners.get('ism-auth-change')||[]])f()});await act(async()=>stale());assert.equal(writes.length,0);
 await act(async()=>{tree.unmount();tree=create(React.createElement(Component,{deskId:'desk_1',item,onChange:changed}))});await act(async()=>button().props.onClick());
 await act(async()=>tree.update(React.createElement(Component,{deskId:'desk_2',item:{...item,id:'item_2'},onChange:changed})));await reply({version:2});assert.equal(changes,1,'A former room completion must not refresh the new room');
 await act(async()=>button().props.onClick());epoch++;await act(async()=>{for(const f of [...listeners.get('ism-auth-change')||[]])f()});await reply('OLD_ACCOUNT_ERROR',true);assert.ok(!json().includes('OLD_ACCOUNT_ERROR'));await act(async()=>tree.unmount());
 console.log('Discussion real component passed: flag/resolve/reopen, original version binding, failure/refresh, stale account callbacks and room completion isolation.');
})().catch(e=>{console.error(e);process.exitCode=1});
