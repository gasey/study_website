import type { CollectionPaper } from './api'
import type { BookletGroup } from './mcsBooklets'

/** These eight registered sources are the 2025 combined Assistant/UDC sitting.
 * Other sources remain separate until their sitting identity is established.
 * Grouping changes navigation only: each booklet retains its own question IDs.
 */
export function groupUdcBooklets(papers: CollectionPaper[]): BookletGroup[] {
  const groups = new Map<string, BookletGroup>()
  for (const paper of papers) {
    const match = /^Old_Questions\/Direct_NG_2024-2027\/Assistant, UDC Paper-(I|II) Series [A-D]\.\.pdf$/.exec(paper.id)
    const grouped = match && paper.year === 2025 && paper.paper_number === match[1]
    const id = grouped ? `udc-assistant-2025:${match[1]}` : paper.id
    if (!groups.has(id)) groups.set(id, {
      id,
      title: grouped ? `2025 · Assistant / UDC · Paper ${match[1]}` : paper.paper_label || paper.title,
      papers: [],
    })
    groups.get(id)!.papers.push(paper)
  }
  return [...groups.values()].map(group => ({
    ...group, papers: [...group.papers].sort((a, b) => a.id.localeCompare(b.id)),
  }))
}
