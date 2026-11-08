const assert=require('node:assert/strict'),fs=require('node:fs');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {act,create}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
global.crypto=require('node:crypto').webcrypto;
let owner=true,fail=false,calls=[],events={},published=[],draft={revision:0,base_version:1,selection:{papers:['p1'],modules:[],excluded_papers:[]}};
global.window={addEventListener:(k,fn)=>events[k]=fn,removeEventListener:k=>delete events[k],dispatchEvent(){}};
const setup=()=>({module:{id:'udc',title:'UDC',live_version:1,visibility:'public'},draft:structuredClone(draft),papers:[{id:'p1',exam_name:'Existing source',year:2020}],history:[]});
const preview={token:'a'.repeat(64),revision:1,before:{papers:1,questions:1,appearances:1},after:{papers:2,questions:2,appearances:2},added_appearances:1,removed_appearances:0,added_papers:[{id:'p2',exam_name:'Added source',year:2021}],removed_papers:[],sources:[],notice:'Only this module changes.'};
const mod={exports:{}};
new Function('module','exports','require',ts.transpileModule(fs.readFileSync(root+'/web/src/components/ModuleCompositionEditor.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText)(mod,mod.exports,id=>id==='../lib/review'?{
 reviewSession:async()=>({grants:owner?[{role:'owner',subject_id:null}]:[{role:'reviewer',subject_id:'english'}]}),
 reviewRequest:async(path,body)=>{calls.push({path,body});if(path.endsWith('/catalog'))return {items:[{id:'udc',title:'UDC',live_version:1,visibility:'public'},{id:'assistant',title:'Assistant',live_version:1,visibility:'public'}]};if(path.includes('/papers?'))return {items:[{id:'p2',exam_name:'Added source',year:2021}],has_more:false};if(path.endsWith('/draft')){draft={...body,revision:body.revision+1};return {revision:draft.revision}}if(path.endsWith('/preview'))return {...preview,revision:draft.revision};if(path.endsWith('/publish')){if(fail)throw Error('Temporary publication failure; draft retained');return {version:2}}return setup()}
}:wr(id));
const Editor=mod.exports.default;let tree;
const button=t=>tree.root.findAllByType('button').find(b=>b.children.join('').includes(t));
async function mount(props={}){await act(async()=>{tree?.unmount();tree=create(React.createElement(Editor,{collection:'udc',onPublished:id=>published.push(id),...props}))})}
(async()=>{
 await mount();assert.ok(button('Module setup'));await act(async()=>button('Module setup').props.onClick());await act(async()=>new Promise(r=>setTimeout(r,280)));
 const writes=()=>calls.filter(c=>c.body!==undefined);assert.equal(writes().length,0);
 await act(async()=>tree.root.findAllByType('input').find(i=>i.props.type==='checkbox'&&i.props.checked===false).props.onChange());assert.equal(writes().length,0);assert.ok(button('Save draft & preview'));
 await act(async()=>button('Save draft & preview').props.onClick());assert.ok(writes().some(c=>c.path.endsWith('/draft')));assert.equal(button('Publish this module').props.disabled,true);
 await act(async()=>tree.root.findByType('textarea').props.onChange({target:{value:'Selected exact source papers for this compilation.'}}));
 fail=true;await act(async()=>button('Publish this module').props.onClick());assert.ok(tree.root.findByProps({role:'alert'}));const first=writes().findLast(c=>c.path.endsWith('/publish'));
 fail=false;await act(async()=>button('Publish this module').props.onClick());const second=writes().findLast(c=>c.path.endsWith('/publish'));assert.equal(first.body.request_key,second.body.request_key);assert.deepEqual(published,['udc']);
 await mount({needsMfa:true});await act(async()=>button('Module setup').props.onClick());const before=writes().length;await act(async()=>button('Preview current selection').props.onClick());assert.equal(writes().length,before);
 owner=false;await act(async()=>events['ism-auth-change']());assert.equal(tree.toJSON(),null);
 await act(async()=>tree.unmount());console.log('Module setup UI passed: owner visibility, explicit saved preview, reason requirement, MFA, retry identity and account reset.');
})().catch(e=>{console.error(e);process.exitCode=1});
