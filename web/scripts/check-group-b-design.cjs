const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),webRequire=require('node:module').createRequire(root+'/web/package.json'),React=webRequire('react'),ts=webRequire('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
let params=new URLSearchParams(),failTopics=false,reads=[],writes=[],progressReads=[];
let progress={answered:0,unique_questions:0,correct:0,accuracy:0,current_streak:0,active_days_30:0,daily_activity:[],sections:[],last_active_at:null};
const listeners=new Map();
global.window={location:{search:''},scrollTo(){},addEventListener(n,f){listeners.set(n,f)},removeEventListener(n){listeners.delete(n)}};
const paper=(id,written,year=2020)=>({id,title:'Departmental '+id,exam:'Departmental examination',year,paper_number:'I',paper_label:'Original paper',questions:10,descriptive:written,source_pdf_url:'/papers/source/'+id,allow_browse:true,answerable_count:written?0:10,scorable:0,practice_count:0});
const ng={id:'group-b-non-gazetted',questions:120,scorable:2,answerable_count:100,paper_list:Array.from({length:12},(_,i)=>paper('ng-'+i,i===0?2:0,2020+i))};
const gaz={id:'group-b-gazetted',questions:10,scorable:0,answerable_count:0,paper_list:[paper('gaz-written',10,2018)]};
const topicData=id=>({collection_id:id,subjects:id===gaz.id?[{id:'gk-gs',title:'General Knowledge',questions:1,topics:[]}]:[{id:'english',title:'English',questions:20,topics:[]},{id:'gk-gs',title:'General Knowledge',questions:30,topics:[{id:'approved-current-id',title:'Current Affairs',questions:5,subtopics:[]}]}],questions:50,unclassified:0});
const cache=new Map();function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};new Function('module','exports','require',ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText)(mod,mod.exports,id=>{
 if(id==='react-router-dom')return {Link:({children,...p})=>React.createElement('a',p,children),useSearchParams:()=>[params,(fn)=>{params=typeof fn==='function'?fn(params):new URLSearchParams(fn)}]};
 if(id==='../lib/api')return {getProgress:async id=>{progressReads.push(id);return progress},getMistakes:async()=>[],getExamStudyTopics:async id=>{reads.push(id);if(failTopics)throw Error('Unavailable');return topicData(id)},getCollection:async id=>id===gaz.id?gaz:ng,getGroupBStudyConfig:async()=>({rules:[]}),getExamBookmarks:async()=>({collection_ids:[]}),saveExamBookmark:async id=>writes.push(['save',id]),removeExamBookmark:async id=>writes.push(['remove',id])};
 if(id==='./ModuleStudy')return {ModuleQuestionBrowser:()=>React.createElement('div',{'data-view':'questions'}),ModuleProgressPanel:({collectionId})=>React.createElement('div',{'data-progress':collectionId})};
 if(file.endsWith('/ModuleStudy.tsx')&&['../components/StudyQuestionCard','../lib/requestCache','../lib/learning','../components/AnswerLayout','../lib/review'].includes(id))return {};
 if(id.endsWith('.css'))return {};
 if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(fs.existsSync(base+'.tsx')?base+'.tsx':base+'.ts')}
 return webRequire(id);
});cache.set(file,mod.exports);return mod.exports;}
const Home=load(root+'/web/src/components/GroupBStudyHome.tsx').default,Archive=load(root+'/web/src/components/GroupBPaperArchive.tsx').default,Topics=load(root+'/web/src/components/ExamStudyTopics.tsx').default,Screen=load(root+'/web/src/screens/GroupBStudy.tsx').default,ProgressPanel=load(root+'/web/src/screens/ModuleStudy.tsx').ModuleProgressPanel;
let tree,Component,props;const links=()=>tree.root.findAllByType('a').map(a=>a.props.to).filter(Boolean),text=()=>JSON.stringify(tree.toJSON());
async function mount(C,p={}){Component=C;props=p;await act(async()=>{tree?.unmount();tree=create(React.createElement(C,p))})}
async function rerender(){await act(async()=>tree.update(React.createElement(Component,props)))}
const button=label=>tree.root.findAllByType('button').find(b=>b.children.join('').includes(label));
(async()=>{
 await mount(Home,{collection:ng.id,sources:[ng],technicalCount:2});assert.ok(text().includes('Choose a subject. Build from there.'));assert.ok(links().some(l=>l.includes('topic_id=approved-current-id')));assert.ok(links().filter(l=>l.startsWith('/group-b')).every(l=>new URL(l,'https://test').searchParams.get('collection')===ng.id));
 await act(async()=>button('Save exam').props.onClick());assert.deepEqual(writes,[['save',ng.id]]);
 await mount(Home,{collection:gaz.id,sources:[gaz],technicalCount:0});assert.ok(text().includes('Start with an original paper.'));assert.ok(text().includes('No answer-ready MCQ practice'));assert.ok(!links().some(l=>l.includes('view=practice')));assert.ok(!links().some(l=>l.includes('study_area=english')||l.includes('topic_id=')));assert.ok(links().some(l=>l.includes('paper_kind=written')));
 failTopics=true;await mount(Home,{collection:ng.id,sources:[ng],technicalCount:0});assert.ok(button('Retry subjects'));failTopics=false;await act(async()=>button('Retry subjects').props.onClick());assert.ok(links().some(l=>l.includes('topic_id=approved-current-id')));
 params=new URLSearchParams('collection=group-b-non-gazetted&view=papers&paper_page=2');await mount(Archive,{sources:[ng]});assert.equal(tree.root.findAllByType('li').length,2);
 await act(async()=>tree.root.findByType('input').props.onChange({target:{value:'ng-0'}}));await rerender();assert.equal(params.has('paper_page'),false);assert.equal(tree.root.findAllByType('li').length,1);assert.ok(links().some(l=>l.includes('/exams/'+ng.id+'/paper?paper=ng-0')));
 params=new URLSearchParams('collection=group-b-gazetted&view=papers&paper_kind=written');await mount(Archive,{sources:[gaz]});assert.equal(tree.root.findAllByType('li').length,1);assert.ok(links()[0].startsWith('/exams/'+gaz.id+'/paper'));
 params=new URLSearchParams('collection=group-b&view=topics');await mount(Topics,{examId:'group-b',area:'common',basePath:'/group-b',allowPractice:false});assert.ok(links().every(l=>l.includes('collection=group-b')));assert.ok(!links().some(l=>l.includes('view=practice')));
 await mount(Topics,{examId:ng.id,area:'common',basePath:'/group-b'});assert.ok(links().some(l=>l.includes('view=practice')));
 // Expansion must work independently, and search results must still be collapsible.
 const toggles=()=>tree.root.findAllByType('button').filter(b=>b.props['aria-controls']?.startsWith('subject-topics-'));
 assert.ok(toggles().every(b=>b.props['aria-expanded']===false));
 await act(async()=>button('Expand all').props.onClick());assert.ok(toggles().every(b=>b.props['aria-expanded']===true));
 await act(async()=>toggles()[0].props.onClick());assert.equal(toggles()[0].props['aria-expanded'],false);assert.equal(toggles()[1].props['aria-expanded'],true);
 await act(async()=>tree.root.findByType('input').props.onChange({target:{value:'Current'}}));assert.equal(toggles().length,1);assert.equal(toggles()[0].props['aria-expanded'],true);
 await act(async()=>toggles()[0].props.onClick());assert.equal(toggles()[0].props['aria-expanded'],false);assert.equal(tree.root.findByProps({id:'subject-topics-gk-gs'}).props.hidden,true);
 await act(async()=>tree.root.findByType('input').props.onChange({target:{value:''}}));assert.equal(toggles().length,2);assert.ok(toggles().every(b=>b.props['aria-expanded']===false));
 params=new URLSearchParams('collection=group-b-gazetted&view=practice');await mount(Screen);assert.equal(tree.root.findAllByProps({'data-view':'questions'}).length,0);assert.ok(text().includes('does not currently have answer-ready'));
 params=new URLSearchParams('collection=group-b-gazetted&view=progress');await mount(Screen);assert.equal(tree.root.findByProps({'data-progress':gaz.id}).props['data-progress'],gaz.id);
 params=new URLSearchParams('collection=group-b&view=progress');await mount(Screen);assert.ok(text().includes('Choose a group for progress'));assert.equal(tree.root.findAll(n=>n.props['data-progress']).length,0);
 await mount(ProgressPanel,{collectionId:gaz.id,collectionTitle:'Group B Gazetted',totalScorable:0,practiceAvailable:false,papersHref:'/group-b?collection='+gaz.id+'&view=papers'});assert.ok(text().includes('Reading & written preparation'));assert.ok(!text().includes('Progress saved automatically'));assert.ok(!links().some(l=>l.includes('view=practice')));assert.deepEqual(links(),['/group-b?collection='+gaz.id+'&view=papers']);assert.equal(progressReads.at(-1),gaz.id);
 await mount(ProgressPanel,{collectionId:ng.id,collectionTitle:'Group B Non-Gazetted',totalScorable:2,practiceHref:'/group-b?collection='+ng.id+'&view=practice'});assert.ok(links().some(l=>l==='/group-b?collection='+ng.id+'&view=practice'));assert.equal(progressReads.at(-1),ng.id);
 await mount(ProgressPanel,{collectionId:'udc',collectionTitle:'UDC',totalScorable:100});assert.ok(links().includes('/exams/udc?view=practice'));assert.ok(links().includes('/exams/udc?view=papers'));
 progress={...progress,answered:3,unique_questions:2,correct:2,accuracy:67};await mount(ProgressPanel,{collectionId:gaz.id,collectionTitle:'Group B Gazetted',totalScorable:0,practiceAvailable:false});assert.ok(text().includes('Recorded answer activity'));assert.ok(text().includes('67%'));assert.ok(!links().some(l=>l.includes('view=practice')));
 await act(async()=>tree.unmount());console.log('Group B design checks passed: scoped subjects/current affairs, written-first Gazetted, real availability, retry, bookmarking, archive pagination, combined-source links and progress isolation.');
})().catch(e=>{console.error(e);process.exitCode=1});
