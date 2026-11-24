import {accountContext,accountGeneration,checkSessionRejected} from './accountContext'
import {extractApiError} from './extractError'
import {ReadRequestCache,catalogTtl,questionQueryString} from './requestCache'
import {scopedApiPath} from './examScope'
import type {AvatarLook} from './avatar'
import { deviceId } from './device'
import {publicBrowseRead,powerFilterQuery} from './publicBrowse'

/** Typed client for the FastAPI service. Same-origin in production (Caddy
 *  routes /api), proxied by Vite in dev — so no base URL either way. */

export type AnswerSource = 'official' | 'key' | 'derived' | 'inferred' | 'none' | 'editorial'

export interface Appearance {
  paper_id: string
  section_label?: string | null
  paper_label?: string | null
  year: number | null
  exam: string | null
  paper: string | null
  qnum: string | null
  page: number | null
  series: string | null
  source_pdf_url: string | null
  figure_image_url?: string | null
}

export interface Question {
  atlas_links?: import('./atlas').AtlasLink[]
  curated?:{card_id:string;presentation_id:string;deck_id:string;deck_title:string;mode:string;source_changed?:boolean;revealed_result?:import('./vocabulary').CuratedResult|null;practice_enabled?:boolean}
  presentation_hash?: string | null
  taxonomy_paths?: {subject_id:string;subject_label:string;topic_id:string|null;topic_label:string|null;subtopic_id:string|null;subtopic_label:string|null;is_primary:boolean}[]
  id: string
  type: 'mcq' | 'descriptive'
  question: string
  direction: string | null
  question_markup: string | null
  options_markup: (string | null)[] | null
  passage: string | null
  options: (string | null)[]
  subject: string | null
  topic: string | null
  taxonomy_subject_id: string | null
  taxonomy_subject: string | null
  taxonomy_topic_id: string | null
  taxonomy_topic: string | null
  taxonomy_subtopic_id: string | null
  taxonomy_subtopic: string | null
  classification_status: 'pending' | 'approved' | null
  answer_status?: "official"|"verified"|"needs-review"|"unsolved"|"written"
  reviewed_derived?: boolean
  held?: boolean
  answer_source: AnswerSource
  verified: boolean
  source_defect: string | null
  key_disputed: boolean
  dispute_note: string | null
  times_asked: number
  first_year: number | null
  last_year: number | null
  figure_image_url?: string | null
  has_diagram?: boolean
  source_appearance?: Appearance | null
}

export interface QuestionDetail extends Question {
  appearances: Appearance[]
}

export interface QuestionPage {
  items: Question[]
  total: number
  limit: number
  offset: number
  browse_allowance?: BrowseAllowance|null
}

export interface BrowseAllowance {tier:'guest'|'account'|'pro';ist_date:string;used:number;limit:number|null;remaining:number|null;unlimited:boolean}
export const getBrowseAllowance=()=>req<BrowseAllowance>('/me/browse-allowance')

export interface QuestionPaperSummary {
  id: string
  exam: string | null
  exam_type: 'Direct' | 'Direct_NG' | 'LDE' | 'Departmental'
  year: number | null
  month: string | null
  paper_number: string | null
  source_file: string | null
  source_pdf_url: string | null
  questions: number
  answered: number
  scorable: number
}

export interface QuestionPaperPage {
  items: QuestionPaperSummary[]
  total: number
  limit: number
  offset: number
}

export interface AnswerResult {
  curated?:boolean;card?:import('./materials').CuratedWordCard|null;next_due?:string|null;graduated?:boolean;outcome?:string
  reward?:{status:string;xp:number;points:number;receipt_id:number|null;rule_version:string}|null
  correct: boolean
  answer_index: number
  answer_text: string
  answer_source: AnswerSource
  verified: boolean
  explanation: string | null
  /** Aggregate, post-reveal only; null below the server's population gate. */
  stats?: import('../components/QuestionStats').QuestionStatsData | null
}

