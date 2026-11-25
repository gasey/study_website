/** Reading location only. Answers, scores and credentials never enter this store. */
export interface BrowsePosition {
  query: string
  questionId: string | null
  questionIndex?: number
  top: number
  savedAt: number
}
export interface BrowseCheckpoint {
  query: string
  questionId: string | null
  questionIndex: number
  top: number
  savedAt: number
}
const PREFIX = 'ism.browse-position.v1:'
const CHECKPOINT_PREFIX = 'ism.browse-checkpoint.v1:'
const FILTERS = [
  'paper',
  'section',
  'subject_id',
  'topic_id',
  'subtopic_id',
  'q',
  'pool',
  'order',
  'status',
  'answer_status',
  'study_area',
] as const
export function browseQuery(params: URLSearchParams) {
  const next = new URLSearchParams()
  for (const field of [...FILTERS, 'seed', 'offset']) {
    const value = params.get(field)
    if (value && value.length <= 1000) next.set(field, value)
  }
  next.set('pool', params.get('pool') || 'all')
  next.set('order', params.get('paper') ? 'paper' : params.get('order') || 'mixed')
  next.sort()
  return next.toString()
}
export function browseContext(params: URLSearchParams) {
  const next = new URLSearchParams(browseQuery(params))
  next.delete('offset')
  next.delete('seed')
  return next.toString()
}
export function hasBrowseSelection(params: URLSearchParams) {
  return FILTERS.some(k=>{const value=params.get(k);return value&&!(k==='pool'&&value==='all')&&!(k==='order'&&value==='mixed')&&!(k==='status'&&value==='all')}) || params.has('offset')
}
export function browseStoreKey(
  user: string,
  collection: string,
  scope: string,
) {
  return (
    PREFIX +
    encodeURIComponent(user) +
    ':' +
    encodeURIComponent(collection) +
    ':' +
    scope
  )
}
interface Store {
  entries: Record<string, BrowsePosition>
  last: string | null
}
function store(key: string): Store {
  try {
    const text = localStorage.getItem(key) || 'null'
    if (text.length > 600000) return { entries: {}, last: null }
    const raw = JSON.parse(text)
    if (
      raw &&
      typeof raw.entries === 'object' &&
      raw.entries !== null &&
      !Array.isArray(raw.entries)
    )
      return {
        entries: Object.fromEntries(
          Object.entries(raw.entries).filter(
            ([, v]) =>
              v &&
              typeof v === 'object' &&
              typeof (v as BrowsePosition).query === 'string' &&
              Number.isFinite((v as BrowsePosition).savedAt),
          ),
        ) as Record<string, BrowsePosition>,
        last: typeof raw.last === 'string' ? raw.last : null,
      }
  } catch {
    /* Storage is optional. */
  }
  return { entries: {}, last: null }
}
export function readBrowsePosition(
  key: string,
  params: URLSearchParams,
): BrowsePosition | null {
  const saved = store(key),
    context = hasBrowseSelection(params) ? browseContext(params) : saved.last
  const value = context ? saved.entries[context] : null
  if (
    !value ||
    typeof value.query !== 'string' ||
    value.query.length > 12000 ||
    !Number.isFinite(value.savedAt) ||
    Date.now() - value.savedAt > 180 * 86400000
  )
    return null
  const query = browseQuery(new URLSearchParams(value.query))
  return {
    query,
    questionId:
      typeof value.questionId === 'string' &&
      /^[\w-]{1,180}$/.test(value.questionId)
        ? value.questionId
        : null,
    questionIndex:
      typeof value.questionIndex === 'number' && Number.isFinite(value.questionIndex) && value.questionIndex >= 1
        ? Math.floor(value.questionIndex)
        : undefined,
    top: Number.isFinite(value.top)
      ? Math.min(2000, Math.max(-2000, value.top))
      : 140,
    savedAt: value.savedAt,
  }
}
export function writeBrowsePosition(key: string, position: BrowsePosition) {
  const saved = store(key),
    context = browseContext(new URLSearchParams(position.query))
  const entries = { ...saved.entries, [context]: position }
  const keep = Object.entries(entries)
    .sort((a, b) => b[1].savedAt - a[1].savedAt)
    .slice(0, 40)
  try {
    localStorage.setItem(
      key,
      JSON.stringify({ entries: Object.fromEntries(keep), last: context }),
    )
    return true
  } catch {
    return false
  }
}
export function clearBrowsePosition(key: string, params: URLSearchParams) {
  const saved = store(key),
    context = browseContext(params)
  delete saved.entries[context]
  if (saved.last === context) saved.last = null
  try {
    localStorage.setItem(key, JSON.stringify(saved))
  } catch {
    /* Browsing still works. */
  }
}
export function restoreBrowseQuery(
  current: URLSearchParams,
  saved: BrowsePosition,
) {
  const next = new URLSearchParams(current)
  for (const key of [...FILTERS, 'seed', 'offset']) next.delete(key)
  new URLSearchParams(saved.query).forEach((v, k) => next.set(k, v))
  next.set('view', 'browse')
  next.delete('fresh')
  return next
}
export function checkpointStoreKey(
  user: string,
  collection: string,
  scope: string,
) {
  return (
    CHECKPOINT_PREFIX +
    encodeURIComponent(user) +
    ':' +
    encodeURIComponent(collection) +
    ':' +
    scope
  )
}
function readCheckpointMap(key: string): Record<string, BrowseCheckpoint> {
  try {
    const text = localStorage.getItem(key) || 'null'
    if (text.length > 300000) return {}
    const raw = JSON.parse(text)
    if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
      return raw as Record<string, BrowseCheckpoint>
    }
  } catch {
    /* Storage is optional. */
  }
  return {}
}
export function readBrowseCheckpoint(
  key: string,
  params: URLSearchParams,
): BrowseCheckpoint | null {
  const map = readCheckpointMap(key)
  const ctx = browseContext(params)
  const value = map[ctx]
  if (
    !value ||
    typeof value.query !== 'string' ||
    !Number.isFinite(value.questionIndex) ||
    !Number.isFinite(value.savedAt)
  ) {
    return null
  }
  return {
    query: browseQuery(new URLSearchParams(value.query)),
    questionId:
      typeof value.questionId === 'string' && /^[\w-]{1,180}$/.test(value.questionId)
        ? value.questionId
        : null,
    questionIndex: Math.max(1, Math.floor(value.questionIndex)),
    top: Number.isFinite(value.top) ? Math.min(2000, Math.max(-2000, value.top)) : 140,
    savedAt: value.savedAt,
  }
}
export function writeBrowseCheckpoint(
  key: string,
  checkpoint: BrowseCheckpoint,
) {
  const map = readCheckpointMap(key)
  const ctx = browseContext(new URLSearchParams(checkpoint.query))
  const entries = Object.entries({ ...map, [ctx]: checkpoint })
    .sort((a, b) => b[1].savedAt - a[1].savedAt)
    .slice(0, 40)
  try {
    localStorage.setItem(key, JSON.stringify(Object.fromEntries(entries)))
    return true
  } catch {
    return false
  }
}
export function clearBrowseCheckpoint(key: string, params: URLSearchParams) {
  const map = readCheckpointMap(key)
  const ctx = browseContext(params)
  delete map[ctx]
  try {
    localStorage.setItem(key, JSON.stringify(map))
  } catch {
    /* Storage is optional. */
  }
}
export function paperBrowseLink(collection: string, paper: string) {
  const params = new URLSearchParams({ view: 'browse', pool: 'all', paper, order: 'paper' })
  if (collection === 'group-b' || collection.startsWith('group-b-')) {
    params.set('collection', collection)
    return '/exams/group-b-gazetted?' + params
  }
  return '/exams/' + encodeURIComponent(collection) + '?' + params
}
