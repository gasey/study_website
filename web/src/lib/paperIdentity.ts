import type {CollectionPaper} from './api'

/** Exam identity and printed paper heading are separate from a download filename. */
export function paperIdentity(paper: Pick<CollectionPaper,'id'|'title'|'exam'|'paper_label'>) {
  const filename=paper.id.split('/').pop()?.replace(/\.pdf$/i,'').replace(/[.\s]+$/,'').replace(/_/g,' ').trim()||''
  const title=paper.paper_label?.trim()||filename||paper.title
  const exam=paper.exam?.trim()||paper.title?.trim()||''
  return {title,exam:exam===title?'':exam,filename}
}
