import type { Question } from './api'

export type QuestRealmId =
  | 'english'
  | 'geography'
  | 'computer'
  | 'history'
  | 'polity'
  | 'science'
  | 'economy'
  | 'maths'
  | 'mizo'

export type QuestModeId = 'expedition' | 'endless' | 'daily'

export type PowerUpId = 'shield' | 'freeze' | 'overdrive' | 'reroll' | 'heal'

export interface QuestRealm {
  id: QuestRealmId
  name: string
  short: string
  icon: string
  accent: string
  tint: string
  guardian: string
  guardianTitle: string
  bossName: string
  apiSubjects: string[]
  defaultEnabled: boolean
  blurb: string
}

export const QUEST_REALMS: QuestRealm[] = [
  {
    id: 'english',
    name: 'English Arena',
    short: 'English',
    icon: '🪶',
    accent: '#0F766E',
    tint: '#CCFBF1',
    guardian: 'Lexicon Scout',
    guardianTitle: 'Grammar & Vocab',
    bossName: 'The Grammar Warden',
    apiSubjects: ['english'],
    defaultEnabled: true,
    blurb: 'Grammar, tenses, voice, synonyms, idioms & sentence spotting',
  },
  {
    id: 'geography',
    name: 'Geography & Mizoram',
    short: 'Geography',
    icon: '⛰️',
    accent: '#15803D',
    tint: '#DCFCE7',
    guardian: 'Ridge Ranger',
    guardianTitle: 'India, World & Mizoram',
    bossName: 'The Monsoon Titan',
    apiSubjects: ['general-studies'],
    defaultEnabled: true,
    blurb: 'Rivers, mountains, climate, biosphere & Mizoram geography',
  },
  {
    id: 'computer',
    name: 'Computer & Tech Lab',
    short: 'Computer',
    icon: '💻',
    accent: '#2563EB',
    tint: '#DBEAFE',
    guardian: 'Circuit Drone',
    guardianTitle: 'IT, OS & Office',
    bossName: 'The Silicon Sentinel',
    apiSubjects: ['computer-science'],
    defaultEnabled: true,
    blurb: 'Hardware, Windows shortcuts, MS Office, networking & SQL',
  },
  {
    id: 'history',
    name: 'History Chronicles',
    short: 'History',
    icon: '🏛️',
    accent: '#B45309',
    tint: '#FEF3C7',
    guardian: 'Relic Keeper',
    guardianTitle: 'Ancient to Freedom Struggle',
    bossName: 'The Chronos Scribe',
    apiSubjects: ['general-studies', 'general-knowledge'],
    defaultEnabled: true,
    blurb: 'Indus Valley, dynasties, 1857, freedom movement & world history',
  },
  {
    id: 'polity',
    name: 'Polity Citadel',
    short: 'Polity',
    icon: '⚖️',
    accent: '#4338CA',
    tint: '#E0E7FF',
    guardian: 'Charter Knight',
    guardianTitle: 'Constitution & Governance',
    bossName: 'The Constitution Sage',
    apiSubjects: ['general-studies'],
    defaultEnabled: true,
    blurb: 'Fundamental Rights, Parliament, Judiciary & Sixth Schedule',
  },
  {
    id: 'science',
    name: 'Science Foundry',
    short: 'Science',
    icon: '⚗️',
    accent: '#0891B2',
    tint: '#CFFAFE',
    guardian: 'Spark Construct',
    guardianTitle: 'Physics, Chem & Bio',
    bossName: 'The Alchemist Prime',
    apiSubjects: ['science'],
    defaultEnabled: true,
    blurb: 'Everyday physics, chemistry formulas, human biology & ISRO',
  },
  {
    id: 'economy',
    name: 'Economy & World GK',
    short: 'Economy & GK',
    icon: '🪙',
    accent: '#A16207',
    tint: '#FEF9C3',
    guardian: 'Mint Sentinel',
    guardianTitle: 'Banking, Budget & GK',
    bossName: 'The Treasury Oracle',
    apiSubjects: ['general-studies', 'general-knowledge'],
    defaultEnabled: true,
    blurb: 'RBI, Union Budget, GDP, static GK, awards & sports',
  },
  {
    id: 'maths',
    name: 'Maths & Reasoning',
    short: 'Maths & Logic',
    icon: '📐',
    accent: '#7E22CE',
    tint: '#F3E8FF',
    guardian: 'Cipher Golem',
    guardianTitle: 'Arithmetic & Logic',
    bossName: 'The Logic Architect',
    apiSubjects: ['mathematics', 'reasoning-and-aptitude'],
    defaultEnabled: true,
    blurb: 'Percentages, ratios, speed, series, coding & puzzles',
  },
  {
    id: 'mizo',
    name: 'Mizo Heritage',
    short: 'Mizo',
    icon: '🌿',
    accent: '#BE123C',
    tint: '#FFE4E6',
    guardian: 'Thangchhuah Scout',
    guardianTitle: 'Mizo Language & Lore',
    bossName: 'Pasaltha Lorekeeper',
    apiSubjects: ['mizo'],
    defaultEnabled: false,
    blurb: 'Opt-in realm · Mizo grammar, vocabulary & literature',
  },
]

