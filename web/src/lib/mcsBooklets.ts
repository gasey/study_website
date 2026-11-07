import type { CollectionPaper } from './api'

export interface BookletGroup { id: string; title: string; papers: CollectionPaper[] }

/** Source paper roles define groups. Never merge question numbers or answers. */
export function groupMcsBooklets(papers: CollectionPaper[]): BookletGroup[] {
  const groups = new Map<string, BookletGroup>()
  for (const paper of papers) {
    const role = paper.section_path === 'gs' ? 'I' : paper.section_path === 'aptitude' ? 'II' : null
    // Unknown roles/years retain their individual identity instead of guessing.
    const id = role && paper.year ? `${paper.year}:${role}` : paper.id
    if (!groups.has(id)) groups.set(id, { id, title: role && paper.year
      ? `${paper.year} · Paper ${role} · ${role === 'I' ? 'General Studies' : 'Aptitude Tests'}`
      : paper.paper_label || paper.title, papers: [] })
    groups.get(id)!.papers.push(paper)
  }
  return [...groups.values()].sort((a, b) =>
    (b.papers[0].year || 0) - (a.papers[0].year || 0) || a.id.localeCompare(b.id))
    .map(group => ({ ...group, papers: [...group.papers].sort((a, b) => a.id.localeCompare(b.id)) }))
}

export function bookletLabel(paper: CollectionPaper): string {
  const match = /(?:Series|Booklet|Set)[\s-]+['"]?([A-D1-4])\b/i.exec(paper.id)
  return match ? `Series ${match[1].toUpperCase()}` : paper.id.split('/').pop()?.replace(/\.pdf$/i, '') || paper.title
}
