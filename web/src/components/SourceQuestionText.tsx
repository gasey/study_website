import { type ReactNode } from 'react'

// Deliberate source-markup subset used by the older MPSC module renderer.
// Tokens are converted into React nodes; this never evaluates HTML.
const TOKEN_SOURCE = String.raw`\*\*\*([^\s*][^*]{0,3998})\*\*\*|\*\*([^\s*][^*]{0,3998})\*\*|__([^\s_][^_]{0,3998})__|\*([^\s*][^*]{0,3998})\*`

function inline(text: string, depth = 0): ReactNode[] {
  if (depth > 3) return [text]
  const nodes: ReactNode[] = []
  let last = 0
  let match: RegExpExecArray | null
  // Each recursive call needs its own cursor. Sharing one global RegExp means
  // parsing a formatted span resets its parent's cursor and can loop forever.
  const token = new RegExp(`_{3,}|${TOKEN_SOURCE}`, 'g')
  while ((match = token.exec(text)) !== null) {
    if (match.index > last) nodes.push(text.slice(last, match.index))
    if (match[1] === undefined && match[2] === undefined && match[3] === undefined && match[4] === undefined) {
      nodes.push(<span key={`blank-${match.index}`} role="img" aria-label="blank" className="source-question-blank" style={{minWidth:`${Math.max(2.4, Math.min(match[0].length,30)*.42).toFixed(1)}em`}} />)
      last = match.index + match[0].length
      continue
    }
    const body = match[1] ?? match[2] ?? match[3] ?? match[4]
    const child = inline(body, depth + 1)
    const key = `${match.index}-${nodes.length}`
    if (match[1] !== undefined) nodes.push(<strong key={key}><em>{child}</em></strong>)
    else if (match[2] !== undefined) nodes.push(<strong key={key}>{child}</strong>)
    else if (match[3] !== undefined) nodes.push(<u key={key} className="decoration-1 underline-offset-2">{child}</u>)
    else nodes.push(<em key={key}>{child}</em>)
    last = match.index + match[0].length
  }
  if (last < text.length) nodes.push(text.slice(last))
  return nodes
}

type SourceTag = 'u' | 'i' | 'em' | 'b' | 'strong' | 'mark'
type SourceFrame = { tag: SourceTag | null; opening: string; nodes: ReactNode[]; key: number }

function sourceText(text: string): ReactNode[] {
  // Reviewed PDFs and legacy modules use both HTML-like emphasis and Markdown.
  // Recognize only attribute-free source tags, constructing React nodes rather
  // than interpreting HTML. Unknown tags and attributes remain escaped text.
  const tags = /<(\/?)(u|i|em|b|strong|mark)\s*>|<br\s*\/?>/gi
  const stack: SourceFrame[] = [{ tag: null, opening: '', nodes: [], key: 0 }]
  let last = 0
  let match: RegExpExecArray | null
  while ((match = tags.exec(text)) !== null) {
    const frame = stack[stack.length - 1]
    if (match.index > last) frame.nodes.push(...inline(text.slice(last, match.index)))
    if (!match[2]) frame.nodes.push(<br key={`br-${match.index}`} />)
    else if (!match[1]) {
      if (stack.length < 16) stack.push({ tag: match[2].toLowerCase() as SourceTag, opening: match[0], nodes: [], key: match.index })
      else frame.nodes.push(match[0])
    } else if (stack.length > 1 && frame.tag === match[2].toLowerCase()) {
      stack.pop()
      const { nodes, key } = frame
      const tag = frame.tag
      let node: ReactNode
      if (tag === 'u') node = <u key={`u-${key}`} className="decoration-1 underline-offset-2">{nodes}</u>
      else if (tag === 'b' || tag === 'strong') node = <strong key={`b-${key}`} className="font-bold">{nodes}</strong>
      else if (tag === 'mark') node = <mark key={`mark-${key}`} className="rounded-sm bg-amber-100 px-0.5 text-amber-950">{nodes}</mark>
      else node = <em key={`em-${key}`} className="italic">{nodes}</em>
      stack[stack.length - 1].nodes.push(node)
    } else frame.nodes.push(match[0])
    last = match.index + match[0].length
  }
  if (last < text.length) stack[stack.length - 1].nodes.push(...inline(text.slice(last)))
  // An unclosed source tag must not silently emphasize the remaining question.
  while (stack.length > 1) {
    const frame = stack.pop()!
    stack[stack.length - 1].nodes.push(frame.opening, ...frame.nodes)
  }
  return stack[0].nodes
}

function enumeratedParts(text: string) {
  const markers = [...text.matchAll(/\((i|ii|iii|iv|v|vi)\)\s+/gi)]
  if (markers.length < 3 || markers[0].index === 0 || markers[0][1].toLowerCase() !== 'i') return null
  if (markers.some((marker, index) => marker[1].toLowerCase() !== ['i', 'ii', 'iii', 'iv', 'v', 'vi'][index])) return null
  const intro = text.slice(0, markers[0].index).trim()
  const parts = markers.map((marker, index) => text.slice(marker.index, markers[index + 1]?.index ?? text.length).trim())
  return intro && parts.every(part => part.length > 3) ? { intro, parts } : null
}

export function SourceQuestionText({ text, className = '', instruction, formatEnumerations = false }: { text: string; className?: string; instruction?: string | null; formatEnumerations?: boolean }) {
  // Older imports encoded an underlined target as **bold**. Only bridge that
  // convention when the actual question instruction explicitly says underlined.
  // Explicit source underline markup takes precedence; never guess a target
  // when the question contains no marked span at all.
  const legacyUnderline = /\bunderlined\b/i.test(instruction || '') && !/<u\s*>|__[^_]/i.test(text)
  const enumeration = formatEnumerations ? enumeratedParts(text) : null
  return <span className={`source-question-text whitespace-pre-wrap ${legacyUnderline ? 'source-question-underline-targets' : ''} ${className}`}>
    {enumeration ? <>{sourceText(enumeration.intro)}<span className="source-question-enumeration">{enumeration.parts.map((part, index) => <span key={index}>{sourceText(part)}</span>)}</span></> : sourceText(text)}
  </span>
}

export function SourceQuestionContext({ direction, passage, collapsed = false }: { direction?: string | null; passage?: string | null; collapsed?: boolean }) {
  if (!direction && !passage) return null
  return <div className="mb-4 rounded-[8px] border-l-[3px] border-[#B9A579] bg-[#F6F2E9] px-4 py-3 text-[13px] leading-relaxed text-secondary">
    {direction && <p><strong className="mr-1 font-semibold text-ink">Instructions. </strong><SourceQuestionText text={direction} /></p>}
    {passage && <details open={!collapsed} className={direction ? 'mt-2 border-t border-[#E4DDCE] pt-2' : ''}>
      <summary className="cursor-pointer font-semibold text-ink">Read the shared passage</summary>
      <div className="mt-2"><SourceQuestionText text={passage} /></div>
    </details>}
  </div>
}
