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
  limit?: number
  offset?: number
}

export function listQuestions(p: ListParams = {}): Promise<QuestionPage> {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(p)) {
    if (v !== undefined && v !== '') qs.set(k, String(v))
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

export { ApiError }
