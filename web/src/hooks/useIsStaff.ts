import { useEffect, useState } from 'react'
import { accountContext } from '../lib/accountContext'
import { reviewSession } from '../lib/review'

let cachedStaff: boolean | null = null
let pendingCheck: Promise<boolean> | null = null

function resetStaffCache() {
  cachedStaff = null
  pendingCheck = null
}

if (typeof window !== 'undefined') {
  window.addEventListener('ism-auth-change', resetStaffCache)
  window.addEventListener('ism-auth-expired', resetStaffCache)
}

function checkIsStaff(): Promise<boolean> {
  if (cachedStaff !== null) return Promise.resolve(cachedStaff)
  if (pendingCheck) return pendingCheck
  pendingCheck = accountContext()
    .then(async (ctx) => {
      if (!ctx.authenticated) return false
      const session = await reviewSession()
      const hasStaffGrant = !!session.grants?.some((g) =>
        ['owner', 'admin', 'editor', 'reviewer', 'moderator', 'curator'].includes(g.role),
      )
      return hasStaffGrant
    })
    .catch(() => false)
    .then((result) => {
      cachedStaff = result
      return result
    })
    .finally(() => {
      pendingCheck = null
    })
  return pendingCheck
}

/** Lightweight cached check — returns true only for signed-in owner/staff accounts. */
export function useIsStaff(): boolean {
  const [staff, setStaff] = useState<boolean>(() => cachedStaff === true)

  useEffect(() => {
    let live = true
    void checkIsStaff().then((val) => {
      if (live) setStaff(val)
    })
    const onAuth = () => {
      resetStaffCache()
      void checkIsStaff().then((val) => {
        if (live) setStaff(val)
      })
    }
    window.addEventListener('ism-auth-change', onAuth)
    return () => {
      live = false
      window.removeEventListener('ism-auth-change', onAuth)
    }
  }, [])

  return staff
}
