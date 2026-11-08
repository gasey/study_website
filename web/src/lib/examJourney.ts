import { studySetLink, nextStudySetLink } from './studySetLinks'
import type { StudySetPreview } from './api'

export interface Journey {
  active_study_session?:Pick<StudySetPreview,'id'|'total'|'position'|'filters'>|null
  recent_study_sessions?:Pick<StudySetPreview,'id'|'total'|'position'|'filters'|'summary'|'finished_at'>[]
  checkpoint: { state: Record<string, string | number>; updated_at: string } | null
  active_mock: { id: string; collection_id: string; paper_id: string | null; section_path: string | null; answer_mode: string } | null
  recent_results: { id: string; score: number; submitted_at: string; n_correct: number; n_wrong: number }[]
  last_practice: { section_path: string | null; paper_id: string | null; at: string } | null
}

export function practiceJourneyLink(id: string, data: Journey | null) {
  if(id==='udc'&&data?.active_study_session)return studySetLink(data.active_study_session.id)
  if(id==='udc'&&data?.recent_study_sessions?.length){const last=data.recent_study_sessions[0];return nextStudySetLink(last.filters,last.total)}
  const params = new URLSearchParams({ view: 'practice' })
  // A checkpoint may restore study filters, never change the selected collection/view.
  const allowed = ['section', 'paper', 'q', 'pool', 'status', 'subject_id', 'topic_id', 'subtopic_id', 'offset', 'order', 'seed']
  if (data?.checkpoint) {
    // Older checkpoints used repetition order; preserve their saved position.
    if(!data.checkpoint.state.order)params.set('order','repeated')
    for (const key of allowed) {
      const value = data.checkpoint.state[key]
      if (typeof value === 'string' || typeof value === 'number') params.set(key, String(value))
    }
  } else {
    if (data?.last_practice?.paper_id) params.set('paper', data.last_practice.paper_id)
    if (data?.last_practice?.section_path) params.set('section', data.last_practice.section_path)
  }
  return `/exams/${encodeURIComponent(id)}?${params}#exam-question-browser`
}
