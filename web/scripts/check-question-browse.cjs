const assert=require('node:assert/strict'),fs=require('node:fs');
const req=require('node:module').createRequire(process.cwd()+'/web/package.json'),ts=req('typescript');
function load(file){const m={exports:{}};new Function('module','exports','require',ts.transpileModule(fs.readFileSync('web/src/lib/'+file+'.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText)(m,m.exports,id=>id.startsWith('./')?load(id.slice(2)):req(id));return m.exports;}
const b=load('questionBrowse'),s=load('studySetLinks'),j=load('examJourney'),cache=load('requestCache');
assert.equal(b.readQuestionOrder(null),'mixed');assert.equal(b.readQuestionOrder('repeated'),'repeated');
assert.equal(b.readStudyStatus('ever_wrong'),'ever_wrong');assert.equal(b.readStudyStatus('bad'),'all');
assert.equal(b.nextBrowseOffset(25,25,'unseen',[{correct:true},{correct:false},undefined]),48);
assert.equal(b.nextBrowseOffset(0,1,'wrong',[{correct:true}]),0);
assert.equal(b.nextBrowseOffset(0,1,'wrong',[{correct:false}]),1);
assert.equal(b.nextBrowseOffset(0,1,'ever_wrong',[{correct:true}]),1);
assert.equal(b.nextBrowseOffset(0,1,'unseen',[undefined]),1,'Reading does not remove an unattempted item');
const filters=s.studySetFilters(new URLSearchParams('order=mixed&seed=stable&status=ever_wrong&offset=10'));
assert.equal(filters.seed,'stable');assert.equal(filters.study_status,'ever_wrong');
const next=new URL(s.nextStudySetLink(filters,10),'https://study.hawayu.in');
assert.equal(next.searchParams.get('seed'),'stable');assert.equal(next.searchParams.get('offset'),'20');
const resume=new URL(j.practiceJourneyLink('ldc',{checkpoint:{state:{order:'mixed',seed:'stable',offset:23,status:'ever_wrong'}}}),'https://study.hawayu.in');
assert.equal(resume.searchParams.get('seed'),'stable');assert.equal(resume.searchParams.get('offset'),'23');
assert.notEqual(cache.questionQueryString({seed:'first',order:'mixed'}),cache.questionQueryString({seed:'second',order:'mixed'}));
console.log('Question browsing passed: validated filters, stable seed/restore, distinct caches, and no skipped shrinking-queue questions.');