export interface ComparedAnswer {
  answer_index:number
  answer_text:string
  explanation:string
  publication_id:string|null
  published_at:string|null
  imported?:boolean
  document:{id:string;title:string;key_status:string|null;page:number;url:string|null}|null
}
export interface AnswerComparisonData {
  official:ComparedAnswer|null
  solution:ComparedAnswer|null
  relation:'agree'|'disagree'|'not-compared'
  held:boolean
  review_note:string|null
  notice:string
}
export function getAnswerComparison(qid:string,paperId?:string|null,signal?:AbortSignal,restore=false) {
  const params=new URLSearchParams({...paperId?{paper_id:paperId}:{},...restore?{restore:'true'}:{}})
  return req<AnswerComparisonData>('/questions/'+encodeURIComponent(qid)+'/answer-comparison'+(params.size?'?'+params:''),{signal})
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

const readRequests=new ReadRequestCache()
// Only bounded question-list metadata is retained here, never answer results,
// private study filters, histories or browser-storage copies of question pages.
const questionPages=new ReadRequestCache(12)
function clearReadCaches(){readRequests.clear();questionPages.clear()}
window.addEventListener('ism-auth-change',clearReadCaches)
window.addEventListener('ism-content-change',clearReadCaches)
window.addEventListener('ism-progress-change',()=>questionPages.clear())
async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const scoped=scopedApiPath(path),method=(init?.method||'GET').toUpperCase()
  const ttl=catalogTtl(scoped),coalesce=method==='GET'&&!init?.signal&&(ttl>0||path==='/auth/session')
  if(method!=='GET')clearReadCaches()
  const epoch=accountGeneration()
  const load=async()=>{
    const publicRead=publicBrowseRead(scoped,init)
    const identity=publicRead?null:await accountContext()
    const csrf:Record<string,string>=method==='GET'?{}:{'x-review-csrf':identity?.csrf||''}
    const controller=method==='GET'&&!init?.signal?new AbortController():null
    const timer=controller?window.setTimeout(()=>controller.abort(),15000):undefined
    try{
    const res = await fetch(`/api${scoped}`, {
      ...init,credentials:publicRead?'omit':'include',...(controller?{signal:controller.signal}:{}),
      headers:publicRead?init?.headers:{'content-type':'application/json','x-device-id':deviceId(),...csrf,...init?.headers},
    })
    if(!res.ok){
      if(res.status===401&&identity)await checkSessionRejected(identity)
      let payload:unknown=null
      try{payload=await res.json()}catch{/* non-JSON gateway or 5xx HTML body */}
      throw new ApiError(res.status,extractApiError(payload,res.statusText,'Something went wrong. Please try again.'))
    }
    const data=await res.json() as T
    if(epoch!==accountGeneration())throw new ApiError(409,'Your account changed. Please reload.')
    if(path.startsWith('/questions?')&&(data as QuestionPage).browse_allowance)window.dispatchEvent(new Event('ism-browse-allowance-change'))
    return data
    }catch(error){
      if(controller?.signal.aborted)throw new ApiError(408,"This request took too long. Please try again.")
      throw error
    }finally{if(timer!==undefined)clearTimeout(timer)}
  }
  const data=await(coalesce?readRequests.read(scoped,load,ttl):load())
  if(method!=='GET'){
    clearReadCaches()
    if(/^\/questions\/[^/]+\/answer$|^\/mocks\/[^/]+\/submit$|^\/study-sessions\/[^/]+\/answer$/.test(path))window.dispatchEvent(new Event('ism-progress-change'))
  }
  // A screen sorting catalog rows must not mutate another consumer's cache.
  return ttl>0?structuredClone(data):data
}

export type GroupBStudyArea = 'common'|'english'|'gk-gs'|'technical'
export interface ListParams {
  atlas_chapter?: string
  atlas_layer?: string
  learning_entry?: string
  exam_scope?: import("./examScope").ExamScope
  study_area?: GroupBStudyArea
  shelf_id?: string
  subtopic_id?: string
  origin?: 'paper' | 'community' | 'all'
  answer_status?: 'official'|'verified'|'needs-review'|'unsolved'|'written'
  pool?: 'all' | 'scorable' | 'practice'
  q?: string
  year_from?: number
  year_to?: number
  /** Repeated, not comma-joined: FastAPI reads `?source=a&source=b`. */
  source?: AnswerSource[]
  repeats_only?: boolean
  subject_id?: string
  topic_id?: string
  collection_id?: string
  paper_id?: string
  essay_kind?: 'essay' | 'letter' | 'precis' | 'comprehension'
  section_path?: string
  order?: 'repeated'|'mixed'|'paper'
  seed?: string
  study_status?: 'all' | 'unseen' | 'answered' | 'wrong' | 'ever_wrong'
  limit?: number
  offset?: number
}

export function listQuestions(p: ListParams = {}): Promise<QuestionPage> {
  const path=`/questions?${questionQueryString(p as Record<string,unknown>)}`
  if(p.study_status&&p.study_status!=='all')return req<QuestionPage>(path)
  return questionPages.read(scopedApiPath(path),()=>req<QuestionPage>(path),15000).then(value=>structuredClone(value))
}

/** At most one caller-selected next page; no recursive prefetch or slow-link traffic. */
export function prefetchQuestionPage(p:ListParams){
  const connection=(navigator as Navigator&{connection?:{saveData?:boolean;effectiveType?:string}}).connection
  if(document.visibilityState!=='visible'||connection?.saveData||/^(slow-)?2g$/.test(connection?.effectiveType||'')||(p.study_status&&p.study_status!=='all'))return
  if((p.limit??25)>25)return
  // Speculation never admits a new paid-capacity query.
  if(powerFilterQuery({...Object.fromEntries(new URLSearchParams(scopedApiPath('/questions').split('?')[1]||'')),...p}))return
  void listQuestions(p).catch(()=>{/* Speculation never replaces the visible-page error state. */})
}

export function listQuestionPapers(p: { q?: string; subject_id?: string; year_from?: number; year_to?: number; exam_type?: QuestionPaperSummary['exam_type']; limit?: number; offset?: number } = {}): Promise<QuestionPaperPage> {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(p)) if (v !== undefined && v !== '') qs.set(k, String(v))
  return req<QuestionPaperPage>(`/questions/papers?${qs}`)
}

export interface TaxonomyFacet {
  subject_questions?:number|null
  subject_id: string
  subject: string
  topic_id: string | null
  topic: string | null
  questions: number
}

export function listTaxonomy(pool: 'all' | 'scorable' | 'practice' = 'all', learning = false): Promise<TaxonomyFacet[]> {
  return req<TaxonomyFacet[]>(`/questions/taxonomy?pool=${pool}&learning=${learning}`)
}

