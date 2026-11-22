/** Site-wide persistent question selection tray (§VII.10.2).
 *  Select questions while browsing `/bank`, a paper, a subject shelf or `/practice`,
 *  then jump straight to `/practice/build` with the selected IDs preserved. */

import { useEffect, useState } from 'react'

const STORAGE_KEY = 'finna-question-selection-tray-v1'
const MAX_TRAY_ITEMS = 100
const CHANGE_EVENT = 'finna-selection-tray-change'

function readStorage(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return [...new Set(parsed.filter((v): v is string => typeof v === 'string' && v.length > 0))].slice(0, MAX_TRAY_ITEMS)
  } catch {
    return []
  }
}

function writeStorage(ids: string[]) {
  const unique = [...new Set(ids.filter((v) => typeof v === 'string' && v.length > 0))].slice(0, MAX_TRAY_ITEMS)
  try {
    if (unique.length) localStorage.setItem(STORAGE_KEY, JSON.stringify(unique))
    else localStorage.removeItem(STORAGE_KEY)
  } catch {
    // Ignore storage quota errors in private browsing.
  }
  window.dispatchEvent(new Event(CHANGE_EVENT))
}

export function getSelectionTray(): string[] {
  return readStorage()
}

export function toggleSelectionTray(qid: string): string[] {
  const current = readStorage()
  const next = current.includes(qid)
    ? current.filter((id) => id !== qid)
    : [...current, qid].slice(0, MAX_TRAY_ITEMS)
  writeStorage(next)
  return next
}

export function addToSelectionTray(qids: string[]): string[] {
  const next = [...readStorage(), ...qids]
  writeStorage(next)
  return readStorage()
}

export function clearSelectionTray(): void {
  writeStorage([])
}

export function selectionTrayBuildHref(ids: string[]): string {
  const params = new URLSearchParams()
  ids.slice(0, MAX_TRAY_ITEMS).forEach((id) => params.append('ids', id))
  return '/practice/build' + (ids.length ? '?' + params.toString() : '')
}

export function useSelectionTray() {
  const [ids, setIds] = useState<string[]>(() => readStorage())

  useEffect(() => {
    const sync = () => setIds(readStorage())
    window.addEventListener(CHANGE_EVENT, sync)
    window.addEventListener('storage', sync)
    return () => {
      window.removeEventListener(CHANGE_EVENT, sync)
      window.removeEventListener('storage', sync)
    }
  }, [])

  return {
    ids,
    has: (qid: string) => ids.includes(qid),
    toggle: (qid: string) => setIds(toggleSelectionTray(qid)),
    addMany: (qids: string[]) => setIds(addToSelectionTray(qids)),
    clear: () => {
      clearSelectionTray()
      setIds([])
    },
    buildHref: selectionTrayBuildHref(ids),
    limit: MAX_TRAY_ITEMS,
  }
}