export const DEFAULT_ENABLED_REALMS: QuestRealmId[] = QUEST_REALMS.filter(
  (r) => r.defaultEnabled,
).map((r) => r.id)

export const REALM_MAP: Record<QuestRealmId, QuestRealm> = Object.fromEntries(
  QUEST_REALMS.map((r) => [r.id, r]),
) as Record<QuestRealmId, QuestRealm>

export interface ShopItem {
  id: PowerUpId
  name: string
  icon: string
  cost: number
  desc: string
  hotkey: string
}

export const SHOP_ITEMS: ShopItem[] = [
  {
    id: 'freeze',
    name: 'Time Freeze',
    icon: '⏳',
    cost: 25,
    desc: 'Adds +15s and pauses countdown tension.',
    hotkey: 'F',
  },
  {
    id: 'reroll',
    name: 'Tactical Reroll',
    icon: '🔄',
    cost: 30,
    desc: 'Swaps the current question without losing streak.',
    hotkey: 'R',
  },
  {
    id: 'shield',
    name: 'Aegis Shield',
    icon: '🛡️',
    cost: 35,
    desc: 'Blocks your next wrong answer & protects streak.',
    hotkey: 'S',
  },
  {
    id: 'overdrive',
    name: 'Overdrive Strike',
    icon: '⚡',
    cost: 40,
    desc: 'Next correct hit deals 2× boss damage & 2× gold.',
    hotkey: 'O',
  },
  {
    id: 'heal',
    name: 'Campfire Heal',
    icon: '❤️',
    cost: 45,
    desc: 'Restores +1 Heart (up to max 3 Hearts).',
    hotkey: 'H',
  },
]

export interface QuestQuestion {
  question: Question
  realmId: QuestRealmId
}

export interface EncounterSpec {
  floor: number
  act: 1 | 2 | 3
  isBoss: boolean
  isFinalBoss: boolean
  name: string
  subtitle: string
  realmId: QuestRealmId
  maxHp: number
  roundSeconds: number
  goldReward: number
}

export interface BattleLogEntry {
  question: Question
  realmId: QuestRealmId
  chosenIndex: number | null
  correctIndex: number | null
  correct: boolean
  crit: boolean
  shielded: boolean
  explanation: string | null
  elapsedSec: number
}

export interface QuestProfile {
  xp: number
  expeditionWins: number
  bestEndlessFloor: number
  bestScore: number
  totalAnswered: number
  totalCorrect: number
  dailyStreak: number
  lastDailyDate: string | null
  lastDailyGrid: string | null
  realmXp: Partial<Record<QuestRealmId, number>>
  muted: boolean
}

const PROFILE_KEY = 'finna_quest_profile_v1'

export function emptyQuestProfile(): QuestProfile {
  return {
    xp: 0,
    expeditionWins: 0,
    bestEndlessFloor: 0,
    bestScore: 0,
    totalAnswered: 0,
    totalCorrect: 0,
    dailyStreak: 0,
    lastDailyDate: null,
    lastDailyGrid: null,
    realmXp: {},
    muted: false,
  }
}

