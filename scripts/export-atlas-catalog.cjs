// Reproducible identity manifest for the existing static chapters; no topic inference.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),ts=require(root+'/web/node_modules/typescript');
const files=new Map(),loaded=new Map();
function read(p){p=path.resolve(p);if(!p.endsWith('.ts'))p+='.ts';if(loaded.has(p))return loaded.get(p);const source=fs.readFileSync(p,'utf8');files.set(path.relative(root,p),crypto.createHash('sha256').update(source).digest('hex'));const m={exports:{}};loaded.set(p,m.exports);new Function('module','exports','require',ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText)(m,m.exports,id=>{if(!id.startsWith('.'))throw Error('Unexpected runtime import '+id);return read(path.resolve(path.dirname(p),id))});return m.exports}
const {chapters}=read(root+'/web/src/atlas/data/index.ts');
const catalog={version:1,attribution:'Existing site chapter identities; no new content or topic review.',source_sha256:Object.fromEntries([...files].sort()),chapters:chapters.map(c=>({id:c.id,title:c.title,subject:c.subject,layers:c.layers.map(l=>({id:l.id,name:l.name})),events:(c.events||[]).map(e=>({id:e.id,label:e.label})),source_sha256:crypto.createHash('sha256').update(JSON.stringify(c)).digest('hex')}))};
const out=JSON.stringify(catalog,null,2)+'\n',target=root+'/api/app/data/atlas-static-catalog.json';
if(process.argv.includes('--check')){if(fs.readFileSync(target,'utf8')!==out)throw Error('Atlas manifest differs from current chapter sources')}else fs.writeFileSync(target,out);
console.log('Static Atlas identity manifest:',chapters.length,'chapters; no bindings seeded.');
