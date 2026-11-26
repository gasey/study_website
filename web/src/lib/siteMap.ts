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
 *  A destination with no `menu` never appears in a dropdown. */
export type NavMenu = 'exams' | 'subjects' | 'practice' | 'games' | 'guides' | 'community'

export type NavIconName = 'home' | 'exam' | 'library' | 'desk' | 'profile' | 'search' | 'create' | 'more'

export interface Destination {
  id: string
  path: string
  label: string
  shortLabel?: string
  section: DestinationSection
  blurb: string
  surfaces: DestinationSurface[]
  menu?: NavMenu
  icon?: NavIconName
  keywords?: string
  minRole?: 'staff' | 'owner'
}

export const SITE_MAP: readonly Destination[] = [
  // Core Student Study-Loop desktop nav (6 items: Home · Exams · Subjects · Practice · Tools & Guides · Community)
  {
    id: 'home',
    path: '/home',
    label: 'Home',
    section: 'study',
    blurb: 'Today’s study plan, tracked exams, focus subjects and live community pulse.',
    surfaces: ['nav', 'tabs', 'index', 'quickfind'],
    icon: 'home',
    keywords: 'today study dashboard feed overview',
  },
  {
    id: 'exams',
    path: '/exams',
    label: 'Exams',
    section: 'study',
    blurb: 'MPSC UDC, LDC, Combined Prelims, Group B, MES and departmental exam booklets.',
    surfaces: ['nav', 'tabs', 'index', 'quickfind'],
    menu: 'exams',
    icon: 'exam',
    keywords: 'udc ldc mcs prelims group-b mes lde syllabus',
  },
  {
    id: 'library',
    path: '/library',
    label: 'Subjects',
    section: 'study',
    blurb: 'Subject-wise exam books and concept shelves across English, GK/GS, Math, Reasoning and Mizo.',
    surfaces: ['nav', 'tabs', 'index', 'quickfind'],
    menu: 'subjects',
    icon: 'library',
    keywords: 'english arithmetic reasoning mizo gk subjects taxonomy books',
  },
  {
    id: 'practice',
    path: '/practice',
    label: 'Practice & Mock',
    shortLabel: 'Practice',
    section: 'practice',
    blurb: 'Guided 50-by-50 & Step-by-Step Practice with instant explanations and Full-Paper Mocks.',
    surfaces: ['nav', 'tabs', 'index', 'quickfind'],
    menu: 'practice',
    icon: 'desk',
    keywords: 'mock test timed untimed quiz questions',
  },
  {
    id: 'games',
    path: '/games',
    label: 'Games',
    section: 'practice',
    blurb: 'Finna Quest 16-bit RPG, Daily Five, Weekly Cup, 1v1 Duels, Speed Sprint and Leaderboards.',
    surfaces: ['nav', 'index', 'quickfind'],
    menu: 'games',
    icon: 'desk',
    keywords: 'games play finna quest rpg daily five weekly cup duel speed gauntlet leaderboard',
  },
  {
    id: 'guides',
    path: '/guides',
    label: 'Tools & Guides',
    section: 'guides',
    blurb: 'Edited concept guides, interactive Atlas, Chronicle timeline, India Stats and Study Desk.',
    surfaces: ['nav', 'index', 'quickfind'],
    menu: 'guides',
    icon: 'library',
    keywords: 'reading codex polity quick revision english notes handbook tools',
  },
  {
    id: 'community',
    path: '/community',
    label: 'Community',
    section: 'community',
    blurb: 'Study notes, question doubts, creators and community-written materials.',
    surfaces: ['nav', 'index', 'quickfind'],
    menu: 'community',
    keywords: 'discussions doubts posts creators contributors feed',
  },

  // Exams dropdown items
  {
    id: 'papers',
    path: '/past-papers',
    label: 'Past papers',
    section: 'study',
    blurb: 'Original past papers, question booklets and written papers organised by year.',
    surfaces: ['index', 'quickfind'],
    menu: 'exams',
    keywords: 'pdf original past paper booklets archive lde',
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
  {
    id: 'subject-books',
    path: '/exams?exam_filter=subjects',
    label: 'Subject-wise exam books',
    section: 'study',
    blurb: 'Hardcover all-exam volumes for GK/GS, English, Mathematics, Reasoning and Mizo.',
    surfaces: ['index', 'quickfind'],
    menu: 'exams',
    keywords: 'subject wise exam books cross exam volumes',
  },

  // Subjects dropdown items (direct hardcover subject-wise exam volumes)
  {
    id: 'subject-gk-gs',
    path: '/subjects/gk-gs',
    label: 'General Knowledge & Studies',
    section: 'study',
    blurb: 'Polity, history, economy, geography and Mizoram GK across every exam.',
    surfaces: ['index', 'quickfind'],
    menu: 'subjects',
    keywords: 'gk gs polity history geography economy mizoram',
  },
  {
    id: 'subject-english',
    path: '/subjects/english',
    label: 'English',
    section: 'study',
    blurb: 'Grammar, comprehension, idioms, vocabulary and writing from real papers.',
    surfaces: ['index', 'quickfind'],
    menu: 'subjects',
    keywords: 'english grammar comprehension vocabulary idioms',
  },
  {
    id: 'subject-mathematics',
    path: '/subjects/mathematics',
    label: 'Mathematics & Arithmetic',
    section: 'study',
    blurb: 'Quantitative aptitude, percentages, ratios, algebra and worked methods.',
    surfaces: ['index', 'quickfind'],
    menu: 'subjects',
    keywords: 'math mathematics arithmetic quantitative aptitude',
  },
  {
    id: 'subject-reasoning',
    path: '/subjects/reasoning',
    label: 'Reasoning & Aptitude',
    section: 'study',
    blurb: 'Logical sequences, syllogisms, coding and analytical puzzles across exams.',
    surfaces: ['index', 'quickfind'],
    menu: 'subjects',
    keywords: 'reasoning logic csat aptitude puzzles',
  },
  {
    id: 'subject-mizo',
    path: '/subjects/mizo',
    label: 'Mizo',
    section: 'study',
    blurb: 'Mizo language, literature, proverbs, grammar and heritage questions.',
    surfaces: ['index', 'quickfind'],
    menu: 'subjects',
    keywords: 'mizo language literature proverbs culture',
  },
  {
    id: 'vocabulary',
    path: '/vocabulary',
    label: 'Vocabulary Builder',
    section: 'study',
    blurb: 'Spaced-repetition vocabulary decks, idioms, synonyms, antonyms and reviewed word cards.',
    surfaces: ['index', 'quickfind', 'quick'],
    menu: 'subjects',
    keywords: 'vocabulary words idioms synonyms antonyms one word substitution spaced review leitner decks',
  },

  // Practice dropdown items
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
  // Games dropdown items
  {
    id: 'quest',
    path: '/games/quest',
    label: 'Finna Quest RPG',
    section: 'practice',
    blurb: 'Battle pixel-art Realm Guardians across 12 floors, Boss fights & Daily 10-Q Gauntlet.',
    surfaces: ['index', 'quickfind'],
    menu: 'games',
    keywords: 'finna quest rpg boss expedition endless tower daily gauntlet pixel game',
  },
  {
    id: 'games-daily',
    path: '/games?mode=daily',
    label: 'Daily Five',
    section: 'practice',
    blurb: 'Today’s 5-question ranked sprint — keep your daily streak alive on the board.',
    surfaces: ['index', 'quickfind'],
    menu: 'games',
    keywords: 'daily five sprint streak ranked game',
  },
  {
    id: 'games-cup',
    path: '/games?mode=cup',
    label: 'Weekly Cup',
    section: 'practice',
    blurb: 'Weekend 15-question competitive tournament across MPSC & Mizoram recruitment.',
    surfaces: ['index', 'quickfind'],
    menu: 'games',
    keywords: 'weekly cup tournament weekend ranked leaderboard',
  },
  {
    id: 'games-duel',
    path: '/games?mode=duel',
    label: '1v1 Duel & Party',
    section: 'practice',
    blurb: 'Challenge a friend or live opponent in fast-paced 20-second quiz rounds.',
    surfaces: ['index', 'quickfind'],
    menu: 'games',
    keywords: 'duel party room multiplayer friends quiz',
  },
  {
    id: 'games-speed',
    path: '/games?mode=speed',
    label: 'Speed & Gauntlet',
    section: 'practice',
    blurb: '60-second Speed Sprint and 20-gate 3-life Gauntlet survival runs.',
    surfaces: ['index', 'quickfind'],
    menu: 'games',
    keywords: 'speed sprint gauntlet survival blitz',
  },
  {
    id: 'games-standings',
    path: '/profile/rewards',
    label: 'Leaderboards & Quests',
    section: 'you',
    blurb: 'Weekly XP divisions, Daily Five standings, daily quests and reward redemptions.',
    surfaces: ['index', 'quickfind'],
    menu: 'games',
    keywords: 'leaderboard standings weekly xp league quests rewards',
  },
  {
    id: 'bank',
    path: '/bank',
    label: 'Question bank chooser',
    section: 'study',
    blurb: 'Power-user chooser across the full corpus — filter by exam, subject, paper or year.',
    surfaces: ['index', 'quickfind'],
    menu: 'practice',
    keywords: 'browse search filter mcq written essay descriptive',
  },

  // Tools & Guides dropdown items
  {
    id: 'atlas',
    path: '/atlas',
    label: 'Interactive Atlas',
    section: 'guides',
    blurb: 'Interactive geography chapters, Mizoram and India map layers and drills.',
    surfaces: ['index', 'quickfind'],
    menu: 'guides',
    keywords: 'maps geography mizoram india districts',
  },
  {
    id: 'chronicle',
    path: '/chronicle',
    label: 'History Chronicle',
    section: 'guides',
    blurb: 'Historical dates, constitutional timelines and linked past-paper questions.',
    surfaces: ['index', 'quickfind'],
    menu: 'guides',
    keywords: 'history timeline important days dates events',
  },
  {
    id: 'stats',
    path: '/stats',
    label: 'India & Global Stats',
    section: 'guides',
    blurb: 'India and Mizoram official statistics, global rankings and the Economic Survey.',
    surfaces: ['index', 'quickfind'],
    menu: 'guides',
    keywords: 'hdi economic survey rankings data india mizoram indicators',
  },
  {
    id: 'desk',
    path: '/desk',
    label: 'Study Desk',
    section: 'you',
    blurb: 'Your personal notes, bookmarks, focus timer and private 6-seat study rooms.',
    surfaces: ['index', 'quickfind', 'quick'],
    menu: 'guides',
    icon: 'desk',
    keywords: 'study desk rooms notes bookmarks pomodoro focus review circle',
  },
  {
    id: 'index',
    path: '/index',
    label: 'All pages',
    section: 'study',
    blurb: 'Compact directory of every study surface, tool and account page on Finna.',
    surfaces: ['index', 'quickfind'],
    menu: 'guides',
    keywords: 'sitemap directory all pages tools more index',
  },

  // Community dropdown items
  {
    id: 'community-doubts',
    path: '/community?tab=questions',
    label: 'Questions & Doubts',
    section: 'community',
    blurb: 'Discuss tricky past-paper questions and help peers clear doubts.',
    surfaces: ['index', 'quickfind'],
    menu: 'community',
    keywords: 'doubts questions discussions help',
  },
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
    id: 'creators',
    path: '/creators',
    label: 'Find learners & profiles',
    section: 'community',
    blurb: 'Search public learner profiles, pixel heroes, target exams, scores & published notes.',
    surfaces: ['index', 'quickfind'],
    menu: 'community',
    keywords: 'find learners profiles search users people leaderboard creators handles authors contributors',
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

  // Personal / You surfaces
  {
    id: 'vault',
    path: '/vault',
    label: 'My Vault',
    section: 'you',
    blurb: 'Your animated personal question safe: save bank items, Pro favorites, custom image questions, drills and shareable packs.',
    surfaces: ['index', 'quickfind'],
    icon: 'library',
    keywords: 'vault safe personal question bank save favorite craft custom flashcard share',
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

/** Dropdown contents for a desktop nav item, in manifest order (excludes the parent trigger itself). */
export function menuFor(menu: NavMenu): Destination[] {
  return SITE_MAP.filter((d) => d.menu === menu && !d.surfaces.includes('nav'))
}
