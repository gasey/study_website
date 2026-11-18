const assert=require('node:assert/strict'),fs=require('node:fs'),wr=require('node:module').createRequire(process.cwd()+'/web/package.json'),ts=wr('typescript'),React=wr('react');
const r=require.resolve('react',{paths:[process.argv[2]]});require.cache[r]={id:r,filename:r,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]}));
function load(file,imports){const m={exports:{}};new Function('module','exports','require',ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText)(m,m.exports,id=>imports[id]||wr(id));return m.exports}
const nav=load('web/src/lib/adminNavigation.ts',{}),Nav=load('web/src/components/AdminNavigation.tsx',{'react-router-dom':{Link:({children,to,...p})=>React.createElement('a',{...p,href:to},children)},'./QuickFind':{default:()=>null},'../lib/adminNavigation':nav}).default;
assert.equal(nav.adminTabHref('users'),'/admin/users');assert.equal(nav.canOpenAdminTab('users',[{role:'owner',subject_id:'english'}]),false);
let tree,last;const owner=[{role:'owner',subject_id:null}];act(()=>tree=create(React.createElement(Nav,{tab:'users',grants:owner,onNavigate:x=>last=x})));
assert.ok(tree.root.findAllByType('a').some(a=>a.props.href==='/admin/users'&&a.props['aria-current']==='page'));
act(()=>tree.root.findByType('select').props.onChange({target:{value:'ops'}}));assert.equal(last,'ops');
act(()=>tree.update(React.createElement(Nav,{tab:'questions',grants:[{role:'reviewer',subject_id:'english'}],onNavigate:x=>last=x})));
assert.ok(!tree.root.findAllByType('a').some(a=>a.props.href==='/admin/users'));assert.ok(!JSON.stringify(tree.toJSON()).includes('Account viewer'));
assert.equal(nav.adminTabHref('questions'),'/admin/bank?tab=questions&answer_status=needs-review');act(()=>tree.unmount());
console.log('Account viewer desktop/phone navigation passed: global owner only, canonical route, active link, selection and preserved question filter.');
