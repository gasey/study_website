import { useCallback, useEffect, useState } from 'react'

export type HomePreset = 'minimal' | 'balanced' | 'everything'

export type HomeWidgetId =
  | 'kpi'
  | 'today'
  | 'leaderboard'
  | 'games'
  | 'discover'
  | 'pulse'
  | 'return'
  | 'tracked_exams'
  | 'subjects'
  | 'feed'
  | 'vault'
  | 'calendar'
  | 'shortcuts'
  | 'desk'
  | 'quests'
  | 'explore'

export interface HomePreferences {
  preset: HomePreset
  hidden: HomeWidgetId[]
  onboarded: boolean
}

export interface HomeWidgetMeta {
  id: HomeWidgetId
  label: string
  description: string
  group: 'top' | 'left' | 'community' | 'right'
}

export const HOME_WIDGET_CATALOG: readonly HomeWidgetMeta[] = [
  // Top & Centre
  {
    id: 'kpi',
    label: 'Study snapshot strip',
    description: '3-tile weekly answers, 7-day accuracy & streak bar at the top.',
    group: 'top',
  },
  {
    id: 'return',
    label: 'Pick up where you left off',
    description: 'Resume your latest unfinished mock or practice set.',
    group: 'top',
  },
  {
    id: 'tracked_exams',
    label: 'Tracked exams overview',
    description: 'Multi-exam progress summary cards in the centre stream.',
    group: 'top',
  },
  {
    id: 'subjects',
    label: 'Subjects & focus',
    description: 'Your focus subject books and topic accuracy breakdown.',
    group: 'top',
  },
  {
    id: 'feed',
    label: 'Community feed preview',
    description: 'Latest learner questions and discussions inside Overview.',
    group: 'top',
  },
  {
    id: 'vault',
    label: 'Personal Question Vault',
    description: 'Quick-access card for your saved & crafted questions.',
    group: 'top',
  },
  // Left column
  {
    id: 'today',
    label: 'Today’s study plan',
    description: 'Daily review count and suggested next step.',
    group: 'left',
  },
  {
    id: 'leaderboard',
    label: 'Live leaderboard',
    description: 'Weekly XP, Daily Five and Weekly Cup standings.',
    group: 'community',
  },
  {
    id: 'games',
    label: 'Popular games',
    description: 'Finna Quest RPG, Daily Five, Weekly Cup & 1v1 Duel.',
    group: 'left',
  },
  {
    id: 'discover',
    label: 'Discover learners & notes',
    description: 'Rotating suggestions of learners and study notes for you.',
    group: 'community',
  },
  {
    id: 'pulse',
    label: '7-day pulse chart',
    description: 'Mini daily activity bar chart and quick stats.',
    group: 'left',
  },
  // Right column
  {
    id: 'quests',
    label: 'Today’s quests',
    description: 'Daily learning goals and reward milestones.',
    group: 'right',
  },
  {
    id: 'shortcuts',
    label: 'Study shortcuts',
    description: 'Quick links to Revision, Missed questions, Papers & Guides.',
    group: 'right',
  },
  {
    id: 'calendar',
    label: 'Study & exam calendar',
    description: 'Compact monthly calendar with practice dots and exam dates.',
    group: 'right',
  },
  {
    id: 'desk',
    label: 'Study desk card',
    description: 'Launcher for your personal desk, notes and study rooms.',
    group: 'right',
  },
  {
    id: 'explore',
    label: 'Explore noticeboard',
    description: 'Spotlight deck of additional Finna tools and features.',
    group: 'right',
  },
] as const

export const HOME_WIDGET_IDS: readonly HomeWidgetId[] = HOME_WIDGET_CATALOG.map((w) => w.id)
const WIDGET_SET = new Set<string>(HOME_WIDGET_IDS)

