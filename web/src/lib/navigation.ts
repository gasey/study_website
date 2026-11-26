import { destinationsForSurface } from './siteMap'

/** Phone primary tabs generated directly from `siteMap.ts`:
 *  Five student-loop tabs: Home · Exams · Subjects · Practice · Me. */
const TAB_ORDER = ['home', 'exams', 'library', 'practice', 'profile']
export const PRIMARY_NAV = destinationsForSurface('tabs')
  .slice()
  .sort((a, b) => TAB_ORDER.indexOf(a.id) - TAB_ORDER.indexOf(b.id))
  .map((d) => ({
    to: d.path,
    label: d.shortLabel || d.label,
    icon: d.icon || 'home',
  }))

export function primarySection(path: string) {
  if (/^\/(home|feed|community)(\/|$)/.test(path) && path !== '/community/questions') return '/home'
  if (path === '/onboarding' || /^\/(exams|group-b|past-papers|calendar)(\/|$)/.test(path)) return '/exams'
  if (/^\/(library|subjects|guides|materials|atlas|chronicle|stats|english|mizo|arithmetic|vocabulary|essay)(\/|$)/.test(path)) return '/library'
  if (/^\/(practice|bank|tests|revise|games|vault|results)(\/|$)/.test(path) || path === '/community/questions') return '/practice'
  return '/profile'
}

export function focusedSession(path: string, search = '') {
  return (
    ((path === '/revise' || path === '/onboarding') && new URLSearchParams(search).has('session')) ||
    (path !== '/games/quest' && path !== '/games/blocks' && /^\/(games|trail)\/[^/]+$/.test(path)) ||
    /^\/exams\/[^/]+\/mock$/.test(path) ||
    /^\/tests\/[^/]+\/take$/.test(path)
  )
}

export function mobileScreen(path: string) {
  if (path === '/home' || path === '/feed') return 'home'
  if (path === '/community') return 'feed'
  if (path === '/index') return 'index'
  if (path === '/guides' || path.startsWith('/guides/')) return 'guides'
  if (path === '/practice') return 'practice'
  if (path === '/practice/build') return 'mock-builder'
  if (/^\/exams\/[^/]+\/mock$|^\/tests\/[^/]+\/take$/.test(path)) return 'mock-player'
  if (path.startsWith('/results/')) return 'mock-result'
  if (path.startsWith('/exams/') || path === '/group-b') return 'exam-detail'
  if (path === '/exams') return 'exams'
  if (path === '/library') return 'library'
  if (/^\/(english|arithmetic|mizo|library\/)/.test(path)) return 'module'
  if (path === '/bank') return 'practice'
  if (path.startsWith('/bank/')) return 'question'
  if (path.startsWith('/desk')) return 'desk'
  if (path === '/inbox') return 'inbox'
  if (path.startsWith('/creators/')) return 'creator'
  if (path === '/games/quest') return 'quest'
  if (path === '/games/blocks') return 'blocks'
  if (path.startsWith('/games/')) return 'game-player'
  if (path === '/games') return 'games'
  if (path === '/profile') return 'me'
  if (path.startsWith('/account/')) return 'settings'
  if (path === '/login' || path === '/join' || path === '/google/finish') return 'sign-in'
  if (path === '/onboarding') return 'check-in'
  if (path === '/revise') return 'revise'
  return path.split('/')[1] || 'landing'
}

export function mobileTitle(path: string) {
  return (
    (
      {
        'check-in': 'Getting started',
        home: 'Home',
        feed: 'Community',
        exams: 'Exams',
        guides: 'Guides',
        index: 'Index',
        library: 'Subjects',
        module: 'Subjects',
        'exam-detail': 'Your exam',
        practice: 'Practice',
        question: 'Question',
        desk: 'Desk',
        inbox: 'Inbox',
        creator: 'Creator',
        games: 'Play',
        quest: 'Finna Quest',
        blocks: 'Finna Blocks',
        'game-player': 'Game',
        me: 'Me',
        settings: 'Account',
        'sign-in': 'Sign in',
        revise: 'Revise',
        'mock-builder': 'Build a test',
        'mock-player': 'Timed paper',
        'mock-result': 'Your result',
        atlas: 'Atlas',
        chronicle: 'Chronicle',
        stats: 'Stats',
        create: 'Create',
        'past-papers': 'Papers',
        rewards: 'Rewards',
        tests: 'Shared tests',
        vocabulary: 'Vocabulary',
        essay: 'Essay',
      } as Record<string, string>
    )[mobileScreen(path)] || 'Finna'
  )
}
