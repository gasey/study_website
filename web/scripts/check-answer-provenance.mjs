import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {createRequire} from 'node:module'
const require=createRequire(new URL('../package.json',import.meta.url)),ts=require('typescript'),React=require('react'),{renderToStaticMarkup}=require('react-dom/server')
function load(file){const mod={exports:{}};const js=ts.transpileModule(readFileSync(new URL(file,import.meta.url),'utf8'),{compilerOptions:{jsx:ts.JsxEmit.ReactJSX,module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText
new Function('require','module','exports',js)(id=>id==='react-router-dom'?{Link:({to,children,...props})=>React.createElement('a',{href:to,...props},children)}:id==='../lib/answerStatus'?load('../src/lib/answerStatus.ts'):require(id),mod,mod.exports);return mod.exports}
const {answerProvenance,evidenceLink,default:Badge}=load('../src/components/AnswerProvenance.tsx')
const {answerStatus,explanationPresentation,answerFeedbackLabel,learnerExplanation}=load('../src/lib/answerStatus.ts')
assert.equal(answerProvenance('derived').status,'needs-review')
assert.equal(answerProvenance('derived',true).status,'verified')
assert.equal(answerProvenance('inferred',true).trusted,false)
assert.equal(answerProvenance('official').status,'official')
assert.equal(answerStatus('key',{disputed:true}).trusted,false)
assert.equal(answerStatus('official',{defect:'duplicate-options'}).status,'needs-review')
assert.equal(answerStatus('official',{questionType:'descriptive'}).status,'written')
assert.match(answerProvenance('key').scoring,/provisional.*final/)
assert.match(answerProvenance('derived',true).scoring,/not official-key/)
assert.equal(answerProvenance('none').label,'No answer yet')
assert.equal(explanationPresentation('','official').status,'missing')
assert.match(explanationPresentation('Working','official').detail,/not been separately verified/)
for(const source of ['official','key','derived','inferred','none']){
 const html=renderToStaticMarkup(React.createElement(Badge,{source,questionId:'cq/a & b'}))
 assert.match(html,/<details/);assert.match(html,/<summary[^>]*title=/)
 assert.doesNotMatch(html,/contribute\/new|Suggest a correction/)
 assert.doesNotMatch(html,/answerIndex|answer_text|model-generated|canonical|provenance|publication checks|MCQ answer index/)
}
assert.match(evidenceLink('cq/a & b'),/question=cq%2Fa/)
console.log('Public answer labels passed: plain language, accessible source help, honest review/official distinctions, provisional warning and no public correction prompts.')

assert.equal(answerFeedbackLabel({correct:true,answer_source:'key'}),'Correct')
assert.equal(answerFeedbackLabel({correct:false,answer_source:'official'}),'Incorrect')
assert.equal(answerFeedbackLabel({correct:true,answer_source:'derived'}),'Suggested answer')
assert.equal(answerFeedbackLabel({correct:false,answer_source:'derived'},{reviewed:true}),'Incorrect')
assert.equal(answerFeedbackLabel({correct:true,answer_source:'key'},{disputed:true}),'Answer under review')

const certificate='Original printed source and ordered choices independently reviewed. Verified worked solution, unofficial; no matching examiner key is asserted.'
assert.equal(learnerExplanation('The answer follows from the diagram. '+certificate),'The answer follows from the diagram.')
assert.equal(learnerExplanation('The official key differs. '+certificate),'The official key differs.')
assert.equal(learnerExplanation('What is AI? The reasoning was independently reviewed.'),'What is AI? The reasoning was independently reviewed.')
assert.equal(learnerExplanation(certificate+' This key remains disputed.'),certificate+' This key remains disputed.')
assert.equal(learnerExplanation(null),'')
