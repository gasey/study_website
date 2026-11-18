// Run with a disposable React 18 test-renderer directory as the first argument.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const reactPath=require.resolve('react',{paths:[process.argv[2]]});require.cache[reactPath]={id:reactPath,filename:reactPath,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]})),Router=wr('react-router-dom');
let calls=[],detail,mutations=0,resolveAction;const listeners=new Map();global.window={addEventListener:(k,f)=>listeners.set(k,f),removeEventListener:(k)=>listeners.delete(k)};
const video={id:'abcdefghijk',title:'Synthetic recap for UI checks',channel_id:'UC'+'a'.repeat(22),channel:'Synthetic channel',published_at:'2026-11-15T00:00:00Z',status:'quota_wait',last_error:'OpenCode free usage limit reached (429)',transcript_hash:'synthetic',next_attempt_at:'2026-11-16T00:00:00Z'};
const overview={channels:[{id:video.channel_id,title:video.channel,enabled:true,languages:['hi'],checked_at:null,last_error:null}],counts:{quota_wait:1},videos:[video],total:1,runs:[],generation:{configured:true,model:'opencode/deepseek-v4.1-flash-free',call_limit:6,calls_last_24h:1}};
const reset=()=>{detail={video,transcript:{language:'hi',automatic:true,provider:'Synthetic fixture',cues:[{id:0,start:15,text:'Synthetic caption content for tests only.'}]},drafts:[],events:[]}};reset();
const api=async(p,b)=>{calls.push({p,b});if(b){mutations++;return new Promise(r=>{resolveAction=r})}return p.includes('/videos/')?detail:overview};
const source=fs.readFileSync(root+'/web/src/screens/CurrentAffairsAutomation.tsx','utf8');const moduleObject={exports:{}};
new Function('module','exports','require',ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText)(moduleObject,moduleObject.exports,id=>['./OfficialCurrentAffairsSources','./CurrentAffairsBriefs'].includes(id)?{default:()=>null}:id==='../lib/review'?{reviewRequest:api}:id==='../lib/stats'?{statsDate:x=>x||'Not checked'}:wr(id));
const Screen=moduleObject.exports.default;let tree;const text=()=>JSON.stringify(tree.toJSON()),button=label=>tree.root.findAllByType('button').find(b=>b.children.join('')===label);
async function mount(){await act(async()=>{tree?.unmount();tree=create(React.createElement(Router.MemoryRouter,null,React.createElement(Screen)))});await act(async()=>button('YouTube videos').props.onClick());await act(async()=>{tree.root.findAllByType('button').find(b=>b.props['aria-pressed']===false).props.onClick()})}
(async()=>{
 await mount();assert.ok(text().includes('Waiting for free quota'));assert.ok(text().includes('captured transcript is saved'));assert.equal(button('Queue draft generation').props.disabled,false);assert.ok(tree.root.findAllByType('a').some(a=>a.props.href==='https://www.youtube.com/watch?v=abcdefghijk&t=15s'));
 detail={...detail,transcript:null};await mount();assert.equal(button('Queue draft generation').props.disabled,true);assert.ok(text().includes('Notes cannot be generated from the title alone'));
 reset();detail.drafts=[{id:'synthetic-draft',status:'pending',model:'synthetic-model',payload:{summary:'Synthetic private study draft',warnings:['Unverified synthetic fixture'],facts:[],mcqs:[],flashcards:[]}}];await mount();assert.equal(button('Create private notes draft').props.disabled,true);
 await act(async()=>tree.root.findByType('textarea').props.onChange({target:{value:'Synthetic handoff note for tests.'}}));assert.equal(button('Create private notes draft').props.disabled,false);
 await act(async()=>{button('Create private notes draft').props.onClick();button('Create private notes draft').props.onClick()});assert.equal(mutations,1,'Rapid double click must create one request');assert.equal(calls.at(-1).b.action,'material_draft');await act(async()=>resolveAction({material_id:'synthetic-material'}));assert.ok(text().includes('Private material draft created'));
 await act(async()=>listeners.get('ism-auth-change')());assert.ok(!text().includes('Private material draft created'),'Account switch clears private action notices');
 assert.ok(!tree.root.findAllByType('button').some(b=>b.children.join('')==='Publish'),'Automation offers private handoff, not publication');
 await act(async()=>tree.unmount());console.log('YouTube owner UI checks passed: quota status, source links, transcript requirement, handoff note, single-flight actions, account notice isolation and no publication control.');
})().catch(e=>{console.error(e);process.exitCode=1});
