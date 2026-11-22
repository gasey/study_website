// Actual Desk screen: filter/pagination ordering and privacy refresh.
const assert=require('node:assert/strict'),fs=require('node:fs'),root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]})),router=wr('react-router-dom');
let reads=[],timers=new Map(),next=0,subscriber;
global.crypto=require('node:crypto').webcrypto;
global.window={setInterval(f){const id=++next;timers.set(id,f);return id},clearInterval(id){timers.delete(id)}};global.document={visibilityState:'visible'};
global.clearInterval=window.clearInterval;
const sync={userId:'author',handle:'author',registered:true,loading:false,status:'saved',privateEnabled:true};
const desk={goal:'',goalSubject:'',tasks:[],notes:[],saved:[],recent:[],completedDays:[],weeklyTarget:100};
const overview={stats:{answered:0,correct:0,unique_questions:0,week_answers:0},subjects:[],questions:[],mistakes:[],sessions:[],server_time:'2026-11-18T00:00:00Z'};
const room={id:'desk_1',name:'Synthetic circle',goal:'',owner_id:'author',version:1,members:[{user_id:'author',handle:'author',is_you:true,blocked:false,focusing:false,progress:null}],sharing:{progress:false,mistakes:false,times:false,muted:false},invitations:[]};
const nullComponent={__esModule:true,default:()=>null};
const mod={exports:{}};const code=ts.transpileModule(fs.readFileSync(root+'/web/src/screens/StudyDesk.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
new Function('module','exports','require',code)(mod,mod.exports,id=>{
 if(id.endsWith('/desk'))return {getDesk:()=>desk,getDeskSync:()=>({...sync}),subscribeDesk:f=>{subscriber=f;return()=>{}},deskRead:(path)=>path.endsWith('/messages')?Promise.resolve({items:[],next_cursor:null}):new Promise((resolve,reject)=>reads.push({path,resolve,reject}))};
 if(id.endsWith('/studyDesks'))return {getOverview:async()=>overview,getRooms:async()=>({items:[{...room,members:1}],invitations:[],can_create:true,enabled:true}),getRoom:async()=>room};
 if(id.endsWith('/DeskPractice'))return {...nullComponent,DeskQuestion:()=>null};
 if(id.endsWith('/AvatarArt'))return {UserAvatar:()=>null};if(id.endsWith('/avatar'))return {AVATAR_COLORS:{}};
 if(id.startsWith('../components/'))return nullComponent;
 if(id.endsWith('/review')||id.endsWith('/api'))return {};
 return id==='react-router-dom'?router:wr(id);
});
const Screen=mod.exports.default;let tree;
const row=(id,state='needed')=>({id,author_id:'author',author:'author',kind:'question',body:id,title:'',question_id:'q',question:'Synthetic question',answer_source:'official',version:1,discussion_state:state,created_at:'2026-11-18T00:00:00Z'});
const json=()=>JSON.stringify(tree.toJSON()),button=t=>tree.root.findAllByType('button').find(b=>b.children.join('')===t),filter=()=>tree.root.findAllByType('select').find(s=>s.findAllByType('option').some(o=>o.props.value==='needed'));
async function reply(data){assert.ok(reads.length);await act(async()=>reads.shift().resolve(data))}
(async()=>{
 await act(async()=>tree=create(React.createElement(router.MemoryRouter,{initialEntries:['/desk/desk_1?tab=shared']},React.createElement(router.Routes,null,React.createElement(router.Route,{path:'/desk/:deskId',element:React.createElement(Screen)})))));
 assert.ok(reads[0].path.includes('kind=question&discussion=all&limit=5'));await reply({items:[row('initial')],next_cursor:'page2'});
 await act(async()=>button('More shared items').props.onClick());const oldPage=reads.shift();assert.ok(oldPage.path.includes('before=page2'));
 await act(async()=>filter().props.onChange({target:{value:'needed'}}));assert.ok(reads[0].path.includes('kind=all&discussion=needed&limit=5'));
 await reply({items:[row('NEEDED_CURRENT')],next_cursor:null});await act(async()=>oldPage.resolve({items:[row('STALE_PAGE')],next_cursor:null}));
 assert.ok(json().includes('NEEDED_CURRENT')&&!json().includes('STALE_PAGE'));
 await act(async()=>filter().props.onChange({target:{value:'resolved'}}));const older=reads.shift();await act(async()=>filter().props.onChange({target:{value:'needed'}}));await reply({items:[row('LATEST_FILTER')],next_cursor:null});await act(async()=>older.resolve({items:[row('OLD_RESOLVED')],next_cursor:null}));assert.ok(json().includes('LATEST_FILTER')&&!json().includes('OLD_RESOLVED'));
 const poll=[...timers.values()][0]();await act(async()=>{await Promise.resolve();await Promise.resolve()});assert.ok(reads[0]);assert.ok(reads[0].path.includes('discussion=needed'));
 await reply({items:[],next_cursor:null});await act(async()=>poll);assert.ok(!json().includes('LATEST_FILTER'),'Periodic refresh must remove revoked/blocked items');
 await act(async()=>{sync.privateEnabled=false;subscriber()});assert.equal(filter(),undefined,'Private-desk gate hides review-circle controls');assert.ok(reads[0].path.includes('kind=question&discussion=all'));
 await reply({items:[],next_cursor:null});await act(async()=>tree.unmount());assert.equal(timers.size,0);
 console.log('Desk screen passed: five-item filters, late pagination/filter suppression, periodic privacy refresh, private-desks gate and timer cleanup.');
})().catch(e=>{console.error(e);process.exitCode=1});
