// Read-only editorial list: reveal/try must never save an inspection or learner attempt.
const assert=require('node:assert/strict'),fs=require('node:fs');
const root=process.cwd(),webRequire=require('node:module').createRequire(root+'/web/package.json'),React=webRequire('react'),ts=webRequire('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
const calls=[];let active=0,maxActive=0,fail='',opened=null;
const items=Array.from({length:7},(_,i)=>({id:'appearance'+i,questionId:'canonical'+i,number:String(i+1),text:'Source question '+i,status:'Not checked'}));
const snapshots=Object.fromEntries(items.map((q,i)=>[q.id,{record:{id:q.id,question:q.text,type:i===6?'descriptive':'mcq',options:i===6?[]:['Alpha','Beta'],answerIndex:i>=5?null:1,answerSource:i>=5?'none':'key',answerKeyRef:'Provisional official key',explanation:i===5?'Source/key conflict: scoring withheld.':'',page:2},paper:{title:'Original paper',source_pdf_url:'/papers/source/exact.pdf'},tag_label:'English / Grammar'}]));
const mod={exports:{}};new Function('module','exports','require',ts.transpileModule(fs.readFileSync(root+'/web/src/components/EditorialReviewList.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText)(mod,mod.exports,id=>{
 if(id==='../lib/review')return {reviewRequest:async(...args)=>{calls.push(args);assert.equal(args.length,1);active++;maxActive=Math.max(maxActive,active);await new Promise(r=>setTimeout(r,5));active--;const appearance=new URL('https://test'+args[0]).searchParams.get('appearance_id');if(fail===appearance)throw Error('Source access unavailable');return snapshots[appearance]}};
 if(id==='./SourceQuestionText')return {SourceQuestionContext:()=>null,SourceQuestionText:({text})=>React.createElement('span',null,text)};
 return webRequire(id);
});
const Component=mod.exports.default;let tree;
const buttons=()=>tree.root.findAllByType('button'),button=t=>buttons().find(b=>b.children.join('')===t);
const settle=()=>act(async()=>new Promise(r=>setTimeout(r,65)));
(async()=>{
 await act(async()=>{tree=create(React.createElement(Component,{items,busy:false,onReview:q=>opened=q}))});
 assert.equal(calls.length,0);assert.equal(tree.root.findAllByType('li').length,7);
 await act(async()=>button('Options / self-check').props.onClick());await settle();
 assert.equal(calls.length,1);assert.ok(calls[0][0].includes('/canonical0?appearance_id=appearance0'));
 const option=buttons().find(b=>b.props['aria-pressed']===false&&b.findAllByType('span').some(s=>s.children.join('')==='B.'));assert.ok(option);
 await act(async()=>option.props.onClick());assert.ok(JSON.stringify(tree.toJSON()).includes('Your pick matches'));assert.equal(calls.length,1);
 await act(async()=>button('Show answers on this page').props.onClick());await settle();
 assert.equal(calls.length,7);assert.ok(maxActive<=3);assert.equal(tree.root.findAll(n=>String(n.props['aria-label']||'').startsWith('Recorded answer for question')).length,7);
 assert.ok(JSON.stringify(tree.toJSON()).includes('No answer recorded'));assert.ok(JSON.stringify(tree.toJSON()).includes('Written response'));assert.ok(JSON.stringify(tree.toJSON()).includes('Provisional official key'));
 await act(async()=>button('Hide all answers').props.onClick());assert.equal(tree.root.findAll(n=>String(n.props['aria-label']||'').startsWith('Recorded answer for question')).length,0);
 await act(async()=>button('Review / edit source →').props.onClick());assert.equal(opened.id,'appearance0');
 await act(async()=>tree.unmount());fail='appearance1';
 await act(async()=>{tree=create(React.createElement(Component,{items:items.slice(1,2),busy:false,onReview(){}}))});
 await act(async()=>button('Show answers on this page').props.onClick());await settle();assert.ok(tree.root.findByProps({role:'alert'}));
 fail='';await act(async()=>button('Retry source').props.onClick());await settle();assert.equal(tree.root.findAllByProps({role:'alert'}).length,0);
 assert.ok(calls.every(c=>c.length===1&&c[0].startsWith('/review/questions/')));await act(async()=>tree.unmount());
 console.log('Editorial list passed: lazy exact-source reads, bounded reveal-all, inline self-check, no mutations, withheld/written answers, hide/reset and retry.');
})().catch(e=>{console.error(e);process.exitCode=1});
