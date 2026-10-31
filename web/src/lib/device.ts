const KEY = 'ism.device'

/** Legacy browser preference identifier. Server-issued HttpOnly guest proof
 * owns progress; this UUID grants no access or transfer rights. */
export function deviceId(): string {
  let id = localStorage.getItem(KEY)
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem(KEY, id)
  }
  return id
}
