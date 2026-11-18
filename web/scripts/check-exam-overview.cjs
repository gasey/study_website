const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path')
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript')
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React}
const {act,create}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}))
let params=new URLSearchParams(),tree
const cache=new Map()
function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};new Function('module','exports','require',ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText)(mod,mod.exports,id=>{
 if(id==='react-router-dom')return {Link:({children,to,...p})=>React.createElement('a',{...p,href:to},children),useSearchParams:()=>[params,fn=>params=typeof fn==='function'?fn(params):new URLSearchParams(fn)]}
 if(id.endsWith('.css'))return {}
 if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(fs.existsSync(base+'.tsx')?base+'.tsx':base+'.ts')}
 return wr(id)
});cache.set(file,mod.exports);return mod.exports}
const paper=(id,year,extra={})=>({id,year,title:'Original examination',exam:'Original examination',paper_label:'Paper I',paper_number:'I',section_path:'general',questions:100,scorable:60,answerable_count:90,descriptive:0,allow_browse:true,allow_practice:true,source_pdf_url:'/papers/'+id,...extra})
const collection={id:'ldc',title:'LDC',questions:300,answerable_count:270,scorable:180,paper_list:[paper('old',2020),paper('new',2026),paper('unknown',null)]}
const {examOverviewGroups}=load(root+'/web/src/lib/examOverview.ts')
assert.deepEqual(examOverviewGroups([collection],'newest').map(g=>g.year),[2026,2020,null])
assert.deepEqual(examOverviewGroups([collection],'oldest').map(g=>g.year),[2020,2026,null])
const Screen=load(root+'/web/src/components/ExamOverview.tsx').default
const text=()=>JSON.stringify(tree.toJSON())
async function mount(extra={}){await act(async()=>{tree?.unmount();tree=create(React.createElement(Screen,{title:'LDC',collections:[collection],...extra}))})}
const links=()=>tree.root.findAllByType('a')
;(async()=>{
 await mount({navigation:React.createElement('nav',{'aria-label':'Existing study views'},'Browse by subject · Practice')})
 assert.equal(tree.root.findAllByType('article').length,3,'Overview lists all paper summaries without fetching question batches')
 assert.ok(text().includes('Browse by subject'))
 const browses=links().filter(a=>a.children.join('')==='Browse questions →')
 assert.equal(browses.length,3)
 const browse=new URL(browses[0].props.href,'https://study.hawayu.in')
 assert.equal(browse.pathname,'/exams/ldc');assert.equal(browse.searchParams.get('view'),'browse');assert.equal(browse.searchParams.get('paper'),'new');assert.equal(browse.searchParams.get('pool'),'all')
 assert.equal(new URL(links().find(a=>a.children.join('')==='Practice').props.href,'https://study.hawayu.in').searchParams.get('paper'),'new')
 await act(async()=>tree.root.findByType('select').props.onChange({target:{value:'oldest'}}));await mount()
 assert.equal(new URL(links().find(a=>a.children.join('')==='Browse questions →').props.href,'https://study.hawayu.in').searchParams.get('paper'),'old')
 await mount({collections:[{...collection,paper_list:[paper('written',2025,{questions:4,descriptive:4,allow_practice:false,answerable_count:0,scorable:0}),paper('pdf-only',2024,{questions:0,allow_browse:false,allow_practice:false,answerable_count:0,scorable:0})]}]})
 assert.equal(links().filter(a=>a.children.join('')==='Practice').length,0)
 assert.equal(links().filter(a=>a.children.join('')==='Browse questions →').length,1)
 assert.equal(links().filter(a=>a.props.target==='_blank').length,2)
 params=new URLSearchParams()
 const booklets=['A','B'].map(series=>paper(`2025 Paper I Series ${series}.pdf`,2025,{section_path:'gs',questions:series==='B'?98:100}))
 await mount({collections:[{...collection,id:'combined-prelims',paper_list:booklets}]})
 assert.equal(tree.root.findAllByType('article').length,1)
 assert.equal(links().filter(a=>a.props.href?.startsWith('/exams/combined-prelims/paper?')).length,2,'Every alternate original remains accessible')
 assert.ok(new URL(links().find(a=>a.children.join('')==='Browse questions →').props.href,'https://study.hawayu.in').searchParams.get('paper').includes('Series A'))
 const navigation=React.createElement('nav',{'aria-label':'Existing study views'},'Browse by subject · Practice')
 await mount({navigation})
 const stableHeader=tree.root.findByType('header')
 await act(async()=>tree.update(React.createElement(Screen,{title:'LDC',collections:[collection],navigation,viewKey:'browse',children:React.createElement('section',null,'Selected paper questions')})))
 assert.equal(tree.root.findByType('header'),stableHeader,'Tab changes retain the same header DOM')
 assert.ok(text().includes('Selected paper questions'))
 assert.ok(!text().includes('Past paper summaries'),'Only the selected tab content is mounted')
 await mount({collections:[],loading:true});assert.ok(text().includes('Loading exam papers'))
 let retried=false;await mount({collections:[],error:'Failed to load',onRetry:()=>retried=true});await act(async()=>tree.root.findByType('button').props.onClick());assert.ok(retried)
 await act(async()=>tree.unmount())
 console.log('Exam overview passed: date order, exact paper Browse/Practice links, existing navigation, written/PDF-only gates, alternate originals and retry.')
})().catch(e=>{console.error(e);process.exitCode=1})
