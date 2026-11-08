// Run from repository root with a directory containing react-test-renderer@18.3.1 as argument.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),webRequire=require('node:module').createRequire(root+'/web/package.json');
const React=webRequire('react');require.cache[require.resolve('react', {paths:[process.argv[2]]})]={id:require.resolve('react', {paths:[process.argv[2]]}),filename:require.resolve('react', {paths:[process.argv[2]]}),loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer', {paths:[process.argv[2]]})),ts=webRequire('typescript');
let calls=[],mode='success',advance=0,saved=0;
const store=new Map();global.sessionStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)};global.window={addEventListener(){},removeEventListener(){},scrollY:0};
function load(file){const module={exports:{}};const src=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;new Function('module','exports','require',src)(module,module.exports,id=>{
 if(id==='react-router-dom')return {Link:({children,...p})=>React.createElement('a',p,children)};
 if(id==='../lib/review')return {reviewRequest:async(...args)=>{calls.push(args);if(mode==='failure')throw Error('Source changed. Reload before saving.');return {created_at:'2026-11-03T12:00:00Z'}}};
 if(id.includes('SourceQuestionText'))return {SourceQuestionText:({text})=>React.createElement('span',null,text),SourceQuestionContext:()=>null};
 if(id.includes('editorialReview'))return load(root+'/web/src/lib/editorialReview.ts');
 return webRequire(id);
 });return module.exports}
const Component=load(root+'/web/src/components/EditorialQuestionReview.tsx').default;
const props={snapshot:{inspection_version:'proof1',baseline_token:'version1',record:{qnum:'1',page:1,question:'Example?',options:['A','B'],answerIndex:0,type:'mcq',explanation:'Evidence'},paper:{title:'UDC',year:2026}},user:'test',assignment:'udc',appearance:'appearance1',question:'question1',needsMfa:false,hasNext:true,onNext:()=>advance++,onSaved:()=>saved++,onBusy:()=>{}};
(async()=>{
 let tree;await act(async()=>{tree=create(React.createElement(Component,props))});
 const buttons=()=>tree.root.findAllByType('button'),next=()=>buttons().find(b=>b.children.join('').includes('Checked & next'));
 assert.equal(next().props.disabled,false); // Explicit attestation needs no filler note.
 await act(async()=>tree.root.findByType('textarea').props.onChange({target:{value:'Compared against source page 1.'}}));
 mode='failure';await act(async()=>{await next().props.onClick()});
 assert.equal(advance,0);assert.equal(saved,0);assert.equal(tree.root.findByType('textarea').props.value,'Compared against source page 1.');assert.ok(tree.root.findByProps({role:'alert'}));
 mode='success';await act(async()=>{await next().props.onClick()});assert.equal(advance,1);assert.equal(saved,1);
 assert.equal(calls.at(-1)[1].source_version,'version1');assert.equal(calls.at(-1)[1].appearance_id,'appearance1');assert.equal(calls.at(-1)[1].attestation,'source-review-v1');assert.equal(calls.at(-1)[1].outcome,'checked');assert.ok(calls.at(-1)[0].endsWith('/quick-checks'));assert.equal(store.size,0);
 await act(async()=>{tree.unmount();tree=create(React.createElement(Component,{...props,needsMfa:true}))});assert.equal(next().props.disabled,true);
 await act(async()=>{tree.unmount();tree=create(React.createElement(Component,props))});
 await act(async()=>buttons().find(b=>b.children.join('')==='Cannot verify').props.onClick());
 let unresolved=()=>buttons().find(b=>b.children.join('').includes('Save unresolved'));
 assert.equal(unresolved().props.disabled,true);
 await act(async()=>tree.root.findByType('select').props.onChange({target:{value:'other'}}));assert.equal(unresolved().props.disabled,true);
 await act(async()=>tree.root.findByType('textarea').props.onChange({target:{value:'The source has an unreadable instruction.'}}));assert.equal(unresolved().props.disabled,false);
 await act(async()=>unresolved().props.onClick());assert.equal(calls.at(-1)[1].reason,'other');assert.equal(calls.at(-1)[1].outcome,'cannot_verify');
 await act(async()=>tree.unmount());console.log('Quick review checks passed: explicit attestation/no filler note, stale-save retention/no advance, success/next, source binding, MFA and unresolved reason gate.');
})().catch(e=>{console.error(e);process.exitCode=1});
