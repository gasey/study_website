// Read generated TypeScript literals without evaluating or importing module code.
import fs from 'node:fs'
import ts from '../web/node_modules/typescript/lib/typescript.js'
const file=process.argv[2],text=fs.readFileSync(file,'utf8')
const ast=ts.createSourceFile(file,text,ts.ScriptTarget.Latest,true)
function literal(n){
 if(ts.isStringLiteral(n)||ts.isNoSubstitutionTemplateLiteral(n))return n.text
 if(ts.isNumericLiteral(n))return Number(n.text)
 if(n.kind===ts.SyntaxKind.TrueKeyword)return true
 if(n.kind===ts.SyntaxKind.FalseKeyword)return false
 if(n.kind===ts.SyntaxKind.NullKeyword)return null
 if(ts.isPrefixUnaryExpression(n)&&n.operator===ts.SyntaxKind.MinusToken&&ts.isNumericLiteral(n.operand))return -Number(n.operand.text)
 if(ts.isArrayLiteralExpression(n))return n.elements.map(literal)
 if(ts.isObjectLiteralExpression(n))return Object.fromEntries(n.properties.map(p=>{if(!ts.isPropertyAssignment(p))throw Error('Non-literal property');return [p.name.text,literal(p.initializer)]}))
 throw Error('Unsupported data expression: '+ts.SyntaxKind[n.kind])
}
const parts=[],papers=[]
for(const st of ast.statements)if(ts.isVariableStatement(st))for(const d of st.declarationList.declarations){const name=d.name.getText(ast);if(/^(questionsPart|groupBQuestionsPart)\d+$/.test(name))parts.push(...literal(d.initializer));if(['mpscUdcLdcPapers','groupBGeneralPapers'].includes(name))papers.push(...literal(d.initializer))}
if(!parts.length||!papers.length)throw Error('Expected generated module question/paper literals')
if(new Set(parts.map(q=>q.id)).size!==parts.length)throw Error('Duplicate module question IDs')
process.stdout.write(JSON.stringify({questions:parts,papers}))
