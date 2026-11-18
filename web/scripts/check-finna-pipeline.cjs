// Controlled API fixtures only; this check cannot contact the live bank.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
const stages=['discovered','acquired','extracted','review','ready','published'];
let params=new URLSearchParams({tab:'intake'}),calls=[],tree;
const row=stage=>({id:'fixture-'+stage,title:'Fixture paper · '+stage,exam:'Fixture exam',year:2026,paper_id:null,paper_url:'',reference_url:'',stage,version:1,source_sha256:null,artifact:null,last_error:null,review_stale:false,review_note:null,sync_id:null});
async function request(url,body){assert.equal(body,undefined,'Browsing must not mutate intake');const q=new URL(url,'https://fixture.invalid').searchParams;calls.push(q);return {items:[row(q.get('stage')==='all'?'discovered':q.get('stage'))],total:q.get('stage')==='all'?6:1,counts:stages.map(stage=>({stage,count:1}))}}
const cache=new Map();function load(file){if(cache.has(file))return cache.get(file);const m={exports:{}};const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(m,m.exports,id=>{
  if(id==='react-router-dom')return {Link:({children,...p})=>React.createElement('a',p,children),useSearchParams:()=>{const [,refresh]=React.useState(0);return [params,v=>{params=typeof v==='function'?v(params):new URLSearchParams(v);refresh(n=>n+1)}]}};
  if(id.endsWith('/review'))return {reviewRequest:request};
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(base+(fs.existsSync(base+'.tsx')?'.tsx':'.ts'))}return wr(id);
 });cache.set(file,m.exports);return m.exports}
const Screen=load(root+'/web/src/screens/PaperIntake.tsx').default;
const text=node=>typeof node==='string'?node:Array.isArray(node)?node.map(text).join(''):node?.children?.map(text).join('')||'';
(async()=>{
 await act(async()=>{tree=create(React.createElement(Screen,{canWrite:false}));});
 assert.deepEqual(calls.filter(q=>q.get('limit')==='3').map(q=>q.get('stage')).sort(),[...stages].sort(),'The board must fetch previews for every stage, not just group one global page');
 for(const stage of stages)assert.ok(JSON.stringify(tree.toJSON()).includes('Fixture paper · '+stage),'Each stage preview is visible: '+stage);
 assert.equal(tree.root.findAllByType('article').length,6);
 const open=tree.root.findAllByType('button').filter(b=>text(b).startsWith('Open stage'));
 await act(async()=>open[4].props.onClick());assert.equal(params.get('stage'),'ready');assert.ok(calls.some(q=>q.get('stage')==='ready'&&!q.has('limit')));
 assert.equal(tree.root.findAllByType('article').length,1,'A stage opens its full paginated list');
 const inspect=tree.root.findAllByType('button').find(b=>text(b)==='Inspect evidence →');
 await act(async()=>inspect.props.onClick());
 assert.ok(tree.root.findAllByType('select').filter(s=>s.props.disabled).length,'Read-only inspection keeps the stage editor disabled');
 assert.ok(!tree.root.findAllByType('button').some(b=>text(b).includes('Save evidenced stage')),'Read-only viewers cannot save a stage');
 assert.equal(calls.length,8,'Opening evidence does not POST or silently advance a stage');
 await act(async()=>tree.unmount());console.log('Finna pipeline passed: independent stage previews, full-list navigation, original pagination and read-only evidence without mutations.');
})().catch(e=>{console.error(e);process.exitCode=1});
