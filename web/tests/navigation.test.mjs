import {test} from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import ts from 'typescript'
async function load(name){const source=await fs.readFile(new URL('../src/lib/'+name+'.ts',import.meta.url),'utf8');const output=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText;return import('data:text/javascript;base64,'+Buffer.from(output).toString('base64'))}
const {ReadRequestCache,catalogTtl}=await load('requestCache')
test('public catalog whitelist excludes private records, content and answers',()=>{
  for(const path of ['/collections','/collections?exam_scope=all','/questions/taxonomy?pool=practice','/library/shelves/history'])assert.equal(catalogTtl(path),30000)
  for(const path of ['/collections/ldc','/questions','/questions/id','/questions/id/answer','/me/progress','/auth/session','/inbox','/mocks','/library/shelves/history/questions'])assert.equal(catalogTtl(path),0)
})
test('cache coalesces pending reads, expires, rejects and respects scope',async()=>{
  let now=0,calls=0;const cache=new ReadRequestCache(2,()=>now),load=async()=>++calls
  assert.deepEqual(await Promise.all([cache.read('all',load,10),cache.read('all',load,10)]),[1,1])
  assert.equal(await cache.read('mizoram',load,10),2)
  assert.equal(await cache.read('all',load,10),1)
  now=11;assert.equal(await cache.read('all',load,10),3)
  await assert.rejects(cache.read('failure',async()=>{throw Error('temporary')},10))
  assert.equal(await cache.read('failure',load,10),4)
  await cache.read('third',load,10);assert.equal(await cache.read('all',load,10),6)
})
test('clearing an in-flight read cannot repopulate stale cache; zero TTL coalesces only pending',async()=>{
  const cache=new ReadRequestCache();let resolve,calls=0
  const first=cache.read('session',()=>new Promise(r=>{resolve=r}));await Promise.resolve();cache.clear()
  assert.equal(await cache.read('session',async()=>++calls),1);resolve('old');assert.equal(await first,'old')
  assert.equal(await cache.read('session',async()=>++calls),2)
  cache.clear();assert.equal(await cache.read('session',async()=>++calls,100),3)
})
const {routeModule,warmRoute}=await load('routeModules')
test('route intent resolves exams, mock, source paper and question destinations',()=>{
  for(const [path,name] of [['/','Home'],['/exams','Exams'],['/exams/ldc','ExamPage'],['/exams/ldc/paper','PaperViewer'],['/exams/ldc/mock','MockRunner'],['/results/run','Results'],['/bank/id','QuestionDetail'],['/library/subjects/english','LibrarySubject']])assert.equal(routeModule(path),name)
  assert.equal(routeModule('/unknown'),null)
})
test('prefetch skips data-saving connections and external links',()=>{
  Object.defineProperty(globalThis,'navigator',{value:{connection:{saveData:true}},configurable:true})
  globalThis.window={location:{href:'https://study.hawayu.in/bank',origin:'https://study.hawayu.in'}}
  assert.doesNotThrow(()=>warmRoute('/exams'))
  navigator.connection.saveData=false;navigator.connection.effectiveType='2g';assert.doesNotThrow(()=>warmRoute('/bank'))
  navigator.connection.effectiveType='4g';assert.doesNotThrow(()=>warmRoute('https://example.com/exams'))
})
const {answerStatus}=await load('answerStatus')
test('answer labels collapse stored provenance without promoting suggestions',()=>{
  assert.equal(answerStatus('official').label,'Official key');assert.equal(answerStatus('key').label,'Official key')
  assert.equal(answerStatus('derived').label,'Needs review');assert.equal(answerStatus('inferred').label,'Needs review')
  assert.equal(answerStatus('none').label,'Unsolved')
})
test('verified solution requires current reviewed-derived evidence',()=>{
  assert.equal(answerStatus('derived',{reviewed:true}).label,'Verified solution · unofficial')
  assert.equal(answerStatus('inferred',{reviewed:true}).label,'Needs review')
  assert.match(answerStatus('derived',{reviewed:true}).scoring,/not official-key/)
})
test('disputes and blocking source defects override trusted badges',()=>{
  assert.equal(answerStatus('official',{disputed:true}).label,'Needs review')
  assert.equal(answerStatus('derived',{reviewed:true,defect:'duplicate-options'}).label,'Needs review')
  assert.equal(answerStatus('key',{defect:'unresolved-source'}).trusted,false)
})
test('descriptive questions do not masquerade as unsolved MCQs',()=>{
  assert.equal(answerStatus('none',{questionType:'descriptive'}).label,'Written question')
})
test('source history survives simplified badges; final-key status is never invented',()=>{
  assert.notEqual(answerStatus('official').sourceDetail,answerStatus('key').sourceDetail)
  assert.match(answerStatus('official').scoring,/does not establish that the key is final/)
  assert.match(answerStatus('none').description,/does not mean/)
})
test('server holds override official labels without granting verification',()=>{
 assert.equal(answerStatus('official',{statusOverride:'needs-review'}).label,'Needs review')
 assert.equal(answerStatus('official',{statusOverride:'unsolved'}).label,'Unsolved')
 assert.equal(answerStatus('derived',{statusOverride:'verified'}).label,'Needs review')
})

