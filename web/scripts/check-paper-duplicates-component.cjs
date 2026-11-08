const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
const paper='Old_Questions/Departmental_2015-2018/3.Departmental Exam for Inspector under Excise 2016 Paper III.pdf';
const a={id:'canonical-a',appearance_id:'desc-3d4c5f6b168c76b1d4c7',type:'descriptive',qnum:'1',page:1,series:null,question:'Define: Cannabis',options:[],direction:'Attempt all questions.',marks:null,answer_source:'none'};
const b={...a,id:'canonical-b',appearance_id:'desc-753c3e58a04fcb5ae9c2',question:'Define:- Cannabis'};
const rows=[a,b],collection={id:'group-b-gazetted',title:'Gazetted',paper_list:[{id:paper,title:'Paper III',questions:2,descriptive:2,year:2016}]};
let params=new URLSearchParams({paper}),tree;
global.window={addEventListener(){},removeEventListener(){}};global.requestAnimationFrame=fn=>fn();
const cache=new Map(),empty=()=>null;
function load(file){
 file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(mod,mod.exports,id=>{
  if(id==='react-router-dom')return {Link:({children,...p})=>React.createElement('a',p,children),useParams:()=>({id:collection.id}),useSearchParams:()=>[params,fn=>{params=typeof fn==='function'?fn(params):fn}]};
  if(id==='../lib/api')return {getCollection:async()=>collection,getPaperReadiness:async()=>null,listPaperQuestions:async()=>({items:rows,total:2,practice_count:0})};
  if(id==='../components/PracticeAnswerPanel'||id==='../components/AnswerProvenance')return {__esModule:true,default:empty};
  if(id==='../components/QuestionDiscussion')return {QuestionActions:({qid})=>React.createElement('div',{'data-correction-for':qid})};
  if(id==='../components/AnswerLayout')return {AnswerLayoutControl:empty,AnswerOptions:({children})=>React.createElement('div',null,children)};
  if(id==='../components/SourceQuestionText')return {SourceQuestionContext:empty,SourceQuestionText:({text})=>React.createElement('span',null,text)};
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(fs.existsSync(base+'.tsx')?base+'.tsx':base+'.ts')}
  return wr(id);
 });cache.set(file,mod.exports);return mod.exports;
}
const Viewer=load(root+'/web/src/screens/PaperViewer.tsx').default;
const text=()=>JSON.stringify(tree.toJSON()),cards=()=>tree.root.findAllByType('article'),button=label=>tree.root.findAllByType('button').find(b=>b.children.join('').includes(label));
async function render(){await act(async()=>{tree?tree.update(React.createElement(Viewer)):tree=create(React.createElement(Viewer))})}
async function click(label){await act(async()=>button(label).props.onClick());await render()}
(async()=>{
 await render();assert.equal(cards().length,1);assert.ok(text().includes('1 printed questions · 2 stored transcriptions'));
 await click('Show all stored transcriptions');assert.equal(cards().length,2);
 assert.equal(tree.root.findAll(n=>n.props['data-correction-for']==='canonical-b').length,1);
 const duplicateFlag=cards()[1].findAllByType('button').find(b=>b.children.join('').includes('Flag to revisit'));
 await act(async()=>duplicateFlag.props.onClick());await click('Group duplicate transcriptions');assert.equal(cards().length,1);
 params.set('status','flagged');await render();assert.equal(cards().length,1);assert.ok(text().includes('Duplicate extraction of this printed question.'));
 params.delete('status');params.set('appearance',b.appearance_id);params.set('view','focus');await render();assert.equal(cards().length,1);
 assert.equal(tree.root.findAll(n=>n.props['data-correction-for']==='canonical-b').length,1);
 await click('Open grouped transcription');assert.equal(params.get('appearance'),a.appearance_id);
 await act(async()=>tree.unmount());console.log('Paper component passed: default grouping, show-all, exact correction IDs, retained flags, direct duplicate link and representative navigation.');
})().catch(e=>{console.error(e);process.exit(1)});
