import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { listQuestions, submitAnswer, type Question } from '../lib/api'
import { resolveQuestionGuide } from '../lib/questionGuideLink'
import { SourceQuestionContext, SourceQuestionText } from '../components/SourceQuestionText'
import {
  apiSubjectsForRealms,
  buildEncounter,
  buildQuestDeck,
  comboMultiplier,
  DEFAULT_ENABLED_REALMS,
  formatDailyShareCard,
  loadQuestProfile,
  QUEST_REALMS,
  questSfx,
  rankForXp,
  REALM_MAP,
  saveQuestProfile,
  SHOP_ITEMS,
  todayIstKey,
  type BattleLogEntry,
  type EncounterSpec,
  type PowerUpId,
  type QuestModeId,
  type QuestProfile,
  type QuestQuestion,
  type QuestRealmId,
} from '../lib/questGame'
import '../styles/quest-game.css'

const LETTERS = ['A', 'B', 'C', 'D']

type Phase = 'lobby' | 'loading' | 'battle' | 'shop' | 'summary'

interface Inventory {
  shield: number
  freeze: number
  overdrive: number
  reroll: number
}

export default function QuestGame() {
  const [params] = useSearchParams()
  const [profile, setProfile] = useState<QuestProfile>(() => loadQuestProfile())
  const [selectedRealms, setSelectedRealms] = useState<QuestRealmId[]>(DEFAULT_ENABLED_REALMS)

  // Active run state
  const [phase, setPhase] = useState<Phase>('lobby')
  const [mode, setMode] = useState<QuestModeId>('expedition')
  const [loadError, setLoadError] = useState('')
  const [deck, setDeck] = useState<QuestQuestion[]>([])
  const [deckCursor, setDeckCursor] = useState(0)
  const [floor, setFloor] = useState(1)
  const [encounter, setEncounter] = useState<EncounterSpec | null>(null)
  const [bossHp, setBossHp] = useState(1)
  const [hearts, setHearts] = useState(3)
  const [gold, setGold] = useState(30)
  const [score, setScore] = useState(0)
  const [streak, setStreak] = useState(0)
  const [bestStreak, setBestStreak] = useState(0)
  const [inventory, setInventory] = useState<Inventory>({
    shield: 1,
    freeze: 1,
    overdrive: 0,
    reroll: 1,
  })
  const [shieldActive, setShieldActive] = useState(false)
  const [overdriveActive, setOverdriveActive] = useState(false)
  const [freezeActive, setFreezeActive] = useState(false)

  // Round state
  const [secondsLeft, setSecondsLeft] = useState(20)
  const [roundStartedAt, setRoundStartedAt] = useState(() => Date.now())
  const [checking, setChecking] = useState(false)
  const [battleError, setBattleError] = useState<string | null>(null)
  const [resolved, setResolved] = useState<{
    chosen: number | null
    correctIndex: number | null
    correct: boolean
    crit: boolean
    shielded: boolean
    explanation: string | null
    banner: string
    bannerTone: 'crit' | 'hit' | 'shield' | 'hurt'
  } | null>(null)
  const [stageAnim, setStageAnim] = useState<'none' | 'hit' | 'hurt'>('none')
  const [battleLog, setBattleLog] = useState<BattleLogEntry[]>([])
  const [victory, setVictory] = useState(false)
  const [earnedXp, setEarnedXp] = useState(0)
  const [copiedShare, setCopiedShare] = useState(false)

  const autoNextTimer = useRef<number | null>(null)
  const todayKey = useMemo(() => todayIstKey(), [])
  const rank = useMemo(() => rankForXp(profile.xp), [profile.xp])
  const currentCard = deck[deckCursor] || null

  const clearAutoTimer = useCallback(() => {
    if (autoNextTimer.current !== null) {
      window.clearTimeout(autoNextTimer.current)
      autoNextTimer.current = null
    }
  }, [])

  useEffect(() => () => clearAutoTimer(), [clearAutoTimer])

  function updateProfile(patch: Partial<QuestProfile>) {
    setProfile((prev) => {
      const next = { ...prev, ...patch }
      saveQuestProfile(next)
      return next
    })
  }

  function toggleRealm(id: QuestRealmId) {
    setSelectedRealms((prev) => {
      if (prev.includes(id)) {
        if (prev.length <= 1) return prev
        return prev.filter((r) => r !== id)
      }
      return [...prev, id]
    })
  }

  const startRun = useCallback(
    async (nextMode: QuestModeId) => {
      clearAutoTimer()
      const activeRealms =
        nextMode === 'daily' ? DEFAULT_ENABLED_REALMS : selectedRealms
      setMode(nextMode)
      setPhase('loading')
      setLoadError('')
      setBattleLog([])
      setVictory(false)
      setEarnedXp(0)
      setCopiedShare(false)
      setResolved(null)

      try {
        const subjects = apiSubjectsForRealms(activeRealms)
        const seedStr =
          nextMode === 'daily'
            ? `finna-daily-${todayKey}`
            : `finna-quest-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`
        const perSubjectLimit = subjects.length <= 2 ? 60 : subjects.length <= 4 ? 40 : 28

        const pages = await Promise.all(
          subjects.map((subject_id) =>
            listQuestions({
              pool: 'practice',
              subject_id,
              order: 'mixed',
              seed: seedStr,
              limit: perSubjectLimit,
              offset: 0,
            }).catch(() => ({ items: [] as Question[], total: 0 })),
          ),
        )

        const raw = pages.flatMap((p) => p.items)
        const built = buildQuestDeck(raw, activeRealms, seedStr)
        if (built.length < 10) {
          throw new Error(
            'Could not gather enough clean 4-option questions for that deck. Try enabling one more realm.',
          )
        }

        const firstEncounter = buildEncounter(nextMode, 1, built[0].realmId)
        setDeck(built)
        setDeckCursor(0)
        setFloor(1)
        setEncounter(firstEncounter)
        setBossHp(firstEncounter.maxHp)
        setHearts(3)
        setGold(nextMode === 'daily' ? 0 : 30)
        setScore(0)
        setStreak(0)
        setBestStreak(0)
        setInventory(
          nextMode === 'daily'
            ? { shield: 1, freeze: 1, overdrive: 0, reroll: 0 }
            : { shield: 1, freeze: 1, overdrive: 0, reroll: 1 },
        )
        setShieldActive(false)
        setOverdriveActive(false)
        setFreezeActive(false)
        setSecondsLeft(firstEncounter.roundSeconds)
        setRoundStartedAt(Date.now())
        setPhase('battle')
      } catch (e) {
        setLoadError(e instanceof Error ? e.message : 'Could not start Finna Quest.')
        setPhase('lobby')
      }
    },
    [clearAutoTimer, selectedRealms, todayKey],
  )

  // Support deep link `/games/quest?mode=daily|expedition|endless`
  useEffect(() => {
    const m = params.get('mode')
    if (m === 'daily' || m === 'expedition' || m === 'endless') {
      void startRun(m)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const finishRun = useCallback(
    (
      didWin: boolean,
      finalLog: BattleLogEntry[],
      finalScore: number,
      finalFloor: number,
      runMode: QuestModeId,
    ) => {
      clearAutoTimer()
      const correctCount = finalLog.filter((l) => l.correct).length
      const xpGain = correctCount * 20 + (didWin ? 120 : 25) + finalFloor * 8
      setVictory(didWin)
      setEarnedXp(xpGain)
      setPhase('summary')

      setProfile((prev) => {
        const nextRealmXp = { ...prev.realmXp }
        for (const entry of finalLog) {
          if (entry.correct) {
            nextRealmXp[entry.realmId] = (nextRealmXp[entry.realmId] || 0) + 15
          }
        }
        const dailyGrid =
          runMode === 'daily'
            ? finalLog
                .map((e) => (e.crit ? '⚡' : e.correct ? '🟩' : e.shielded ? '🛡️' : '🟥'))
                .join('')
            : prev.lastDailyGrid
        const nextDailyStreak =
          runMode === 'daily'
            ? prev.lastDailyDate === todayKey
              ? Math.max(1, prev.dailyStreak)
              : prev.dailyStreak + 1
            : prev.dailyStreak

        const next: QuestProfile = {
          ...prev,
          xp: prev.xp + xpGain,
          expeditionWins: prev.expeditionWins + (runMode === 'expedition' && didWin ? 1 : 0),
          bestEndlessFloor:
            runMode === 'endless'
              ? Math.max(prev.bestEndlessFloor, finalFloor)
              : prev.bestEndlessFloor,
          bestScore: Math.max(prev.bestScore, finalScore),
          totalAnswered: prev.totalAnswered + finalLog.length,
          totalCorrect: prev.totalCorrect + correctCount,
          dailyStreak: nextDailyStreak,
          lastDailyDate: runMode === 'daily' ? todayKey : prev.lastDailyDate,
          lastDailyGrid: dailyGrid,
          realmXp: nextRealmXp,
        }
        saveQuestProfile(next)
        return next
      })
    },
    [clearAutoTimer, todayKey],
  )

  const advanceAfterResolution = useCallback(
    (
      nextBossHp: number,
      nextHearts: number,
      nextScore: number,
      nextLog: BattleLogEntry[],
    ) => {
      clearAutoTimer()
      if (!encounter) return

      // Check defeat
      if (nextHearts <= 0) {
        finishRun(false, nextLog, nextScore, floor, mode)
        return
      }

      const nextIdx = (deckCursor + 1) % deck.length
      const nextCard = deck[nextIdx]

      // Daily Gauntlet: 10 fixed rounds
      if (mode === 'daily') {
        if (floor >= 10) {
          questSfx.bossDown(profile.muted)
          finishRun(true, nextLog, nextScore, 10, mode)
          return
        }
        const nf = floor + 1
        const ne = buildEncounter('daily', nf, nextCard.realmId)
        setDeckCursor(nextIdx)
        setFloor(nf)
        setEncounter(ne)
        setBossHp(ne.maxHp)
        setSecondsLeft(ne.roundSeconds)
        setRoundStartedAt(Date.now())
        setFreezeActive(false)
        setResolved(null)
        return
      }

      // Guardian / Boss still standing — draw next question against same boss
      if (nextBossHp > 0) {
        setDeckCursor(nextIdx)
        setSecondsLeft(encounter.roundSeconds)
        setRoundStartedAt(Date.now())
        setFreezeActive(false)
        setResolved(null)
        return
      }

      // Guardian defeated!
      if (mode === 'expedition' && floor >= 12) {
        questSfx.bossDown(profile.muted)
        finishRun(true, nextLog, nextScore, 12, mode)
        return
      }

      setDeckCursor(nextIdx)
      setFreezeActive(false)
      setResolved(null)

      // Open Campfire Shop after defeating any Boss (Floor 4, 8, ...)
      if (encounter.isBoss) {
        questSfx.bossDown(profile.muted)
        setPhase('shop')
        return
      }

      const nf = floor + 1
      const ne = buildEncounter(mode, nf, nextCard.realmId)
      setFloor(nf)
      setEncounter(ne)
      setBossHp(ne.maxHp)
      setSecondsLeft(ne.roundSeconds)
      setRoundStartedAt(Date.now())
    },
    [clearAutoTimer, deck, deckCursor, encounter, finishRun, floor, mode, profile.muted],
  )

  const submitPick = useCallback(
    async (chosenIndex: number | null) => {
      if (phase !== 'battle' || !currentCard || !encounter || checking || resolved) return
      setChecking(true)
      setBattleError(null)
      const elapsedSec = Math.max(0.4, (Date.now() - roundStartedAt) / 1000)

      try {
        let correct = false
        let correctIndex: number | null = null
        let explanation: string | null = null

        if (chosenIndex !== null) {
          const res = await submitAnswer(currentCard.question.id, chosenIndex, 'practice')
          correct = !!res.correct
          correctIndex = res.answer_index ?? null
          explanation = res.explanation || null
        }

        let nextHearts = hearts
        let nextBossHp = bossHp
        let nextGold = gold
        let nextScore = score
        let nextStreak = streak
        let nextBestStreak = bestStreak
        let crit = false
        let shielded = false
        let banner = ''
        let bannerTone: 'crit' | 'hit' | 'shield' | 'hurt' = 'hit'

        if (correct) {
          nextStreak = streak + 1
          nextBestStreak = Math.max(bestStreak, nextStreak)
          crit = elapsedSec <= 6.0 || overdriveActive
          const dmg = overdriveActive ? 2 : 1
          nextBossHp = Math.max(0, bossHp - dmg)
          const mult = comboMultiplier(nextStreak)
          const pts = Math.round((100 + (crit ? 45 : 0)) * mult * (overdriveActive ? 1.5 : 1))
          const goldDrop = (nextBossHp === 0 ? encounter.goldReward : 10) * (overdriveActive ? 2 : 1) + (crit ? 5 : 0)
          nextScore = score + pts
          nextGold = gold + goldDrop
          setOverdriveActive(false)
          setStageAnim('hit')
          if (crit) {
            questSfx.crit(profile.muted)
            banner = `⚡ CRITICAL HIT! −${dmg} HP · +${pts} pts · +${goldDrop}g`
            bannerTone = 'crit'
          } else {
            questSfx.hit(profile.muted)
            banner = `✓ DIRECT HIT! −${dmg} HP · +${pts} pts · +${goldDrop}g`
            bannerTone = 'hit'
          }
        } else if (shieldActive) {
          shielded = true
          setShieldActive(false)
          setOverdriveActive(false)
          questSfx.shield(profile.muted)
          banner = chosenIndex === null ? '🛡️ TIME OUT BLOCKED BY AEGIS SHIELD!' : '🛡️ AEGIS SHIELD BLOCKED DAMAGE · STREAK SAVED!'
          bannerTone = 'shield'
        } else {
          nextHearts = Math.max(0, hearts - 1)
          nextStreak = 0
          setOverdriveActive(false)
          setStageAnim('hurt')
          questSfx.damage(profile.muted)
          banner = chosenIndex === null ? '⏱ TIME UP! Guardian strikes (−1 ❤️)' : '✕ GUARDIAN COUNTER-ATTACK! (−1 ❤️)'
          bannerTone = 'hurt'
        }

        const logEntry: BattleLogEntry = {
          question: currentCard.question,
          realmId: currentCard.realmId,
          chosenIndex,
          correctIndex,
          correct,
          crit,
          shielded,
          explanation,
          elapsedSec,
        }
        const nextLog = [...battleLog, logEntry]

        setHearts(nextHearts)
        setBossHp(nextBossHp)
        setGold(nextGold)
        setScore(nextScore)
        setStreak(nextStreak)
        setBestStreak(nextBestStreak)
        setBattleLog(nextLog)
        setResolved({
          chosen: chosenIndex,
          correctIndex,
          correct,
          crit,
          shielded,
          explanation,
          banner,
          bannerTone,
        })

        window.setTimeout(() => setStageAnim('none'), 380)

        // Snappy auto-advance on hit (1.25s), slightly longer on miss (2.3s) so player sees right option
        autoNextTimer.current = window.setTimeout(() => {
          advanceAfterResolution(nextBossHp, nextHearts, nextScore, nextLog)
        }, correct ? 1250 : 2300)
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'Connection hiccup'
        const isLimit = /429|allowance|limit|free|quota/i.test(msg)
        setBattleError(
          isLimit
            ? `${msg} You can still view your Battle Debrief & Concept Guide links below.`
            : `Connection hiccup (${msg}). Tap an option again to retry — timer paused.`,
        )
      } finally {
        setChecking(false)
      }
    },
    [
      advanceAfterResolution,
      battleLog,
      bestStreak,
      bossHp,
      checking,
      currentCard,
      encounter,
      gold,
      hearts,
      overdriveActive,
      phase,
      profile.muted,
      resolved,
      roundStartedAt,
      score,
      shieldActive,
      streak,
    ],
  )

  // Countdown tick (pauses automatically while checking, resolved, frozen, or waiting on network retry)
  useEffect(() => {
    if (phase !== 'battle' || checking || resolved || freezeActive || !!battleError) return
    const id = window.setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          window.clearInterval(id)
          void submitPick(null)
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => window.clearInterval(id)
  }, [phase, checking, resolved, freezeActive, submitPick])

  const usePowerUp = useCallback(
    (id: Exclude<PowerUpId, 'heal'>) => {
      if (phase !== 'battle' || resolved || checking) return
      if (inventory[id] <= 0) return

      if (id === 'shield') {
        if (shieldActive) return
        setInventory((inv) => ({ ...inv, shield: inv.shield - 1 }))
        setShieldActive(true)
        questSfx.shield(profile.muted)
      } else if (id === 'freeze') {
        if (freezeActive) return
        setInventory((inv) => ({ ...inv, freeze: inv.freeze - 1 }))
        setFreezeActive(true)
        setSecondsLeft((s) => s + 15)
        questSfx.buy(profile.muted)
      } else if (id === 'overdrive') {
        if (overdriveActive) return
        setInventory((inv) => ({ ...inv, overdrive: inv.overdrive - 1 }))
        setOverdriveActive(true)
        questSfx.crit(profile.muted)
      } else if (id === 'reroll') {
        setInventory((inv) => ({ ...inv, reroll: inv.reroll - 1 }))
        setDeckCursor((idx) => (idx + 1) % deck.length)
        setSecondsLeft(encounter?.roundSeconds ?? 18)
        setRoundStartedAt(Date.now())
        setFreezeActive(false)
        questSfx.buy(profile.muted)
      }
    },
    [
      checking,
      deck.length,
      encounter?.roundSeconds,
      freezeActive,
      inventory,
      overdriveActive,
      phase,
      profile.muted,
      resolved,
      shieldActive,
    ],
  )

  // Desktop keyboard shortcuts: 1-4 answer, F/S/O/R power-ups, Space/Enter next
  useEffect(() => {
    if (phase !== 'battle') return
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      if (resolved && (e.key === ' ' || e.key === 'Enter')) {
        e.preventDefault()
        advanceAfterResolution(bossHp, hearts, score, battleLog)
        return
      }
      if (resolved || checking) return
      if (['1', '2', '3', '4'].includes(e.key)) {
        void submitPick(Number(e.key) - 1)
      } else if (e.key.toLowerCase() === 's') {
        usePowerUp('shield')
      } else if (e.key.toLowerCase() === 'f') {
        usePowerUp('freeze')
      } else if (e.key.toLowerCase() === 'o') {
        usePowerUp('overdrive')
      } else if (e.key.toLowerCase() === 'r') {
        usePowerUp('reroll')
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [
    advanceAfterResolution,
    battleLog,
    bossHp,
    checking,
    hearts,
    phase,
    resolved,
    score,
    submitPick,
    usePowerUp,
  ])

  function buyShopItem(id: PowerUpId, cost: number) {
    if (gold < cost) return
    if (id === 'heal' && hearts >= 3) return
    setGold((g) => g - cost)
    questSfx.buy(profile.muted)
    if (id === 'heal') {
      setHearts((h) => Math.min(3, h + 1))
    } else {
      setInventory((inv) => ({ ...inv, [id]: inv[id] + 1 }))
    }
  }

  function leaveShop() {
    const nf = floor + 1
    const nextCard = deck[deckCursor]
    if (!nextCard) return
    const ne = buildEncounter(mode, nf, nextCard.realmId)
    setFloor(nf)
    setEncounter(ne)
    setBossHp(ne.maxHp)
    setSecondsLeft(ne.roundSeconds)
    setRoundStartedAt(Date.now())
    setPhase('battle')
  }

  function copyShareSummary() {
    const text =
      mode === 'daily'
        ? formatDailyShareCard(todayKey, battleLog, score, bestStreak)
        : `⚔️ Finna Quest (${mode === 'expedition' ? '12-Floor Expedition' : 'Endless Tower'})\n${victory ? '👑 Summit Conquered!' : `Reached Floor ${floor}`} · Score ${score.toLocaleString('en-IN')} · 🔥${bestStreak} Streak\nPlay: https://study.hawayu.in/games/quest`
    void navigator.clipboard?.writeText(text).then(() => {
      setCopiedShare(true)
      window.setTimeout(() => setCopiedShare(false), 2400)
    })
  }

  const realm = currentCard ? REALM_MAP[currentCard.realmId] : null
  const missedEntries = useMemo(
    () => battleLog.filter((e) => !e.correct),
    [battleLog],
  )

  return (
    <div className="fq-shell" data-screen="quest-game">
      {phase === 'lobby' && (
        <>
          <header className="fq-hero">
            <div className="fq-hero-top">
              <span className="fq-eyebrow">⚔️ Finna Quest · RPG Knowledge Adventure</span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => updateProfile({ muted: !profile.muted })}
                  className="rounded-full border border-white/25 bg-white/10 px-3 py-1.5 text-xs font-semibold text-white hover:bg-white/20"
                >
                  {profile.muted ? '🔇 Sound off' : '🔊 Sound on'}
                </button>
                <Link
                  to="/games"
                  className="rounded-full border border-white/25 bg-white/10 px-3 py-1.5 text-xs font-semibold text-white hover:bg-white/20"
                >
                  ← Games Hub
                </Link>
              </div>
            </div>
            <h1>Ascend the Blue Mountain</h1>
            <p>
              Battle Realm Guardians across curated general-knowledge subjects — English, Geography, Computer,
              History, Polity, Science, Economy &amp; Maths. Earn gold, visit the Campfire Shop, and conquer 3 Bosses!
            </p>
            <div className="fq-rank-strip">
              <div className="fq-stat-tile">
                <span>Level {rank.level} Rank</span>
                <strong>{rank.title}</strong>
                <div className="fq-xp-bar" aria-label={`XP progress ${rank.pct}%`}>
                  <span style={{ width: `${rank.pct}%` }} />
                </div>
              </div>
              <div className="fq-stat-tile">
                <span>Quest Victories</span>
                <strong>👑 {profile.expeditionWins}</strong>
              </div>
              <div className="fq-stat-tile">
                <span>Best Endless Floor</span>
                <strong>🏔️ Floor {profile.bestEndlessFloor}</strong>
              </div>
              <div className="fq-stat-tile">
                <span>Daily Streak</span>
                <strong>🔥 {profile.dailyStreak}d</strong>
              </div>
            </div>
          </header>

          {loadError && (
            <p role="alert" className="mt-4 rounded-xl border border-wrong bg-wrong-soft p-3 text-sm text-wrong-dark">
              {loadError}
            </p>
          )}

          <section className="fq-modes-grid" aria-label="Choose Quest mode">
            <article className="fq-mode-card is-featured">
              <div>
                <span className="fq-mode-kicker">Flagship Campaign · 5–7 min</span>
                <h2>⚔️ Quest Expedition</h2>
                <p>
                  12 floors across 3 Acts, 3 Bosses, 3 Hearts, and Campfire Power-up Shops between Acts.
                  Defeat The Summit Sovereign on Floor 12!
                </p>
              </div>
              <button
                type="button"
                onClick={() => void startRun('expedition')}
                className="finna-btn min-h-12 w-full justify-center text-[15px]"
              >
                Start 12-Floor Quest →
              </button>
            </article>

            <article className="fq-mode-card">
              <div>
                <span className="fq-mode-kicker">Survival High-Score</span>
                <h2>🏔️ Endless Tower</h2>
                <p>
                  Climb infinite floors on 3 Hearts. Boss + Campfire Shop every 4th floor as the timer
                  tightens. Beat your Floor {profile.bestEndlessFloor || 1} record!
                </p>
              </div>
              <button
                type="button"
                onClick={() => void startRun('endless')}
                className="inline-flex min-h-12 w-full items-center justify-center rounded-pill border-2 border-ink bg-ink px-4 text-sm font-bold text-paper hover:opacity-90"
              >
                Enter Endless Tower →
              </button>
            </article>

            <article className="fq-mode-card">
              <div>
                <span className="fq-mode-kicker">Shared Seed · {todayKey} IST</span>
                <h2>📅 Daily 10-Q Gauntlet</h2>
                <p>
                  Same 10 general-knowledge battles for everyone today across all 8 realms. Earn a
                  WhatsApp-ready emoji result card!
                </p>
                {profile.lastDailyDate === todayKey && profile.lastDailyGrid && (
                  <p className="mt-2 font-mono text-xs text-correct-dark">
                    Today’s run: {profile.lastDailyGrid}
                  </p>
                )}
              </div>
              <button
                type="button"
                onClick={() => void startRun('daily')}
                className="inline-flex min-h-12 w-full items-center justify-center rounded-pill border border-hairline2 bg-paper px-4 text-sm font-bold text-ink hover:border-ink"
              >
                {profile.lastDailyDate === todayKey ? 'Replay Today’s Gauntlet →' : 'Play Daily Gauntlet →'}
              </button>
            </article>
          </section>

          <section className="fq-deck-card" aria-label="Customize question realms">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h2 className="font-display text-xl text-ink">
                  Customize Your Realm Deck ({selectedRealms.length} active)
                </h2>
                <p className="text-xs text-secondary">
                  Toggle which subjects spawn Guardians in Quest Expedition &amp; Endless Tower.
                </p>
              </div>
              <div className="flex flex-wrap gap-1.5">
                <button
                  type="button"
                  onClick={() => setSelectedRealms(DEFAULT_ENABLED_REALMS)}
                  className="rounded-full border border-hairline px-3 py-1.5 text-xs font-semibold hover:border-ink"
                >
                  All 8 General
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedRealms(['english', 'geography', 'computer', 'history', 'polity'])}
                  className="rounded-full border border-hairline px-3 py-1.5 text-xs font-semibold hover:border-ink"
                >
                  Core 5 Mix
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedRealms(['computer', 'science', 'maths'])}
                  className="rounded-full border border-hairline px-3 py-1.5 text-xs font-semibold hover:border-ink"
                >
                  Tech &amp; Logic
                </button>
              </div>
            </div>

            <div className="fq-guardrail">
              <span>
                <strong>✓ Fair General-Knowledge Allowlist:</strong> Draws only from your toggled general realms —
                Radiology, Nursing, Dental, Pharmacy, Veterinary, Accounts &amp; Engineering are strictly excluded.
              </span>
            </div>

            <div className="fq-realm-grid">
              {QUEST_REALMS.map((r) => {
                const on = selectedRealms.includes(r.id)
                const rxp = profile.realmXp[r.id] || 0
                return (
                  <button
                    key={r.id}
                    type="button"
                    aria-pressed={on}
                    onClick={() => toggleRealm(r.id)}
                    className={`fq-realm-chip${on ? ' is-on' : ''}`}
                    style={{ ['--fq-accent' as string]: r.accent }}
                  >
                    <div className="fq-realm-chip-top">
                      <strong>
                        {r.icon} {r.short}
                      </strong>
                      <span
                        className="fq-check-pill"
                        style={{
                          background: on ? r.accent : 'rgba(15,23,42,.08)',
                          color: on ? '#fff' : 'inherit',
                        }}
                      >
                        {on ? 'ON' : r.id === 'mizo' ? 'OPT-IN' : 'OFF'}
                      </span>
                    </div>
                    <small>{r.blurb}</small>
                    {rxp > 0 && (
                      <small className="font-mono font-bold" style={{ color: r.accent }}>
                        {rxp} XP mastery
                      </small>
                    )}
                  </button>
                )
              })}
            </div>
          </section>
        </>
      )}

      {phase === 'loading' && (
        <section className="fq-hero text-center" aria-live="polite">
          <span className="fq-eyebrow">Preparing expedition</span>
          <h1>Summoning Realm Guardians…</h1>
          <p className="mx-auto mt-2">
            Shuffling verified general-knowledge MCQs from your selected realms.
          </p>
        </section>
      )}

      {phase === 'battle' && encounter && currentCard && realm && (
        <div className="fq-arena">
          <div className="fq-hud">
            <div className="fq-hud-group">
              <span className="fq-hud-pill">
                {mode === 'expedition'
                  ? `Floor ${floor}/12 · Act ${encounter.act}`
                  : mode === 'daily'
                    ? `Daily ${floor}/10`
                    : `Tower Floor ${floor}`}
              </span>
              <span className="fq-hud-pill" aria-label={`${hearts} hearts remaining`}>
                {'❤️'.repeat(hearts)}
                {'🖤'.repeat(Math.max(0, 3 - hearts))}
              </span>
              {shieldActive && <span className="fq-hud-pill is-shield">🛡️ Shield Ready</span>}
              {overdriveActive && <span className="fq-hud-pill is-combo">⚡ Overdrive 2×</span>}
            </div>
            <div className="fq-hud-group">
              {streak >= 2 && (
                <span className="fq-hud-pill is-combo">
                  🔥 {streak} Streak ({comboMultiplier(streak)}×)
                </span>
              )}
              {mode !== 'daily' && <span className="fq-hud-pill is-gold">🪙 {gold}g</span>}
              <span className="fq-hud-pill">⭐ {score.toLocaleString('en-IN')}</span>
              <button
                type="button"
                onClick={() => updateProfile({ muted: !profile.muted })}
                className="rounded-full bg-white/10 px-2.5 py-1 text-xs font-bold hover:bg-white/20"
                aria-label="Toggle sound"
              >
                {profile.muted ? '🔇' : '🔊'}
              </button>
              <button
                type="button"
                onClick={() => {
                  clearAutoTimer()
                  setPhase('lobby')
                }}
                className="rounded-full bg-white/10 px-3 py-1 text-xs font-bold hover:bg-white/20"
              >
                Retreat
              </button>
            </div>
          </div>

          <section
            className={`fq-stage${encounter.isBoss ? ' is-boss' : ''}${
              stageAnim === 'hit' ? ' anim-hit' : stageAnim === 'hurt' ? ' anim-hurt' : ''
            }`}
            style={{ ['--fq-accent' as string]: realm.accent }}
          >
            <div className="fq-stage-row">
              <div className="fq-guardian">
                <div className="fq-guardian-avatar" aria-hidden="true">
                  {encounter.isFinalBoss ? '👑' : encounter.isBoss ? '🐉' : realm.icon}
                </div>
                <div>
                  <div className="fq-guardian-name">{encounter.name}</div>
                  <div className="fq-guardian-sub">{encounter.subtitle}</div>
                </div>
              </div>
              <div className="fq-hp-wrap">
                <div className="fq-hp-label">
                  <span>{encounter.isBoss ? 'BOSS HP' : 'GUARDIAN HP'}</span>
                  <span>
                    {bossHp} / {encounter.maxHp}
                  </span>
                </div>
                <div className="fq-hp-segments">
                  {Array.from({ length: encounter.maxHp }).map((_, i) => (
                    <span key={i} className={`fq-hp-seg${i < bossHp ? ' is-full' : ''}`} />
                  ))}
                </div>
              </div>
            </div>

            {resolved && (
              <div className={`fq-callout-banner is-${resolved.bannerTone}`} role="status">
                {resolved.banner}
              </div>
            )}

            <div className="fq-timer-track" aria-label={`${secondsLeft} seconds remaining`}>
              <div
                className={`fq-timer-fill${
                  freezeActive
                    ? ' is-frozen'
                    : secondsLeft <= 4
                      ? ' is-danger'
                      : secondsLeft <= 8
                        ? ' is-warn'
                        : ''
                }`}
                style={{
                  width: `${Math.min(100, Math.round((secondsLeft / encounter.roundSeconds) * 100))}%`,
                }}
              />
            </div>
            <div className="mt-1.5 flex justify-between font-mono text-[11px] text-slate-300">
              <span>{freezeActive ? '❄️ Clock frozen' : `⏱ ${secondsLeft}s left · Fast <6s = CRIT ⚡`}</span>
              <span>Keys: 1–4 answer · S/F/O/R relics</span>
            </div>
          </section>

          <section className="fq-qcard">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span
                className="rounded-full px-3 py-1 font-mono text-xs font-bold"
                style={{ background: realm.tint, color: realm.accent }}
              >
                {realm.icon} {realm.name}
              </span>
              {currentCard.question.source_appearance?.exam && (
                <span className="font-mono text-xs text-muted">
                  {currentCard.question.source_appearance.exam}
                  {currentCard.question.source_appearance.year
                    ? ` · ${currentCard.question.source_appearance.year}`
                    : ''}
                </span>
              )}
            </div>

            <div className="fq-qstem">
              <SourceQuestionContext
                direction={currentCard.question.direction}
                passage={currentCard.question.passage}
              />
              <SourceQuestionText
                text={currentCard.question.question_markup || currentCard.question.question}
              />
            </div>

            <div className="fq-opts">
              {currentCard.question.options.slice(0, 4).map((opt, idx) => {
                const isRight = resolved && resolved.correctIndex === idx
                const isWrong = resolved && resolved.chosen === idx && !resolved.correct
                return (
                  <button
                    key={idx}
                    type="button"
                    disabled={checking || !!resolved}
                    onClick={() => void submitPick(idx)}
                    className={`fq-opt${isRight ? ' is-right' : isWrong ? ' is-wrong' : ''}`}
                  >
                    <span className="fq-opt-key">{LETTERS[idx]}</span>
                    <span className="flex-1">
                      <SourceQuestionText
                        text={currentCard.question.options_markup?.[idx] || opt || ''}
                      />
                    </span>
                  </button>
                )
              })}
            </div>

            {battleError && (
              <div
                role="alert"
                className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-wrong bg-wrong-soft p-3 text-sm text-wrong-dark"
              >
                <span className="min-w-0 flex-1">{battleError}</span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setBattleError(null)}
                    className="rounded-pill border border-wrong/40 bg-card px-3 py-1.5 text-xs font-bold text-ink"
                  >
                    Resume
                  </button>
                  {battleLog.length > 0 && (
                    <button
                      type="button"
                      onClick={() => finishRun(false, battleLog, score, floor, mode)}
                      className="rounded-pill bg-ink px-3 py-1.5 text-xs font-bold text-paper"
                    >
                      View Debrief →
                    </button>
                  )}
                </div>
              </div>
            )}

            {resolved && (
              <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-hairline bg-paper p-3 text-sm">
                <p className="min-w-0 flex-1 text-secondary">
                  {resolved.explanation
                    ? resolved.explanation.slice(0, 220) + (resolved.explanation.length > 220 ? '…' : '')
                    : resolved.correct
                      ? 'Clean strike! Moving to next battle…'
                      : 'Logged into your Battle Debrief with Concept Guide link.'}
                </p>
                <button
                  type="button"
                  onClick={() => advanceAfterResolution(bossHp, hearts, score, battleLog)}
                  className="inline-flex min-h-10 items-center rounded-pill bg-ink px-4 text-xs font-bold text-paper"
                >
                  Continue →
                </button>
              </div>
            )}

            <div className="fq-power-belt">
              <button
                type="button"
                disabled={!!resolved || checking || inventory.shield <= 0 || shieldActive}
                onClick={() => usePowerUp('shield')}
                className={`fq-power-btn${shieldActive ? ' is-active' : ''}`}
              >
                🛡️ Shield ({inventory.shield}) <kbd className="opacity-60">S</kbd>
              </button>
              <button
                type="button"
                disabled={!!resolved || checking || inventory.freeze <= 0 || freezeActive}
                onClick={() => usePowerUp('freeze')}
                className={`fq-power-btn${freezeActive ? ' is-active' : ''}`}
              >
                ⏳ Freeze ({inventory.freeze}) <kbd className="opacity-60">F</kbd>
              </button>
              <button
                type="button"
                disabled={!!resolved || checking || inventory.overdrive <= 0 || overdriveActive}
                onClick={() => usePowerUp('overdrive')}
                className={`fq-power-btn${overdriveActive ? ' is-active' : ''}`}
              >
                ⚡ Overdrive ({inventory.overdrive}) <kbd className="opacity-60">O</kbd>
              </button>
              <button
                type="button"
                disabled={!!resolved || checking || inventory.reroll <= 0}
                onClick={() => usePowerUp('reroll')}
                className="fq-power-btn"
              >
                🔄 Reroll ({inventory.reroll}) <kbd className="opacity-60">R</kbd>
              </button>
            </div>
          </section>
        </div>
      )}

      {phase === 'shop' && (
        <section className="fq-shop" aria-label="Campfire Relic Shop">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <span className="fq-mode-kicker text-amber-800 dark:text-amber-300">
                🔥 Act {encounter?.act} Boss Defeated · Campfire Rest
              </span>
              <h1 className="mt-1 font-display text-3xl text-ink">Campfire Power-Up Shop</h1>
              <p className="mt-1 text-sm text-secondary">
                Spend your gold before climbing to Floor {floor + 1}.
              </p>
            </div>
            <div className="flex items-center gap-3 rounded-xl bg-ink px-4 py-2.5 font-mono text-sm font-bold text-paper">
              <span>{'❤️'.repeat(hearts)}{'🖤'.repeat(Math.max(0, 3 - hearts))}</span>
              <span className="text-yellow-300">🪙 {gold}g</span>
            </div>
          </div>

          <div className="fq-shop-grid">
            {SHOP_ITEMS.map((item) => {
              const disabled = gold < item.cost || (item.id === 'heal' && hearts >= 3)
              const owned = item.id === 'heal' ? null : inventory[item.id]
              return (
                <article key={item.id} className="fq-shop-item">
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-2xl">{item.icon}</span>
                      {owned !== null && (
                        <span className="font-mono text-xs text-muted">Owned: {owned}</span>
                      )}
                    </div>
                    <h3 className="mt-2 font-display text-lg font-bold text-ink">{item.name}</h3>
                    <p className="mt-1 text-xs leading-relaxed text-secondary">{item.desc}</p>
                  </div>
                  <button
                    type="button"
                    disabled={disabled}
                    onClick={() => buyShopItem(item.id, item.cost)}
                    className="inline-flex min-h-10 items-center justify-center rounded-pill border border-ink bg-ink px-4 text-xs font-bold text-paper disabled:opacity-40"
                  >
                    {item.id === 'heal' && hearts >= 3 ? 'Hearts Full' : `Buy · 🪙 ${item.cost}g`}
                  </button>
                </article>
              )
            })}
          </div>

          <div className="mt-6 flex justify-end">
            <button
              type="button"
              onClick={leaveShop}
              className="finna-btn min-h-12 px-7 text-[15px]"
            >
              Climb to Floor {floor + 1} →
            </button>
          </div>
        </section>
      )}

      {phase === 'summary' && (
        <div className="space-y-6">
          <header className="fq-hero">
            <span className="fq-eyebrow">
              {victory ? '👑 Expedition Victory' : '⚔️ Expedition Complete'}
            </span>
            <h1>
              {victory
                ? mode === 'daily'
                  ? `Daily Gauntlet Cleared!`
                  : 'You Conquered the Summit!'
                : `Fallen at Floor ${floor}`}
            </h1>
            <p>
              {battleLog.filter((e) => e.correct).length} / {battleLog.length} right · Score{' '}
              <strong>{score.toLocaleString('en-IN')}</strong> · Best Streak{' '}
              <strong>🔥 {bestStreak}</strong> · Earned <strong>+{earnedXp} XP</strong>
            </p>
            {mode === 'daily' && (
              <p className="mt-3 font-mono text-lg tracking-widest">
                {battleLog
                  .map((e) => (e.crit ? '⚡' : e.correct ? '🟩' : e.shielded ? '🛡️' : '🟥'))
                  .join(' ')}
              </p>
            )}
            <div className="mt-5 flex flex-wrap gap-2.5">
              <button
                type="button"
                onClick={() => void startRun(mode)}
                className="inline-flex min-h-11 items-center rounded-pill bg-white px-5 text-sm font-bold text-slate-900 hover:bg-slate-100"
              >
                Play Again →
              </button>
              <button
                type="button"
                onClick={copyShareSummary}
                className="inline-flex min-h-11 items-center rounded-pill border border-white/30 bg-white/10 px-5 text-sm font-bold text-white hover:bg-white/20"
              >
                {copiedShare ? '✓ Copied for WhatsApp!' : '📤 Share Score Card'}
              </button>
              <button
                type="button"
                onClick={() => setPhase('lobby')}
                className="inline-flex min-h-11 items-center rounded-pill border border-white/25 px-5 text-sm font-semibold text-white/90 hover:bg-white/10"
              >
                Change Realms / Mode
              </button>
            </div>
          </header>

          <section className="fq-deck-card" aria-label="Battle debrief and missed concepts">
            <h2 className="font-display text-xl text-ink">
              Battle Debrief · {missedEntries.length === 0 ? 'Flawless Run!' : `${missedEntries.length} Concepts to Master`}
            </h2>
            {missedEntries.length === 0 ? (
              <p className="mt-2 text-sm text-secondary">
                Zero mistakes this run — your general-knowledge accuracy was 100%! Try Endless Tower or add more realms.
              </p>
            ) : (
              <div className="mt-4 space-y-3">
                {missedEntries.map((entry, i) => {
                  const r = REALM_MAP[entry.realmId]
                  const guide = resolveQuestionGuide(entry.question)
                  const rightOpt =
                    entry.correctIndex !== null ? entry.question.options[entry.correctIndex] : null
                  return (
                    <article
                      key={`${entry.question.id}-${i}`}
                      className="rounded-xl border border-hairline bg-paper p-4"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span
                          className="rounded-full px-2.5 py-0.5 font-mono text-xs font-bold"
                          style={{ background: r.tint, color: r.accent }}
                        >
                          {r.icon} {r.short} {entry.shielded ? '· 🛡️ Shielded' : ''}
                        </span>
                        {guide && (
                          <Link
                            to={guide.to}
                            state={{ fromQuestion: true }}
                            className={`sq-guide-pill is-${guide.tone}`}
                          >
                            <span>📖</span>
                            <span>{guide.label}</span>
                            <span>→</span>
                          </Link>
                        )}
                      </div>
                      <p className="mt-2 text-sm font-semibold text-ink">
                        {entry.question.question}
                      </p>
                      {rightOpt && (
                        <p className="mt-1.5 text-xs font-semibold text-correct-dark">
                          ✓ Correct answer: {LETTERS[entry.correctIndex!]} · {rightOpt}
                        </p>
                      )}
                      {entry.explanation && (
                        <p className="mt-1 text-xs leading-relaxed text-secondary">
                          {entry.explanation}
                        </p>
                      )}
                    </article>
                  )
                })}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
