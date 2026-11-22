/** Single navigation manifest for Finna (§VII.3.1).
 *  Every navigation surface (desktop nav, phone tabs, `/index`, ⌘K QuickFind,
 *  and Footer) reads from this manifest and from nothing else. */

export type DestinationSection =
  | 'study'
  | 'practice'
  | 'guides'
  | 'community'
  | 'you'
  | 'admin'

export type DestinationSurface = 'nav' | 'tabs' | 'quick' | 'index' | 'quickfind'

/** Which desktop nav item opens a dropdown containing this destination.
 *  A destination with no `menu` never appears in a dropdown. The nav item
 *  itself stays a real link — the chevron is a separate control, so
 *  "click Exams" still goes to /exams (§VII.3.3, revised 22 Nov 2026). */
export type NavMenu = 'exams' | 'practice' | 'guides' | 'community'

export type NavIconName = 'home' | 'exam' | 'library' | 'desk' | 'profile' | 'search' | 'create' | 'more'

export interface Destination {
  id: string
  path: string
  label: string
  section: DestinationSection
  blurb: string
  surfaces: DestinationSurface[]
  menu?: NavMenu
  icon?: NavIconName
  keywords?: string
  minRole?: 'staff' | 'owner'
}

export const SITE_MAP: readonly Destination[] = [
  // Core desktop nav (6 plain links: Exams · Papers · Practice · Guides · Community · Index)
  {
    id: 'home',
    path: '/home',
    label: 'Home',
    section: 'study',
    blurb: 'Today’s study plan, resume where you left off, weekly recap and one weak spot.',
    surfaces: ['tabs', 'index', 'quickfind'],
    icon: 'home',
    keywords: 'today study dashboard feed',
  },
  {
    id: 'exams',
    path: '/exams',
    label: 'Exams',
    section: 'study',
    blurb: 'MPSC UDC, LDC, Combined Prelims, Group B, MES and LDE syllabi and papers.',
    surfaces: ['nav', 'tabs', 'index', 'quickfind'],
    menu: 'exams',
    icon: 'exam',
    keywords: 'udc ldc mcs prelims group-b mes lde syllabus',
  },
  {
    id: 'papers',
    path: '/past-papers',
    label: 'Papers',
    section: 'study',
    blurb: 'Original past papers, question booklets and written/LDE papers by year.',
    surfaces: ['nav', 'index', 'quickfind'],
    keywords: 'pdf original past paper booklets archive lde',
  },
  {
    id: 'practice',
    path: '/practice',
    label: 'Practice',
    section: 'practice',
    blurb: 'Pick what, pick how many, and toggle the timer on or off in one flow.',
    surfaces: ['nav', 'index', 'quickfind'],
    menu: 'practice',
    keywords: 'mock test timed untimed quiz questions',
  },
  {
    id: 'guides',
    path: '/guides',
    label: 'Guides',
    section: 'guides',
    blurb: 'First-party study guides, how to use Finna, and subject reference reading.',
    surfaces: ['nav', 'tabs', 'index', 'quickfind'],
    menu: 'guides',
    icon: 'library',
    keywords: 'reading codex polity quick revision english notes handbook',
  },
  {
    id: 'community',
    path: '/community',
    label: 'Community',
    section: 'community',
    blurb: 'Study notes, question doubts, creators and community-written materials.',
    surfaces: ['nav', 'index', 'quickfind'],
    menu: 'community',
    keywords: 'discussions doubts posts creators contributors',
  },
  {
    id: 'index',
    path: '/index',
    label: 'Index',
    section: 'study',
    blurb: 'Complete directory of every study surface, tool and account page on Finna.',
    surfaces: ['nav', 'index', 'quickfind'],
    keywords: 'sitemap directory all pages tools more',
  },

  // Study surfaces
  {
    id: 'bank',
    path: '/bank',
    label: 'Question bank',
    section: 'study',
    blurb: 'Browse and filter every question in the bank, including written prompts.',
    surfaces: ['index', 'quickfind'],
    menu: 'exams',
    keywords: 'browse search filter mcq written essay descriptive',
  },
  {
    id: 'library',
    path: '/library',
    label: 'Subjects & shelves',
    section: 'study',
    blurb: 'Browse questions by subject shelf, English, Arithmetic, Mizo and topics.',
    surfaces: ['index', 'quickfind'],
    menu: 'guides',
    keywords: 'english arithmetic reasoning mizo subjects taxonomy',
  },
  {
    id: 'atlas',
    path: '/atlas',
    label: 'Atlas',
    section: 'study',
    blurb: 'Interactive geography chapters, Mizoram and India map layers and drills.',
    surfaces: ['index', 'quickfind'],
    menu: 'guides',
    keywords: 'maps geography mizoram india districts',
  },
  {
    id: 'chronicle',
    path: '/chronicle',
    label: 'Chronicle',
    section: 'study',
    blurb: 'Historical dates, timelines and linked past-paper questions.',
    surfaces: ['index', 'quickfind'],
    menu: 'guides',
    keywords: 'history timeline important days dates events',
  },
  {
    id: 'stats',
    path: '/stats',
    label: 'Stats',
    section: 'study',
    blurb: 'India and Mizoram official statistics, global rankings and the Economic Survey.',
    surfaces: ['index', 'quickfind'],
    menu: 'guides',
    keywords: 'hdi economic survey rankings data india mizoram indicators',
  },
  {
    id: 'calendar',
    path: '/calendar',
    label: 'Exam calendar',
    section: 'study',
    blurb: 'Official exam dates, notices, review forecast and your study schedule.',
    surfaces: ['index', 'quickfind'],
    menu: 'exams',
    keywords: 'dates notices news schedule notifications ics',
  },

  // Practice surfaces
  {
    id: 'practice-build',
    path: '/practice/build',
    label: 'Build a test',
    section: 'practice',
    blurb: 'Assemble a custom timed or untimed test from the bank or your selection tray.',
    surfaces: ['index', 'quickfind'],
    menu: 'practice',
    keywords: 'make test builder custom mock share',
  },
  {
    id: 'tests',
    path: '/tests',
    label: 'Shared tests',
    section: 'practice',
    blurb: 'Browse featured Finna tests and community-shared practice tests.',
    surfaces: ['index', 'quickfind'],
    menu: 'practice',
    keywords: 'shared mock test links catalog',
  },
  {
    id: 'revise',
    path: '/revise',
    label: 'Revise',
    section: 'practice',
    blurb: 'Scheduled spaced reviews, past mistakes and vocabulary drills.',
    surfaces: ['index', 'quickfind', 'quick'],
    menu: 'practice',
    keywords: 'spaced repetition leitner mistakes vocabulary due review',
  },
  {
    id: 'games',
    path: '/games',
    label: 'Play',
    section: 'practice',
    blurb: 'Daily Five, Topic Trail, duels and party games over verified questions.',
    surfaces: ['index', 'quickfind'],
    menu: 'practice',
    keywords: 'daily five topic trail duel cup party games',
  },

  // Community & content surfaces
  {
    id: 'materials',
    path: '/materials',
    label: 'From the community',
    section: 'community',
    blurb: 'User-written study notes and summaries published by learners.',
    surfaces: ['index', 'quickfind'],
    menu: 'community',
    keywords: 'community materials user notes reading',
  },
  {
    id: 'create',
    path: '/create',
    label: 'Create & contribute',
    section: 'community',
    blurb: 'Suggest a question or correction, draft community notes or build a test.',
    surfaces: ['index', 'quickfind'],
    menu: 'community',
    keywords: 'contribute submit question edit studio draft',
  },
  {
    id: 'creators',
    path: '/creators',
    label: 'Creators',
    section: 'community',
    blurb: 'Discover learners who publish notes, tests and reviewed contributions.',
    surfaces: ['index', 'quickfind'],
    menu: 'community',
    keywords: 'profiles authors contributors',
  },

  // Personal / You surfaces
  {
    id: 'desk',
    path: '/desk',
    label: 'Desk',
    section: 'you',
    blurb: 'Your personal notes, bookmarks, focus timer and private 6-seat study rooms.',
    surfaces: ['tabs', 'index', 'quickfind', 'quick'],
    icon: 'desk',
    keywords: 'study desk rooms notes bookmarks pomodoro focus review circle',
  },
  {
    id: 'profile',
    path: '/profile',
    label: 'Me',
    section: 'you',
    blurb: 'Your profile, activity stats, mastery, rewards, leaderboard and avatar.',
    surfaces: ['tabs', 'index', 'quickfind'],
    icon: 'profile',
    keywords: 'profile progress stats rewards board avatar leaderboard',
  },
  {
    id: 'inbox',
    path: '/inbox',
    label: 'Inbox',
    section: 'you',
    blurb: 'All notifications, contribution updates and room invites in one place.',
    surfaces: ['index', 'quickfind'],
    keywords: 'notifications alerts messages',
  },
  {
    id: 'account',
    path: '/account/security',
    label: 'Account & privacy',
    section: 'you',
    blurb: 'Password, sign-in security, email preferences, privacy requests and recovery.',
    surfaces: ['index', 'quickfind'],
    keywords: 'security mfa privacy export delete recovery email',
  },
  {
    id: 'plans',
    path: '/plans',
    label: 'Plans & billing',
    section: 'you',
    blurb: 'Free allowance (1 timed run/month, 50 untimed answers/day) and Pro membership.',
    surfaces: ['index', 'quickfind'],
    keywords: 'pricing membership pro billing subscription',
  },
  {
    id: 'onboarding',
    path: '/onboarding',
    label: 'Getting started',
    section: 'you',
    blurb: 'Three-step intro and optional 10-question exam check-in.',
    surfaces: ['index', 'quickfind'],
    keywords: 'intro welcome setup check-in',
  },
] as const

export const SECTION_ORDER: readonly { id: DestinationSection; title: string }[] = [
  { id: 'study', title: 'Study' },
  { id: 'practice', title: 'Practice' },
  { id: 'guides', title: 'Guides' },
  { id: 'community', title: 'Community' },
  { id: 'you', title: 'You' },
] as const

export function destinationsForSurface(surface: DestinationSurface): Destination[] {
  return SITE_MAP.filter((d) => d.surfaces.includes(surface))
}

export function destinationPath(id: string): string {
  return SITE_MAP.find((d) => d.id === id)?.path ?? '/index'
}

/** Dropdown contents for a desktop nav item, in manifest order. The nav item's
 *  own destination is excluded — clicking the label already goes there. */
export function menuFor(menu: NavMenu): Destination[] {
  return SITE_MAP.filter((d) => d.menu === menu && d.id !== menu)
}
