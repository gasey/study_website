// Isolated response fixtures: no production API or bank writes.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
const listeners=new Map();global.window={addEventListener(n,f){if(!listeners.has(n))listeners.set(n,new Set());listeners.get(n).add(f)},removeEventListener(n,f){listeners.get(n)?.delete(f)}};
let calls=[],failure=false,waiting=null,quality={total:80,needs_review:31,missing:7,held:3},tasks={task_counts:{all:80,answer:26,source:9,publishing:2,failed:4,other:39}};
async function request(url,body){assert.equal(body,undefined,'Counting must be read-only');calls.push(url);if(waiting)return waiting;if(failure)throw Error('Fixture unavailable');if(url==='/admin/bank/quality')return quality;if(url==='/admin/bank/questions?issue=all&review_task=all&limit=1')return tasks;throw Error('Unexpected endpoint: '+url)}
const cache=new Map();function load(file){if(cache.has(file))return cache.get(file);const m={exports:{}};const js=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',js)(m,m.exports,id=>{
  if(id==='react-router-dom')return {Link:({children,...p})=>React.createElement('a',p,children)};
  if(id==='../lib/review')return {reviewRequest:request};
  if(id.startsWith('.')){const p=path.resolve(path.dirname(file),id);return load(p+(fs.existsSync(p+'.tsx')?'.tsx':'.ts'))}return wr(id);
 });cache.set(file,m.exports);return m.exports;
}
const Screen=load(root+'/web/src/components/AdminReviewAttention.tsx').default;
const text=node=>typeof node==='string'?node:Array.isArray(node)?node.map(text).join(''):node?.children?.map(text).join('')||'';
const health={questions:900,missing_answers:700,held:600,defects:500,queue:[{state:'submitted',count:5},{state:'publication_failed',count:422}]};
const props={health,grants:[{role:'owner',subject_id:null}]};let tree;
const rows=()=>tree.root.findAll(n=>n.props.className==='finna-attention-row');
const row=label=>rows().find(r=>text(r.findByType('h3'))===label);
const count=label=>text(row(label).findByType('strong'));
const href=label=>row(label).findByType('a').props.to;
const refresh=()=>tree.root.findAllByType('button').find(b=>text(b)==='Refresh counts').props.onClick();
(async()=>{
 await act(async()=>{tree=create(React.createElement(Screen,props))});
 assert.equal(count('Answers needing review'),'31','Unconfirmed answers must not be replaced by missing answers');
 assert.equal(count('MCQ answers missing'),'7','Use the scoped question count instead of global health');
 assert.equal(count('Held from scoring'),'3');
 assert.equal(count('Source / scoring problems'),'9');
 assert.equal(count('Questions awaiting publication'),'2');
 assert.equal(count('Questions with failed publications'),'4','Do not count 422 historical failed correction records');
 assert.equal(count('Submitted corrections'),'5');
 assert.equal(href('Answers needing review'),'/admin/bank?tab=questions&answer_status=needs-review');
 assert.equal(href('MCQ answers missing'),'/admin/bank?tab=questions&issue=missing');
 for(const [label,task] of [['Source / scoring problems','source'],['Questions awaiting publication','publishing'],['Questions with failed publications','failed']])assert.equal(new URL(href(label),'https://fixture.invalid').searchParams.get('review_task'),task);
 assert.equal(calls.length,2);
 failure=true;await act(async()=>refresh());assert.ok(text(tree.toJSON()).includes('Fixture unavailable'));assert.equal(count('Answers needing review'),'—','Failed requests must not show a fabricated zero or previous count');
 failure=false;quality={total:6,needs_review:2,missing:1,held:0};tasks={task_counts:{all:6,answer:3,other:3}};
 await act(async()=>tree.update(React.createElement(Screen,{...props,grants:[{role:'reviewer',subject_id:'english'}]})));
 assert.equal(count('Answers needing review'),'2','Changed permissions reload scoped counts');assert.equal(count('Questions with failed publications'),'0','An absent lane is an empty current queue');
 quality={...quality,needs_review:1};await act(async()=>{for(const f of listeners.get('ism-content-change')||[])f()});assert.equal(count('Answers needing review'),'1','Publication changes refresh review needs');
 let resolve;waiting=new Promise(r=>resolve=r);await act(async()=>refresh());assert.equal(count('Answers needing review'),'—');
 await act(async()=>tree.unmount());waiting=null;await act(async()=>resolve(quality));
 console.log('Admin review counts passed: unconfirmed vs missing, scoped totals, current vs historical failures, matching filter links, retry/empty/loading states, permission changes and publication refresh.');
})().catch(e=>{console.error(e);process.exitCode=1});
