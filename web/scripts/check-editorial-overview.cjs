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
const Component=load(root+'/web/src/components/EditorialPaperOverview.tsx').default;
const papers=Array.from({length:18},(_,i)=>({id:'paper-'+i+'.pdf',exam_name:'UDC',year:2026-i,paper_subject:'Subject '+i,questions:100,recorded:[0,2,3].includes(i)?100:i===1?25:0,checked:i===0||i===2?99:i===3?100:i===1?25:0,recheck:i===2?1:0,bank:'mpsc',corrections:{pending:0,published:0,failed:0},flagged:i===0?1:0,last_activity:i===1?'2026-11-03T12:00:00Z':null,resume:{question:'q'+i,appearance:'a'+i,offset:25}}));
(async()=>{let tree,opened;await act(async()=>{tree=create(React.createElement(Component,{papers,busy:false,onOpen:p=>opened=p.id}))});
 const button=(text)=>tree.root.findAllByType('button').find(b=>b.children.join('').includes(text));
 assert.equal(tree.root.findAllByType('article').length,8);
 await act(async()=>button('Continue review').props.onClick());assert.equal(opened,'paper-1.pdf');
 await act(async()=>button('Next →').props.onClick());assert.equal(tree.root.findAllByType('article').length,8);
 await act(async()=>button('Next →').props.onClick());assert.equal(tree.root.findAllByType('article').length,2);
 await act(async()=>button('Needs attention').props.onClick());assert.equal(tree.root.findAllByType('article').length,2);
 await act(async()=>button('Review flagged question').props.onClick());assert.equal(opened,'paper-0.pdf');
 await act(async()=>button('In progress').props.onClick());assert.equal(tree.root.findAllByType('article').length,3);
 await act(async()=>button('Review complete').props.onClick());assert.equal(tree.root.findAllByType('article').length,1);
 await act(async()=>tree.root.findByType('input').props.onChange({target:{value:'no matching paper'}}));assert.equal(tree.root.findAllByType('article').length,0);
 await act(async()=>tree.unmount());console.log('Paper overview checks passed: eight-card paging, resume target, flagged/in-progress filters and search empty state.');
})().catch(e=>{console.error(e);process.exitCode=1});
