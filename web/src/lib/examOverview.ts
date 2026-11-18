import type { CollectionDetail, CollectionPaper } from './api'
import { groupMcsBooklets, type BookletGroup } from './mcsBooklets'
import { groupUdcBooklets } from './udcBooklets'
import {
  groupSourceBooklets,
  representativeBooklet,
  withoutBooklet,
} from './sourceBooklets'
import { sortArchivePapers } from './paperArchive'

export type OverviewPaper = {
  collectionId: string
  paper: CollectionPaper
  booklets: BookletGroup
}
export type OverviewExam = {
  id: string
  title: string
  year: number | null
  papers: OverviewPaper[]
}
export function collectionBooklets(
  collectionId: string,
  papers: CollectionPaper[],
) {
  return collectionId === 'combined-prelims'
    ? groupMcsBooklets(papers)
    : collectionId === 'udc'
      ? groupUdcBooklets(papers)
      : groupSourceBooklets(papers)
}

/** Reuse the established booklet families; grouping never changes stored appearances. */
export function examOverviewGroups(
  collections: CollectionDetail[],
  order: 'newest' | 'oldest',
): OverviewExam[] {
  const sources: OverviewPaper[] = collections.flatMap((c) => {
    const groups = collectionBooklets(c.id, c.paper_list)
    return groups.map((booklets) => ({
      collectionId: c.id,
      paper: representativeBooklet(booklets),
      booklets,
    }))
  })
  const sorted = sortArchivePapers(
    sources.map((s, i) => ({
      ...s.paper,
      id: String(i),
      exam:
        s.collectionId === 'combined-prelims' ? s.booklets.title : s.paper.exam,
    })),
    order,
  ).map((p) => sources[Number(p.id)])
  const groups = new Map<string, OverviewExam>()
  for (const source of sorted) {
    const p = source.paper,
      title = withoutBooklet(p.exam?.trim() || p.title),
      key = JSON.stringify([
        source.collectionId,
        p.year,
        title,
        p.year === null ? p.id : null,
      ])
    if (!groups.has(key))
      groups.set(key, { id: key, title, year: p.year, papers: [] })
    groups.get(key)!.papers.push(source)
  }
  return [...groups.values()]
}
