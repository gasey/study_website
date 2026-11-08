// Run from repository root with a directory containing react-test-renderer@18.3.1 as argument.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),webRequire=require('node:module').createRequire(root+'/web/package.json');
const React=webRequire('react');require.cache[require.resolve('react', {paths:[process.argv[2]]})]={id:require.resolve('react', {paths:[process.argv[2]]}),filename:require.resolve('react', {paths:[process.argv[2]]}),loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer', {paths:[process.argv[2]]})),ts=webRequire('typescript');
let calls=[],mode='success',advance=0,saved=0;
const store=new Map();global.sessionStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)};global.window={addEventListener(){},removeEventListener(){},scrollY:0};

let requestLog=[];let mfa=false;
function load(file){const module={exports:{}};const src=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;new Function('module','exports','require',src)(module,module.exports,id=>{
 if(id==='react-router-dom')return {Link:({children,...p})=>React.createElement('a',p,children)};
 if(id==='../lib/review')return {stateLabel:s=>s,reviewRequest:async(url,body)=>{requestLog.push({url,body});if(body){if(mfa)throw Error('MFA required');return {id:'reserved'}};if(url==='/editorial/manage')return {items:[]};if(url.includes('/catalog'))return {items:[{id:url.includes('kind=papers')?'paper-future':'future-module',title:'Future module',papers:2,bank:'website'}],has_more:false};return {bank:'mpsc',reviewers:[{handle:'Reviewer'}],modules:[{id:'future',title:'Future module'}],shared_papers:2,corrections:[{state:'submitted',count:1}],mine:[{id:'mine',kind:'explanation',state:'draft'}]};}};
 return webRequire(id);
 });return module.exports}
const Manager=load(root+'/web/src/components/EditorialAssignmentManager.tsx').default;
const Context=load(root+'/web/src/components/EditorialReviewContext.tsx').default;
const waitChoices=()=>act(async()=>{await new Promise(r=>setTimeout(r,230))});
(async()=>{let tree,changed=0;await act(async()=>{tree=create(React.createElement(Manager,{needsMfa:false,onChanged:()=>changed++}))});
 await act(async()=>tree.root.findByType('details').props.onToggle({currentTarget:{open:true}}));await waitChoices();
 const button=text=>tree.root.findAllByType('button').find(b=>b.children.join('').includes(text));
 assert.equal(button('Reserve selected').props.disabled,true);
 await act(async()=>tree.root.findAllByType('input').find(i=>i.props.type==='radio').props.onChange({target:{checked:true}}));
 await act(async()=>tree.root.findAllByType('input').find(i=>i.props.type==='email').props.onChange({target:{value:'reviewer@example.test'}}));
 await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}));
 assert.equal(requestLog.at(-2).body.collection_id,'future-module');assert.equal(changed,1);
 await act(async()=>button('Choose individual').props.onClick());await waitChoices();assert.equal(button('Reserve selected').props.disabled,true);
 await act(async()=>tree.root.findAllByType('input').find(i=>i.props.type==='checkbox').props.onChange({target:{checked:true}}));
 await act(async()=>tree.root.findAllByType('input').find(i=>i.props.placeholder?.startsWith('Example:')).props.onChange({target:{value:'Website source review'}}));
 await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}));
 const payload=requestLog.findLast(r=>r.body).body;assert.deepEqual(payload.paper_ids,['paper-future']);assert.equal(payload.title,'Website source review');assert.equal(payload.collection_id,undefined);
 await act(async()=>{tree.unmount();tree=create(React.createElement(Manager,{needsMfa:true,onChanged(){}}))});await act(async()=>tree.root.findByType('details').props.onToggle({currentTarget:{open:true}}));assert.equal(tree.root.findByType('fieldset').props.disabled,true);
 await act(async()=>{tree.unmount();tree=create(React.createElement(Context,{assignment:'a',appearance:'app',refresh:0}))});
 assert.equal(tree.root.findAllByType('a')[0].props.to,'/contributions/mine');
 const text=JSON.stringify(tree.toJSON());assert.ok(text.includes('MPSC bank')&&text.includes('Future module')&&text.includes('shared question'));
 await act(async()=>tree.unmount());console.log('Workspace UI checks passed: future module selection, exact Website paper payload, scope reset, MFA disabling and own-proposal/context links.');
})().catch(e=>{console.error(e);process.exitCode=1});