export interface QuestionYearFacet {
  year: number
  questions: number
}

export interface QuestionFacets {
  collection_id: string | null
  total: number
  unclassified: number
  subjects: ExamStudyTopics['subjects']
  years: QuestionYearFacet[]
}

export function getQuestionFacets(p: {
  collection_id?: string
  section_path?: string
  paper_id?: string
  subject_id?: string
  study_area?: GroupBStudyArea
  pool?: 'all' | 'scorable' | 'practice'
} = {}): Promise<QuestionFacets> {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(p)) {
    if (v !== undefined && v !== '') qs.set(k, String(v))
  }
  const suffix = qs.toString() ? `?${qs}` : ''
  return req<QuestionFacets>(`/questions/facets${suffix}`)
}

const SUBJECT_ROUTE_TO_COLLECTION: Record<string, string> = {
  english: 'subject-english',
  mathematics: 'subject-mathematics',
  arithmetic: 'subject-mathematics',
  reasoning: 'subject-reasoning',
  'reasoning-and-aptitude': 'subject-reasoning',
  'gk-gs': 'subject-gk-gs',
  gk: 'subject-gk-gs',
  gs: 'subject-gk-gs',
  mizo: 'subject-mizo',
}

export function resolveModuleCollectionId(rawId: string, isSubjectRoute = false): string {
  if (!isSubjectRoute) return rawId
  return SUBJECT_ROUTE_TO_COLLECTION[rawId] || (rawId.startsWith('subject-') ? rawId : `subject-${rawId}`)
}

export function isSubjectModule(c: Pick<Collection, 'id' | 'kind'>): boolean {
  return c.kind === 'practice' && c.id !== 'subject-wise-practice'
}

export function moduleHref(c: Pick<Collection, 'id' | 'kind' | 'route'>): string {
  if (c.route && (c.route.startsWith('/exams/') || c.route.startsWith('/subjects/'))) {
    return c.route
  }
  return c.kind === 'practice' ? `/subjects/${c.id.replace(/^subject-/, '')}` : `/exams/${c.id}`
}

export const getQuestion = (id: string) => req<QuestionDetail>(`/questions/${id}`)

export interface EssayDraft { question_id: string; body: string; updated_at: string | null }
export const getEssayDraft = (id: string) => req<EssayDraft>(`/me/essay-drafts/${encodeURIComponent(id)}`)
export const saveEssayDraft = (id: string, body: string) => req<EssayDraft>(`/me/essay-drafts/${encodeURIComponent(id)}`, { method: 'PUT', body: JSON.stringify({ body }) })

export const submitAnswer = (id: string, chosen_index: number, context = 'practice', collection_id?: string, paper_id?: string, section_path?: string) =>
  req<AnswerResult>(`/questions/${id}/answer`, {
    method: 'POST',headers:{'idempotency-key':crypto.randomUUID()},
    body: JSON.stringify({ chosen_index, context, collection_id, paper_id, section_path }),
  })

export interface Progress {
  answered: number
  correct: number
  unique_questions: number
  accuracy: number
  current_streak: number
  streak_basis?: string
  active_days_30: number
  last_active_at: string | null
  daily_activity: { day: string; answered: number; correct: number }[]
  subjects: { subject_id: string; subject: string; answered: number; correct: number; unique_questions: number }[]
  collections: { scope_id: string; label: string; answered: number; correct: number; unique_questions: number; accuracy: number }[]
  sections: { scope_id: string; label: string; answered: number; correct: number; unique_questions: number; accuracy: number }[]
}

export const getProgressSummary = () => req<Progress>('/me/progress')

export const getProgress = (collectionId?: string, sectionPath?: string) => {
  const qs = new URLSearchParams({detail:'true'})
  if (collectionId) qs.set('collection_id',collectionId)
  if (sectionPath) qs.set('section_path',sectionPath)
  return req<Progress>(`/me/progress?${qs}`)
}

export interface LearningProgressItem {
  item_id: string
  visited: boolean
  correct: boolean | null
  updated_at?: string
}

export const getLearningProgress = (moduleId: string) =>
  req<{ module_id: string; items: LearningProgressItem[] }>(`/me/learning-progress/${encodeURIComponent(moduleId)}`)

export const saveLearningProgress = (moduleId: string, items: LearningProgressItem[]) =>
  req<{ module_id: string; items: LearningProgressItem[] }>(`/me/learning-progress/${encodeURIComponent(moduleId)}`, {
    method: 'PUT',
    body: JSON.stringify({ items }),
  })

export const getMistakes = (collectionId?: string, sectionPath?: string) => {
  const qs = new URLSearchParams()
  if (collectionId) qs.set('collection_id',collectionId)
  if (sectionPath) qs.set('section_path',sectionPath)
  return req<Mistake[]>(`/me/mistakes${qs.size ? `?${qs}` : ''}`)
}

export interface Mistake {
  id: string
  question: string
  options: (string | null)[]
  answer_text: string | null
  chosen_text: string | null
  explanation: string | null
  times_wrong: number
  last_attempt: string
}
export interface PrivateProfile {
  avatar: AvatarLook | null
  avatar_version: number
  name: string | null
  handle: string
  role: string
  level: number
  created_at: string
  account_type: 'browser' | 'account'
  email: string | null
  plan_code: string
  plan_status: string
  trial_ends_at: string | null
  plan_ends_at: string | null
  progress: Progress
}
export const getProfile = () => req<PrivateProfile>('/me/profile')
export const updateProfile = (name: string) => req<PrivateProfile>('/me/profile', {
  method: 'PATCH', body: JSON.stringify({ name }),
})