export const PRESET_HIDDEN: Record<HomePreset, HomeWidgetId[]> = {
  minimal: [
    'kpi',
    'leaderboard',
    'games',
    'pulse',
    'tracked_exams',
    'feed',
    'vault',
    'calendar',
    'shortcuts',
    'desk',
    'explore',
  ],
  balanced: [
    'pulse',
    'feed',
    'vault',
    'calendar',
    'desk',
  ],
  everything: [],
}

export const PRESET_DETAILS: readonly {
  id: HomePreset
  title: string
  badge?: string
  summary: string
}[] = [
  {
    id: 'minimal',
    title: 'Minimal',
    summary: 'Calmest view: Exam hero, Continue, Focus subjects, Discover & Today’s quests.',
  },
  {
    id: 'balanced',
    title: 'Balanced',
    badge: 'Recommended',
    summary: 'Clean 4-column home with Explore deck (Stats, Atlas, Guides), Discover, Leaderboard & Games.',
  },
  {
    id: 'everything',
    title: 'Everything',
    summary: 'Show all widgets, including Calendar, 7-day pulse, Study desk, Community feed & Vault.',
  },
] as const

const STORAGE_KEY = 'finna-home-prefs-v3'
const LEGACY_STORAGE_KEYS = ['finna-home-prefs-v2', 'finna-home-prefs-v1'] as const
const CHANGE_EVENT = 'finna-home-prefs-change'

export function widgetLabel(id: HomeWidgetId): string {
  return HOME_WIDGET_CATALOG.find((w) => w.id === id)?.label || id
}

export function normalizeHidden(items: unknown): HomeWidgetId[] {
  if (!Array.isArray(items)) return []
  const seen = new Set<string>()
  const out: HomeWidgetId[] = []
  for (const item of items) {
    if (typeof item === 'string' && WIDGET_SET.has(item) && !seen.has(item)) {
      seen.add(item)
      out.push(item as HomeWidgetId)
    }
  }
  return out
}

export function defaultHomePrefs(): HomePreferences {
  return {
    preset: 'balanced',
    hidden: [...PRESET_HIDDEN.balanced],
    onboarded: false,
  }
}

export function readLocalHomePrefs(): HomePreferences {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<HomePreferences>
      const preset: HomePreset =
        parsed.preset === 'minimal' || parsed.preset === 'balanced' || parsed.preset === 'everything'
          ? parsed.preset
          : 'balanced'
      const hidden =
        Array.isArray(parsed.hidden) ? normalizeHidden(parsed.hidden) : [...PRESET_HIDDEN[preset]]
      return {
        preset,
        hidden,
        onboarded: Boolean(parsed.onboarded),
      }
    }
    for (const legacyKey of LEGACY_STORAGE_KEYS) {
      const legacyRaw = localStorage.getItem(legacyKey)
      if (legacyRaw) {
        const parsed = JSON.parse(legacyRaw) as Partial<HomePreferences>
        const preset: HomePreset =
          parsed.preset === 'minimal' || parsed.preset === 'balanced' || parsed.preset === 'everything'
            ? parsed.preset
            : 'balanced'
        const hidden = (
          Array.isArray(parsed.hidden) ? normalizeHidden(parsed.hidden) : [...PRESET_HIDDEN[preset]]
        ).filter((id) => id !== 'discover' && id !== 'explore')
        return {
          preset,
          hidden,
          onboarded: Boolean(parsed.onboarded),
        }
      }
    }
    return defaultHomePrefs()
  } catch {
    return defaultHomePrefs()
  }
}

export function writeLocalHomePrefs(prefs: HomePreferences) {
  const clean: HomePreferences = {
    preset: prefs.preset,
    hidden: normalizeHidden(prefs.hidden),
    onboarded: Boolean(prefs.onboarded),
  }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(clean))
  } catch {
    /* ignore storage quota errors */
  }
  window.dispatchEvent(new Event(CHANGE_EVENT))
}

interface ServerHomePrefsResponse {
  exists: boolean
  preset: HomePreset
  hidden: string[]
  onboarded: boolean
}

