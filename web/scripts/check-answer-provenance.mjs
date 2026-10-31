import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {createRequire} from 'node:module'
const require=createRequire(new URL('../package.json',import.meta.url)),ts=require('typescript'),React=require('react'),{renderToStaticMarkup}=require('react-dom/server')
const mod={exports:{}};const js=ts.transpileModule(readFileSync(new URL('../src/components/AnswerProvenance.tsx',import.meta.url),'utf8'),{compilerOptions:{jsx:ts.JsxEmit.ReactJSX,module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText
new Function('require','module','exports',js)(id=>id==='react-router-dom'?{Link:({to,children,...props})=>React.createElement('a',{href:to,...props},children)}:require(id),mod,mod.exports)
const {answerProvenance,evidenceLink,default:Badge}=mod.exports
assert.equal(answerProvenance('derived').label,'Derived answer')
assert.equal(answerProvenance('derived',true).label,'Reviewed solution')
assert.equal(answerProvenance('derived',true).verified,false)
assert.equal(answerProvenance('official').verified,true)
assert.match(answerProvenance('inferred').scoring,/Excluded/)
assert.match(answerProvenance('none').description,/does not establish/)
const html=renderToStaticMarkup(React.createElement(Badge,{source:'derived',questionId:'cq/a & b'}))
assert.match(html,/<details/);assert.match(html,/<summary[^>]*title=/);assert.match(html,/10 contribution points/)
assert.match(html,/intent=verify/);assert.match(evidenceLink('cq/a & b'),/question=cq%2Fa/)
assert.doesNotMatch(html,/answerIndex|answer_text/)
console.log('Provenance checks passed: accessible help, provenance separation, safe evidence links and publication-only contribution credit.')
