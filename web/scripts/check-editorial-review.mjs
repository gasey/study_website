import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {createRequire} from 'node:module'
const require=createRequire(new URL('../package.json',import.meta.url)),ts=require('typescript'),mod={exports:{}}
new Function('module','exports',ts.transpileModule(readFileSync(new URL('../src/lib/editorialReview.ts',import.meta.url),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText)(mod,mod.exports)
const {adjacentQuestion,blankDraft,canSaveCheck,draftKey,parseDraft,matchesReview}=mod.exports
assert.equal(adjacentQuestion(0,-1,0,25,51),null)
assert.deepEqual(adjacentQuestion(24,1,0,25,51),{index:0,offset:25})
assert.deepEqual(adjacentQuestion(0,-1,25,25,51),{index:24,offset:0})
assert.deepEqual(adjacentQuestion(24,1,25,25,51),{index:0,offset:50})
assert.equal(adjacentQuestion(0,1,50,1,51),null)
assert.equal(adjacentQuestion(-1,1,0,25,51),null)
const draft=blankDraft();draft.note='Compared with PDF page 2.'
assert.equal(canSaveCheck(draft),false)
for(const key of Object.keys(draft.flags))draft.flags[key]=true
assert.equal(canSaveCheck(draft),true)
draft.note='          ';assert.equal(canSaveCheck(draft),false)
draft.note='Missing source evidence';draft.outcome='cannot_verify';draft.flags.source_checked=false
assert.equal(canSaveCheck(draft),true)
const raw=JSON.stringify({...draft,updatedAt:100000000})
assert.equal(parseDraft(raw,100000001).note,draft.note)
assert.equal(parseDraft(raw,200000000),null)
assert.equal(parseDraft('{broken'),null)
assert.equal(parseDraft(JSON.stringify({...draft,updatedAt:Date.now(),flags:{}})),null)
assert.notEqual(draftKey('a','b','c','v1'),draftKey('a','b','c','v2'))
assert.notEqual(draftKey('a','b','c','v1'),draftKey('other','b','c','v1'))
assert.notEqual(draftKey('a','b','c','v1'),draftKey('a','other','c','v1'))
assert.equal(matchesReview({previous_check:null},'unreviewed'),true)
assert.equal(matchesReview({previous_check:{outcome:'checked'}},'flagged'),false)
assert.equal(matchesReview({previous_check:{outcome:'cannot_verify'}},'flagged'),true)
assert.equal(matchesReview({previous_check:{outcome:'checked',stale:true}},'recheck'),true)
assert.equal(matchesReview({previous_check:{outcome:'cannot_verify',stale:true}},'flagged'),false)
console.log('Editorial regression checks passed: page boundaries, evidence gates, draft validation/expiry/isolation, and review filters.')

const filterMod={exports:{}}
new Function('module','exports',ts.transpileModule(readFileSync(new URL('../src/lib/editorialTagFilters.ts',import.meta.url),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText)(filterMod,filterMod.exports)
const {tagPaperScope,updateTagFilter}=filterMod.exports
const workParams=new URLSearchParams({assignment:'udc',paper:'my-current-paper',workspace:'attention',tag_offset:'40'})
assert.equal(tagPaperScope(workParams),'')
const scoped=updateTagFilter(workParams,'tag_paper','cleanup-paper')
assert.equal(tagPaperScope(scoped),'cleanup-paper')
assert.equal(scoped.get('paper'),'my-current-paper')
assert.equal(scoped.has('tag_offset'),false)
const cleared=updateTagFilter(scoped,'tag_paper','')
assert.equal(tagPaperScope(cleared),'')
assert.equal(cleared.get('paper'),'my-current-paper')
const legacy=new URLSearchParams({tab:'retag',paper:'legacy-paper'})
assert.equal(tagPaperScope(legacy),'legacy-paper')
assert.equal(updateTagFilter(legacy,'tag_paper','').has('paper'),false)
console.log('Tag cleanup scope checks passed: independent paper position, pagination reset and legacy links.')
