// Render actual owner controls against controlled API fixtures; never publishes live data.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
global.crypto=require('node:crypto').webcrypto;
const store=new Map();global.sessionStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)};
global.window={location:{origin:'https://study.hawayu.in'},addEventListener(){},removeEventListener(){}};global.document={title:'India Study Map'};
let calls=[],tree,rows=[],params=new URLSearchParams(),next=0,published=[];
const table=(id,title,group)=>({id,title,group,total:12,description:'Controlled fixture',href:'/admin/bank',columns:[{name:'id',type:'text',required:true,primary_key:true}]});
const map={tables:[table('canonical_questions','Questions','bank'),table('appearances','Paper positions','bank'),table('learning_catalog','Collections','delivery')],relationships:[['canonical_questions','learning_catalog','selected by saved rules']],foreign_keys:[{id:'appearance_question_fk',source:'appearances',target:'canonical_questions',source_columns:['canonical_id'],target_columns:['id'],source_unique:false,optional:false}],coverage:{questions:12,without_topic:4,without_subtopic:8},observed_at:'2026-11-06T00:00:00Z',read_only:true,scope:'Content tables only'};
async function request(url,body){calls.push({url,body});
 if(url==='/review/taxonomy')return [{id:'english',label:'English',level:'subject'},{id:'mizo',label:'Mizo',level:'subject'}];
 if(url==='/admin/bank/routine-edits')return {contribution_id:'con_owner',publication:{id:'pub_owner',state:'publishing'}};
 if(url.endsWith('/owner-preview'))return {version:3,preview_hash:'bound-preview',title:'Saved source paper',exam_name:'Synthetic exam',year:2026,questions:2,mcq:1,written:1,keyed:0,unanswered:1,unexplained:1};
 if(url.endsWith('/owner-publish'))return {job_id:'job_owner'};
 if(url==='/admin/bank/database-map')return map;
 if(url==='/learning-catalog/manage?timed=true')return {items:rows,user_id:'owner',can_owner_publish:true};
 if(url.startsWith('/tests/find?'))return {items:[{id:'cq_one',question:'Fixture question',options:['A','B']}],total:1};
 if(url.startsWith('/tests/selection?'))return {items:[{id:'cq_one',question:'Fixture question',options:['A','B']}]};
 if(url==='/learning-catalog'){const row={id:body.id,version:1,state:'draft',author_id:'owner',payload:body.content,live_payload:null,history:[]};rows=[row];return row}
 if(url.endsWith('/decision'))return {...rows[0],version:2,state:'published',live_payload:rows[0].payload,history:[]};
 return {};
}
const cache=new Map();function load(file){if(cache.has(file))return cache.get(file);const m={exports:{}};
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(m,m.exports,id=>{
  if(id==='react-router-dom')return {Link:({to,children,...p})=>React.createElement('a',{href:to,...p},children),useNavigate:()=>()=>{},useSearchParams:()=>[params,v=>{params=typeof v==='function'?v(params):new URLSearchParams(v)}]};
  if(id==='../lib/review')return {reviewRequest:request};
  if(id==='../lib/accountContext')return {accountContext:async()=>({authenticated:true})};
  if(id==='./SearchableTaxonomyPicker')return {default:({onChange})=>React.createElement('button',{type:'button',onClick:()=>onChange({subject_id:'mizo'})},'Choose Mizo'),pathLabel:p=>p.subject_id};
  if(id==='./AdminReviewProgress')return {default:()=>React.createElement('p',{role:'status'},'Queued')};
  if(id==='./TestShare'||id==='../components/TestShare')return {default:()=>null};
  if(id==='./SourceQuestionText'||id==='../components/SourceQuestionText')return {SourceQuestionText:({text})=>React.createElement('span',null,text)};
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(fs.existsSync(base)?base:fs.existsSync(base+'.tsx')?base+'.tsx':base+'.ts')}
  return wr(id);
 });cache.set(file,m.exports);return m.exports;
}
const text=n=>Array.isArray(n)?n.map(text).join(''):typeof n==='string'?n:n&&text(n.children);
const button=label=>tree.root.findAllByType('button').find(b=>text(b.children)===label);
function field(label){return tree.root.findAllByType('label').find(l=>text(l.children).startsWith(label)).findAll(n=>['input','textarea','select'].includes(n.type))[0]}
async function mount(C,p={}){await act(async()=>{tree=create(React.createElement(C,p))})}async function unmount(){await act(async()=>tree.unmount());store.clear()}
(async()=>{
 const Editor=load(root+'/web/src/components/QuestionCorrectionEditor.tsx').default;
 const snapshot={solo_owner:true,canonical_id:'cq_one',can_publish:true,edit_hash:'hash1',baseline_token:'source1',record:{id:'app_one',type:'mcq',question:'Fixture?',options:['A','B'],answerIndex:0,explanation:'An existing complete source explanation.',classification:{subject_id:'english'}},paper:{title:'Fixture'},documents:[]};
 await mount(Editor,{snapshot,user:'owner',onNext:()=>next++});await act(async()=>button('Choose Mizo').props.onClick());
 assert.equal(field('Owner note').props.required,false);assert.equal(button('Save & next').props.disabled,false);
 await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){},nativeEvent:{submitter:{getAttribute:()=> 'next'}}}));
 const edit=calls.find(c=>c.url==='/admin/bank/routine-edits');assert.equal(edit.body.note,'');assert.equal(edit.body.source_version,'source1');assert.equal(edit.body.canonical_id,'cq_one');assert.equal(next,1);assert.ok(!calls.some(c=>c.url.endsWith('/decisions')));await unmount();
 await mount(Editor,{snapshot:{...snapshot,documents:[{id:'doc_one',kind:'paper',sha256:'a'.repeat(64),title:'Original paper'}]},user:'owner'});
 await act(async()=>button('Source reference').props.onClick());await act(async()=>tree.root.findByProps({'aria-label':'Physical PDF page'}).props.onChange({target:{value:'2'}}));await act(async()=>tree.root.findByProps({'aria-label':'Printed question number'}).props.onChange({target:{value:'13'}}));
 await act(async()=>field('Source document').props.onChange({target:{value:'doc_one'}}));await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}));
 const linked=calls.findLast(c=>c.url==='/admin/bank/routine-edits');assert.equal(linked.body.note,'');assert.equal(linked.body.evidence[0].document_id,'doc_one');assert.ok(linked.body.evidence[0].note.length>=5);assert.ok(!linked.body.evidence[0].note.includes('inspected'));await unmount();
 await mount(Editor,{snapshot,user:'owner'});await act(async()=>button('Text / context').props.onClick());
 await act(async()=>field('Option A').props.onChange({target:{value:'Changed correct answer'}}));await act(async()=>field('Answer mapping').props.onChange({target:{value:'0'}}));
 assert.equal(field('Supporting note').props.required,true);assert.equal(button('Save & publish').props.disabled,true);await unmount();
 const Paper=load(root+'/web/src/components/OwnerPaperPublish.tsx').default,props={id:'draft1',version:3,state:'draft',dirty:true,onPublished:job=>published.push(job)};
 await mount(Paper,props);assert.equal(button('Preview publication').props.disabled,true);
 await act(async()=>tree.update(React.createElement(Paper,{...props,dirty:false})));await act(async()=>button('Preview publication').props.onClick());assert.ok(!calls.some(c=>c.url.endsWith('/owner-publish')));
 await act(async()=>button('Publish this saved paper as owner').props.onClick());const receipt=calls.find(c=>c.url.endsWith('/owner-publish'));assert.deepEqual(receipt.body,{expected_version:3,preview_hash:'bound-preview',inspected:true,note:''});assert.deepEqual(published,['job_owner']);
 await act(async()=>tree.update(React.createElement(Paper,{...props,dirty:false,version:4})));assert.ok(button('Preview publication'));await unmount();
 const Maker=load(root+'/web/src/screens/TestMaker.tsx').default;await mount(Maker);
 await act(async()=>field('Title').props.onChange({target:{value:'Owner fixture'}}));await act(async()=>field('Instructions').props.onChange({target:{value:'Read each fixture question carefully.'}}));await act(async()=>field('Main subject').props.onChange({target:{value:'english'}}));
 await act(async()=>button('Find questions').props.onClick());await act(async()=>button('Add question').props.onClick());
 const preview=tree.root.findAllByType('button').find(b=>text(b.children).includes('Preview')&&!text(b.children).includes('saved'));assert.ok(preview);await act(async()=>preview.props.onClick());
 const publish=tree.root.findAllByType('button').find(b=>text(b.children).includes('Publish')&&text(b.children).includes('owner'));assert.ok(publish);await act(async()=>publish.props.onClick());
 const decision=calls.find(c=>c.url.endsWith('/decision'));assert.equal(decision.body.action,'owner_publish');assert.equal(decision.body.preview_confirmed,true);assert.ok(!calls.some(c=>c.body?.action==='submit'));await unmount();
 const Database=load(root+'/web/src/components/DatabaseMap.tsx').default;calls=[];await mount(Database);assert.ok(tree.root.findByProps({'aria-label':'Scrollable database diagram'}));
 await act(async()=>button('Tables & foreign keys').props.onClick());assert.ok(text(tree.toJSON()).includes('canonical_id → id'));assert.ok(text(tree.toJSON()).includes('many → one'));
 await act(async()=>tree.root.findByProps({'aria-label':'Zoom in database map'}).props.onClick());assert.ok(text(tree.toJSON()).includes('125%'));await act(async()=>button('Reset zoom').props.onClick());
 await act(async()=>tree.root.findByProps({'aria-label':'Database area'}).props.onChange({target:{value:'delivery'}}));assert.ok(text(tree.root.findByProps({'aria-label':'Selected database table'}).toJSON?.()||tree.toJSON()).includes('Collections'));
 await act(async()=>button('Content flow').props.onClick());await act(async()=>button('List').props.onClick());assert.ok(!tree.root.findAllByProps({'aria-label':'Scrollable database diagram'}).length);
 await act(async()=>tree.root.findByProps({'aria-label':'Find a database table'}).props.onChange({target:{value:'unknown'}}));assert.ok(button('Show all mapped tables'));await act(async()=>button('Show all mapped tables').props.onClick());assert.ok(button('Questions12canonical_questions'));
 await act(async()=>button('Refresh live counts').props.onClick());assert.equal(calls.length,2);assert.ok(calls.every(c=>c.url==='/admin/bank/database-map'&&c.body===undefined));await unmount();
 console.log('Solo owner UI passed: optional routine notes, exact source binding, Save & next, answer evidence boundary, saved paper preview/publication, owner test publication and read-only interactive database map.');
})().catch(e=>{console.error(e);process.exitCode=1});
