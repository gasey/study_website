// Actual room-goal component: account changes, response ordering and stale CAS.
const assert=require('node:assert/strict'),fs=require('node:fs'),root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
let epoch=0,reads=[],writes=[],listeners=new Map(),intervals=new Map(),next=0;
global.window={addEventListener(n,f){if(!listeners.has(n))listeners.set(n,new Set());listeners.get(n).add(f)},removeEventListener(n,f){listeners.get(n)?.delete(f)},setInterval(f){const id=++next;intervals.set(id,f);return id},clearInterval(id){intervals.delete(id)}};
global.document={visibilityState:'visible'};
const mod={exports:{}};
const code=ts.transpileModule(fs.readFileSync(root+'/web/src/components/DeskWeeklyGoal.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
new Function('module','exports','require',code)(mod,mod.exports,id=>id.endsWith('/desk')?{deskRead:(...args)=>new Promise((resolve,reject)=>reads.push({args,resolve,reject}))}:id.endsWith('/studyDesks')?{deskWrite:(...args)=>new Promise((resolve,reject)=>writes.push({args,resolve,reject}))}:id.endsWith('/accountContext')?{accountGeneration:()=>epoch}:wr(id));
const Component=mod.exports.default;
const goal={week_start:'2026-11-16',week_end:'2026-11-22',resets_at:'2026-11-22T18:30:00Z',as_of:'2026-11-18T12:00:00Z',timezone:'Asia/Kolkata',target:null,version:0,scored_attempts:0,sharing_members:0,completed:false,can_edit:true};
let tree;
const json=()=>JSON.stringify(tree.toJSON()),button=t=>tree.root.findAllByType('button').find(b=>b.children.join('')===t);
async function reply(queue,value,error=false){assert.ok(queue.length);await act(async()=>{const r=queue.shift();error?r.reject(Error(value)):r.resolve(value)})}
async function emit(name){await act(async()=>{for(const f of [...listeners.get(name)||[]])f()})}
async function target(value){await act(async()=>tree.root.findByType('input').props.onChange({target:{value}}))}
async function submit(){await act(async()=>{void tree.root.findByType('form').props.onSubmit({preventDefault(){}})})}
(async()=>{
  await act(async()=>tree=create(React.createElement(Component,{deskId:'desk_1'})));
  assert.equal(reads[0].args[0],'/rooms/desk_1/weekly-goal');assert.ok(json().includes('Loading weekly goal'));
  await reply(reads,goal);assert.ok(json().includes('No shared goal this week'));assert.equal(tree.root.findAllByProps({role:'progressbar'}).length,0);
  await act(async()=>button('Set weekly target').props.onClick());await target('300');await submit();
  assert.deepEqual(writes[0].args,['/rooms/desk_1/weekly-goal',{week_start:'2026-11-16',expected_version:0,target:300}]);
  assert.ok(tree.root.findByType('input').props.disabled);await reply(writes,{saved:true,version:1});await reply(reads,{...goal,target:300,version:1,scored_attempts:450,completed:true});
  const bar=tree.root.findByProps({role:'progressbar'});assert.equal(bar.props['aria-valuenow'],300);assert.ok(json().includes('450')&&json().includes('Weekly goal reached')&&json().includes('earns no XP or points'));
  await act(async()=>button('Edit weekly target').props.onClick());await target('600');await emit('focus');await reply(reads,{...goal,target:400,version:2});
  assert.equal(tree.root.findByType('input').props.value,'600');assert.ok(json().includes('goal or week changed'));
  await submit();assert.equal(writes[0].args[1].expected_version,1,'A background refresh never silently rebases a draft');await reply(writes,'The weekly goal changed; refresh before saving',true);
  assert.equal(tree.root.findByType('input').props.value,'600');assert.ok(json().includes('weekly goal changed'));
  await act(async()=>button('Cancel').props.onClick());
  await emit('focus');const older=reads.shift();await emit('focus');await reply(reads,{...goal,target:700,version:3});await act(async()=>older.resolve({...goal,target:123,version:1}));
  assert.equal(tree.root.findByProps({role:'progressbar'}).props['aria-valuemax'],700);
  await emit('focus');await reply(reads,'Temporarily unavailable',true);assert.ok(json().includes('Temporarily unavailable'));assert.equal(tree.root.findAllByProps({role:'progressbar'}).length,0,'Outage clears private stale counts');
  await act(async()=>button('Refresh goal').props.onClick());await reply(reads,{...goal,target:7,version:3,can_edit:false});assert.ok(!button('Edit weekly target'));
  await emit('focus');const pending=reads.shift();epoch++;await emit('ism-auth-change');await act(async()=>pending.resolve({...goal,target:999,version:1}));assert.ok(!json().includes('999'));assert.equal(tree.root.findAllByProps({role:'progressbar'}).length,0);
  await act(async()=>tree.unmount());assert.equal(intervals.size,0);
  await act(async()=>tree=create(React.createElement(Component,{deskId:'desk_1'})));await reply(reads,goal);await act(async()=>button('Set weekly target').props.onClick());await target('10');await submit();
  await act(async()=>tree.update(React.createElement(Component,{deskId:'desk_2'})));await reply(reads,{...goal,target:5,version:1});await reply(writes,{saved:true,version:1});assert.ok(!json().includes('Weekly target saved'),'Old room write cannot update the new room');
  await act(async()=>tree.unmount());assert.equal(intervals.size,0);assert.equal(reads.length,0);assert.equal(writes.length,0);
  console.log('Desk goal component passed: honest empty/read-only/reached states, bounded progress, versioned edits, stale drafts/responses/account/room isolation, outages and cleanup.');
})().catch(e=>{console.error(e);process.exitCode=1});
