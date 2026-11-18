// Real QuestionActions/TestShare controls; clipboard/native adapters only are faked.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]})),router=wr('react-router-dom');
const events=new Map();global.window={location:{origin:'https://fixture.test',search:'?result=PRIVATE&session=PRIVATE&email=PRIVATE'},addEventListener(n,f){events.set(n,f)},removeEventListener(n){events.delete(n)}};
global.navigator={};let scope='all',copies=[],pending,shareFailure;
navigator.clipboard={writeText:url=>{copies.push(url);return pending?new Promise((resolve,reject)=>pending.push({resolve,reject})):Promise.resolve()}};
navigator.share=async value=>{copies.push(value);if(shareFailure)throw shareFailure};
const stub=()=>null,cache=new Map();function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};cache.set(file,mod.exports);
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(mod,mod.exports,id=>{
  if(id.endsWith('/examScope'))return {scopeLink:x=>x+(scope==='all'?(x.includes('?')?'&':'?')+'exam_scope=all':'')};
  if(id.endsWith('/useQuestionStaff'))return {useQuestionStaff:()=>false};
  if(id.endsWith('/QuestionReport')||id.endsWith('/AvatarArt')||id.endsWith('/ContributorStanding')||id.endsWith('/PostEditing')||id.endsWith('/AcceptanceNudge')||id.endsWith('/BlockAuthor')||id.endsWith('/CommunityText')||id.endsWith('/DraftNotice'))return {default:stub,UserAvatar:stub};
  if(id.endsWith('/useComposerDraft')||id.endsWith('/communityDrafts')||id.endsWith('/device')||id.endsWith('/review'))return {};
  if(id==='react-router-dom')return router;
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(base+(fs.existsSync(base+'.tsx')?'.tsx':'.ts'))}return wr(id);
 });return mod.exports}
const Actions=load(root+'/web/src/components/QuestionDiscussion.tsx').QuestionActions,Test=load(root+'/web/src/components/TestShare.tsx').default;
let tree;const text=n=>typeof n==='string'?n:(n?.children||[]).map(text).join(''),json=()=>JSON.stringify(tree.toJSON()),button=label=>tree.root.findAllByType('button').find(n=>text(n)===label);
const action=props=>React.createElement(router.MemoryRouter,null,React.createElement(Actions,props));
(async()=>{
 await act(async()=>{tree=create(action({qid:'cq & word',context:{paper_id:'paper / 2020',collection_id:'PRIVATE COLLECTION'}}))});
 let link=tree.root.findAllByType('a').find(n=>text(n).includes('Share on WhatsApp'));let invitation=new URL(link.props.href).searchParams.get('text');
 assert.ok(invitation.includes('/api/questions/cq%20%26%20word/share?paper=paper+%2F+2020&exam_scope=all'));
 assert.ok(!invitation.includes('PRIVATE')&&!invitation.includes('#discussion'));assert.equal(link.props.rel,'noreferrer');
 await act(async()=>button('Share').props.onClick());assert.ok(json().includes('Link copied'));assert.ok(copies[0].startsWith('https://fixture.test/api/questions/'));
 pending=[];await act(async()=>button('Link copied').props.onClick());const old=pending.shift();await act(async()=>tree.update(action({qid:'new',context:{paper_id:'new-paper'}})));await act(async()=>old.resolve());assert.ok(!json().includes('Link copied'));
 await act(async()=>button('Share').props.onClick());await act(async()=>pending.shift().reject(Error('Clipboard denied')));assert.equal(tree.root.findByType('input').props.value,'https://fixture.test/api/questions/new/share?paper=new-paper&exam_scope=all');
 scope='mizoram-recruitment';pending=null;await act(async()=>tree.update(action({qid:'no-source'})));assert.equal(tree.root.findAllByType('input').length,0);await act(async()=>button('Share').props.onClick());assert.equal(copies.at(-1),'https://fixture.test/api/questions/no-source/share');
 await act(async()=>{tree.unmount();tree=create(React.createElement(Test,{id:'test1',title:'Synthetic test'}))});
 await act(async()=>button('Copy test link').props.onClick());assert.ok(json().includes('Test link copied.'));assert.equal(copies.at(-1),'https://fixture.test/api/tests/test1/share');
 link=tree.root.findAllByType('a')[0];assert.ok(new URL(link.props.href).searchParams.get('text').includes('Synthetic test\nTake this mock test on Finna:'));
 pending=[];await act(async()=>button('Copy test link').props.onClick());const stale=pending.shift();await act(async()=>tree.update(React.createElement(Test,{id:'test2',title:'Second test'})));await act(async()=>stale.reject(Error('old failure')));assert.ok(!json().includes('Copy the link below.'));
 shareFailure={name:'AbortError'};await act(async()=>button('More sharing options').props.onClick());assert.ok(!json().includes('Sharing could not open'));
 shareFailure=Error('Unavailable');await act(async()=>button('More sharing options').props.onClick());assert.ok(json().includes('Sharing could not open'));
 await act(async()=>button('Copy test link').props.onClick());await act(async()=>pending.shift().reject(Error('Denied')));assert.equal(tree.root.findByType('input').props.value,'https://fixture.test/api/tests/test2/share');
 tree.unmount();console.log('Real public sharing controls passed: source/scope binding, no private URL context, copy/fallback/WhatsApp/native actions, stale outcomes.');
})().catch(e=>{console.error(e);process.exitCode=1});