export function loadQuestProfile(): QuestProfile {
  try {
    const raw = localStorage.getItem(PROFILE_KEY)
    if (!raw) return emptyQuestProfile()
    return { ...emptyQuestProfile(), ...JSON.parse(raw) }
  } catch {
    return emptyQuestProfile()
  }
}

export function saveQuestProfile(p: QuestProfile): void {
  try {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(p))
  } catch {
    // Private browsing / quota
  }
}

export function rankForXp(xp: number): { title: string; level: number; nextXp: number; pct: number } {
  const tiers = [
    { min: 0, title: 'Novice Scout' },
    { min: 300, title: 'Trail Seeker' },
    { min: 900, title: 'Realm Scholar' },
    { min: 2000, title: 'Citadel Warden' },
    { min: 4000, title: 'Blue Mountain Champion' },
    { min: 7500, title: 'Grand Summit Master' },
  ]
  let idx = 0
  for (let i = 0; i < tiers.length; i++) {
    if (xp >= tiers[i].min) idx = i
  }
  const cur = tiers[idx]
  const next = tiers[idx + 1]
  const pct = next
    ? Math.min(100, Math.round(((xp - cur.min) / (next.min - cur.min)) * 100))
    : 100
  return { title: cur.title, level: idx + 1, nextXp: next ? next.min : cur.min, pct }
}

/** Today's India Standard Time date key (YYYY-MM-DD) for deterministic Daily Gauntlet. */
export function todayIstKey(): string {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date())
  const get = (t: string) => parts.find((p) => p.type === t)?.value || '00'
  return `${get('year')}-${get('month')}-${get('day')}`
}

/** Strictly classify any fetched bank question into one of our 9 whitelisted realms.
 *  Returns null for any specialist/technical subject (Radiology, Nursing, Engg, Dental, etc.). */
export function classifyQuestRealm(q: Question): QuestRealmId | null {
  const subj = (q.taxonomy_subject_id || q.subject || '').toLowerCase()
  const topic = (q.taxonomy_topic_id || q.topic || '').toLowerCase()
  const stem = (q.question || '').toLowerCase()

  if (subj === 'english' || topic.startsWith('english/')) return 'english'
  if (subj === 'computer-science' || topic.startsWith('computer-science/')) return 'computer'
  if (subj === 'science' || topic.startsWith('science/')) return 'science'
  if (subj === 'mathematics' || subj === 'reasoning-and-aptitude' || topic.startsWith('mathematics/') || topic.startsWith('reasoning-and-aptitude/')) {
    return 'maths'
  }
  if (subj === 'mizo' || topic.startsWith('mizo/')) return 'mizo'

  if (subj === 'general-studies' || subj === 'general-knowledge') {
    if (topic.includes('polity') || /\b(constitution|article \d|parliament|lok sabha|rajya sabha|supreme court|governor|president|preamble|fundamental right|dpsp|sixth schedule|panchayat)\b/.test(stem)) {
      return 'polity'
    }
    if (topic.includes('geography') || topic.includes('environment') || topic.includes('mizoram') || /\b(river|mountain|himalaya|monsoon|soil|biosphere|national park|mizoram|aizawl|phawngpui|tropic of cancer|latitude|longitude)\b/.test(stem)) {
      return 'geography'
    }
    if (topic.includes('history') || topic.includes('art-and-culture') || /\b(harappa|indus valley|maurya|ashoka|gupta|mughal|sultan|plassey|1857|gandhi|congress|swadeshi|quit india|vedic|buddh|jain|dynasty|battle of)\b/.test(stem)) {
      return 'history'
    }
    if (topic.includes('indian-economy') || topic.includes('static-gk') || topic.includes('sports') || topic.includes('current-affairs') || /\b(rbi|gdp|inflation|budget|tax|gst|bank|mudra|unemployment|wto|imf|olympic|nobel|award|capital of|currency)\b/.test(stem)) {
      return 'economy'
    }
    return 'economy'
  }

  return null
}

/** Strict quality filter: clean 4-option scannable MCQs only, never specialist leaks or passages. */
export function isPlayableQuestQuestion(q: Question): boolean {
  if (q.type !== 'mcq') return false
  if (q.held || q.key_disputed || q.answer_source === 'none') return false
  if (['duplicate-options', 'unresolved-source'].includes(q.source_defect || '')) return false
  const opts = (q.options || []).filter((o): o is string => typeof o === 'string' && o.trim().length > 0)
  if (opts.length !== 4) return false
  if (!q.question || q.question.trim().length < 12 || q.question.length > 290) return false
  if (q.passage && q.passage.length > 220) return false
  if (q.figure_image_url) return false
  return true
}

