const KEY = 'ism.device'

/** A per-browser id used to attribute practice progress before there are
 *  real accounts. It is not a credential: it lives in localStorage, anyone
 *  can forge one, and nothing that matters may be gated on it. When accounts
 *  arrive, the signed-in user adopts this device's attempts. */
export function deviceId(): string {
  let id = localStorage.getItem(KEY)
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem(KEY, id)
  }
  return id
}
