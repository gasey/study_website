const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),webRequire=require('node:module').createRequire(root+'/web/package.json'),React=webRequire('react'),ts=webRequire('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
let params=new URLSearchParams(),calls=[],failSave=false;const store=new Map();
global.crypto=require('node:crypto').webcrypto;
global.sessionStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)};
global.window={addEventListener(){},removeEventListener(){},scrollY:0,setTimeout,clearTimeout};
const snap={baseline_token:'source1',inspection_version:'proof1',can_publish:true,record:{id:'appearance1',type:'mcq',question:'Synthetic question',options:['A','B'],answerIndex:0,answerSource:'derived',classification:{subject_id:'english'}},paper:{title:'Original paper',year:2020,source_pdf_url:null}};
const overview=()=>({scope:{id:params.get('scope'),title:'Future compiled module',collection_id:'future-module',revision:'revision1',kind:'module',assignment_id:null,area:null},items:[{id:'paper1',questions:2,recorded:1,checked:1,flagged:0,recheck:0,exam_name:'Original paper',exam_type:'Direct',year:2020,corrections:{pending:0,published:0,failed:0},resume:{appearance:'appearance1',question:'q1',offset:0},reused:1}],summary:{appearances:2,questions:1,checked:1,reused:1,flagged:0,recheck:0},selection:{definition_revision:'definition1',description:'Existing source rules'}});
function load(file){file=path.resolve(file);const mod={exports:{}};new Function('module','exports','require',ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText)(mod,mod.exports,id=>{
 if(id==='react-router-dom')return {Link:({children,...p})=>React.createElement('a',p,children),useSearchParams:()=>[params,fn=>{params=typeof fn==='function'?fn(params):new URLSearchParams(fn)}]};
 if(id==='../lib/review')return {reviewRequest:async(url,body)=>{calls.push({url,body});if(body){if(failSave)throw Error('Source changed; draft retained');return {created_at:'2026-11-04'}}if(url.startsWith('/editorial/scopes'))return {items:[{id:'module:future-module',title:'Future compiled module',kind:'module'}],has_more:false};if(url.startsWith('/editorial/scope/questions')&&new URL('https://test'+url).searchParams.get('after'))return {items:[{id:'appearance2',canonical_id:'q2',qnum:'26',question:'Next unresolved',can_check:true,unresolved_checks:[]}],offset:25,total:26,next:{appearance:'appearance2',question:'q2'}};if(url.startsWith('/editorial/scope/questions'))return {items:[{id:'appearance1',canonical_id:'q1',qnum:'1',question:'Synthetic question',checked:true,flagged:false,can_check:true,unresolved_checks:[],previous_check:{reviewer:'Source reviewer'}}],total:1};if(url.startsWith('/editorial/scope?'))return overview();if(url.startsWith('/review/questions'))return snap;return {}}};
 if(file.endsWith('/SharedModuleReview.tsx')&&id==='./EditorialPaperOverview')return {default:({onOpen,papers})=>React.createElement('button',{onClick:()=>onOpen(papers[0])},'Open source paper'),paperTitle:p=>p.exam_name};
 if(file.endsWith('/SharedModuleReview.tsx')&&id==='./EditorialQuestionReview')return {default:p=>React.createElement('div',{'data-scope':p.scope,'data-revision':p.scopeRevision,'data-appearance':p.appearance},React.createElement('button',{onClick:()=>{p.onSaved();p.onNext()}},'Save test inspection'))};
 if(id==='./ModuleCompositionEditor')return {default:()=>null};
 if(id==='./EditorialReviewContext')return {default:()=>null};
 if(id==='./SourceQuestionText')return {SourceQuestionContext:()=>null,SourceQuestionText:({text})=>React.createElement('span',null,text)};
 if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(fs.existsSync(base+'.tsx')?base+'.tsx':base+'.ts')}
 return webRequire(id);
});return mod.exports;}
const Module=load(root+'/web/src/components/SharedModuleReview.tsx').default,Question=load(root+'/web/src/components/EditorialQuestionReview.tsx').default;
let tree;async function mount(C,props){await act(async()=>{tree?.unmount();tree=create(React.createElement(C,props))});await act(async()=>new Promise(r=>setTimeout(r,240)))}
const button=text=>tree.root.findAllByType('button').find(b=>b.children.join('').includes(text));
(async()=>{
 params=new URLSearchParams('scope=module:future-module&assignment=old-assignment');await mount(Module,{user:'owner',needsMfa:false,onBusy(){}});
 assert.ok(JSON.stringify(tree.toJSON()).includes('Already checked elsewhere'));
 await act(async()=>button('Open source paper').props.onClick());await act(async()=>tree.update(React.createElement(Module,{user:'owner',needsMfa:false,onBusy(){}})));await act(async()=>new Promise(r=>setTimeout(r,20)));
 assert.equal(params.get('assignment'),null);assert.equal(params.get('appearance'),'appearance1');assert.equal(params.get('scope'),'module:future-module');
 params.set('review_layout','focus');await mount(Module,{user:'owner',needsMfa:false,onBusy(){}});
 const source=tree.root.findByProps({'data-scope':'module:future-module'});assert.equal(source.props['data-revision'],'revision1');
 assert.ok(JSON.stringify(tree.toJSON()).includes('Source reviewer'));
 await act(async()=>button('Save test inspection').props.onClick());
 await act(async()=>new Promise(r=>setTimeout(r,30)));
 assert.equal(params.get('appearance'),'appearance2');assert.equal(params.get('offset'),'25');assert.equal(params.get('review_queue'),'remaining');
 assert.ok(calls.some(c=>c.url.includes('after=appearance1')));
 const props={snapshot:snap,user:'owner',assignment:'',scope:'module:future-module',scopeRevision:'revision1',appearance:'appearance1',question:'q1',needsMfa:false,hasNext:false,onNext(){},onSaved(){},onBusy(){},unresolvedChecks:[{id:5,reviewer:'Reviewer',note:'Source issue'}]};
 await mount(Question,props);await act(async()=>tree.root.findByProps({'aria-label':'Optional inspection note'}).props.onChange({target:{value:'My source note'}}));
 failSave=true;await act(async()=>button('Record checked').props.onClick());assert.ok(tree.root.findByProps({role:'alert'}));assert.ok(store.size);
 const first=calls.findLast(c=>c.body);assert.equal(first.url,'/editorial/checks');assert.equal(first.body.scope,'module:future-module');assert.equal(first.body.scope_revision,'revision1');
 failSave=false;await act(async()=>button('Record checked').props.onClick());assert.equal(calls.findLast(c=>c.body).body.request_key,first.body.request_key);assert.equal(store.size,0);
 await mount(Question,{...props,canInspect:false});assert.equal(button('Record checked').props.disabled,true);
 await mount(Question,props);await act(async()=>tree.root.findByType('input').props.onChange({target:{checked:true}}));await act(async()=>tree.root.findAllByType('textarea').find(t=>t.props.maxLength===2000).props.onChange({target:{value:'Compared source evidence and resolved the recorded issue.'}}));await act(async()=>button('Record checked').props.onClick());assert.deepEqual(calls.findLast(c=>c.body).body.resolve_checks,[5]);
 await act(async()=>tree.unmount());console.log('Shared review UI passed: module/source URL binding, attributed reuse, capability disabling, retained drafts, idempotent retry and explicit issue resolution.');
})().catch(e=>{console.error(e);process.exitCode=1});
