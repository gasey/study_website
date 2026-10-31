import {cp,mkdir,readFile} from 'node:fs/promises'
const root=new URL('../',import.meta.url)
const packageRoot=new URL('node_modules/pdfjs-dist/',root)
const {version}=JSON.parse(await readFile(new URL('package.json',packageRoot),'utf8'))
const target=new URL('public/vendor/pdfjs/'+version+'/',root)
await mkdir(target,{recursive:true})
for(const folder of ['cmaps','standard_fonts','wasm'])await cp(new URL(folder,packageRoot),new URL(folder,target),{recursive:true})
await cp(new URL('LICENSE',packageRoot),new URL('LICENSE',target))
