// Normal user/guest workflows with mocked APIs; no live account or publication.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
global.crypto=require('node:crypto').webcrypto;
global.window={location:{origin:'https://study.hawayu.in'},setTimeout,clearTimeout,addEventListener(){},removeEventListener(){}};
global.document={title:'India Study Map'};
let copied='',authenticated=true,params=new URLSearchParams(),route={},navigated=[],calls=[],rows=[],tree,started=[],existing=null;
global.navigator={clipboard:{async writeText(v){copied=v}}};
const question={id:'cq_test',question:'Choose the source-backed option.',options:['A','B'],answer_source:'official'};
const config={duration_minutes:7,marks_correct:2,marks_wrong:.5,answer_mode:'official'};
const meta={id:'learn_'+'a'.repeat(32),revision:3,title:'GK & English?',description:'Read the instructions and choose one option.',question_count:1,subject_id:'english',config,path:'/tests/learn_'+'a'.repeat(32)};
const session={id:'mock1',collection_id:'shared-tests',learning_test_id:meta.id,learning_test_version:3,learning_test_title:meta.title,paper_id:null,section_path:null,paper_mode:'practice',answer_mode:'official',questions:[{...question,position:0}],seconds_remaining:420,duration_seconds:420,saved_answers:{},marked_questions:[],current_position:0};
const navigate=to=>navigated.push(to);
let refresh=()=>{};
async function request(url,body){calls.push({url,body});
 if(url==='/learning-catalog/manage?timed=true')return {items:rows,user_id:'normal-user'};
 if(url==='/review/taxonomy')return [{id:'english',label:'English',level:'subject'}];
 if(url.startsWith('/tests/find?')||url.startsWith('/tests/selection?'))return {items:[question],total:1};
 if(url==='/learning-catalog'){
  const row={id:body.id,version:1,state:'draft',author_id:'normal-user',payload:body.content,live_payload:null,history:[]};rows=[row];return row;
 }
 if(url.endsWith('/decision')){rows=rows.map(r=>({...r,version:r.version+1,state:'submitted'}));return rows[0]}
 if(url==='/tests/'+meta.id)return meta;
 if(url==='/tests')return {items:[meta],total:1};
 return {};
}
const cache=new Map();
function load(file){if(cache.has(file))return cache.get(file);const m={exports:{}};
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020,esModuleInterop:false}}).outputText;
 new Function('module','exports','require',code)(m,m.exports,id=>{
  if(id==='react-router-dom')return {Link:({children,to,...p})=>React.createElement('a',{href:to,...p},children),useParams:()=>route,useNavigate:()=>navigate,useSearchParams:()=>[params,(next)=>{params=typeof next==='function'?next(params):new URLSearchParams(next);refresh()}]};
  if(id==='../lib/accountContext')return {accountContext:async()=>({authenticated})};
  if(id==='../lib/review'||id==='./review')return {reviewRequest:request};
  if(id==='../lib/api')return {currentMock:async()=>existing,getCollection:async()=>{throw Error('Shared tests must not load a hidden exam')},isLaterExamCollection:()=>false,startMock:async body=>{started.push(body);return session},saveMockAnswer:async()=>({ok:true}),submitMock:async()=>({id:'result1'}),getMockResult:async()=>({id:'result1'})};
  if(id==='../components/MockResultView')return {default:()=>null,mmss:s=>String(s)};
  if(id==='../components/AnswerLayout')return {AnswerOptions:({children})=>React.createElement('div',null,children),AnswerLayoutControl:()=>null};
  if(id==='../components/SourceQuestionText')return {SourceQuestionText:({text})=>React.createElement('span',null,text),SourceQuestionContext:()=>null};
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(fs.existsSync(base)?base:fs.existsSync(base+'.tsx')?base+'.tsx':base+'.ts')}
  return wr(id);
 });cache.set(file,m.exports);return m.exports;
}
const text=n=>Array.isArray(n)?n.map(text).join(''):typeof n==='string'?n:n&&text(n.children);
function button(label){return tree.root.findAllByType('button').find(b=>text(b.children)===label)}
function field(label){const l=tree.root.findAllByType('label').find(l=>text(l.children).startsWith(label));return l.findAll(n=>n.type==='input'||n.type==='select'||n.type==='textarea')[0]}
async function mount(Component){refresh=()=>tree?.update(React.createElement(Component));await act(async()=>{tree=create(React.createElement(Component))})}
(async()=>{
 const lib=load(root+'/web/src/lib/sharedTests.ts');
 assert.equal(lib.mockResumePath(session),'/tests/'+meta.id+'/take');assert.equal(lib.mockResumePath({...session,learning_test_id:null,collection_id:'ldc',paper_id:'source',paper_mode:'full'}),'/exams/ldc/mock?paper=source&simulation=full');
 const wa=new URL(lib.testWhatsAppUrl(meta.id,meta.title));assert.equal(wa.origin,'https://wa.me');assert.ok(wa.searchParams.get('text').startsWith(meta.title));assert.ok(!wa.searchParams.get('text').includes('score'));
 const Maker=load(root+'/web/src/screens/TestMaker.tsx').default;
 authenticated=false;await mount(Maker);assert.ok(JSON.stringify(tree.toJSON()).includes('Sign in to make a test'));assert.equal(calls.length,0);await act(async()=>tree.unmount());
 authenticated=true;await mount(Maker);assert.ok(button('Save draft'));assert.equal(button('Save draft').props.disabled,true);
 await act(async()=>field('Title').props.onChange({target:{value:'A normal user test'}}));await act(async()=>field('Instructions').props.onChange({target:{value:'Read each question carefully and choose one option.'}}));await act(async()=>field('Main subject').props.onChange({target:{value:'english'}}));
 await act(async()=>button('Find questions').props.onClick());assert.ok(calls.find(c=>c.url.startsWith('/tests/find?subject')||c.url.includes('subject=english')));
 await act(async()=>button('Add question').props.onClick());assert.equal(button('Save draft').props.disabled,false);
 await act(async()=>button('Save draft').props.onClick());const saved=calls.find(c=>c.url==='/learning-catalog');assert.deepEqual(saved.body.content.question_ids,['cq_test']);assert.equal(saved.body.content.test_config.duration_minutes,20);
 assert.ok(button('Submit saved test for review'));assert.ok(!JSON.stringify(tree.toJSON()).includes('Share on WhatsApp'));
 await act(async()=>field('Title').props.onChange({target:{value:'Unsaved edit'}}));assert.equal(button('Submit saved test for review').props.disabled,true);
 await act(async()=>button('Save draft').props.onClick());await act(async()=>button('Submit saved test for review').props.onClick());assert.ok(calls.find(c=>c.url.endsWith('/decision')).body.action==='submit');await act(async()=>tree.unmount());
 const Share=load(root+'/web/src/components/TestShare.tsx').default;await act(async()=>{tree=create(React.createElement(Share,{id:meta.id,title:meta.title}))});await act(async()=>button('Copy test link').props.onClick());assert.equal(copied,'https://study.hawayu.in/api/tests/'+meta.id+'/share');assert.ok(tree.root.findAllByType('a').some(a=>a.props.href.startsWith('https://wa.me/?text=')));await act(async()=>tree.unmount());
 route={testId:meta.id};params=new URLSearchParams();const Runner=load(root+'/web/src/screens/MockRunner.tsx').default;
 await mount(Runner);assert.equal(started[0].learning_test_id,meta.id);assert.equal(started[0].learning_test_version,3);assert.ok(JSON.stringify(tree.toJSON()).includes(meta.title));await act(async()=>tree.unmount());
 existing=session;route={id:'shared-tests'};await mount(Runner);assert.ok(navigated.includes('/tests/'+meta.id+'/take'));await act(async()=>tree.unmount());
 const Guide=load(root+'/web/src/components/PdfLibraryGuide.tsx').default;await mount(Guide);assert.ok(JSON.stringify(tree.toJSON()).includes('How to use PDF Library'));assert.ok(tree.root.findAllByType('a').some(a=>a.props.href.includes('pdf_view=attention')));await act(async()=>tree.unmount());
 console.log('Shareable test UI passed: normal-user creation, guest sign-in boundary, saved-before-submit, review-before-sharing, WhatsApp encoding/copy, private results, pinned test start, legacy resume redirect and PDF guide links.');
})().catch(e=>{console.error(e);process.exitCode=1});
