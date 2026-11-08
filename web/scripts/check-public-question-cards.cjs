const assert=require('node:assert/strict'),fs=require('node:fs');
const req=require('node:module').createRequire(process.cwd()+'/web/package.json'),React=req('react'),ts=req('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
const events=new Map();global.window={location:{origin:'http://test',pathname:'/bank/q1',search:'?paper=p1'},addEventListener:(n,f)=>events.set(n,f),removeEventListener:(n)=>events.delete(n)};
function load(name,mocks){const m={exports:{}};new Function('module','exports','require',ts.transpileModule(fs.readFileSync('web/src/'+name,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText)(m,m.exports,id=>mocks[id]||req(id));return m.exports;}
const router={Link:({children,...p})=>React.createElement('a',p,children)};
const source={SourceQuestionText:({text})=>React.createElement('span',null,text)};
const entry=i=>({answer_index:i,answer_text:'Option '+i,explanation:'Reasoning '+i,document:null});
const json=t=>JSON.stringify(t.toJSON());
let calls=[],reply={official:entry(1),solution:entry(1),relation:'agree',held:false},fail=false,pending;
const Comparison=load('components/AnswerComparison.tsx',{'../lib/answerStatus':load('lib/answerStatus.ts',{}),'./SourceQuestionText':source,'../lib/api':{getAnswerComparison:(q,p,signal,restore)=>{calls.push([q,p,signal,restore]);return pending?new Promise(r=>pending.resolve=r):fail?Promise.reject(Error('Network failed')):Promise.resolve(reply)}}}).default;
let authenticated=true,posted=[],postError=false,staff=false;
const account={accountContext:async()=>({authenticated})};
const review={reviewRequest:async(...args)=>{posted.push(args);if(postError)throw Error('Please retry');return {id:1,status:'open'}}};
const Report=load('components/QuestionReport.tsx',{'react-router-dom':router,'../lib/accountContext':account,'../lib/review':review}).default;
const Actions=load('components/QuestionDiscussion.tsx',{'react-router-dom':router,'./QuestionReport':{default:Report},'../lib/useQuestionStaff':{useQuestionStaff:()=>staff},'../lib/examScope':{scopeLink:x=>x},'./AvatarArt':{UserAvatar:()=>null},'../lib/device':{deviceId:()=>''},'../lib/review':review}).QuestionActions;
(async()=>{
 let tree;await act(async()=>{tree=create(React.createElement(Comparison,{qid:'q1',paperId:'p1'}))});
 assert.equal(calls.length,0);assert.ok(!json(tree).includes('Reasoning'));
 await act(async()=>tree.root.findByType('button').props.onClick());
 assert.deepEqual(calls[0].slice(0,2),['q1','p1']);assert.equal(calls[0][3],false);assert.ok(json(tree).includes('Official key and verified answer agree'));assert.ok(!tree.root.findByType('details').props.open);
 reply={official:entry(1),solution:entry(2),relation:'disagree',held:true};
 await act(async()=>tree.update(React.createElement(Comparison,{qid:'q2',paperId:'p2',revealed:true})));
 assert.equal(calls.at(-1)[3],true);assert.ok(json(tree).includes('Answer conflict'));assert.ok(json(tree).includes('Excluded from scored tests pending review.'));assert.equal(tree.root.findAllByType('dd').length,2);
 await act(async()=>tree.update(React.createElement(Comparison,{qid:'q2',paperId:'p2',revealed:true,options:['Option 2','Option 1']})));
 assert.deepEqual(tree.root.findAllByType('dd').map(d=>d.findByType('span').children.join('')),['B · Option 1','A · Option 2']);
 reply={official:entry(1),solution:null,relation:'not-compared',held:false};
 await act(async()=>tree.update(React.createElement(Comparison,{qid:'q3',revealed:true})));
 assert.ok(!json(tree).includes('Our answer:'));assert.ok(!json(tree).includes('answers agree'));assert.ok(!json(tree).includes('contribute/new'));
 // A current unreviewed answer can differ from a key without becoming verified.
 reply={official:entry(1),solution:null,relation:'not-compared',held:false};
 await act(async()=>tree.update(React.createElement(Comparison,{qid:'candidate',revealed:true,options:['Option 1','Option 2'],answer:{answer_text:'Option 2',answer_index:1,answer_source:'inferred'}})));
 assert.ok(json(tree).includes('Answer under review'));assert.ok(json(tree).includes('Suggested answer'));assert.ok(!json(tree).includes('Verified answer'));
 await act(async()=>tree.update(React.createElement(Comparison,{qid:'candidate',revealed:true,options:['Option 1','Option 2'],answer:{answer_text:'Option 1',answer_index:0,answer_source:'inferred'}})));
 assert.equal(tree.root.findAllByProps({'aria-label':'Answer conflict'}).length,0);
 // An agreeing verified solution must not hide a differing unverified practice answer.
 reply={official:entry(1),solution:entry(1),relation:'agree',held:false};
 await act(async()=>tree.update(React.createElement(Comparison,{qid:'candidate-conflict',revealed:true,options:['Option 1','Option 2'],answer:{answer_text:'Option 2',answer_index:1,answer_source:'derived'}})));
 assert.ok(json(tree).includes('Answer under review'));assert.ok(json(tree).includes('Suggested answer'));
 // Different imported letters for the same answer text are agreement.
 reply={official:{...entry(1),answer_text:'Same text'},solution:{...entry(2),answer_text:'Same text'},relation:'agree',held:false};
 await act(async()=>tree.update(React.createElement(Comparison,{qid:'same-text',revealed:true})));
 assert.equal(tree.root.findAllByProps({'aria-label':'Answer conflict'}).length,0);
 reply={official:entry(1),solution:null,relation:'not-compared',held:false};
 fail=true;await act(async()=>tree.update(React.createElement(Comparison,{qid:'q4',revealed:true,children:React.createElement('p',null,'Existing answer explanation')})));
 assert.ok(tree.root.findByProps({role:'alert'}));assert.equal(tree.root.findAllByType('details').length,0);assert.ok(json(tree).includes('Existing answer explanation'));fail=false;await act(async()=>tree.root.findByType('button').props.onClick());assert.equal(tree.root.findAllByProps({role:'alert'}).length,0);
 pending={};await act(async()=>tree.update(React.createElement(Comparison,{qid:'slow',revealed:true})));const old=pending,signal=calls.at(-1)[2];pending=null;
 await act(async()=>tree.update(React.createElement(Comparison,{qid:'hidden'})));assert.ok(signal.aborted);
 await act(async()=>old.resolve({...reply,solution:entry(3)}));assert.ok(!json(tree).includes('Reasoning 3'));
 await act(async()=>tree.unmount());
 await act(async()=>{tree=create(React.createElement(Actions,{qid:'q1',context:{paper_id:'p1'}}))});
 assert.ok(!json(tree).includes('Review / edit'));assert.ok(!json(tree).includes('Suggest correction'));assert.equal(tree.root.findAllByType('form').length,0);
 staff=true;await act(async()=>tree.update(React.createElement(Actions,{qid:'q1',context:{paper_id:'p1'}})));assert.ok(json(tree).includes('Review / edit'));
 const report=tree.root.findAllByType('button').find(b=>b.children.includes('Report an issue'));
 await act(async()=>report.props.onClick());
 await act(async()=>tree.root.findByType('textarea').props.onChange({target:{value:'The explanation does not match the stated question.'}}));
 authenticated=false;await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}));assert.equal(posted.length,0);assert.ok(json(tree).includes('Sign in to send your report'));
 authenticated=true;postError=true;await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}));assert.ok(json(tree).includes('Please retry'));assert.ok(tree.root.findByType('textarea').props.value.includes('does not match'));
 postError=false;await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}));assert.equal(posted.at(-1)[0],'/review/questions/q1/report');assert.equal(posted.at(-1)[1].paper_id,'p1');assert.ok(json(tree).includes('sent to our review team'));await act(async()=>tree.unmount());
 // Auth changes immediately remove staff affordances; late requests cannot restore them.
 let resolveSession;const hook=load('lib/useQuestionStaff.ts',{'./accountContext':account,'./review':{reviewSession:()=>new Promise(r=>resolveSession=r)}}).useQuestionStaff;
 function Gate(){return React.createElement('span',null,hook()?'staff':'public')}
 await act(async()=>{tree=create(React.createElement(Gate))});assert.ok(json(tree).includes('public'));
 authenticated=false;await act(async()=>events.get('ism-auth-change')());await act(async()=>resolveSession({grants:[{role:'owner'}]}));assert.ok(json(tree).includes('public'));await act(async()=>tree.unmount());
 console.log('Public cards passed: gated answer reveal, agree/differ/missing states, retry, stale request cancellation, staff-only editing, private reports and auth boundaries.');
})().catch(e=>{console.error(e);process.exitCode=1});
