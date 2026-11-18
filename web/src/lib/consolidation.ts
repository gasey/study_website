/** Old bookmarks retain their filters and saved sessions at the owning surface. */
export function consolidatedDestination(path: string, search = '', hash = '') {
  const params = new URLSearchParams(search)
  let target = path
  if (path === '/mistakes') { target = '/revise'; params.set('tab', 'queue') }
  if (path === '/revision') {
    target = '/revise'
    if (params.get('session')?.startsWith('rev_')) params.set('tab', 'legacy')
    else { params.delete('session'); params.delete('tab') }
  }
  if (path === '/vocabulary') { target = '/revise'; params.set('tab', 'vocabulary') }
  if (path === '/important-days') {
    target = '/chronicle'
    if (!params.has('view')) params.set('view', 'list')
  }
  if (path === '/notifications' || path === '/contribute/notifications') target = '/inbox'
  if (path === '/duel') { target = '/games'; params.set('mode', 'duel') }
  return { pathname: target, search: params.size ? '?' + params : '', hash }
}

/** Legacy daily sessions are resumable, but no longer start a second daily plan. */
export function legacyRevisionLink(id: string) {
  return '/revise?' + new URLSearchParams({tab: 'legacy', session: id})
}