export interface AccountSession { avatar?:AvatarLook|null; avatar_version?:number; authenticated: boolean; email?: string; plan_code?: string; plan_status?: string; trial_ends_at?: string | null; plan_ends_at?: string | null }
export const getAccountSession = () => req<AccountSession>('/auth/session')
export const registerAccount = (email: string, password: string, referralCode?:string) => req<AccountSession>('/auth/register', { method:'POST', body:JSON.stringify({email,password,...(referralCode?{referral_code:referralCode}:{})}) })
export const loginAccount = (email: string, password: string,code?:string) => req<AccountSession>('/auth/login', { method:'POST', body:JSON.stringify({email,password,code:code||undefined}) })
export const logoutAccount = () => req<AccountSession>('/auth/logout', { method:'POST', body:'{}' })
export const changePassword = (current_password:string,new_password:string) => req<{changed:boolean}>('/auth/password',{method:'POST',body:JSON.stringify({current_password,new_password})})

export interface BillingConfig { enabled: boolean; plans: { code:string; period:string; amount_paise:number }[]; class_plan_available:boolean }
export const getBillingConfig = () => req<BillingConfig>('/billing/config')
export const createCheckout = (period:string) => req<{key_id:string; subscription_id:string; email:string; amount_paise:number; period:string; name:string; description:string}>('/billing/checkout',{method:'POST',body:JSON.stringify({period})})
export const verifyCheckout = (data:{razorpay_payment_id:string;razorpay_subscription_id:string;razorpay_signature:string}) => req<{verified:boolean;status:string}>('/billing/verify',{method:'POST',body:JSON.stringify(data)})
export const getBilling = () => req<any>('/billing/me')
export const cancelBilling = () => req<{cancelled:boolean;status:string}>('/billing/cancel',{method:'POST',body:'{}'})


export interface CollectionSection {
  path: string
  title: string
  position: number
  formats: string[]
  papers: number
  scorable: number
  questions: number
  note: string | null
}

export interface Collection {
  id: string
  title: string
  kind: string
  route: string | null
  visibility: string
  sections: number
  scorable: number
  questions: number
}

export interface CollectionDetail extends Collection {
  practice_count: number
  answerable_count: number
  needs_review: number
  unsolved: number
  section_list: CollectionSection[]
  paper_list: CollectionPaper[]
}

export interface CollectionPaper {
  paper_label?: string | null
  instructions?: string | null
  practice_count: number
  answerable_count: number
  verified_solutions: number
  needs_review: number
  unsolved: number
  missing_explanations: number
  blocked_count: number
  id: string
  title: string
  year: number | null
  exam: string | null
  paper_number: string | null
  subject: string | null
  source_file: string | null
  source_pdf_url: string | null
  section_path: string | null
  questions: number
  scorable: number
  descriptive: number
  allow_browse: boolean
  allow_practice: boolean
  allow_timed_test: boolean
  duration_minutes: number | null
  marks_correct: number | null
  marks_wrong: number | null
  rule_source: string
}

export interface PaperQuestion {
  id: string
  appearance_id: string
  qnum: string | null
  page: number | null
  year: number | null
  series: string | null
  type: 'mcq' | 'descriptive'
  question: string
  direction: string | null
  question_markup: string | null
  options_markup: (string | null)[] | null
  passage: string | null
  marks: number | null
  essay_kind: string | null
  options: (string | null)[]
  /** Printed position -> canonical option position; used when submitting. */
  option_order: number[] | null
  answer_source: AnswerSource
  verified: boolean
  reviewed_derived?: boolean
  held?: boolean
  answer_status?: 'official'|'verified'|'needs-review'|'unsolved'|'written'
  source_defect?: string | null
  key_disputed?: boolean
  dispute_note?: string | null
  taxonomy_subject_id: string | null
  taxonomy_subject: string | null
  taxonomy_topic_id: string | null
  taxonomy_topic: string | null
  figure_image_url?: string | null
}

export interface PaperQuestionPage {
  items: PaperQuestion[]
  total: number
  practice_count: number
  limit: number
  offset: number
}

export interface HomeData {
  total_questions: number
  scorable_questions: number
  practice_questions: number
  featured_question: Question | null
  featured_source: string | null
  collections: Pick<Collection, 'id' | 'title' | 'kind' | 'route' | 'sections'>[]
}

export const getHome = () => req<HomeData>('/home')

export const getCommunityFeed = (tab: CommunityFeedResponse['tab'] = 'for-you', offset = 0, discussion: 'all' | 'doubts' | 'unanswered' = 'all', shelfId?:string) =>
  req<CommunityFeedResponse>(`/community/feed?content_version=2&tab=${encodeURIComponent(tab)}&offset=${offset}&discussion=${discussion}${shelfId?`&shelf_id=${encodeURIComponent(shelfId)}`:''}`)

export interface ModerationSummary {
  open_reports: number
  pending_posts: number
  open_appeals: number
  handled_today: number
}

