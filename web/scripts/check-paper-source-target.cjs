const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
const cache=new Map();
function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};new Function('module','exports','require',ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText)(mod,mod.exports,id=>id.startsWith('.')?load(path.resolve(path.dirname(file),id)+'.ts'):wr(id));cache.set(file,mod.exports);return mod.exports}
const Component=load(root+'/web/src/components/PaperSourceTarget.tsx').default,{linkRegisteredPaper}=load(root+'/web/src/lib/paperWorkbench.ts');
const source={paper_id:'original-common-paper',exam_name:'Registered common exam',year:2016,paper_subject:null,source_version:'a'.repeat(64),question_count:0,unambiguous:true};
const payload={title:'Prepared paper',exam_name:'Draft name',year:2026,paper_subject:'Draft subject',questions:[{id:'written-one',question:'Write a response',answer_index:null,answer_source:'none'}]};
const before=JSON.stringify(payload);let tree,changed;
async function render(p=payload,sources=[source],editable=true,published=false){await act(async()=>{tree?.unmount();tree=create(React.createElement(Component,{payload:p,sources,editable,published,onChange:value=>changed=value}))})}
const button=label=>tree.root.findAllByType('button').find(b=>b.children.join('').includes(label));
(async()=>{
 await render(payload,[]);assert.equal(tree.toJSON(),null);
 await render();assert.ok(button('Use this empty original'));await act(async()=>button('Use this empty original').props.onClick());
 assert.equal(changed.target_paper_id,source.paper_id);assert.equal(changed.target_source_version,source.source_version);assert.equal(changed.exam_name,source.exam_name);assert.equal(changed.year,2016);assert.equal(changed.paper_subject,'');assert.equal(changed.questions,payload.questions);assert.equal(JSON.stringify(payload),before);
 const linked=changed;await render(linked);assert.ok(JSON.stringify(tree.toJSON()).includes('Linked to this original'));assert.equal(button('Use this empty original'),undefined);
 await act(async()=>button('Remove original link').props.onClick());assert.equal(changed.target_paper_id,null);assert.equal(changed.target_source_version,null);assert.equal(changed.questions,payload.questions);
 await render(linked,[{...source,source_version:'b'.repeat(64)}]);assert.equal(tree.root.findAllByProps({role:'alert'}).length,1);assert.ok(button('Refresh original link'));
 for(const s of [{...source,question_count:1},{...source,unambiguous:false}]){await render(payload,[s]);assert.equal(button('Use this empty original').props.disabled,true);assert.throws(()=>linkRegisteredPaper(payload,s));}
 await render(linked,[source],false);assert.equal(tree.root.findAllByType('button').length,0);
 await render(linked,[{...source,question_count:10}],false,true);assert.equal(tree.root.findAllByProps({role:'alert'}).length,0);assert.ok(JSON.stringify(tree.toJSON()).includes('Published into this original'));
 await render(linked,[],false);assert.equal(tree.root.findAllByProps({role:'alert'}).length,1);
 await act(async()=>tree.unmount());console.log('Existing source UI passed: explicit link, metadata adoption, preserved question/answer objects, stale and ambiguous/populated guards, read-only review and unlink.');
})().catch(e=>{console.error(e);process.exit(1)});