/** Compute the minimal set of safe `subject_id` API calls needed for the player's selected realms. */
export function apiSubjectsForRealms(selected: QuestRealmId[]): string[] {
  const out = new Set<string>()
  for (const id of selected) {
    const realm = REALM_MAP[id]
    if (!realm) continue
    for (const s of realm.apiSubjects) out.add(s)
  }
  return [...out]
}

/** Deterministic PRNG (Mulberry32) so Daily Gauntlet draws the exact same order for everyone. */
function mulberry32(seedStr: string): () => number {
  let h = 2166136261 >>> 0
  for (let i = 0; i < seedStr.length; i++) {
    h ^= seedStr.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  let a = h >>> 0
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/** Bucket and interleave playable questions evenly across selected realms. */
export function buildQuestDeck(
  rawQuestions: Question[],
  selectedRealms: QuestRealmId[],
  seedStr: string,
): QuestQuestion[] {
  const allowed = new Set<QuestRealmId>(selectedRealms)
  const seen = new Set<string>()
  const buckets = new Map<QuestRealmId, QuestQuestion[]>()
  for (const r of selectedRealms) buckets.set(r, [])

  for (const q of rawQuestions) {
    if (seen.has(q.id)) continue
    if (!isPlayableQuestQuestion(q)) continue
    const realmId = classifyQuestRealm(q)
    if (!realmId || !allowed.has(realmId)) continue
    seen.add(q.id)
    buckets.get(realmId)!.push({ question: q, realmId })
  }

  const rng = mulberry32(seedStr)
  for (const list of buckets.values()) {
    for (let i = list.length - 1; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1))
      ;[list[i], list[j]] = [list[j], list[i]]
    }
  }

  // Round-robin interleave realms so players experience rich variety every floor
  const realmOrder = [...selectedRealms]
  for (let i = realmOrder.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1))
    ;[realmOrder[i], realmOrder[j]] = [realmOrder[j], realmOrder[i]]
  }

  const deck: QuestQuestion[] = []
  let added = true
  while (added) {
    added = false
    for (const r of realmOrder) {
      const list = buckets.get(r)
      if (list && list.length > 0) {
        deck.push(list.shift()!)
        added = true
      }
    }
  }
  return deck
}

/** Build the Guardian/Boss spec for any floor in Expedition, Endless, or Daily mode. */
export function buildEncounter(
  mode: QuestModeId,
  floor: number,
  realmId: QuestRealmId,
): EncounterSpec {
  const realm = REALM_MAP[realmId]
  if (mode === 'daily') {
    const isFinal = floor === 10
    return {
      floor,
      act: floor <= 3 ? 1 : floor <= 7 ? 2 : 3,
      isBoss: isFinal,
      isFinalBoss: isFinal,
      name: isFinal ? 'Daily Summit Guardian' : realm.guardian,
      subtitle: `${realm.name} · Round ${floor}/10`,
      realmId,
      maxHp: 1,
      roundSeconds: 18,
      goldReward: isFinal ? 35 : 15,
    }
  }

  const isBoss = floor % 4 === 0
  const isFinalBoss = mode === 'expedition' && floor === 12
  const act: 1 | 2 | 3 = floor <= 4 ? 1 : floor <= 8 ? 2 : 3

  if (isFinalBoss) {
    return {
      floor,
      act: 3,
      isBoss: true,
      isFinalBoss: true,
      name: 'The Summit Sovereign',
      subtitle: 'Final Boss · All Realms',
      realmId,
      maxHp: 5,
      roundSeconds: 15,
      goldReward: 80,
    }
  }

  if (isBoss) {
    const hp = Math.min(5, 2 + Math.ceil(floor / 4))
    return {
      floor,
      act,
      isBoss: true,
      isFinalBoss: false,
      name: realm.bossName,
      subtitle: `Act ${act} Boss · ${realm.name}`,
      realmId,
      maxHp: hp,
      roundSeconds: Math.max(12, 19 - act * 2),
      goldReward: 40 + act * 10,
    }
  }

  const maxHp = floor <= 3 ? 1 : 2
  const roundSeconds =
    mode === 'endless'
      ? Math.max(10, 20 - Math.floor((floor - 1) / 4) * 2)
      : act === 1
        ? 20
        : act === 2
          ? 16
          : 14

  return {
    floor,
    act,
    isBoss: false,
    isFinalBoss: false,
    name: realm.guardian,
    subtitle: `${realm.name} · ${realm.guardianTitle}`,
    realmId,
    maxHp,
    roundSeconds,
    goldReward: 15 + act * 5,
  }
}

