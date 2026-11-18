export interface StudyReference {kind:'question'|'material'|'paper'|'exam';id:string;label?:string;url?:string}

export function parseStudyReference(value:string,origin:string):StudyReference|null {
  if(!value.trim())return null
  let url:URL
  try{url=new URL(value.trim(),origin)}catch{throw new Error('Paste a Finna question, material, original paper or exam link.')}
  if(![origin,'https://study.hawayu.in'].includes(url.origin))throw new Error('Use a link to an item on Finna.')
  const path=url.pathname
  let match:RegExpMatchArray|null
  try{
    if((match=path.match(/^\/exams\/[^/]+\/paper\/?$/))&&url.searchParams.get('paper'))return {kind:'paper',id:url.searchParams.get('paper')!}
    if((match=path.match(/^\/bank\/([^/]+)\/?$/)))return {kind:'question',id:decodeURIComponent(match[1])}
    if((match=path.match(/^\/materials\/([^/]+)\/?$/)))return {kind:'material',id:decodeURIComponent(match[1])}
    if((match=path.match(/^\/exams\/([^/]+)\/?$/)))return {kind:'exam',id:decodeURIComponent(match[1])}
    if((match=path.match(/^\/papers\/source\/(Old_Questions\/.+\.pdf)$/i)))return {kind:'paper',id:decodeURIComponent(match[1])}
  }catch{throw new Error('This Finna link could not be read. Copy it again from the item.')}
  throw new Error('Paste the link to a Finna question, material, original paper or exam.')
}