export async function fetchServerHomePrefs(): Promise<ServerHomePrefsResponse | null> {
  try {
    const res = await fetch('/api/me/home-preferences', {
      credentials: 'same-origin',
      headers: { Accept: 'application/json' },
    })
    if (!res.ok) return null
    return (await res.json()) as ServerHomePrefsResponse
  } catch {
    return null
  }
}

export async function pushServerHomePrefs(prefs: HomePreferences): Promise<boolean> {
  try {
    const res = await fetch('/api/me/home-preferences', {
      method: 'PUT',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        preset: prefs.preset,
        hidden: normalizeHidden(prefs.hidden),
        onboarded: Boolean(prefs.onboarded),
      }),
    })
    return res.ok
  } catch {
    return false
  }
}

export async function syncHomePrefsWithServer(authenticated: boolean): Promise<HomePreferences> {
  const local = readLocalHomePrefs()
  if (!authenticated) return local
  const remote = await fetchServerHomePrefs()
  if (!remote) return local
  if (remote.exists) {
    const merged: HomePreferences = {
      preset:
        remote.preset === 'minimal' || remote.preset === 'balanced' || remote.preset === 'everything'
          ? remote.preset
          : 'balanced',
      hidden: normalizeHidden(remote.hidden),
      onboarded: Boolean(remote.onboarded),
    }
    writeLocalHomePrefs(merged)
    return merged
  }
  // Signed-in user has no server row yet: migrate guest setup once if already completed locally.
  if (local.onboarded) {
    void pushServerHomePrefs(local)
  }
  return local
}

export function useHomePrefs(authenticated = false) {
  const [prefs, setPrefs] = useState<HomePreferences>(() => readLocalHomePrefs())

  useEffect(() => {
    const sync = () => setPrefs(readLocalHomePrefs())
    window.addEventListener(CHANGE_EVENT, sync)
    window.addEventListener('storage', sync)
    return () => {
      window.removeEventListener(CHANGE_EVENT, sync)
      window.removeEventListener('storage', sync)
    }
  }, [])

  const save = useCallback(
    (next: HomePreferences) => {
      const clean: HomePreferences = {
        preset: next.preset,
        hidden: normalizeHidden(next.hidden),
        onboarded: Boolean(next.onboarded),
      }
      setPrefs(clean)
      writeLocalHomePrefs(clean)
      if (authenticated) {
        void pushServerHomePrefs(clean)
      }
    },
    [authenticated],
  )

  const hiddenSet = new Set<HomeWidgetId>(prefs.hidden)
  const isHidden = useCallback((id: HomeWidgetId) => hiddenSet.has(id), [prefs.hidden])

  const hideWidget = useCallback(
    (id: HomeWidgetId) => {
      const nextHidden = prefs.hidden.includes(id) ? prefs.hidden : [...prefs.hidden, id]
      save({ ...prefs, hidden: nextHidden })
    },
    [prefs, save],
  )

  const showWidget = useCallback(
    (id: HomeWidgetId) => {
      const nextHidden = prefs.hidden.filter((item) => item !== id)
      save({ ...prefs, hidden: nextHidden })
    },
    [prefs, save],
  )

  const toggleWidget = useCallback(
    (id: HomeWidgetId) => {
      const nextHidden = prefs.hidden.includes(id)
        ? prefs.hidden.filter((item) => item !== id)
        : [...prefs.hidden, id]
      save({ ...prefs, hidden: nextHidden })
    },
    [prefs, save],
  )

  const applyPreset = useCallback(
    (preset: HomePreset, onboarded = prefs.onboarded) => {
      save({
        preset,
        hidden: [...PRESET_HIDDEN[preset]],
        onboarded,
      })
    },
    [prefs.onboarded, save],
  )

  return {
    prefs,
    hiddenSet,
    isHidden,
    save,
    hideWidget,
    showWidget,
    toggleWidget,
    applyPreset,
  }
}
