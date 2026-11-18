// Exercise the real hook and all four actual authoring screens.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]})),router=wr('react-router-dom');
const events=new Map(),posts=[];let epoch=0,owner=false;
global.window={addEventListener(n,f){if(!events.has(n))events.set(n,new Set());events.get(n).add(f)},removeEventListener(n,f){events.get(n)?.delete(f)},setTimeout,clearTimeout,setInterval,clearInterval,location:{reload(){}}};global.document={};global.crypto||=require('node:crypto').webcrypto;
const documentValue={title:'Synthetic source-based note',summary:'A useful synthetic summary for checking the author workflow.',preview:'',kind:'note',access:'free',price_paise:0,tags:[],collection_id:null,subject_id:null,blocks:[{id:'paragraph',type:'paragraph',text:'My own synthetic explanation.'}]};
const content={kind:'practice',title:'Synthetic reviewed pool',description:'A useful description of the linked bank questions.',subject_id:'english',question_ids:['cq_synthetic'],sources:[],month:null,day:null,occurrences:[],themes:[],suggested_minutes:10,test_config:null};
let draft,detail,entry;function reset(){posts.length=0;draft={id:'m',author_id:'u',revision:1,lock_version:1,published_revision:null,workflow_state:'draft',document:structuredClone(documentValue),events:[],revisions:[]};detail={id:'c',title:'Synthetic proposal',kind:'explanation',state:'draft',revision:1,lock_version:1,author:'Synthetic author',author_id:'u',viewer_id:'u',is_author:true,permissions:[],current:{baseline:{},payload:{title:'Synthetic proposal',kind:'explanation',canonical_id:null,subject_id:'english',patch:{explanation:'Own reasoning'},rationale:'A useful source-based reason for the change.',evidence:[{kind:'reasoning',note:'Own synthetic calculation.'}]}},decisions:[],events:[],appeals:[],publications:[]};entry={id:'l',version:1,state:'draft',author_id:'u',payload:structuredClone(content),live_payload:null,history:[]}}
async function request(url,body){
 if(body!==undefined){posts.push({url,body});if(url.endsWith('/submit')){if(url.startsWith('/studio'))draft={...draft,workflow_state:'submitted',lock_version:2};else detail={...detail,state:'submitted',lock_version:2};return {state:'submitted'}}if(url.endsWith('/decision')){entry={...entry,state:body.action==='owner_publish'?'published':'submitted',version:2};return entry}if(url==='/learning-catalog'){entry={...entry,payload:body.content,version:2};return entry}throw Error('Unexpected write '+url)}
 if(url==='/contributions/c')return structuredClone(detail);
 if(url==='/studio/materials/m')return structuredClone(draft);
 if(url.startsWith('/learning-catalog/manage'))return {user_id:'u',can_owner_publish:owner,items:[structuredClone(entry)]};
 if(url==='/review/taxonomy')return [{id:'english',label:'English',level:'subject'}];
 if(url.startsWith('/tests/selection'))return {items:[]};
 throw Error('Unexpected read '+url)
}
const stub=()=>null,cache=new Map();function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};cache.set(file,mod.exports);
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(mod,mod.exports,id=>{
  if(id.endsWith('/accountContext'))return {accountGeneration:()=>epoch,accountContext:async()=>({authenticated:true})};
  if(id.endsWith('/review'))return {reviewRequest:request,kindLabel:x=>x,stateLabel:x=>x};
  if(id.endsWith('/materials'))return {contentRequest:request,EMPTY_DOCUMENT:documentValue,newBlock:()=>({id:'new',type:'paragraph',text:''}),BLOCK_LABELS:{paragraph:'Paragraph'}};
  if(id.endsWith('/api'))return {listCollections:async()=>[],listTaxonomy:async()=>[],listQuestions:async()=>({items:[]})};
  if(['/MaterialComparison','/AdminContentReview','/MaterialBody','/AdminReviewProgress','/ModuleEvidenceCitation','/TestShare'].some(n=>id.endsWith(n)))return {default:stub,MaterialFeedback:stub,ModuleEvidenceCitation:stub};
  if(id==='./Materials')return {CONTENT_BUTTON:'button',CONTENT_INPUT:'input'};
  if(id==='react-router-dom')return router;
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(base+(fs.existsSync(base+'.tsx')?'.tsx':'.ts'))}return wr(id);
 });return mod.exports}
