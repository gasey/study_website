import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {createRequire} from 'node:module'
const require=createRequire(new URL('../package.json',import.meta.url)),ts=require('typescript'),mod={exports:{}}
new Function('module','exports',ts.transpileModule(readFileSync(new URL('../src/lib/paperDuplicates.ts',import.meta.url),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText)(mod,mod.exports)
const {paperDuplicateGroups,paperPresentationItems}=mod.exports
const paper='Old_Questions/Departmental_2015-2018/3.Departmental Exam for Inspector under Excise 2016 Paper III.pdf'
const a={appearance_id:'desc-3d4c5f6b168c76b1d4c7',type:'descriptive',qnum:'1',page:1,series:null,question:'Define: (a) Cannabis',options:[],direction:'Attempt all questions.'}
const b={...a,appearance_id:'desc-753c3e58a04fcb5ae9c2',question:'Define:- (a) Cannabis'}
const rows=[a,b],before=JSON.stringify(rows),group=paperDuplicateGroups(paper,rows)
assert.equal(group.hidden,1);assert.equal(group.printedCount,1)
assert.deepEqual(paperPresentationItems(rows,group,false,'').map(q=>q.appearance_id),[a.appearance_id])
assert.equal(paperPresentationItems(rows,group,true,'').length,2)
assert.equal(paperPresentationItems(rows,group,false,b.appearance_id).length,2)
assert.equal(paperDuplicateGroups('another-paper',rows).hidden,0)
assert.equal(paperDuplicateGroups(paper,[b]).hidden,0)
for(const patch of [{question:'Different words'},{page:2},{qnum:'1(a)'},{direction:'Choose one.'},{passage:'Different passage'},{held:true},{figure_image_url:'/changed.png'},{taxonomy_topic_id:'changed'},{type:'mcq'},{options:['a','b']},{question_markup:'<u>Different emphasis</u>'}])assert.equal(paperDuplicateGroups(paper,[a,{...b,...patch}]).hidden,0)
assert.equal(JSON.stringify(rows),before)
if(process.argv[2]){
 const live=JSON.parse(readFileSync(process.argv[2],'utf8')).items
 const actual=paperDuplicateGroups(paper,live)
 assert.equal(actual.hidden,4);assert.equal(actual.printedCount,23)
 assert.equal(paperPresentationItems(live,actual,false,'').length,23)
 assert.equal(paperPresentationItems(live,actual,true,'').length,27)
 console.log('Live source fixture: 27 stored transcriptions, 23 printed questions, four audited groups.')
}
console.log('Duplicate presentation passed: audited identities, exact source/context/hold checks, direct links, show-all and immutable input.')