export interface ModerationItem {
  content_version?:number
  edit_history?:import('../components/PostEditing').PostRevision[]
  material?:{label?:string;url?:string;unavailable?:boolean}|null
  id: string
  item_type: 'reported' | 'new_user' | 'appeal' | 'action'
  post_id: number | null
  appeal_id: number | null
  action_id: number | null
  canonical_id: string | null
  question: string | null
  body: string
  author: string
  author_role: string
  created_at: string
  reasons: string[]
  report_count: number
  report_score: number
  signal: string | null
  note: string | null
  action: string | null
  undone: boolean
  before_state: Record<string, unknown> | null
}

export interface ModerationQueue {
  tab: 'Reported' | 'New users' | 'Appeals' | 'My actions'
  counts: ModerationSummary
  items: ModerationItem[]
}

export type ModerationTab = ModerationQueue['tab']
export type ModerationAction = 'approve' | 'reject' | 'hide' | 'dismiss' | 'grant_appeal' | 'deny_appeal'

const adminHeaders = (token: string) => ({ Authorization: `Bearer ${token}` })
export const getModerationQueue = (token: string, tab: ModerationTab) =>
  req<ModerationQueue>(`/admin/moderation/queue?tab=${encodeURIComponent(tab)}`, { headers: adminHeaders(token) })
export const reviewModerationPost = (token: string, postId: number, action: ModerationAction, note = '', expectedVersion=0) =>
  req<{ ok: boolean }>(`/admin/moderation/posts/${postId}/action`, { method: 'POST', headers: adminHeaders(token), body: JSON.stringify({ action, note, expected_version:expectedVersion }) })
export const decideModerationAppeal = (token: string, appealId: number, action: ModerationAction, note = '') =>
  req<{ ok: boolean }>(`/admin/moderation/appeals/${appealId}/action`, { method: 'POST', headers: adminHeaders(token), body: JSON.stringify({ action, note }) })
export const undoModerationAction = (token: string, actionId: number) =>
  req<{ ok: boolean }>(`/admin/moderation/actions/${actionId}/undo`, { method: 'POST', headers: adminHeaders(token) })

export interface CommunityFeedItem {
  author_tier?: 'Helper'|'Regular'|'Mentor'|'Guide'|null
  author_profile_id?:string|null
  content_version?:number
  edited_at?:string|null
  avatar?:AvatarLook|null
  id: number
  question_id: string | null
  question: string | null
  kind: 'explanation' | 'doubt' | 'study' | 'material-share'
  topic_label?:string|null
  study_reference?:{kind:string;id:string}|null
  material?:{kind:string;id:string;label:string;url:string;access:string;format:string}|null
  body: string
  author: string
  author_role: string
  created_at: string
  helpful: number
  pinned: boolean
  accepted_answer: string | null
  accepted_answer_edited_at?:string|null
  source_context: string | null
}

export interface CommunityFeedResponse {
  tab: 'for-you' | 'following' | 'mcqs' | 'doubts' | 'questions' | 'materials'
  available: boolean
  message: string | null
  items: CommunityFeedItem[]
  has_more: boolean
}

/** LDE collections are intentionally held back until the exam library grows. */
export function isLaterExamCollection(collection: Pick<Collection, 'id' | 'title' | 'kind'>): boolean {
  return /\bL\.?D\.?E\.?\b|\blimited departmental(?: examination| exam)?\b/i.test(
    `${collection.id} ${collection.title} ${collection.kind}`,
  )
}

export const listCollections = () => req<Collection[]>('/collections')
export type CollectionHeader = Pick<Collection,'id'|'title'|'kind'|'route'|'visibility'>
export const getCollectionHeader = (id:string) => req<CollectionHeader>(`/collections/${encodeURIComponent(id)}/header`)
export const getCollection = (id: string) => req<CollectionDetail>(`/collections/${id}`)
export interface ExamStudySubtopic { id:string; title:string; questions:number }
export interface ExamStudyTopic { id:string; title:string; questions:number; subtopics:ExamStudySubtopic[] }
export interface ExamStudySubject { id:string; title:string; questions:number; topics:ExamStudyTopic[] }
export interface ExamStudyTopics { collection_id:string; title:string; questions:number; unclassified:number; subjects:ExamStudySubject[] }
export const getExamStudyTopics = (id:string, area?:GroupBStudyArea, section?:string) => { const params=new URLSearchParams();if(area)params.set('study_area',area);if(section)params.set('section_path',section);return req<ExamStudyTopics>(`/collections/${encodeURIComponent(id)}/study-topics?${params}`) }
export const getGroupBStudyConfig = () => req<{version:string;rules:{collection_id:string;paper_id:string;role:'english'|'gk-gs'|'technical';recruitment_stream:string;evidence:string}[]}>('/collections/group-b/study-config')
export interface ExamProgressSummary {
  collection_id: string
  answered: number
  correct: number
  unique_questions: number
  accuracy: number
}
export const getExamProgress = () => req<ExamProgressSummary[]>('/me/exam-progress')
export const getExamBookmarks = () => req<{ collection_ids: string[];primary_collection_id:string|null }>('/me/exam-bookmarks')
export const saveExamBookmark = (id: string) => req<{ saved: boolean }>(`/me/exam-bookmarks/${encodeURIComponent(id)}`, { method: 'PUT' })
export const removeExamBookmark = (id: string) => req<{ saved: boolean }>(`/me/exam-bookmarks/${encodeURIComponent(id)}`, { method: 'DELETE' })
export const listPaperQuestions = (collectionId: string, paperId: string, offset = 0, limit = 50, signal?:AbortSignal) =>
  req<PaperQuestionPage>(`/collections/${encodeURIComponent(collectionId)}/paper-questions?paper_id=${encodeURIComponent(paperId)}&offset=${offset}&limit=${limit}`,{signal})

