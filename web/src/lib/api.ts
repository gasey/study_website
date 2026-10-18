import { deviceId } from './device'

/** Typed client for the FastAPI service. Same-origin in production (Caddy
 *  routes /api), proxied by Vite in dev — so no base URL either way. */

export type AnswerSource = 'official' | 'key' | 'derived' | 'inferred' | 'none'

export interface Appearance {
  paper_id: string
  year: number | null
  exam: string | null
  paper: string | null
  qnum: string | null
  page: number | null
  series: string | null
}

export interface Question {
  id: string
  type: 'mcq' | 'descriptive'
  question: string
  options: string[]
  subject: string | null
  topic: string | null
  difficulty: string | null
  answer_source: AnswerSource
  verified: boolean
  source_defect: string | null
  times_asked: number
  first_year: number | null
  last_year: number | null
}

export interface QuestionDetail extends Question {
  appearances: Appearance[]
}

export interface QuestionPage {
  items: Question[]
  total: number
  limit: number
  offset: number
}

export interface AnswerResult {
  correct: boolean
  answer_index: number
  answer_text: string
  answer_source: AnswerSource
  verified: boolean
  explanation: string | null
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: {
      'content-type': 'application/json',
      'x-device-id': deviceId(),
      ...init?.headers,
    },
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      detail = (await res.json()).detail ?? detail
    } catch {
      /* non-JSON error body; the status text will do */
    }
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}

export interface ListParams {
  pool?: 'scorable' | 'practice'
  q?: string
  year_from?: number
  year_to?: number
  /** Repeated, not comma-joined: FastAPI reads `?source=a&source=b`. */
  source?: AnswerSource[]
  repeats_only?: boolean
  limit?: number
  offset?: number
}

export function listQuestions(p: ListParams = {}): Promise<QuestionPage> {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(p)) {
    if (v === undefined || v === '' || v === false) continue
    if (Array.isArray(v)) v.forEach((x) => qs.append(k, String(x)))
    else qs.set(k, String(v))
  }
  return req<QuestionPage>(`/questions?${qs}`)
}

export const getQuestion = (id: string) => req<QuestionDetail>(`/questions/${id}`)

export const submitAnswer = (id: string, chosen_index: number, context = 'practice') =>
  req<AnswerResult>(`/questions/${id}/answer`, {
    method: 'POST',
    body: JSON.stringify({ chosen_index, context }),
  })

export interface Progress {
  answered: number
  correct: number
  unique_questions: number
}

export const getProgress = () => req<Progress>('/me/progress')


export interface CollectionSection {
  path: string
  title: string
  position: number
  formats: string[]
  papers: number
  scorable: number
}

export interface Collection {
  id: string
  title: string
  kind: string
  route: string | null
  visibility: string
  sections: number
  scorable: number
}

export interface CollectionDetail extends Collection {
  section_list: CollectionSection[]
}

export const listCollections = () => req<Collection[]>('/collections')
export const getCollection = (id: string) => req<CollectionDetail>(`/collections/${id}`)

export { ApiError }

// ── mocks ───────────────────────────────────────────────────────────────
export interface MockQuestion {
  id: string
  position: number
  question: string
  options: string[]
}

export interface MockSession {
  id: string
  collection_id: string
  section_path: string | null
  duration_seconds: number
  started_at: string
  /** Computed server-side. The countdown shown is cosmetic; the server
   *  recomputes elapsed time on submit regardless of what the client did. */
  seconds_remaining: number
  questions: MockQuestion[]
}

export interface MockReviewRow {
  position: number
  question_id: string
  question: string
  chosen_text: string | null
  answer_text: string | null
  correct: boolean
  explanation: string | null
}

export interface MockResult {
  id: string
  n_correct: number
  n_wrong: number
  n_skipped: number
  score: number
  total: number
  elapsed_seconds: number
  late: boolean
  review: MockReviewRow[]
}

export interface MockStart {
  collection_id: string
  section_path?: string
  count?: number
  duration_minutes?: number
  marks_correct?: number
  marks_wrong?: number
}

export const startMock = (b: MockStart) =>
  req<MockSession>('/mocks', { method: 'POST', body: JSON.stringify(b) })

export const currentMock = () => req<MockSession | null>('/mocks/current')

export const submitMock = (id: string, answers: { question_id: string; chosen_index: number }[]) =>
  req<MockResult>(`/mocks/${id}/submit`, { method: 'POST', body: JSON.stringify({ answers }) })

export interface MockSummary {
  id: string
  collection_id: string
  collection_title: string
  section_path: string | null
  total: number
  n_correct: number | null
  n_wrong: number | null
  n_skipped: number | null
  score: number | null
  elapsed_seconds: number | null
  late: boolean
  started_at: string
  submitted_at: string | null
}

export interface Mistake {
  id: string
  question: string
  options: string[]
  answer_text: string | null
  chosen_text: string | null
  explanation: string | null
  times_wrong: number
  last_attempt: string
}

export const listMocks = () => req<MockSummary[]>('/mocks')
export const getMockResult = (id: string) => req<MockResult>(`/mocks/${id}`)
export const getMistakes = () => req<Mistake[]>('/me/mistakes')

export interface ScoringFacts {
  total: number
  scorable: number
  practice: number
  official: number
  transcribed: number
  dup_defect: number
}

export const getScoringFacts = () => req<ScoringFacts>('/scoring-facts')
