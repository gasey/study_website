import { useSyncExternalStore } from 'react'
import { choosePreferredExam } from './preferredExam'
import type { Collection } from './api'

const EXAMS_KEY = 'finna-tracked-exams'
const EXAMS_EVENT = 'finna-tracked-exams-change'

const FOCUS_KEY = 'finna-focus-subjects'
const FOCUS_EVENT = 'finna-focus-local-change'

export const MAX_FOCUS_SUBJECTS = 5

let cachedExamsRaw: string | null = null
let cachedExamsList: string[] = []

function readTrackedExams(): string[] {
  try {
    const raw = localStorage.getItem(EXAMS_KEY)
    if (raw === cachedExamsRaw) return cachedExamsList
    cachedExamsRaw = raw
    if (!raw) {
      cachedExamsList = []
      return cachedExamsList
    }
    const parsed = JSON.parse(raw)
    cachedExamsList = Array.isArray(parsed)
      ? Array.from(new Set(parsed.filter((x): x is string => typeof x === 'string' && x.length > 0)))
      : []
    return cachedExamsList
  } catch {
    return []
  }
}

function writeTrackedExams(ids: string[]) {
  const unique = Array.from(new Set(ids.filter(Boolean)))
  try {
    const raw = JSON.stringify(unique)
    localStorage.setItem(EXAMS_KEY, raw)
    cachedExamsRaw = raw
    cachedExamsList = unique
  } catch {
    cachedExamsList = unique
  }
  window.dispatchEvent(new Event(EXAMS_EVENT))
}

function subscribeExams(callback: () => void) {
  window.addEventListener(EXAMS_EVENT, callback)
  window.addEventListener('storage', callback)
  return () => {
    window.removeEventListener(EXAMS_EVENT, callback)
    window.removeEventListener('storage', callback)
  }
}

const EMPTY_IDS: string[] = []

export function useTrackedExamIds(): string[] {
  return useSyncExternalStore(subscribeExams, readTrackedExams, () => EMPTY_IDS)
}

/** Merge authoritative server exam bookmarks with local tracked list. */
export function hydrateTrackedExams(serverIds: string[], primaryId?: string | null) {
  const validServer = Array.from(new Set(serverIds.filter(Boolean)))
  if (validServer.length > 0) {
    const ordered = primaryId && validServer.includes(primaryId)
      ? [primaryId, ...validServer.filter((id) => id !== primaryId)]
      : validServer
    writeTrackedExams(ordered)
  }
  if (primaryId) choosePreferredExam(primaryId)
}

export function addLocalTrackedExam(id: string) {
  if (!id) return
  const current = readTrackedExams()
  if (current.includes(id)) return
  writeTrackedExams([...current, id])
}

export function removeLocalTrackedExam(id: string) {
  const current = readTrackedExams()
  if (!current.includes(id)) return
  writeTrackedExams(current.filter((item) => item !== id))
}

export function setLocalTrackedExams(ids: string[]) {
  writeTrackedExams(ids)
}

/** Resolve tracked exam Collection objects, always ensuring the active exam is included when available. */
export function resolveTrackedExams(
  allExams: Collection[],
  trackedIds: string[],
  activeExam: Collection | null,
): Collection[] {
  if (!allExams.length) return []
  const byId = new Map(allExams.map((e) => [e.id, e]))
  const resolved: Collection[] = []
  const seen = new Set<string>()

  // Always show active exam first so the switcher feels anchored
  if (activeExam && byId.has(activeExam.id)) {
    resolved.push(activeExam)
    seen.add(activeExam.id)
  }
  for (const id of trackedIds) {
    if (seen.has(id)) continue
    const match = byId.get(id)
    if (match) {
      resolved.push(match)
      seen.add(id)
    }
  }
  return resolved
}

// ── Guest-friendly local focus subjects mirror ──────────────────────────────

let cachedFocusRaw: string | null = null
let cachedFocusList: string[] = []

export function readLocalFocusSubjects(): string[] {
  try {
    const raw = localStorage.getItem(FOCUS_KEY)
    if (raw === cachedFocusRaw) return cachedFocusList
    cachedFocusRaw = raw
    if (!raw) {
      cachedFocusList = []
      return cachedFocusList
    }
    const parsed = JSON.parse(raw)
    cachedFocusList = Array.isArray(parsed)
      ? Array.from(new Set(parsed.filter((x): x is string => typeof x === 'string' && x.length > 0))).slice(
          0,
          MAX_FOCUS_SUBJECTS,
        )
      : []
    return cachedFocusList
  } catch {
    return []
  }
}

export function writeLocalFocusSubjects(ids: string[]) {
  const clean = Array.from(new Set(ids.filter(Boolean))).slice(0, MAX_FOCUS_SUBJECTS)
  try {
    const raw = JSON.stringify(clean)
    localStorage.setItem(FOCUS_KEY, raw)
    cachedFocusRaw = raw
    cachedFocusList = clean
  } catch {
    cachedFocusList = clean
  }
  window.dispatchEvent(new Event(FOCUS_EVENT))
}

function subscribeFocus(callback: () => void) {
  window.addEventListener(FOCUS_EVENT, callback)
  window.addEventListener('storage', callback)
  return () => {
    window.removeEventListener(FOCUS_EVENT, callback)
    window.removeEventListener('storage', callback)
  }
}

export function useLocalFocusSubjectIds(): string[] {
  return useSyncExternalStore(subscribeFocus, readLocalFocusSubjects, () => EMPTY_IDS)
}

/** Short display label for pills and compact exam tabs. */
export function shortExamLabel(exam: Pick<Collection, 'id' | 'title'>): string {
  const known: Record<string, string> = {
    udc: 'UDC',
    ldc: 'LDC',
    assistant: 'Assistant',
    'combined-prelims': 'Prelims',
    'mcs-main': 'MCS Mains',
    'group-b-gazetted': 'Group B Gaz.',
    'group-b-non-gazetted': 'Group B Non-Gaz.',
    'iti-instructor-2026': 'ITI Instructor',
    mes: 'MES',
  }
  if (known[exam.id]) return known[exam.id]
  return exam.title.replace(/\s*[·(].*$/, '').slice(0, 22)
}
