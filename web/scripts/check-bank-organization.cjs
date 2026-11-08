// UI behaviour checks with a disposable in-memory session and mocked API only.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),webRequire=require('node:module').createRequire(root+'/web/package.json'),React=webRequire('react'),ts=webRequire('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
global.crypto=require('node:crypto').webcrypto;
global.window={setTimeout,clearTimeout,addEventListener(){},removeEventListener(){}};
global.sessionStorage={getItem(){return null},setItem(){},removeItem(){}};
let params=new URLSearchParams(),calls=[],tree,refresh=()=>{};
const nodes=[{id:'general-studies',label:'General Studies',level:'subject'}, {id:'general-knowledge',label:'General Knowledge',level:'subject'},
 {id:'general-studies/geography',label:'Geography',parent_id:'general-studies',level:'topic'}, {id:'general-knowledge/geography',label:'Geography',parent_id:'general-knowledge',level:'topic'},
 {id:'english',label:'English',level:'subject'},{id:'english/writing',label:'Writing',parent_id:'english',level:'topic'}];
const row={id:'cq_correctly_tagged',appearance_id:'app_exact',question:'A fully tagged question requiring a semantic repair',paper_id:'paper_exact',paper_title:'Legacy original',qnum:'7',bank:'mpsc',subject_label:'English',topic_label:'Writing',report_count:0,invalid:false};
const snapshot={canonical_id:row.id,baseline_token:'source1',record:{id:row.appearance_id,question:row.question,options:[],classification:{subject_id:'english',topic_id:'english/writing'}},paper:{id:'paper_exact'}};
const cache=new Map();
function load(file){if(file.endsWith('.json'))return {default:JSON.parse(fs.readFileSync(file,'utf8'))};if(cache.has(file))return cache.get(file);const m={exports:{}};
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020,esModuleInterop:false}}).outputText;
 new Function('module','exports','require',code)(m,m.exports,id=>{
  if(id==='react-router-dom')return {Link:({children,...p})=>React.createElement('a',p,children),useSearchParams:()=>[params,(next)=>{params=typeof next==='function'?next(params):next;refresh()}]};
  if(id==='../lib/review')return {reviewSession:async()=>({user_id:'owner'}),reviewRequest:async(url,body)=>{calls.push({url,body});if(url==='/collections')return [];if(url.endsWith('/providers'))return [{id:'mpsc',label:'Mizoram MPSC'}];if(url.endsWith('/views'))return [];if(url.includes('/tag-issues?'))return {items:[row],total:1};if(url.startsWith('/review/questions/'))return snapshot;if(url.includes('/tag-sources?'))return {items:[],has_more:false};if(url.includes('/questions?'))return {items:[],total:0};if(url.endsWith('/inventory/exams'))return {items:[]};return {}}};
  if(id==='./AdminAnswerDecision'||id==='./AdminReviewProgress')return {default:()=>null};
  if(id==='./QuestionCorrectionEditor')return {default:({onNext})=>React.createElement('button',{onClick:onNext},'Save and next stub')};
  if(['./QuestionOrganizationContext','./SourceQuestionText'].includes(id))return id.endsWith('SourceQuestionText')?{SourceQuestionText:({text})=>React.createElement('span',null,text)}:{default:()=>null};
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(fs.existsSync(base)?base:fs.existsSync(base+'.tsx')?base+'.tsx':base+'.ts')}
  return webRequire(id);
 });cache.set(file,m.exports);return m.exports;
}
const filters=load(root+'/web/src/lib/editorialTagFilters.ts'),taxonomy=load(root+'/web/src/lib/learningTaxonomy.ts');
const href=filters.tagReviewHref(row.id,row.appearance_id,row.paper_id,'/admin/bank?tab=questions&year=2017');
const deep=new URL(href,'https://example.test');assert.equal(deep.searchParams.get('tag_issue'),'all');assert.equal(filters.tagQuery(deep.searchParams),row.id);assert.equal(deep.searchParams.get('tag_appearance'),row.appearance_id);
assert.equal(filters.tagQuery(new URLSearchParams('tab=retag&q=cq_old')), 'cq_old');assert.equal(filters.tagQuery(filters.updateTagFilter(new URLSearchParams('tab=retag&q=cq_old'),'tag_q','')), '');assert.equal(filters.tagReturn(new URLSearchParams('tag_return=https://evil.test')), '');
const choices=taxonomy.learningChoices(nodes);assert.equal(choices.filter(c=>c.id==='gk-gs').length,1);assert.equal(choices.filter(c=>c.id==='gk-gs:geography').length,1);assert.ok(!choices.some(c=>c.path.subject_id==='gk-gs'));
const preferred=taxonomy.learningChoices(nodes,'general-knowledge').find(c=>c.id==='gk-gs:geography');assert.equal(preferred.path.subject_id,'general-knowledge');
const Cleanup=load(root+'/web/src/components/EditorialTagCleanup.tsx').default;
(async()=>{
 params=deep.searchParams;const props={nodes,canWrite:true};refresh=()=>tree?.update(React.createElement(Cleanup,props));
 await act(async()=>{tree=create(React.createElement(Cleanup,props))});await act(async()=>new Promise(r=>setTimeout(r,280)));
 assert.ok(calls.some(c=>c.url==='/review/questions/'+row.id+'?appearance_id='+row.appearance_id));
 assert.ok(JSON.stringify(tree.toJSON()).includes('A fully tagged question'));
 const back=tree.root.findAllByType('button').find(b=>b.children.join('').includes('Back to tag list'));await act(async()=>back.props.onClick());
 assert.equal(params.get('tag_selected'),null);assert.equal(params.get('tag_q'),row.id);assert.equal(params.get('tag_paper'),'paper_exact');
 const topic=tree.root.findByProps({'aria-label':'Current topic'});await act(async()=>topic.props.onChange({target:{value:'english/writing'}}));
 const scope=tree.root.findByProps({'aria-label':'Classification path scope'});await act(async()=>scope.props.onChange({target:{value:'related'}}));await act(async()=>new Promise(r=>setTimeout(r,280)));
 const request=new URL(calls.findLast(c=>c.url.includes('/tag-issues?')).url,'https://example.test');assert.equal(request.searchParams.get('topic'),'english/writing');assert.equal(request.searchParams.get('path'),'related');
 assert.ok(tree.root.findByProps({'aria-label':'Exam era'}));
 const yearField=()=>tree.root.findByProps({'aria-label':'Tag exam year'});
 assert.ok(!yearField().findAll(n=>n.type==='details').length);
 for(let parent=yearField().parent;parent;parent=parent.parent)assert.notEqual(parent.type,'details','Exam year must be visible without expanding filters');
 params.set('tag_offset','40');params.set('tag_bank','mpsc');refresh();
 await act(async()=>yearField().props.onChange({target:{value:'20'}}));await act(async()=>new Promise(r=>setTimeout(r,620)));assert.equal(params.get('tag_year'),null);
 await act(async()=>yearField().props.onChange({target:{value:'2017'}}));await act(async()=>new Promise(r=>setTimeout(r,340)));await act(async()=>new Promise(r=>setTimeout(r,280)));
 assert.equal(params.get('tag_year'),'2017');assert.equal(params.get('tag_offset'),null);assert.equal(params.get('tag_bank'),'mpsc');
 const yearRequest=new URL(calls.findLast(c=>c.url.includes('/tag-issues?')).url,'https://example.test');assert.equal(yearRequest.searchParams.get('year'),'2017');assert.equal(yearRequest.searchParams.get('paper'),'paper_exact');
 const clearYear=tree.root.findAllByType('button').find(b=>b.children.join('').includes('Exam year: 2017'));await act(async()=>clearYear.props.onClick());assert.equal(params.get('tag_year'),null);assert.equal(yearField().props.value,'');assert.equal(params.get('tag_bank'),'mpsc');await act(async()=>tree.unmount());
 const Inline=load(root+'/web/src/components/InlineQuestionCorrection.tsx').default;let advanced=0;await act(async()=>{tree=create(React.createElement(Inline,{question:row.id,appearance:row.appearance_id,onNext:()=>advanced++}))});const before=calls.filter(c=>c.url.startsWith('/review/questions/')).length;await act(async()=>tree.root.findByType('details').props.onToggle({currentTarget:{open:true}}));assert.equal(calls.filter(c=>c.url.startsWith('/review/questions/')).length,before+1);assert.ok(tree.root.findAllByType('button').some(b=>b.children.join('')==='Save and next stub'));await act(async()=>tree.root.findAllByType('button').find(b=>b.children.join('')==='Save and next stub').props.onClick());assert.equal(advanced,1);await act(async()=>tree.unmount());
 const Workbench=load(root+'/web/src/components/AdminQuestionWorkbench.tsx').default;
 params=new URLSearchParams('tab=questions&exam=udc&offset=40');const workProps={taxonomy:nodes,grants:[{role:'owner',subject_id:null}],onHold(){}};refresh=()=>tree?.update(React.createElement(Workbench,workProps));await act(async()=>{tree=create(React.createElement(Workbench,workProps))});
 const questionYear=()=>tree.root.findByProps({'aria-label':'Question exam year'});for(let parent=questionYear().parent;parent;parent=parent.parent)assert.notEqual(parent.type,'details');
 await act(async()=>questionYear().props.onChange({target:{value:'20'}}));await act(async()=>new Promise(r=>setTimeout(r,340)));assert.equal(params.get('year'),null);
 await act(async()=>questionYear().props.onChange({target:{value:'2020'}}));await act(async()=>new Promise(r=>setTimeout(r,340)));
 assert.equal(params.get('year'),'2020');assert.equal(params.get('offset'),null);assert.equal(params.get('exam'),'udc');const questionRequest=new URL(calls.findLast(c=>c.url.includes('/questions?')).url,'https://example.test');assert.equal(questionRequest.searchParams.get('year'),'2020');assert.equal(questionRequest.searchParams.get('exam_id'),'udc');
 await act(async()=>tree.root.findAllByType('button').find(b=>b.children.join('').includes('Exam year: 2020')).props.onClick());assert.equal(params.get('year'),null);assert.equal(params.get('exam'),'udc');await act(async()=>tree.unmount());
 console.log('Bank organisation UI passed: source/return scopes, taxonomy filters, and visible Questions/Learning-tags year controls with safe partial typing, API year binding, offset reset, preserved exam/source filters and clearing.');
})().catch(e=>{console.error(e);process.exitCode=1});
