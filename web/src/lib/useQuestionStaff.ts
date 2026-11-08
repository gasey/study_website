import {useEffect, useState} from 'react'
import {accountContext} from './accountContext'
import {reviewSession} from './review'

/** Presentation only; the editorial APIs enforce subject permissions. */
export function useQuestionStaff() {
  const [staff, setStaff] = useState(false)
  useEffect(() => {
    let live = true, version = 0
    const load = async () => {
      const run = ++version
      setStaff(false)
      try {
        const account = await accountContext()
        if (!account.authenticated) return
        const session = await reviewSession()
        if (live && run === version) setStaff(session.grants.length > 0)
      } catch { /* Public actions remain available when staff access cannot load. */ }
    }
    void load()
    window.addEventListener('ism-auth-change', load)
    return () => { live = false; version++; window.removeEventListener('ism-auth-change', load) }
  }, [])
  return staff
}
