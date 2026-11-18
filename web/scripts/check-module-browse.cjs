const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path')
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript')
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React}
const {act,create}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}))
let params=new URLSearchParams('view=browse&order=repeated&paper=paper-i&section=gs'),reads=[],tree
const events={};global.window={setTimeout,clearTimeout,addEventListener:(n,f)=>events[n]=f,removeEventListener:n=>delete events[n]};global.requestAnimationFrame=f=>setTimeout(f,0)
const cache=new Map()
function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};new Function('module','exports','require',ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText)(mod,mod.exports,id=>{
 if(id==='react-router-dom')return {useSearchParams:()=>[params,fn=>{params=typeof fn==='function'?fn(params):new URLSearchParams(fn)}],Link:({children,to,...p})=>React.createElement('a',{...p,href:to},children)}
 if(id==='../hooks/useBrowsePosition')return {useBrowsePosition:()=>({initializing:false,message:'Saved',startAgain(){}})}
 if(id==='../lib/api')return {getAccountSession:async()=>({authenticated:false}),getExamStudyTopics:async()=>({subjects:[{id:'english',title:'English',questions:50,topics:[{id:'grammar',title:'Grammar',questions:20,subtopics:[]}]}]}),listQuestions:async p=>{reads.push(p);return {items:[],total:100}},prefetchQuestionPage(){}}
 if(id==='../lib/review'||id==='../lib/learning')return {}
 if(id==='../lib/pagination')return {scrollToResults(){}}
 if(id==='../components/StudyQuestionCard')return {default:()=>null}
 if(id==='../components/AnswerLayout')return {AnswerLayoutControl:()=>null}
 if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(fs.existsSync(base+'.tsx')?base+'.tsx':base+'.ts')}
 return wr(id)
});cache.set(file,mod.exports);return mod.exports}
const Screen=load(root+'/web/src/screens/ModuleStudy.tsx').ModuleQuestionBrowser
const props={collectionId:'combined-prelims',papers:[{id:'paper-i',year:2025,title:'Paper I',questions:100,section_path:'gs',paper_number:'I'},{id:'paper-ii',year:2025,title:'Paper II',questions:100,section_path:'aptitude',paper_number:'II'}],sections:[{path:'gs',title:'General Studies'},{path:'aptitude',title:'Aptitude'}]}
async function render(){await act(async()=>{if(tree)tree.update(React.createElement(Screen,props));else tree=create(React.createElement(Screen,props));await new Promise(r=>setTimeout(r,20))})}
async function settle(){await render();await act(async()=>new Promise(r=>setTimeout(r,20)))}
const button=text=>tree.root.findAllByType('button').find(b=>b.children.join('').includes(text))
;(async()=>{
 await settle()
 const row=tree.root.findByProps({'aria-label':'Question filters'})
 assert.equal(row.findAllByType('label').length,6)
 assert.ok(reads.some(p=>p.paper_id==='paper-i'&&p.section_path==='gs'))
 assert.equal(reads.at(-1).order,'paper','Opening a paper reads its printed sequence even from an old mixed/repeated URL')
 await act(async()=>button('Next paper').props.onClick());await settle()
 assert.equal(params.get('paper'),'paper-ii');assert.equal(params.get('section'),'aptitude','Next paper clears incompatible Paper I filter')
 assert.ok(reads.some(p=>p.paper_id==='paper-ii'&&p.section_path==='aptitude'))
 assert.equal(reads.at(-1).order,'paper','Next paper retains printed order')
 await act(async()=>tree.root.findByProps({'aria-label':'Paper type'}).props.onChange({target:{value:'gs'}}));await settle()
 assert.equal(params.has('paper'),false,'Paper type change clears incompatible exact paper')
 assert.equal(reads.at(-1).order,'repeated','General Browse retains the chosen order')
 await act(async()=>tree.root.findByProps({'aria-label':'Question status'}).props.onChange({target:{value:'answer:written'}}));await settle()
 assert.ok(reads.some(p=>p.answer_status==='written'&&p.pool==='all'))
 await act(async()=>tree.root.findByProps({'aria-label':'Question status'}).props.onChange({target:{value:'study:unseen'}}));await settle()
 assert.equal(params.has('answer_status'),false);assert.ok(reads.some(p=>p.study_status==='unseen'))
 params=new URLSearchParams('view=practice&paper=paper-i&order=mixed&seed=practice-seed');await settle()
 assert.equal(reads.at(-1).order,'mixed','Paper practice keeps its existing mixed order')
 await act(async()=>tree.unmount())
 console.log('Module Browse passed: printed paper order, unchanged general/practice ordering, aligned controls, next paper, compatible filters and status requests.')
})().catch(e=>{console.error(e);process.exitCode=1})
