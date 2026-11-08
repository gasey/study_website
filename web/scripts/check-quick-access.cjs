// Uses the disposable renderer install passed as the first argument.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
const listeners=new Map();global.window={addEventListener(n,f){listeners.set(n,f)},removeEventListener(n){listeners.delete(n)}};
global.document={body:{style:{overflow:''}},activeElement:null};
let destination='',key='first',failed=false;
const rows=[{id:'udc',title:'Upper Division Clerk (UDC)',kind:'exam'},{id:'ldc',title:'Lower Division Clerk (LDC)',kind:'exam'},{id:'later',title:'Later exam',kind:'exam'}];
const cache=new Map();function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};new Function('module','exports','require',ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText)(mod,mod.exports,id=>{
 if(id==='react-dom')return {createPortal:x=>x};
 if(id==='react-router-dom')return {Link:({children,...p})=>React.createElement('a',p,children),useNavigate:()=>to=>{destination=to},useLocation:()=>({key})};
 if(id==='../lib/api')return {listCollections:async()=>{if(failed)throw Error('offline');return rows},isLaterExamCollection:c=>c.id==='later'};
 if(id==='../lib/examScope')return {useExamScope:()=> 'all'};
 if(id==='./NavIcon')return {default:()=>null};
 if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(base+(fs.existsSync(base+'.tsx')?'.tsx':'.ts'))}return wr(id);
 });cache.set(file,mod.exports);return mod.exports}
const helpers=load(root+'/web/src/lib/quickAccess.ts'),QuickStudy=load(root+'/web/src/components/QuickStudy.tsx').default,QuickFind=load(root+'/web/src/components/QuickFind.tsx').default;
const publicAccess={grants:[],assigned:false},owner={grants:[{role:'owner',subject_id:null}],assigned:false};
let tree,modal=false;async function render(Component,props){await act(async()=>{tree?.unmount();tree=create(React.createElement(Component,props),{createNodeMock:element=>element.type==='dialog'?{showModal(){modal=true},close(){modal=false},querySelectorAll(){return []}}:element.type==='input'?{focus(){}}:null})})}
const button=label=>tree.root.findAllByType('button').find(b=>b.props['aria-label']===label||b.children.join('').includes(label));
(async()=>{
 const publicItems=helpers.quickDestinations(rows,publicAccess);assert.ok(!publicItems.some(x=>x.to.startsWith('/admin')||x.to.startsWith('/editorial')));
 const assigned=helpers.quickDestinations(rows,{grants:[],assigned:true});assert.ok(assigned.some(x=>x.to==='/editorial'));assert.ok(!assigned.some(x=>x.to.startsWith('/admin')));
 const scoped=helpers.quickDestinations(rows,{grants:[{role:'reviewer',subject_id:'science'}],assigned:false});assert.ok(!scoped.some(x=>x.to.includes('pdf-library')));
 assert.ok(helpers.quickDestinations(rows,owner).some(x=>x.to.includes('pdf-library')));
 assert.equal(helpers.matchDestinations(publicItems,'upper clerk')[0].to,'/exams/udc');
 for(const id of ['udc','ldc','assistant'])for(const task of ['mixed','unseen','ever_wrong','papers']){
  const url=new URL(helpers.quickStudyHref(id,task),'https://study.hawayu.in');assert.equal(url.pathname,'/exams/'+id);assert.equal(url.searchParams.get('view'),task==='papers'?'papers':'browse');assert.equal(url.searchParams.get('status'),['unseen','ever_wrong'].includes(task)?task:null);assert.ok(!url.pathname.endsWith('/mock'));assert.equal(url.hash,task==='papers'?'#past-paper-results':'#exam-question-browser');
 }
 await render(QuickStudy);assert.ok(button('Open').props.disabled);assert.ok(!JSON.stringify(tree.toJSON()).includes('Later exam'));
 await act(async()=>tree.root.findByProps({'aria-label':'Quick start exam'}).props.onChange({target:{value:'udc'}}));
 await act(async()=>tree.root.findByProps({'aria-label':'Quick start task'}).props.onChange({target:{value:'ever_wrong'}}));
 await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}));assert.equal(destination,helpers.quickStudyHref('udc','ever_wrong'));
 failed=true;await render(QuickStudy);assert.ok(button('Open').props.disabled);failed=false;await act(async()=>button('Try again').props.onClick());assert.ok(!JSON.stringify(tree.toJSON()).includes('couldn’t load'));
 await render(QuickFind,{access:owner});await act(async()=>button('Quick find').props.onClick());assert.equal(modal,true);assert.equal(document.body.style.overflow,'hidden');
 await act(async()=>tree.root.findByType('input').props.onChange({target:{value:'PDF'}}));assert.ok(tree.root.findAllByType('a').some(a=>a.props.to.includes('pdf-library')));
 await act(async()=>tree.update(React.createElement(QuickFind,{access:publicAccess})));assert.ok(!tree.root.findAllByType('a').some(a=>a.props.to.startsWith('/admin')));
 await act(async()=>tree.root.findByType('input').props.onChange({target:{value:'question text'}}));await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}));assert.equal(destination,'/search?q=question+text');assert.equal(modal,false);assert.equal(document.body.style.overflow,'');
 await act(async()=>listeners.get('keydown')({ctrlKey:true,key:'k',preventDefault(){}}));assert.equal(modal,true);
 await act(async()=>tree.root.findByType('dialog').props.onCancel());assert.equal(modal,false);
 await act(async()=>tree.unmount());assert.ok(!listeners.has('keydown'));
 console.log('Quick access passed: staff/assignment boundaries, public catalog search, safe practice routes, selection/retry, sign-out isolation, modal cleanup, search handoff and keyboard shortcut.');
})().catch(e=>{console.error(e);process.exit(1)});
