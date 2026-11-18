const assert=require('node:assert/strict'),fs=require('node:fs');
const req=require('node:module').createRequire(process.cwd()+'/web/package.json'),ts=req('typescript');
let epoch=0,identityReads=0;const calls=[];
global.window={addEventListener(){},dispatchEvent(){},setTimeout,clearTimeout};
global.fetch=async(path,init)=>{calls.push({path,init});return {ok:true,json:async()=>path.includes('/questions?')?{items:[],total:0,limit:20,offset:0}:[]}};
function load(name){const module={exports:{}};new Function('module','exports','require',ts.transpileModule(fs.readFileSync('web/src/lib/'+name+'.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText)(module,module.exports,id=>{
 if(id==='./accountContext')return {accountContext:async()=>{identityReads++;return {authenticated:true,csrf:'test-csrf'}},accountGeneration:()=>epoch,checkSessionRejected:async()=>{}};
 if(id==='./examScope')return {scopedApiPath:path=>path};
 if(id==='./device')return {deviceId:()=> 'synthetic-device'};
 return id.startsWith('./')?load(id.slice(2)):req(id);
});return module.exports;}
const policy=load('publicBrowse');
for(const path of ['/questions/taxonomy?exam_scope=all','/questions/papers','/questions/cq_test','/collections','/collections/udc/header','/collections/udc/paper-questions?paper_id=source'])assert(policy.publicBrowseRead(path),path);
for(const path of ['/questions','/questions?study_status=wrong','/questions/id/answer-comparison','/questions/id/practice-state','/me/progress','/collections/udc/progress','/admin/bank','/collections/udc?learning_entry=x'])assert(!policy.publicBrowseRead(path),path);
for(const headers of [{Authorization:'Bearer token'},{Cookie:'guest=proof'},{'X-Device-Id':'device'}])assert(!policy.publicBrowseRead('/collections',{headers}));
assert(!policy.publicBrowseRead('/collections',{method:'POST'}));
(async()=>{
 const api=load('api');
 await api.listTaxonomy();
 assert.equal(identityReads,0,'Public catalog does not wait for account/session lookup');
 assert.equal(calls.at(-1).init.credentials,'omit');
 assert.equal(calls.at(-1).init.headers,undefined);
 await api.listQuestions();
 assert.equal(identityReads,1,'Question list keeps proven guest/account booklet history');
 assert.equal(calls.at(-1).init.credentials,'include');
 assert.equal(calls.at(-1).init.headers['x-device-id'],'synthetic-device');
 const original=global.fetch;global.fetch=async(...args)=>{const result=await original(...args);epoch++;return result};
 await assert.rejects(api.listTaxonomy('practice'),/account changed/,'An account switch still rejects an in-flight public request');
 console.log('Public browse transport passed: credential-free catalogs, private question lists, and account-switch guards.');
})().catch(error=>{console.error(error);process.exitCode=1});