export function comboMultiplier(streak: number): number {
  if (streak >= 10) return 3.0
  if (streak >= 6) return 2.5
  if (streak >= 4) return 2.0
  if (streak >= 2) return 1.5
  return 1.0
}

export function formatDailyShareCard(
  dateKey: string,
  log: BattleLogEntry[],
  score: number,
  bestStreak: number,
): string {
  const icons = log
    .map((e) => (e.crit ? '⚡' : e.correct ? '🟩' : e.shielded ? '🛡️' : '🟥'))
    .join('')
  const correct = log.filter((e) => e.correct).length
  return `⚔️ Finna Quest · Daily ${dateKey}\n${icons}\n${correct}/${log.length} · ${score.toLocaleString('en-IN')} pts · 🔥${bestStreak} streak\nPlay: https://study.hawayu.in/games/quest`
}

/** Synthesized Web Audio API arcade SFX — zero audio asset downloads, mute-safe. */
class QuestAudioEngine {
  private ctx: AudioContext | null = null

  private ensure(): AudioContext | null {
    if (typeof window === 'undefined') return null
    const AC = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    if (!AC) return null
    if (!this.ctx) this.ctx = new AC()
    if (this.ctx.state === 'suspended') {
      void this.ctx.resume().catch(() => {})
    }
    return this.ctx
  }

  private tone(freq: number, dur: number, type: OscillatorType, gainVal: number, delay = 0) {
    try {
      const ctx = this.ensure()
      if (!ctx) return
      const now = ctx.currentTime + delay
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = type
      osc.frequency.setValueAtTime(freq, now)
      gain.gain.setValueAtTime(0.001, now)
      gain.gain.exponentialRampToValueAtTime(gainVal, now + 0.015)
      gain.gain.exponentialRampToValueAtTime(0.001, now + dur)
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start(now)
      osc.stop(now + dur + 0.02)
    } catch {
      // Ignore autoplay/audio restrictions
    }
  }

  hit(muted: boolean) {
    if (muted) return
    this.tone(523.25, 0.11, 'triangle', 0.12, 0)
    this.tone(659.25, 0.14, 'triangle', 0.12, 0.07)
  }

  crit(muted: boolean) {
    if (muted) return
    this.tone(587.33, 0.09, 'square', 0.09, 0)
    this.tone(880, 0.11, 'square', 0.09, 0.06)
    this.tone(1174.66, 0.22, 'triangle', 0.14, 0.12)
  }

  shield(muted: boolean) {
    if (muted) return
    this.tone(392, 0.12, 'sine', 0.14, 0)
    this.tone(587.33, 0.22, 'sine', 0.12, 0.08)
  }

  damage(muted: boolean) {
    if (muted) return
    this.tone(220, 0.16, 'sawtooth', 0.1, 0)
    this.tone(155.56, 0.24, 'sawtooth', 0.11, 0.11)
  }

  bossDown(muted: boolean) {
    if (muted) return
    this.tone(523.25, 0.12, 'triangle', 0.14, 0)
    this.tone(659.25, 0.12, 'triangle', 0.14, 0.09)
    this.tone(783.99, 0.14, 'triangle', 0.14, 0.18)
    this.tone(1046.5, 0.34, 'triangle', 0.16, 0.27)
  }

  buy(muted: boolean) {
    if (muted) return
    this.tone(740, 0.08, 'sine', 0.1, 0)
    this.tone(987.77, 0.14, 'sine', 0.12, 0.07)
  }
}

export const questSfx = new QuestAudioEngine()
