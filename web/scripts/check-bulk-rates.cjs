// Actual new screens and saved-player mode with deterministic API adapters.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]})),router=wr('react-router-dom');
const events=new Map();let epoch=0,calls=[],prices=[],claims=[];
global.window={location:{origin:'https://fixture.test',search:''},dispatchEvent(e){for(const f of events.get(e.type)||[])f(e)},addEventListener(n,f){if(!events.has(n))events.set(n,new Set());events.get(n).add(f)},removeEventListener(n,f){events.get(n)?.delete(f)}};
global.crypto||=require('node:crypto').webcrypto;
const deferred=queue=>(...args)=>new Promise((resolve,reject)=>queue.push({args,resolve,reject}));
const api={getGroupPrice:deferred(prices),claimGroupPrice:deferred(claims)},review={reviewRequest:deferred(calls)};
const stub=()=>null,cache=new Map();function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};cache.set(file,mod.exports);
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;
 new Function('module','exports','require',code)(mod,mod.exports,id=>{
  if(id.endsWith('/api'))return api;
  if(id.endsWith('/review'))return review;
  if(id.endsWith('/accountContext'))return {accountGeneration:()=>epoch};
  if(id.endsWith('/StudyQuestionCard'))return {default:p=>React.createElement('div',{'data-collection':p.collectionId},p.q.question)};
  if(id.endsWith('/CuratedWordQuestion')||id.endsWith('/QuestionStudyControls'))return {default:stub};
  if(id.endsWith('/AnswerLayout'))return {AnswerLayoutControl:stub};
  if(id.endsWith('/pagination'))return {scrollToResults:()=>{}};
  if(id.endsWith('/answerStatus'))return {answerFeedbackLabel:()=> 'Checked'};
  if(id.endsWith('/questionBrowse'))return {newQuestionSeed:()=> 'seed'};
  if(id.endsWith('/studySetLinks'))return {studySetFilters:()=>({}),studySetLink:id=>'/exams/udc?session='+id,nextStudySetLink:()=>'/exams/udc'};
  if(id==='react-router-dom')return router;
  if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(base+(fs.existsSync(base+'.tsx')?'.tsx':'.ts'))}return wr(id);
 });return mod.exports}
const Receipts=load(root+'/web/src/components/BulkClaimReceipts.tsx').default;
const Admin=load(root+'/web/src/components/BulkRatesAdmin.tsx').default,Claim=load(root+'/web/src/components/GroupRateClaim.tsx').default;
let tree;const text=n=>typeof n==='string'?n:(n?.children||[]).map(text).join(''),json=()=>JSON.stringify(tree.toJSON()),button=label=>tree.root.findAllByType('button').find(n=>text(n)===label);
const field=label=>tree.root.findAllByType('label').find(n=>text(n).startsWith(label)).findAll(n=>['input','textarea'].includes(n.type))[0];
const data={enabled:true,emails:[],codes:[],emails_has_more:false,codes_has_more:false};
async function resolve(queue,value){assert.ok(queue.length);await act(async()=>queue.shift().resolve(value))}
async function change(label,value){await act(async()=>field(label).props.onChange({target:{value}}))}
async function emit(){epoch++;await act(async()=>window.dispatchEvent(new Event('ism-auth-change')))}
(async()=>{
 await act(async()=>{tree=create(React.createElement(Admin))});await resolve(calls,data);
 await change('Find saved email','older@example.test');await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}));assert.equal(calls[0].args[0],'/billing/bulk/admin?q=older%40example.test');await resolve(calls,data);
 await change('Batch note','Synthetic group');await change('Email addresses','member@example.test');
 await act(async()=>button('Preview email batch').props.onClick());assert.equal(calls[0].args[0],'/billing/bulk/admin/preview');await resolve(calls,{preview_hash:'a'.repeat(64),total:1,already_listed:0,verified_accounts:1,pending_verification_or_signup:0});
 await act(async()=>button('Add previewed email list at ₹50/month').props.onClick());const key=calls[0].args[1].request_key;await act(async()=>calls.shift().reject(Error('Uncertain result')));
 await act(async()=>button('Add previewed email list at ₹50/month').props.onClick());assert.equal(calls[0].args[1].request_key,key);await emit();await resolve(calls,{added:1,applied:1});assert.ok(!json().includes('entries added'));await resolve(calls,data);
 await change('Group note','New group');await act(async()=>button('Create ₹50/month group code').props.onClick());assert.equal(calls[0].args[1].max_uses,100);assert.equal(calls[0].args[1].days,30);const codeKey=calls[0].args[1].request_key;await act(async()=>calls.shift().reject(Error('Temporary failure')));await act(async()=>button('Create ₹50/month group code').props.onClick());assert.equal(calls[0].args[1].request_key,codeKey);
 const stale=button('Create ₹50/month group code').props.onClick;await emit();await act(async()=>stale());assert.equal(calls.length,2);await resolve(calls,{code:'PRIVATE_OLD_CODE'});assert.ok(!json().includes('PRIVATE_OLD_CODE'));await resolve(calls,{...data,enabled:false});assert.ok(json().includes('New assignments are paused'));
 await act(async()=>{tree.unmount();tree=create(React.createElement(Receipts,{code:'A'.repeat(24)}))});
 await act(async()=>button('View claim receipts').props.onClick());assert.ok(calls[0].args[0].includes('/claims?'));await resolve(calls,{items:[{user_id:'old',email:'old@example.test',handle:'old',amount_paise:5000,created_at:'2026-11-18',closed:false}],next_cursor:null});assert.ok(json().includes('old@example.test'));
 const oldReceipt=button('Refresh claim receipts').props.onClick;await emit();await act(async()=>oldReceipt());assert.equal(calls.length,0);assert.ok(!json().includes('old@example.test'));
 await act(async()=>{tree.unmount();tree=create(React.createElement(router.MemoryRouter,{initialEntries:['/billing?group_code='+('A'.repeat(24))]},React.createElement(Claim)))});assert.equal(claims.length,0,'A link never auto-claims');await resolve(prices,{amount_paise:10000,enabled:true});
 await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}));assert.deepEqual(claims[0].args,['A'.repeat(24),10000]);await emit();await resolve(claims,{saved:true,already_redeemed:false,amount_paise:5000});assert.ok(!json().includes('Your next new subscription is ₹50'));await resolve(prices,{amount_paise:10000,enabled:true});
 await change('Group code','B'.repeat(24));await act(async()=>tree.root.findByType('form').props.onSubmit({preventDefault(){}}));await resolve(claims,{saved:false,already_redeemed:true,amount_paise:10000});assert.ok(json().includes('Current next-subscription price: ₹100/month.'));
 await act(async()=>tree.unmount());console.log('Bulk real components passed: preview/explicit application, stable retry keys, bounded defaults, paused states, no automatic claim, stale account outcomes and actual replay price.');
})().catch(e=>{console.error(e);process.exitCode=1});