const {useSubmissionChecklist}=load(root+'/web/src/components/SubmissionChecklist.tsx');const helpers=load(root+'/web/src/lib/submissionChecklist.ts');
let api,tree;const text=n=>typeof n==='string'?n:(n?.children||[]).map(text).join(''),json=()=>JSON.stringify(tree.toJSON()),button=label=>tree.root.findAllByType('button').find(n=>text(n)===label);
function Harness(props){api=useSubmissionChecklist(props.binding,props.body,props.issues,props.disabled);return React.createElement('div',null,api.accountChanged?api.notice:api.panel)}
async function renderHarness(props){await act(async()=>{tree?.unmount();tree=create(React.createElement(Harness,props))})}
async function checks(){const box=tree.root.findByProps({'aria-label':'Before you submit'});for(let index=0;index<3;index++)await act(async()=>box.findAllByType('input')[index].props.onChange({target:{checked:true}}))}
async function emit(name){if(name==='ism-auth-change')epoch++;await act(async()=>{for(const fn of [...(events.get(name)||[])])fn()})}
async function mount(file,url,route){reset();const Component=load(root+'/web/src/screens/'+file).default;await act(async()=>{tree?.unmount();tree=create(React.createElement(router.MemoryRouter,{initialEntries:[url]},React.createElement(router.Routes,null,React.createElement(router.Route,{path:route,element:React.createElement(Component)}))))})}
(async()=>{
 const body={note:'A'.repeat(65525)};assert.equal(helpers.submissionBytes(body),65536);assert.ok(helpers.submissionBytes({note:'🙂'.repeat(17000)})>65536);
 await renderHarness({binding:'a',body:{note:'Synthetic draft'},issues:[],disabled:false});assert.ok(!api.ready);await checks();assert.ok(api.ready);
 await act(async()=>tree.update(React.createElement(Harness,{binding:'b',body:{note:'Edited draft'},issues:[],disabled:false})));assert.ok(!api.ready);await act(async()=>tree.update(React.createElement(Harness,{binding:'a',body:{note:'Synthetic draft'},issues:[],disabled:false})));assert.ok(!api.ready,'Returning to old text cannot resurrect confirmation');
 await checks();const staleReady=api.isReady;await emit('ism-auth-expired');assert.ok(!staleReady()&&json().includes('Your account changed'));
 await renderHarness({binding:'large',body:{note:'🙂'.repeat(17000)},issues:[],disabled:false});await checks();assert.ok(!api.ready&&json().includes('64 KiB submission limit'));
 await renderHarness({binding:'disabled',body:{},issues:[],disabled:true});await checks();assert.ok(!api.ready);
 assert.ok(helpers.materialIssues({...documentValue,blocks:[{id:'a',type:'link',url:'https://example.test/source',text:''}]}).some(x=>x.includes('name the linked source')));
 owner=false;await mount('ContributionDetail.tsx','/contributions/c','/contributions/:id');assert.ok(button('Submit for review').props.disabled);await act(async()=>button('Submit for review').props.onClick());assert.equal(posts.length,0);await checks();assert.ok(!button('Submit for review').props.disabled);await act(async()=>button('Submit for review').props.onClick());assert.deepEqual(posts[0],{url:'/contributions/c/submit',body:{expected_version:1,reason:''}});
 await mount('ContentStudio.tsx','/studio/m','/studio/:id');assert.ok(button('Submit for publication').props.disabled);await checks();assert.ok(!button('Submit for publication').props.disabled);const oldSubmit=button('Submit for publication').props.onClick;await emit('ism-auth-change');await act(async()=>oldSubmit());assert.equal(posts.length,0);assert.ok(json().includes('Your account changed')&&!json().includes(documentValue.title));
 await mount('ContentStudio.tsx','/studio/m','/studio/:id');await checks();await act(async()=>button('Submit for publication').props.onClick());assert.deepEqual(posts[0],{url:'/studio/materials/m/submit',body:{expected_version:1}});
 await mount('LearningCatalogAdmin.tsx','/learning/manage?entry=l','/learning/manage');assert.ok(button('Submit saved revision').props.disabled);await checks();assert.ok(!button('Submit saved revision').props.disabled);await act(async()=>button('Submit saved revision').props.onClick());assert.equal(posts[0].url,'/learning-catalog/l/decision');assert.equal(posts[0].body.action,'submit');assert.equal(posts[0].body.expected_version,1);
 owner=true;reset();entry.payload.test_config={duration_minutes:20,marks_correct:1,marks_wrong:0,answer_mode:'official'};
 const TestMaker=load(root+'/web/src/screens/TestMaker.tsx').default;await act(async()=>{tree?.unmount();tree=create(React.createElement(router.MemoryRouter,{initialEntries:['/tests/make?test=l']},React.createElement(TestMaker)))});
 assert.ok(button('Submit saved test for review').props.disabled);await act(async()=>button('Preview owner publication').props.onClick());assert.ok(button('Publish test as owner').props.disabled);await checks();assert.ok(!button('Publish test as owner').props.disabled);await act(async()=>button('Publish test as owner').props.onClick());assert.equal(posts[0].body.action,'owner_publish');assert.equal(posts[0].body.preview_confirmed,true);
 await act(async()=>tree.unmount());assert.ok([...events.values()].every(set=>!set.size));
 console.log('Submission checklists passed: all four real authoring screens; source/rights/format confirmations, UTF-8 body limit, permanent edit/revert invalidation, current-account guards, same-revision submit payloads, owner preview/publication gating and no role/API changes.');
})().catch(e=>{console.error(e);process.exitCode=1});
