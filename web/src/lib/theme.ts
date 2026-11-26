import { useEffect, useState } from 'react'

export type StudyTheme = 'library' | 'paper' | 'focus' | 'night'
export type StudyBackground = 'library' | 'grid' | 'lamp' | 'none'

export const STUDY_THEMES: readonly {
  id: Exclude<StudyTheme, 'focus'>
  label: string
  shortLabel: string
  icon: string
  description: string
}[] = [
  {
    id: 'library',
    label: 'Library',
    shortLabel: 'Library',
    icon: '❦',
    description: 'Warm cream paper & deep navy',
  },
  {
    id: 'paper',
    label: 'Light',
    shortLabel: 'Light',
    icon: '☀',
    description: 'Crisp Finna daylight',
  },
  {
    id: 'night',
    label: 'Dark',
    shortLabel: 'Dark',
    icon: '☾',
    description: 'Night Owl dark study',
  },
] as const

export const STUDY_BACKGROUNDS: readonly {
  id: StudyBackground
  label: string
  description: string
}[] = [
  {
    id: 'library',
    label: 'Library photo',
    description: 'Reading-room header band with editorial greeting',
  },
  {
    id: 'grid',
    label: 'Graph paper',
    description: 'Subtle ruled study grid across the page',
  },
  {
    id: 'lamp',
    label: 'Desk lamp',
    description: 'Warm amber & teal radial study glow',
  },
  {
    id: 'none',
    label: 'Plain',
    description: 'Solid study surface with no backdrop',
  },
] as const

const STORAGE_KEY = 'ism-study-theme-v2'
const LEGACY_KEY = 'ism-study-theme'
const BG_STORAGE_KEY = 'ism-study-bg'
const EVENT_NAME = 'ism-theme-change'
const BG_EVENT_NAME = 'ism-bg-change'

export function getStudyTheme(): StudyTheme {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      const saved = window.localStorage.getItem(STORAGE_KEY)
      if (saved === 'library' || saved === 'paper' || saved === 'night') return saved
      const legacy = window.localStorage.getItem(LEGACY_KEY)
      if (legacy === 'night') return 'night'
    }
    if (typeof document !== 'undefined' && document.documentElement) {
      const attr = document.documentElement.getAttribute('data-theme')
      if (attr === 'library' || attr === 'paper' || attr === 'night') return attr
    }
  } catch {
    // Ignore storage access errors in restricted or test environments
  }
  return 'library'
}

export function applyStudyTheme(theme: StudyTheme): void {
  const normalized: Exclude<StudyTheme, 'focus'> = theme === 'focus' ? 'paper' : theme
  try {
    if (typeof document !== 'undefined' && document.documentElement) {
      document.documentElement.setAttribute('data-design', 'finna')
      document.documentElement.setAttribute('data-theme', normalized)
      document.documentElement.classList.toggle('dark', normalized === 'night')
    }
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem(STORAGE_KEY, normalized)
      window.localStorage.setItem(LEGACY_KEY, normalized)
    }
    if (typeof window !== 'undefined' && typeof CustomEvent !== 'undefined' && window.dispatchEvent) {
      window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail: normalized }))
    }
  } catch {
    // Ignore DOM/storage errors in headless test runners
  }
}

export function cycleStudyTheme(current?: StudyTheme): StudyTheme {
  const active = current ?? getStudyTheme()
  const order: Exclude<StudyTheme, 'focus'>[] = ['library', 'paper', 'night']
  const idx = order.indexOf(active === 'focus' ? 'paper' : active)
  const next = order[(idx + 1) % order.length]
  applyStudyTheme(next)
  return next
}

export function useStudyTheme(): [StudyTheme, (next: StudyTheme) => void, () => void] {
  const [theme, setThemeState] = useState<StudyTheme>(() => getStudyTheme())

  useEffect(() => {
    const initial = getStudyTheme()
    setThemeState(initial)
    if (typeof document !== 'undefined' && document.documentElement) {
      const normalized = initial === 'focus' ? 'paper' : initial
      document.documentElement.setAttribute('data-design', 'finna')
      document.documentElement.setAttribute('data-theme', normalized)
      document.documentElement.classList.toggle('dark', normalized === 'night')
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

export function getStudyBackground(): StudyBackground {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      const saved = window.localStorage.getItem(BG_STORAGE_KEY)
      if (saved === 'library' || saved === 'grid' || saved === 'lamp' || saved === 'none') {
        return saved
      }
    }
    if (typeof document !== 'undefined' && document.documentElement) {
      const attr = document.documentElement.getAttribute('data-bg')
      if (attr === 'library' || attr === 'grid' || attr === 'lamp' || attr === 'none') {
        return attr
      }
    }
  } catch {
    /* ignore */
  }
  return 'library'
}

export function applyStudyBackground(bg: StudyBackground): void {
  try {
    if (typeof document !== 'undefined' && document.documentElement) {
      document.documentElement.setAttribute('data-bg', bg)
    }
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem(BG_STORAGE_KEY, bg)
    }
    if (typeof window !== 'undefined' && typeof CustomEvent !== 'undefined' && window.dispatchEvent) {
      window.dispatchEvent(new CustomEvent(BG_EVENT_NAME, { detail: bg }))
    }
  } catch {
    /* ignore */
  }
}

export function useStudyBackground(): [StudyBackground, (next: StudyBackground) => void] {
  const [bg, setBgState] = useState<StudyBackground>(() => getStudyBackground())

  useEffect(() => {
    const initial = getStudyBackground()
    setBgState(initial)
    if (typeof document !== 'undefined' && document.documentElement) {
      document.documentElement.setAttribute('data-bg', initial)
    }
    if (typeof window === 'undefined' || !window.addEventListener) return
    const sync = () => setBgState(getStudyBackground())
    window.addEventListener(BG_EVENT_NAME, sync)
    window.addEventListener('storage', sync)
    return () => {
      window.removeEventListener(BG_EVENT_NAME, sync)
      window.removeEventListener('storage', sync)
    }
  }, [])

  const setBg = (next: StudyBackground) => {
    setBgState(next)
    applyStudyBackground(next)
  }

  return [bg, setBg]
}
