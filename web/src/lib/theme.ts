import { useEffect, useState } from 'react'

export type StudyTheme = 'paper' | 'focus' | 'night'

export const STUDY_THEMES: readonly {
  id: StudyTheme
  label: string
  shortLabel: string
  icon: string
  description: string
}[] = [
  {
    id: 'paper',
    label: 'Light',
    shortLabel: 'Light',
    icon: '☀',
    description: 'Finna light theme',
  },
  {
    id: 'night',
    label: 'Dark',
    shortLabel: 'Dark',
    icon: '☾',
    description: 'Finna dark theme',
  },
] as const

const STORAGE_KEY = 'ism-study-theme'
const EVENT_NAME = 'ism-theme-change'

export function getStudyTheme(): StudyTheme {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      const saved = window.localStorage.getItem(STORAGE_KEY)
      if (saved === 'focus') return 'paper'
      if (saved === 'paper' || saved === 'night') return saved
    }
    if (typeof document !== 'undefined' && document.documentElement) {
      const attr = document.documentElement.getAttribute('data-theme')
      if (attr === 'paper' || attr === 'focus' || attr === 'night') return attr
    }
  } catch {
    // Ignore storage access errors in restricted or test environments
  }
  return 'paper'
}

export function applyStudyTheme(theme: StudyTheme): void {
  try {
    if (typeof document !== 'undefined' && document.documentElement) {
      document.documentElement.setAttribute('data-design', 'finna')
      document.documentElement.setAttribute('data-theme', theme === 'focus' ? 'paper' : theme)
      document.documentElement.classList.toggle('dark', theme === 'night')
    }
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem(STORAGE_KEY, theme)
    }
    if (typeof window !== 'undefined' && typeof CustomEvent !== 'undefined' && window.dispatchEvent) {
      window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail: theme }))
    }
  } catch {
    // Ignore DOM/storage errors in headless test runners
  }
}

export function cycleStudyTheme(current?: StudyTheme): StudyTheme {
  const active = current ?? getStudyTheme()
  const order: StudyTheme[] = ['paper', 'night']
  const next = order[(order.indexOf(active) + 1) % order.length]
  applyStudyTheme(next)
  return next
}

export function useStudyTheme(): [StudyTheme, (next: StudyTheme) => void, () => void] {
  const [theme, setThemeState] = useState<StudyTheme>(() => getStudyTheme())

  useEffect(() => {
    const initial = getStudyTheme()
    setThemeState(initial)
    if (typeof document !== 'undefined' && document.documentElement && !document.documentElement.getAttribute('data-theme')) {
      document.documentElement.setAttribute('data-theme', initial)
      document.documentElement.classList.toggle('dark', initial === 'night')
    }
    if (typeof window === 'undefined' || !window.addEventListener) return
    const sync = () => setThemeState(getStudyTheme())
    window.addEventListener(EVENT_NAME, sync)
    window.addEventListener('storage', sync)
    return () => {
      window.removeEventListener(EVENT_NAME, sync)
      window.removeEventListener('storage', sync)
    }
  }, [])

  const setTheme = (next: StudyTheme) => {
    setThemeState(next)
    applyStudyTheme(next)
  }

  const cycle = () => {
    const next = cycleStudyTheme(theme)
    setThemeState(next)
  }

  return [theme, setTheme, cycle]
}