export { ApiError }

// ── mocks ───────────────────────────────────────────────────────────────
export interface MockQuestion {
  figure_image_url?: string | null
  id: string
  position: number
  question: string
  options: (string | null)[]
  direction: string | null
  question_markup: string | null
  options_markup: (string | null)[] | null
  passage: string | null
  page: number | null
  source_pdf_url: string | null
}

export interface MockSession {
  learning_test_id?:string|null
  learning_test_version?:number|null
  learning_test_title?:string|null
  paper_mode?: 'practice' | 'full'
  excluded_presentations?:number
  id: string
  collection_id: string
  answer_mode: 'official' | 'derived-practice'
  section_path: string | null
  paper_id: string | null
  current_position: number
  saved_answers: Record<string, number>
  marked_questions: string[]
  duration_seconds: number
  started_at: string
  /** Computed server-side. The countdown shown is cosmetic; the server
   *  recomputes elapsed time on submit regardless of what the client did. */
  seconds_remaining: number
  questions: MockQuestion[]
}

export interface MockReviewRow {
  topic_label?: string | null
  figure_image_url?: string | null
  direction?: string | null
  question_markup?: string | null
  passage?: string | null
  position: number
  question_id: string
  question: string
  chosen_text: string | null
  answer_text: string | null
  correct: boolean
  explanation: string | null
  answer_source: string | null
}

export interface MockResult {
  marks_correct?: number; marks_wrong?: number;
  learning_test_id?:string|null
  learning_test_version?:number|null
  learning_test_title?:string|null
  id: string
  collection_id?:string|null
  answer_mode: 'official' | 'derived-practice'
  n_correct: number
  n_wrong: number
  n_skipped: number
  score: number
  total: number
  elapsed_seconds: number
  late: boolean
  review: MockReviewRow[]
  score_breakdown?:{official_subset:ScoreTotals;maximum:number}|null
  legacy_unversioned?:boolean
}

export interface MockStart {
  learning_test_id?:string|null
  learning_test_version?:number|null
  learning_test_title?:string|null
  paper_mode?: 'practice' | 'full'
  collection_id: string
  answer_mode?: 'official' | 'derived-practice'
  section_path?: string
  paper_id?: string
  count?: number
  duration_minutes?: number
  marks_correct?: number
  marks_wrong?: number
}

export const startMock = (b: MockStart) =>
  req<MockSession>('/mocks', { method: 'POST', body: JSON.stringify(b) })

export const currentMock = () => req<MockSession | null>('/mocks/current')
export const saveMockAnswer = (mockId: string, answer: { question_id: string; chosen_index: number | null; marked: boolean; position: number }) =>
  req<{ok:boolean}>(`/mocks/${encodeURIComponent(mockId)}/answers`, { method: 'PUT', body: JSON.stringify(answer) })

export const submitMock = (id: string, answers: { question_id: string; chosen_index: number }[]) =>
  req<MockResult>(`/mocks/${id}/submit`, { method: 'POST', body: JSON.stringify({ answers }) })