const {questionCurrentness}=await load('questionCurrentness')
test('LDC news wording gets a dated source hint without changing historical answers',()=>{
 const hint=questionCurrentness("Recently, the QUAD nations launched the 'At Sea Observer Mission' to boost maritime cooperation. Which of the following are members of QUAD?")
 assert.match(hint.reference.url,/pib\.gov\.in/)
 assert.match(hint.reference.label,/30 June 2025/)
 assert.ok(questionCurrentness('Recently which climate activist of India was detained under an Act?'))
 assert.equal(questionCurrentness('In Excel, add A1 from Sheet2 to B1 of the current sheet.'),null)
 assert.equal(questionCurrentness('The jelly like substance present inside the cell is known as:'),null)
 assert.equal(questionCurrentness('The current arrow points right. Which direction is next?'),null)
 assert.equal(questionCurrentness('Choose the present perfect tense.'),null)
})

const {answerStatusAppearance}=await load('answerStatus')
test('official and solved provenance use distinct colour, symbol and explicit wording',()=>{
 const official=answerStatusAppearance('official'),solved=answerStatusAppearance('verified'),review=answerStatusAppearance('needs-review')
 assert.notEqual(official.badge,solved.badge);assert.notEqual(official.symbol,solved.symbol);assert.notEqual(review.badge,solved.badge)
 assert.match(solved.shortLabel,/unofficial/);assert.match(official.meaning,/authority/)
 assert.equal(answerStatus('derived').status,'needs-review');assert.equal(answerStatus('official',{disputed:true}).status,'needs-review')
})

const {questionTopicLabel}=await load('questionLabels')
test('learning topic is independent of official GK or GS paper wording',()=>{
  assert.equal(questionTopicLabel({taxonomy_subject_id:'general-studies',taxonomy_subject:'General Studies',taxonomy_topic:'Current Affairs'}),'Current Affairs')
  for(const id of ['general-studies','general-knowledge']) assert.equal(questionTopicLabel({taxonomy_subject_id:id}),'GK/GS')
  assert.equal(questionTopicLabel({taxonomy_subject:'English'}),'English')
  for(const exam of ['udc','ldc','assistant'])for(const id of ['general-studies','general-knowledge'])assert.equal(questionTopicLabel({taxonomy_subject_id:id},exam),'General Knowledge')
  assert.equal(questionTopicLabel({taxonomy_subject_id:'general-studies',taxonomy_topic:'Current Affairs'},'udc'),'Current Affairs')
})

const learningTaxonomy=await load('learningTaxonomy')
test('GK/GS picker combines equivalent topics and preserves valid registry paths',()=>{
  const nodes=[{id:'general-knowledge',label:'General Knowledge',level:'subject',parent_id:null},{id:'general-studies',label:'General Studies',level:'subject',parent_id:null},{id:'gk-current',label:'Current Affairs',level:'topic',parent_id:'general-knowledge'},{id:'gs-current',label:'Current Affairs',level:'topic',parent_id:'general-studies'}]
  const choices=learningTaxonomy.topicChoices(nodes,'gk-gs')
  assert.equal(choices.length,1)
  assert.equal(learningTaxonomy.resolveTopic(choices[0][1],'general-studies').topic_id,'gs-current')
  assert.equal(learningTaxonomy.resolveTopic(choices[0][1],'english').topic_id,'gk-current')
  assert.equal(learningTaxonomy.learningPathLabel({subject_id:'general-studies',topic_id:'gs-current'},nodes),'GK/GS → Current Affairs')
})

const {questionQueryString}=await load('requestCache')
test('visible exam requests and prefetched defaults share one key',()=>{
 const first={collection_id:'udc',pool:'all',study_status:'all',offset:0,limit:25}
 assert.equal(questionQueryString(first),questionQueryString({limit:25,collection_id:'udc'}))
 assert.notEqual(questionQueryString({...first,study_status:'wrong'}),questionQueryString(first))
 assert.notEqual(questionQueryString({...first,pool:'practice'}),questionQueryString(first))
 assert.notEqual(questionQueryString({...first,offset:25}),questionQueryString(first))
 assert.equal(new URLSearchParams(questionQueryString({source:['key','official']})).getAll('source').length,2)
})
