import type {ReactNode} from 'react'
/** Deliberately small Markdown subset. Every token is React text, never HTML. */
function inline(value:string):ReactNode[]{
 return value.split(/(`[^`\n]+`|\*\*[^*\n]+\*\*)/g).map((part,i)=>part.startsWith('`')&&part.endsWith('`')&&part.length>2
  ?<code key={i} className="rounded bg-canvas px-1 py-0.5 font-mono text-[0.9em] [overflow-wrap:anywhere]">{part.slice(1,-1)}</code>
  :part.startsWith('**')&&part.endsWith('**')&&part.length>4?<strong key={i}>{part.slice(2,-2)}</strong>:part)
}
export default function CommunityText({body,className=''}:{body:string;className?:string}){
 const blocks:ReactNode[]=[],lines=body.split('\n')
 for(let i=0;i<lines.length;){
  const match=lines[i].match(/^\s{0,3}([-*]|\d{1,3}\.)\s+(.+)$/)
  if(match){const ordered=match[1].endsWith('.'),items:ReactNode[]=[];const start=ordered?Number.parseInt(match[1]):1
   while(i<lines.length){const next=lines[i].match(/^\s{0,3}([-*]|\d{1,3}\.)\s+(.+)$/);if(!next||next[1].endsWith('.')!==ordered)break;items.push(<li key={i}>{inline(next[2])}</li>);i++}
   blocks.push(ordered?<ol key={'list'+i} start={start} className="list-decimal space-y-1 pl-5">{items}</ol>:<ul key={'list'+i} className="list-disc space-y-1 pl-5">{items}</ul>)
  }else if(!lines[i].trim()){i++}
  else{const text:string[]=[];const start=i;while(i<lines.length&&lines[i].trim()&&!/^\s{0,3}([-*]|\d{1,3}\.)\s+.+$/.test(lines[i]))text.push(lines[i++]);blocks.push(<p key={start} className="whitespace-pre-wrap">{inline(text.join('\n'))}</p>)}
 }
 return <div className={'min-w-0 space-y-3 break-words [overflow-wrap:anywhere] '+className}>{blocks}</div>
}
export function ComposerFormatting({body,sourceLinks=false}:{body:string;sourceLinks?:boolean}){return <details className="mt-3 text-[12px] text-secondary"><summary className="inline-flex min-h-11 cursor-pointer items-center font-semibold">Formatting help & preview</summary><p className="mt-1">Use **bold**, - lists, 1. numbered lists and `inline code`. Raw HTML is displayed as text. {sourceLinks?'Citations use the separate source fields below.':'References use a separate Finna link card; external links are unavailable.'}</p><div aria-label="Formatting preview" className="mt-3 rounded-[8px] border border-hairline bg-paper p-3 text-[14px] leading-relaxed">{body?<CommunityText body={body}/>:<p>Your formatted text appears here.</p>}</div></details>}