export interface MockSummary {
  learning_test_id?:string|null
  learning_test_version?:number|null
  learning_test_title?:string|null
  id: string
  collection_id: string
  collection_title: string
  answer_mode: 'official' | 'derived-practice'
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

export const listMocks = () => req<MockSummary[]>('/mocks')
export const getMockResult = (id: string) => req<MockResult>(`/mocks/${id}`)

export interface ScoringFacts {
  total: number
  scorable: number
  practice: number
  official: number
  transcribed: number
  dup_defect: number
}

export const getScoringFacts = () => req<ScoringFacts>('/scoring-facts')

export interface ScoreTotals {
  n_correct:number; n_wrong:number; n_skipped:number; n_excluded:number
  scorable_total:number; score:number|null; maximum:number; accuracy:number|null
}
export interface MockAssessment extends ScoreTotals {
  id:string; computed_at:string; policy_version:string; original_score:number; original_total:number
  legacy_unversioned:boolean; changed_questions:number
  official_subset:ScoreTotals; original_official_subset:ScoreTotals
  marking:{correct:number;wrong_penalty:number}
  rows:{question_id:string;position:number;question:string|null;chosen_text:string|null;original_answer:string|null;original_outcome:string;answer_text:string|null;answer_source:string|null;outcome:string;reason:string}[]
}
export const getMockAssessments=(id:string)=>req<{items:MockAssessment[];pending:boolean}>('/mocks/'+encodeURIComponent(id)+'/assessments')
export const reassessMock=(id:string)=>req<MockAssessment>('/mocks/'+encodeURIComponent(id)+'/reassess',{method:'POST',body:'{}'})
export interface ScoreSummary {practice_adjusted:{assessed:number;correct:number;wrong:number;excluded:number;total:number};mocks_original:{completed:number;original_marks:number};profile_basis:string}
export const getScoreSummary=()=>req<ScoreSummary>('/me/score-summary')

export interface LibraryShelf {id:string;title:string;description:string;questions:number;match_ids:string[]}
export interface ShelfDetail extends LibraryShelf {topics:{subject_id:string;subject:string;topic_id:string|null;topic:string|null;subtopic_id:string|null;subtopic:string|null;questions:number}[];exams:{id:string;title:string}[]}
export const listLibraryShelves=()=>req<LibraryShelf[]>('/library/shelves')
export const getLibraryShelf=(id:string)=>req<ShelfDetail>('/library/shelves/'+encodeURIComponent(id))

/** Viewing never creates an attempt or a reward. Indices remain canonical. */
export type ViewedAnswer = Omit<AnswerResult, 'correct' | 'reward'> & {viewed:true;retry_at:string;retry_after_seconds:number}
export const revealAnswer = (id:string,paperId?:string|null) =>
  req<ViewedAnswer>(`/questions/${id}/reveal${paperId?'?paper_id='+encodeURIComponent(paperId):''}`,{method:'POST'})

export interface PracticeState {question_id:string;paper_id:string|null;viewed:boolean;answer:ViewedAnswer|null;retry_at:string|null;retry_after_seconds:number;restricted:boolean;message?:string}
export const loadPracticeStates=(items:{question_id:string;paper_id?:string|null}[])=>req<{items:PracticeState[]}>('/questions/practice-state',{method:'POST',body:JSON.stringify({items})})
export const getNextQuestion=(qid:string,paperId?:string|null)=>req<{question_id:string|null;paper_id:string}>(`/questions/${qid}/next${paperId?'?paper_id='+encodeURIComponent(paperId):''}`)

export interface StudySetFilters {
  year_from?: number; year_to?: number;
  order?: 'repeated'|'mixed'; seed?: string;
  subject_id?: string | null; topic_id?: string | null; subtopic_id?: string | null;
  paper_id?: string | null; section_path?: string | null; q?: string | null;
  study_status?: 'all'|'unseen'|'answered'|'wrong'|'ever_wrong'; pool?: 'practice'|'scorable';
  answer_status?: 'official'|'verified'|'needs-review'|null; offset?: number;
  onboarding_version?:number;exam_title?:string;review_session_id?: string;has_curated?:boolean;deck_id?:string|null;
}
export interface StudySetSummary { curated_checked?:number;correct:number;wrong:number;viewed:number;skipped:number;unofficial:number;total:number;reward?:{status:string;xp:number;points:number;receipt_id?:number} }
export interface StudySetPreview {
  collection_id: string|null; kind:'practice'|'review';
  id:string;requested_size:10|20;total:number;position:number;version:number;
  filters:StudySetFilters;created_at:string;updated_at:string;finished_at:string|null;summary:StudySetSummary|null;
}
export interface StudySetState extends StudySetPreview {
  viewed_ids:string[];results:Record<string,{result:AnswerResult;chosen_index:number|null;updated_fields?:string[]}>;
  summary:StudySetSummary;
}
export interface StudySet extends StudySetState { question_ids:string[];items:Question[] }
export const listStudySets=()=>req<{items:StudySetPreview[]}>('/study-sessions')
const WORD_REVIEW_HEADERS={'x-finna-review-items':'curated-v1'}
export const getStudySet=(id:string)=>req<StudySet>('/study-sessions/'+encodeURIComponent(id),{headers:WORD_REVIEW_HEADERS})
export const startStudySet=(request_key:string,size:10|20,filters:StudySetFilters,review_session_id?:string)=>req<StudySet>('/study-sessions',{method:'POST',body:JSON.stringify({request_key,size,filters,review_session_id})})
export const moveStudySet=(id:string,version:number,position:number)=>req<StudySetState>('/study-sessions/'+encodeURIComponent(id)+'/position',{method:'POST',headers:WORD_REVIEW_HEADERS,body:JSON.stringify({version,position})})
export const checkStudySet=(id:string,version:number,question_id:string,chosen_index:number,presentation_hash?:string|null)=>req<StudySetState>('/study-sessions/'+encodeURIComponent(id)+'/answer',{method:'POST',headers:WORD_REVIEW_HEADERS,body:JSON.stringify({version,question_id,chosen_index,presentation_hash})})
export const viewStudySet=(id:string,question_id:string)=>req<StudySetState>('/study-sessions/'+encodeURIComponent(id)+'/viewed',{method:'POST',headers:WORD_REVIEW_HEADERS,body:JSON.stringify({question_id})})
export const revealStudyWord=(id:string,version:number,question_id:string)=>req<StudySet>('/study-sessions/'+encodeURIComponent(id)+'/word-reveal',{method:'POST',headers:WORD_REVIEW_HEADERS,body:JSON.stringify({version,question_id})})
export const finishStudySet=(id:string,version:number)=>req<StudySetState>('/study-sessions/'+encodeURIComponent(id)+'/finish',{method:'POST',headers:WORD_REVIEW_HEADERS,body:JSON.stringify({version})})

export interface FocusSubjects {items:{subject_id:string;label:string}[];available?:{id:string;label:string;selected:boolean}[];limit:number}
export interface TopicMastery {subject_id:string;subject_label:string;topic:string;topic_label:string;state:'exploring'|'practicing'|'proficient'|'mastered';distinct_attempted:number;distinct_correct_latest:number;accuracy:number;rusty:boolean;focused:boolean;in_primary_exam:boolean}
export interface MasterySnapshot {items:TopicMastery[];basis:string;rule_version:string;exam:{id:string;title:string}|null}
export interface ReviewQueue {curated_due_count?:number;curated_scheduled_count?:number;curated_writes_enabled?:boolean;vocabulary_due_count?:number;vocabulary_scheduled_count?:number;due_count:number;scheduled_count:number;has_more:boolean;items:{item_id:string;item_type?:'question'|'vocab';curated?:boolean;deck_id?:string|null;question:string;box:number;due_on:string;focused:boolean;subject_label:string;topic_label:string|null}[]}
export interface WeeklyRecap {week_start:string;week_end:string;xp:number;reviews_cleared:number;active_days:number;streak_kept:boolean;focus_seconds:number;topics:{topic:string;topic_label:string;tier:string}[];more_topics:boolean;topic_basis:string;focus_basis:string}
export interface TodayPlan {atlas_suggestions?:{chapter_id:string;title:string;url:string;practice_url:string}[];vocabulary?:{target:number;introduced:number;remaining:number;due:number;eligible:number;url:string}|null;exam_preparation?:{title:string;date:string;days_remaining:number;new_limit:number;phase:string;mock_url:string|null}|null;weekly_recap?:WeeklyRecap|null;account:boolean;ist_date:string;exam:{id:string;title:string;is_primary:boolean}|null;focus:FocusSubjects;due_count:number;scheduled_count:number;new_questions:{subject_label:string;topic_label:string;target:number;url:string;exam_title?:string;progress?:number;completed?:boolean}|null;plan_status?:{started:boolean;completed?:boolean;progress?:number;target?:number};daily_five:{status:string;url:string};quests:{key:string;title:string;progress:number;target:number;completed:boolean;claimed:boolean}[];empty_reason:string}
export interface CalendarLayers {community:{id:string;day:string;title:string;starts_at:string;ends_at:string;url:string;kind:string}[];desk_schedule_available:boolean;registered:boolean;entries:import('./calendar').OwnedEntry[];occurrences:import('./calendar').OwnedOccurrence[];official:import('./calendar').CalendarEvent[];forecast:{day:string;count:number}[];habit:{day:string;count:number}[];forecast_basis:string}
export const getToday=()=>req<TodayPlan>('/me/today',{headers:WORD_REVIEW_HEADERS})
export const getMastery=()=>req<MasterySnapshot>('/me/mastery')
export const getReviewQueue=(offset=0,deck_id?:string)=>req<ReviewQueue>('/me/review-queue?limit=100&offset='+offset+(deck_id?'&deck_id='+encodeURIComponent(deck_id):''),{headers:WORD_REVIEW_HEADERS})
export const getFocusSubjects=()=>req<FocusSubjects>('/me/focus-subjects')
export const saveFocusSubjects=(subject_ids:string[])=>req<FocusSubjects>('/me/focus-subjects',{method:'PATCH',body:JSON.stringify({subject_ids})})
export const setPrimaryExam=(id:string)=>req<{primary_collection_id:string}>('/me/exam-bookmarks/'+encodeURIComponent(id)+'/primary',{method:'PUT'})
export const startSmartReview=(request_key:string,focus_only=false,through?:string,item_type:'all'|'question'|'vocab'='all',deck_id?:string)=>req<StudySet>('/review-sessions',{method:'POST',headers:WORD_REVIEW_HEADERS,body:JSON.stringify({request_key,focus_only,through,item_type,deck_id})})
export const getCalendarLayers=(start:string,end:string)=>req<CalendarLayers>('/me/calendar-layers?'+new URLSearchParams({start,end}))

export const getPaperReadiness=(collection:string,paper:string)=>req<import('./bankOrganization').PaperReadiness>('/collections/'+encodeURIComponent(collection)+'/paper-readiness?paper_id='+encodeURIComponent(paper))


export interface OnboardingStatus {exam:{id:string;title:string;live_version:number}|null;session:StudySetPreview|null;available:boolean;reason:string|null}
export interface OnboardingSummary {finished:boolean;subjects:{subject_id:string;label:string;checked:number;correct:number}[];suggested_subject_ids:string[];basis?:string}
async function onboardingRequest<T>(path:string,init?:RequestInit){const generation=accountGeneration(),identity=await req<{user_id:string}>('/review/session');if(generation!==accountGeneration())throw new Error('Your account changed. Please reload.');return req<T>(path,{...init,headers:{...init?.headers,'x-learning-user':identity.user_id||''}})}
export const getOnboarding=()=>onboardingRequest<OnboardingStatus>('/me/onboarding')
export const startOnboarding=(collection_id:string,request_key:string)=>onboardingRequest<StudySet>('/me/onboarding',{method:'POST',body:JSON.stringify({collection_id,request_key})})
export const getOnboardingSummary=(sid:string)=>onboardingRequest<OnboardingSummary>('/me/onboarding/'+encodeURIComponent(sid)+'/summary')

export const getGroupPrice=()=>onboardingRequest<{amount_paise:number;enabled:boolean}>('/billing/bulk/me')
export const claimGroupPrice=(code:string,expected_amount_paise:number)=>onboardingRequest<{saved:boolean;already_redeemed:boolean;amount_paise:number}>('/billing/bulk/claim',{method:'POST',body:JSON.stringify({code,expected_amount_paise})})
