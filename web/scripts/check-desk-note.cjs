// Real linked-note reader: current privacy, stale ordering and room/account cleanup.
const assert=require('node:assert/strict'),fs=require('node:fs'),root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
let epoch=0,reads=[],listeners=new Map(),intervals=new Map(),next=0;
global.window={addEventListener(n,f){if(!listeners.has(n))listeners.set(n,new Set());listeners.get(n).add(f)},removeEventListener(n,f){listeners.get(n)?.delete(f)},setInterval(f){const id=++next;intervals.set(id,f);return id},clearInterval(id){intervals.delete(id)}};global.document={visibilityState:'visible'};
const mod={exports:{}};const code=ts.transpileModule(fs.readFileSync(root+'/web/src/components/DeskLinkedNote.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
new Function('module','exports','require',code)(mod,mod.exports,id=>id.endsWith('/desk')?{deskRead:(...args)=>new Promise((resolve,reject)=>reads.push({args,resolve,reject}))}:id.endsWith('/accountContext')?{accountGeneration:()=>epoch}:id==='react-router-dom'?{Link:({to,children,...rest})=>React.createElement('a',{href:to,...rest},children)}:wr(id));
const Component=mod.exports.default;let tree;const json=()=>JSON.stringify(tree.toJSON());
async function reply(value,error=false){await act(async()=>{const r=reads.shift();assert.ok(r);error?r.reject(Error(value)):r.resolve(value)})}
async function emit(name){await act(async()=>{for(const f of [...listeners.get(name)||[]])f()})}
(async()=>{
 await act(async()=>tree=create(React.createElement(Component,{deskId:'desk1',noteId:'note1'})));assert.equal(reads[0].args[0],'/rooms/desk1/notes/note1');await reply({title:'Source note',body:'BODY_ONE',author:'Synthetic',question_id:'cq_test'});
 assert.ok(json().includes('BODY_ONE'));assert.equal(tree.root.findByType('a').props.href,'/bank/cq_test');
 await emit('focus');const older=reads.shift();await emit('focus');await reply('Finish your assessment',true);await act(async()=>older.resolve({body:'OLD_SECRET',title:'Stale',author:'Old'}));assert.ok(!json().includes('BODY_ONE')&&!json().includes('OLD_SECRET'));assert.ok(json().includes('Finish your assessment'));
 await emit('focus');await reply({title:'Available again',body:'BODY_TWO',author:'Synthetic',question_id:null});assert.equal(tree.root.findAllByType('a').length,0);
 await emit('focus');const old=reads.shift();epoch++;await emit('ism-auth-change');await act(async()=>old.resolve({title:'SECRET',body:'WRONG_ACCOUNT',author:'Other'}));assert.ok(!json().includes('WRONG_ACCOUNT'));
 await act(async()=>tree.unmount());assert.equal(intervals.size,0);
 await act(async()=>tree=create(React.createElement(Component,{deskId:'desk1',noteId:'note1'})));const wrongRoom=reads.shift();await act(async()=>tree.update(React.createElement(Component,{deskId:'desk2',noteId:'note2'})));await reply({title:'Room two',body:'CURRENT',author:'Synthetic'});await act(async()=>wrongRoom.resolve({body:'WRONG_ROOM',title:'Old',author:'Other'}));assert.ok(json().includes('CURRENT')&&!json().includes('WRONG_ROOM'));await act(async()=>tree.unmount());assert.equal(intervals.size,0);
 console.log('Linked note reader passed: canonical link, live disclosure/unavailability, stale response/account/room isolation and cleanup.');
})().catch(e=>{console.error(e);process.exitCode=1});
