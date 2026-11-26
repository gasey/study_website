import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { listQuestions, submitAnswer, type Question } from '../lib/api'
import { UserAvatar } from '../components/AvatarArt'
import { CatLoader, CatXpBar } from '../components/CatLoader'
import { SourceQuestionContext, SourceQuestionText } from '../components/SourceQuestionText'
import { learnerExplanation } from '../lib/answerStatus'
import {
  addStoneBlock,
  anyPieceFits,
  applyClutchBlast,
  applyLaserClear,
  blockSfx,
  BOARD_SIZE,
  canPlace,
  checkpointBlockRun,
  createEmptyBoard,
  createRng,
  dealTray,
  finishBlockRun,
  getBlockLeaderboard,
  getMyBlockStats,
  knowledgeMultiplier,
  LASER_CHARGE_COST,
  MAX_CLUTCH_SAVES,
  pieceFitsAnywhere,
  placePiece,
  previewClearLines,
  scorePlacement,
  startBlockRun,
  SUBJECT_SCOPES,
  todayIstDate,
  type BlockLeaderboardData,
  type BlockMode,
  type Board,
  type BoardPeriod,
  type MyBlockStats,
  type PieceSpec,
} from '../lib/blockPuzzle'
import '../styles/block-puzzle.css'

const LETTERS = ['A', 'B', 'C', 'D']
const EXCLUDE_SPECIALIST_RE =
  /(radiology|radiotherapy|nursing|obstetric|gynaecolog|dental|veterinary|forensic|engineering|horticulture|sericulture|pharmac|medical|mimer)/i

type QuestionPurpose = 'forge' | 'reroll' | 'clutch' | 'boost'

interface ActiveQuestionModal {
  purpose: QuestionPurpose
  question: Question
  chosen: number | null
  correct: boolean | null
  answerIndex: number | null
  explanation: string | null
  submitting: boolean
}

interface ReviewedItem {
  id: string
  question: string
  correct: boolean
  answerText: string
  explanation: string
}

function isPlayableBankQuestion(q: Question): boolean {
  if (!q.options || q.options.length !== 4) return false
  if (q.has_diagram || q.figure_image_url) return false
  if (q.answer_status === 'written' || q.answer_status === 'unsolved') return false
  const text = `${q.question || ''} ${q.source_appearance?.exam || ''}`
  if (EXCLUDE_SPECIALIST_RE.test(text)) return false
  return true
}

export default function BlockBlastGame() {
  const [mode, setMode] = useState<BlockMode>(() =>
    new URLSearchParams(window.location.search).get('mode') === 'daily' ? 'daily' : 'endless',
  )
  const [subjectScope, setSubjectScope] = useState<string>('all')
  const [muted, setMuted] = useState(false)

  // Puzzle state
  const rngRef = useRef<() => number>(createRng(Date.now()))
  const [board, setBoard] = useState<Board>(() => createEmptyBoard())
  const [tray, setTray] = useState<(PieceSpec | null)[]>(() => dealTray(rngRef.current, 'normal'))
  const [selectedSlot, setSelectedSlot] = useState<number | null>(0)
  const [hoverCell, setHoverCell] = useState<[number, number] | null>(null)
  const [flashCells, setFlashCells] = useState<Set<string>>(() => new Set())
  const [laserMode, setLaserMode] = useState(false)

  // Scoring & synergy state
  const [score, setScore] = useState(0)
  const [linesCleared, setLinesCleared] = useState(0)
  const [piecesPlaced, setPiecesPlaced] = useState(0)
  const [traysCleared, setTraysCleared] = useState(0)
  const [clearStreak, setClearStreak] = useState(0)
  const [knowledgeStreak, setKnowledgeStreak] = useState(0)
  const [bestStreak, setBestStreak] = useState(0)
  const [maxCombo, setMaxCombo] = useState(1)
  const [questionsAnswered, setQuestionsAnswered] = useState(0)
  const [questionsCorrect, setQuestionsCorrect] = useState(0)
  const [laserCharge, setLaserCharge] = useState(0)
  const [laserReadyCount, setLaserReadyCount] = useState(0)
  const [clutchSavesUsed, setClutchSavesUsed] = useState(0)
  const [callout, setCallout] = useState<string | null>(null)
  const [gameOver, setGameOver] = useState(false)
  const [finishSummary, setFinishSummary] = useState<{
    xpAwarded: number
    isNewBest: boolean
    finalScore: number
  } | null>(null)
  const [copied, setCopied] = useState(false)
  const [reviewed, setReviewed] = useState<ReviewedItem[]>([])

  // Run & Bank deck state
  const [runId, setRunId] = useState<string | null>(null)
  const [qDeck, setQDeck] = useState<Question[]>([])
  const [qCursor, setQCursor] = useState(0)
  const [deckLoading, setDeckLoading] = useState(false)
  const [qModal, setQModal] = useState<ActiveQuestionModal | null>(null)

  // Leaderboard & personal stats
  const [boardPeriod, setBoardPeriod] = useState<BoardPeriod>('week')
  const [leaderboard, setLeaderboard] = useState<BlockLeaderboardData | null>(null)
  const [boardLoading, setBoardLoading] = useState(true)
  const [myStats, setMyStats] = useState<MyBlockStats | null>(null)

  const calloutTimer = useRef<number | null>(null)
  const showCallout = useCallback((msg: string) => {
    setCallout(msg)
    if (calloutTimer.current) window.clearTimeout(calloutTimer.current)
    calloutTimer.current = window.setTimeout(() => setCallout(null), 1900)
  }, [])

  const loadLeaderboard = useCallback((period: BoardPeriod) => {
    setBoardLoading(true)
    getBlockLeaderboard(period)
      .then((d) => setLeaderboard(d))
      .catch(() => setLeaderboard(null))
      .finally(() => setBoardLoading(false))
  }, [])

  const loadStats = useCallback(() => {
    getMyBlockStats()
      .then((s) => setMyStats(s))
      .catch(() => {})
  }, [])

  useEffect(() => {
    loadLeaderboard(boardPeriod)
  }, [boardPeriod, loadLeaderboard])

  useEffect(() => {
    loadStats()
  }, [loadStats])

  const fetchBankDeck = useCallback(async (scopeId: string, activeMode: BlockMode) => {
    setDeckLoading(true)
    try {
      const spec = SUBJECT_SCOPES.find((s) => s.id === scopeId)
      const seed =
        activeMode === 'daily'
          ? `blocks-${todayIstDate()}`
          : String(Math.floor(Math.random() * 100000))
      const page = await listQuestions({
        pool: 'scorable',
        order: 'mixed',
        seed,
        subject_id: spec?.apiSubject,
        limit: 40,
      })
      const clean = (page.items || []).filter(isPlayableBankQuestion)
      setQDeck(clean)
      setQCursor(0)
      return clean
    } catch {
      return []
    } finally {
      setDeckLoading(false)
    }
  }, [])

  const startNewRun = useCallback(
    async (nextMode: BlockMode = mode, nextScope: string = subjectScope) => {
      const seed =
        nextMode === 'daily' ? `finna-blocks-${todayIstDate()}` : Date.now()
      rngRef.current = createRng(seed)
      setBoard(createEmptyBoard())
      const freshTray = dealTray(rngRef.current, 'normal')
      setTray(freshTray)
      setSelectedSlot(0)
      setHoverCell(null)
      setLaserMode(false)
      setScore(0)
      setLinesCleared(0)
      setPiecesPlaced(0)
      setTraysCleared(0)
      setClearStreak(0)
      setKnowledgeStreak(0)
      setBestStreak(0)
      setMaxCombo(1)
      setQuestionsAnswered(0)
      setQuestionsCorrect(0)
      setLaserCharge(0)
      setLaserReadyCount(0)
      setClutchSavesUsed(0)
      setGameOver(false)
      setFinishSummary(null)
      setQModal(null)
      setReviewed([])
      setCopied(false)

      void fetchBankDeck(nextScope, nextMode)
      try {
        const started = await startBlockRun(nextMode, nextScope)
        setRunId(started.run_id)
      } catch {
        setRunId(null)
      }
    },
    [mode, subjectScope, fetchBankDeck],
  )

  useEffect(() => {
    void startNewRun(mode, 'all')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    blockSfx.muted = muted
  }, [muted])

  // Keyboard shortcuts: 1/2/3 to pick piece, Escape to exit laser mode
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (qModal || gameOver) return
      if (e.key === '1' && tray[0]) setSelectedSlot(0)
      if (e.key === '2' && tray[1]) setSelectedSlot(1)
      if (e.key === '3' && tray[2]) setSelectedSlot(2)
      if (e.key === 'Escape') setLaserMode(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [tray, qModal, gameOver])

  const syncProgress = useCallback(
    (
      overrides: Partial<{
        score: number
        linesCleared: number
        piecesPlaced: number
        questionsAnswered: number
        questionsCorrect: number
        bestStreak: number
        maxCombo: number
        clutchSavesUsed: number
      }>,
      finish = false,
    ) => {
      if (!runId) return
      const payload = {
        score: overrides.score ?? score,
        lines_cleared: overrides.linesCleared ?? linesCleared,
        pieces_placed: overrides.piecesPlaced ?? piecesPlaced,
        questions_answered: overrides.questionsAnswered ?? questionsAnswered,
        questions_correct: overrides.questionsCorrect ?? questionsCorrect,
        best_streak: overrides.bestStreak ?? bestStreak,
        max_combo: overrides.maxCombo ?? maxCombo,
        clutch_saves_used: overrides.clutchSavesUsed ?? clutchSavesUsed,
      }
      const fn = finish ? finishBlockRun : checkpointBlockRun
      void fn(runId, payload)
        .then((res) => {
          if (finish) {
            setFinishSummary({
              xpAwarded: res.xp_awarded,
              isNewBest: res.is_new_best,
              finalScore: res.score,
            })
            loadLeaderboard(boardPeriod)
            loadStats()
          }
        })
        .catch(() => {
          if (finish) {
            setFinishSummary({
              xpAwarded: 0,
              isNewBest: false,
              finalScore: payload.score,
            })
          }
        })
    },
    [
      runId,
      score,
      linesCleared,
      piecesPlaced,
      questionsAnswered,
      questionsCorrect,
      bestStreak,
      maxCombo,
      clutchSavesUsed,
      boardPeriod,
      loadLeaderboard,
      loadStats,
    ],
  )

  const openBankQuestion = useCallback(
    async (purpose: QuestionPurpose) => {
      let pool = qDeck
      let cursor = qCursor
      if (!pool.length || cursor >= pool.length) {
        pool = await fetchBankDeck(subjectScope, mode)
        cursor = 0
      }
      const nextQ = pool[cursor]
      if (!nextQ) {
        // Fallback if offline/empty: refill directly
        if (purpose === 'forge' || purpose === 'reroll') {
          const fresh = dealTray(rngRef.current, 'normal')
          setTray(fresh)
          setSelectedSlot(0)
        }
        return
      }
      setQCursor(cursor + 1)
      setQModal({
        purpose,
        question: nextQ,
        chosen: null,
        correct: null,
        answerIndex: null,
        explanation: null,
        submitting: false,
      })
    },
    [qDeck, qCursor, fetchBankDeck, subjectScope, mode],
  )

  const triggerBoardJamCheck = useCallback(
    (nextBoard: Board, nextTray: (PieceSpec | null)[], currentStats: {
      score: number
      linesCleared: number
      piecesPlaced: number
      clutchSavesUsed: number
    }) => {
      if (anyPieceFits(nextBoard, nextTray)) return
      if (currentStats.clutchSavesUsed < MAX_CLUTCH_SAVES) {
        showCallout('🛡 Board jammed! Answer a Clutch MCQ to blast open!')
        void openBankQuestion('clutch')
      } else {
        setGameOver(true)
        syncProgress(currentStats, true)
      }
    },
    [openBankQuestion, showCallout, syncProgress],
  )

  const selectedPiece = selectedSlot !== null ? tray[selectedSlot] : null

  const ghostPreview = useMemo(() => {
    if (!hoverCell || !selectedPiece || laserMode) return null
    const [hr, hc] = hoverCell
    const ok = canPlace(board, selectedPiece, hr, hc)
    const cells = new Set<string>()
    for (const [dr, dc] of selectedPiece.cells) {
      const r = hr + dr
      const c = hc + dc
      if (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE) {
        cells.add(`${r}:${c}`)
      }
    }
    const willClear = ok ? previewClearLines(board, selectedPiece, hr, hc) : { rows: [], cols: [] }
    return {
      ok,
      cells,
      clearRows: new Set(willClear.rows),
      clearCols: new Set(willClear.cols),
    }
  }, [hoverCell, selectedPiece, laserMode, board])

  function flashRange(rows: number[], cols: number[]) {
    const set = new Set<string>()
    for (const r of rows) {
      for (let c = 0; c < BOARD_SIZE; c++) set.add(`${r}:${c}`)
    }
    for (const c of cols) {
      for (let r = 0; r < BOARD_SIZE; r++) set.add(`${r}:${c}`)
    }
    setFlashCells(set)
    window.setTimeout(() => setFlashCells(new Set()), 360)
  }

  function handleCellClick(r: number, c: number) {
    if (gameOver || qModal) return

    if (laserMode) {
      if (laserReadyCount <= 0) {
        setLaserMode(false)
        return
      }
      const { board: clearedBoard, clearedCells } = applyLaserClear(board, r, c)
      blockSfx.laser()
      flashRange([r], [c])
      const bonus = Math.max(150, clearedCells * 35)
      const nextScore = score + bonus
      const nextLines = linesCleared + 2
      setBoard(clearedBoard)
      setScore(nextScore)
      setLinesCleared(nextLines)
      setLaserReadyCount((n) => Math.max(0, n - 1))
      setLaserMode(false)
      showCallout(`⚡ LASER CROSS! +${bonus}`)
      syncProgress({ score: nextScore, linesCleared: nextLines })
      return
    }

    if (selectedSlot === null || !selectedPiece) return
    if (!canPlace(board, selectedPiece, r, c)) {
      blockSfx.wrong()
      return
    }

    const res = placePiece(board, selectedPiece, r, c)
    const nextClearStreak = res.totalLines > 0 ? clearStreak + 1 : 0
    const earned = scorePlacement(res.cellsPlaced, res.totalLines, knowledgeStreak, nextClearStreak)
    const nextScore = score + earned
    const nextLines = linesCleared + res.totalLines
    const nextPieces = piecesPlaced + 1

    if (res.totalLines > 0) {
      blockSfx.clear(res.totalLines)
      flashRange(res.clearedRows, res.clearedCols)
      const label =
        res.totalLines >= 4
          ? 'QUAD BLAST!!'
          : res.totalLines === 3
            ? 'TRIPLE BLAST!'
            : res.totalLines === 2
              ? 'DOUBLE BLAST!'
              : 'LINE CLEAR!'
      const mult = knowledgeMultiplier(knowledgeStreak)
      showCallout(`${label} +${earned}${mult > 1 ? ` (×${mult})` : ''}`)
    } else {
      blockSfx.place()
    }

    setBoard(res.board)
    setScore(nextScore)
    setLinesCleared(nextLines)
    setPiecesPlaced(nextPieces)
    setClearStreak(nextClearStreak)
    setHoverCell(null)

    const nextTray = tray.map((p, idx) => (idx === selectedSlot ? null : p))
    const remaining = nextTray
      .map((p, idx) => (p ? idx : -1))
      .filter((idx) => idx >= 0)

    if (remaining.length === 0) {
      const nextTrays = traysCleared + 1
      setTraysCleared(nextTrays)
      setTray(nextTray)
      setSelectedSlot(null)
      syncProgress({ score: nextScore, linesCleared: nextLines, piecesPlaced: nextPieces })
      // Every 2nd tray cleared triggers a fast Study Forge question to earn blessed blocks + combo!
      if (nextTrays % 2 === 0) {
        void openBankQuestion('forge')
      } else {
        const dealt = dealTray(rngRef.current, knowledgeStreak >= 3 ? 'blessed' : 'normal')
        setTray(dealt)
        setSelectedSlot(0)
        triggerBoardJamCheck(res.board, dealt, {
          score: nextScore,
          linesCleared: nextLines,
          piecesPlaced: nextPieces,
          clutchSavesUsed,
        })
      }
    } else {
      setTray(nextTray)
      setSelectedSlot(remaining[0])
      if (res.totalLines > 0) {
        syncProgress({ score: nextScore, linesCleared: nextLines, piecesPlaced: nextPieces })
      }
      triggerBoardJamCheck(res.board, nextTray, {
        score: nextScore,
        linesCleared: nextLines,
        piecesPlaced: nextPieces,
        clutchSavesUsed,
      })
    }
  }

  async function handleAnswerQuestion(optIdx: number) {
    if (!qModal || qModal.submitting || qModal.chosen !== null) return
    setQModal({ ...qModal, chosen: optIdx, submitting: true })
    try {
      const result = await submitAnswer(qModal.question.id, optIdx, 'game')
      const isRight = Boolean(result.correct)
      const ansIdx =
        typeof result.answer_index === 'number'
          ? result.answer_index
          : qModal.question.options.findIndex((o) => o === result.answer_text)
      const explanation = result.explanation ? learnerExplanation(result.explanation) : null

      const nextAnswered = questionsAnswered + 1
      const nextCorrect = questionsCorrect + (isRight ? 1 : 0)
      const nextStreak = isRight ? knowledgeStreak + 1 : 0
      const nextBest = Math.max(bestStreak, nextStreak)
      const mult = knowledgeMultiplier(nextStreak)
      const nextMaxCombo = Math.max(maxCombo, Math.round(mult))

      setQuestionsAnswered(nextAnswered)
      setQuestionsCorrect(nextCorrect)
      setKnowledgeStreak(nextStreak)
      setBestStreak(nextBest)
      setMaxCombo(nextMaxCombo)

      setReviewed((prev) => [
        {
          id: qModal.question.id,
          question: qModal.question.question,
          correct: isRight,
          answerText:
            result.answer_text ||
            (ansIdx >= 0 ? qModal.question.options[ansIdx] : null) ||
            'See bank source',
          explanation: explanation || '',
        },
        ...prev,
      ])

      if (isRight) {
        blockSfx.correct()
        const bonus = Math.round(120 * mult)
        const nextScore = score + bonus
        setScore(nextScore)
        const nextCharge = laserCharge + 1
        if (nextCharge >= LASER_CHARGE_COST) {
          setLaserCharge(0)
          setLaserReadyCount((n) => n + 1)
          showCallout(`⚡ LASER CLEAR CHARGED! +${bonus}`)
        } else {
          setLaserCharge(nextCharge)
          showCallout(`🔥 Streak ×${mult} · +${bonus} pts`)
        }
        syncProgress({
          score: nextScore,
          questionsAnswered: nextAnswered,
          questionsCorrect: nextCorrect,
          bestStreak: nextBest,
          maxCombo: nextMaxCombo,
        })
      } else {
        blockSfx.wrong()
        syncProgress({
          questionsAnswered: nextAnswered,
          questionsCorrect: nextCorrect,
          bestStreak: nextBest,
          maxCombo: nextMaxCombo,
        })
      }

      setQModal((cur) =>
        cur
          ? {
              ...cur,
              chosen: optIdx,
              correct: isRight,
              answerIndex: ansIdx >= 0 ? ansIdx : null,
              explanation,
              submitting: false,
            }
          : null,
      )
    } catch {
      setQModal((cur) => (cur ? { ...cur, submitting: false, chosen: null } : null))
    }
  }

  function handleContinueAfterQuestion() {
    if (!qModal || qModal.correct === null) return
    const { purpose, correct } = qModal
    setQModal(null)

    if (purpose === 'clutch') {
      if (correct) {
        const nextClutch = clutchSavesUsed + 1
        const { board: rescued, origin } = applyClutchBlast(board)
        setClutchSavesUsed(nextClutch)
        setBoard(rescued)
        flashRange([origin[0], origin[0] + 1, origin[0] + 2], [])
        const blessed = dealTray(rngRef.current, 'blessed')
        setTray(blessed)
        setSelectedSlot(0)
        showCallout('🛡 CLUTCH SAVE! 3×3 crater cleared!')
        syncProgress({ clutchSavesUsed: nextClutch })
      } else {
        setGameOver(true)
        syncProgress({}, true)
      }
      return
    }

    if (purpose === 'reroll') {
      const nextTray = dealTray(rngRef.current, correct ? 'blessed' : 'normal')
      setTray(nextTray)
      setSelectedSlot(0)
      triggerBoardJamCheck(board, nextTray, {
        score,
        linesCleared,
        piecesPlaced,
        clutchSavesUsed,
      })
      return
    }

    if (purpose === 'forge') {
      const nextBoard = correct ? board : addStoneBlock(board, rngRef.current)
      const nextTray = dealTray(rngRef.current, correct ? 'blessed' : 'tough')
      setBoard(nextBoard)
      setTray(nextTray)
      setSelectedSlot(0)
      triggerBoardJamCheck(nextBoard, nextTray, {
        score,
        linesCleared,
        piecesPlaced,
        clutchSavesUsed,
      })
      return
    }

    // purpose === 'boost'
    if (!correct) {
      const nextBoard = addStoneBlock(board, rngRef.current)
      setBoard(nextBoard)
      triggerBoardJamCheck(nextBoard, tray, {
        score,
        linesCleared,
        piecesPlaced,
        clutchSavesUsed,
      })
    }
  }

  function copyShareCard() {
    const text = [
      `🧱 Finna Blocks (${mode === 'daily' ? `Daily ${todayIstDate()}` : 'Endless'})`,
      `🏆 Score: ${score.toLocaleString('en-IN')} pts · ${linesCleared} lines`,
      `📚 Bank MCQs: ${questionsCorrect}/${questionsAnswered} · Best Streak: ${bestStreak}`,
      `Play free at https://study.hawayu.in/games/blocks`,
    ].join('\n')
    void navigator.clipboard?.writeText(text).then(() => {
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2200)
    })
  }

  const mult = knowledgeMultiplier(knowledgeStreak)
  const personalBest =
    mode === 'daily'
      ? Math.max(score, myStats?.best_daily_today ?? 0)
      : Math.max(score, myStats?.best_endless ?? 0)

  return (
    <div className="bp-page">
      {/* Top Arcade Header */}
      <header className="bp-hero">
        <div>
          <span className="bp-eyebrow">Finna Arcade · Block Puzzle × Question Bank</span>
          <h1>Finna Blocks</h1>
          <p>
            Clear rows &amp; columns on the 8×8 board. Answer real MPSC bank questions to charge{' '}
            <strong>Knowledge Multipliers (up to ×4)</strong>, fire{' '}
            <strong>⚡ Laser Clears</strong>, and pull off <strong>🛡 Clutch Saves</strong>.
          </p>
        </div>

        <div className="bp-hero-controls">
          <div className="bp-mode-pills" role="group" aria-label="Game mode">
            <button
              type="button"
              className={mode === 'endless' ? 'is-on' : ''}
              onClick={() => {
                setMode('endless')
                void startNewRun('endless', subjectScope)
              }}
            >
              ♾️ Endless
            </button>
            <button
              type="button"
              className={mode === 'daily' ? 'is-on' : ''}
              onClick={() => {
                setMode('daily')
                setBoardPeriod('daily')
                void startNewRun('daily', subjectScope)
              }}
            >
              ☀️ Daily Seed
            </button>
          </div>

          <select
            aria-label="Question subject filter"
            value={subjectScope}
            onChange={(e) => {
              const next = e.target.value
              setSubjectScope(next)
              void startNewRun(mode, next)
            }}
            className="bp-select"
          >
            {SUBJECT_SCOPES.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>

          <button
            type="button"
            className="bp-icon-btn"
            onClick={() => setMuted((m) => !m)}
            aria-pressed={muted}
          >
            {muted ? '🔇 Muted' : '🔊 Sound'}
          </button>

          <button
            type="button"
            className="bp-icon-btn"
            onClick={() => void startNewRun(mode, subjectScope)}
          >
            ↻ New Run
          </button>
        </div>
      </header>

      <div className="bp-layout">
        {/* Main Game Stage */}
        <section className="bp-stage" aria-label="Block puzzle board">
          {/* 4-Tile Live HUD */}
          <div className="bp-hud">
            <div className="bp-hud-tile is-score">
              <small>Score</small>
              <strong>{score.toLocaleString('en-IN')}</strong>
            </div>
            <div className="bp-hud-tile">
              <small>{mode === 'daily' ? 'Daily best' : 'Personal best'}</small>
              <strong>{personalBest.toLocaleString('en-IN')}</strong>
            </div>
            <div className="bp-hud-tile">
              <small>Knowledge combo</small>
              <strong>
                🔥 ×{mult}
              </strong>
            </div>
            <div className="bp-hud-tile">
              <small>Lines · MCQs</small>
              <strong>
                {linesCleared} · {questionsCorrect}/{questionsAnswered}
              </strong>
            </div>
          </div>

          <div className="bp-board-card">
            {callout && (
              <div role="status" className="bp-callout">
                {callout}
              </div>
            )}

            {laserMode && (
              <div className="bp-laser-banner">
                <span>⚡ Laser Ready — tap any square to wipe its entire row + column!</span>
                <button
                  type="button"
                  className="finna-st-btn"
                  onClick={() => setLaserMode(false)}
                >
                  Cancel
                </button>
              </div>
            )}

            {/* 8x8 Interactive Board */}
            <div
              className={`bp-board${laserMode ? ' is-laser' : ''}`}
              role="grid"
              aria-label="8 by 8 puzzle board"
              onMouseLeave={() => setHoverCell(null)}
            >
              {board.map((row, r) =>
                row.map((cell, c) => {
                  const key = `${r}:${c}`
                  const isGhost = ghostPreview?.cells.has(key)
                  const willClear =
                    ghostPreview?.clearRows.has(r) || ghostPreview?.clearCols.has(c)
                  const isLaserTarget =
                    laserMode && hoverCell && (hoverCell[0] === r || hoverCell[1] === c)
                  const isFlash = flashCells.has(key)

                  let cls = 'bp-cell'
                  if (cell) cls += ` bp-cell--${cell}`
                  else if (ghostPreview && isGhost && selectedPiece) {
                    cls += ghostPreview.ok
                      ? ` bp-cell--${selectedPiece.color} bp-cell--ghost-ok`
                      : ' bp-cell--ghost-bad'
                  }
                  if (willClear) cls += ' bp-cell--will-clear'
                  if (isLaserTarget) cls += ' bp-cell--laser-target'
                  if (isFlash) cls += ' bp-cell--flash'

                  return (
                    <button
                      key={key}
                      type="button"
                      role="gridcell"
                      aria-label={`Row ${r + 1} Column ${c + 1}${cell ? ' filled' : ' empty'}`}
                      className={cls}
                      onMouseEnter={() => setHoverCell([r, c])}
                      onFocus={() => setHoverCell([r, c])}
                      onClick={() => handleCellClick(r, c)}
                    />
                  )
                }),
              )}
            </div>

            {/* 3-Piece Polyomino Tray */}
            <div className="bp-tray" aria-label="Available block pieces">
              {tray.map((piece, idx) => {
                const fits = piece ? pieceFitsAnywhere(board, piece) : false
                const isSelected = selectedSlot === idx && piece !== null
                return (
                  <button
                    key={piece?.uid || `empty-${idx}`}
                    type="button"
                    disabled={!piece || gameOver}
                    aria-pressed={isSelected}
                    onClick={() => {
                      setLaserMode(false)
                      setSelectedSlot(idx)
                    }}
                    className={`bp-tray-slot${isSelected ? ' is-selected' : ''}${piece && !fits ? ' is-unfit' : ''}`}
                  >
                    {piece ? (
                      <>
                        <div
                          className="bp-mini-grid"
                          style={{
                            gridTemplateColumns: `repeat(${piece.cols}, 15px)`,
                            gridTemplateRows: `repeat(${piece.rows}, 15px)`,
                          }}
                          aria-hidden="true"
                        >
                          {Array.from({ length: piece.rows * piece.cols }).map((_, i) => {
                            const rr = Math.floor(i / piece.cols)
                            const cc = i % piece.cols
                            const active = piece.cells.some(([cr, cc2]) => cr === rr && cc2 === cc)
                            return (
                              <span
                                key={i}
                                className={
                                  active ? `bp-mini-cell bp-mini--${piece.color}` : 'bp-mini-cell'
                                }
                              />
                            )
                          })}
                        </div>
                        <span className="bp-slot-key">
                          {fits ? `Piece ${idx + 1}` : 'No space'}
                        </span>
                      </>
                    ) : (
                      <span className="bp-slot-key">Placed ✓</span>
                    )}
                  </button>
                )
              })}
            </div>

            {/* Power-Up & Question Synergy Controls */}
            <div className="bp-powers">
              <CatXpBar
                value={laserReadyCount > 0 ? LASER_CHARGE_COST : laserCharge}
                max={LASER_CHARGE_COST}
                tone={laserReadyCount > 0 ? 'gold' : 'teal'}
                label={
                  laserReadyCount > 0
                    ? `⚡ Laser Clear READY (×${laserReadyCount})`
                    : `⚡ Laser Clear charge (${laserCharge}/${LASER_CHARGE_COST} correct MCQs)`
                }
                meta={`🛡 Clutch Saves: ${MAX_CLUTCH_SAVES - clutchSavesUsed}/${MAX_CLUTCH_SAVES}`}
              />

              <div className="bp-power-btns">
                <button
                  type="button"
                  disabled={laserReadyCount <= 0 || gameOver}
                  onClick={() => setLaserMode((v) => !v)}
                  className={`bp-power-btn${laserReadyCount > 0 ? ' is-ready' : ''}`}
                >
                  <span>⚡ Laser Clear ({laserReadyCount})</span>
                  <small>Wipe 1 row + 1 col</small>
                </button>
                <button
                  type="button"
                  disabled={gameOver || deckLoading}
                  onClick={() => void openBankQuestion('reroll')}
                  className="bp-power-btn"
                >
                  <span>🔄 Study Reroll</span>
                  <small>Answer 1 MCQ → fresh tray</small>
                </button>
                <button
                  type="button"
                  disabled={gameOver || deckLoading}
                  onClick={() => void openBankQuestion('boost')}
                  className="bp-power-btn"
                >
                  <span>📚 Study Boost</span>
                  <small>Charge ×combo &amp; Laser</small>
                </button>
              </div>
            </div>
          </div>

          {/* Game Over & End-of-Run Review Card */}
          {gameOver && (
            <section className="finna-card" aria-label="Run summary">
              <div className="finna-section-top">
                <div>
                  <span className="finna-eyebrow">Run complete</span>
                  <h2>
                    {finishSummary?.isNewBest ? '🏆 New Personal Best!' : 'Great endless run!'}
                  </h2>
                </div>
                <strong className="font-mono text-2xl font-black text-practice-dark">
                  {score.toLocaleString('en-IN')} pts
                </strong>
              </div>
              <p className="text-sm text-secondary">
                <strong>{linesCleared}</strong> lines cleared ·{' '}
                <strong>
                  {questionsCorrect}/{questionsAnswered}
                </strong>{' '}
                bank MCQs right · Best streak <strong>{bestStreak}</strong>
                {finishSummary?.xpAwarded ? (
                  <>
                    {' '}
                    · <strong className="text-correct-dark">+{finishSummary.xpAwarded} XP earned</strong>
                  </>
                ) : null}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="finna-btn"
                  onClick={() => void startNewRun(mode, subjectScope)}
                >
                  Play again →
                </button>
                <button
                  type="button"
                  className="finna-btn finna-btn-quiet"
                  onClick={copyShareCard}
                >
                  {copied ? '✓ Score card copied!' : '📋 Copy score card'}
                </button>
                <Link to="/games" className="finna-btn finna-btn-quiet">
                  All games
                </Link>
              </div>

              {reviewed.length > 0 && (
                <details className="mt-4 border-t border-hairline pt-3">
                  <summary className="cursor-pointer text-sm font-bold text-ink">
                    Review {reviewed.length} bank questions from this run
                  </summary>
                  <div className="mt-3 flex flex-col gap-2">
                    {reviewed.map((item, i) => (
                      <div
                        key={item.id + '-' + i}
                        className="rounded-xl border border-hairline bg-paper p-3 text-sm"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span
                            className={
                              item.correct
                                ? 'font-bold text-correct-dark'
                                : 'font-bold text-wrong-dark'
                            }
                          >
                            {item.correct ? '✓ Correct' : '✕ Missed'}
                          </span>
                          <Link
                            to={`/bank/${encodeURIComponent(item.id)}`}
                            className="text-xs font-bold text-link underline"
                          >
                            Source ↗
                          </Link>
                        </div>
                        <p className="mt-1 font-semibold">{item.question}</p>
                        <p className="mt-1 text-xs text-secondary">
                          <strong>Answer:</strong> {item.answerText}
                        </p>
                        {item.explanation && (
                          <p className="mt-1 text-xs text-secondary">{item.explanation}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </section>
          )}
        </section>

        {/* Right Column: Live Competitive High-Score Leaderboard + Synergy Guide */}
        <aside className="bp-side" aria-label="High-score leaderboard and rules">
          <section className="finna-card hl-card">
            <div className="hl-card-head">
              <div className="min-w-0">
                <span className="hl-eyebrow">High-score competition</span>
                <h2 className="hl-title">Blocks Leaderboard</h2>
              </div>
              <button
                type="button"
                className="hl-shuffle-btn"
                onClick={() => loadLeaderboard(boardPeriod)}
                title="Refresh standings"
              >
                ↻
              </button>
            </div>

            <div className="hl-tabs" role="tablist" aria-label="Leaderboard timeframe">
              {(
                [
                  ['week', 'This Week'],
                  ['daily', 'Daily Seed'],
                  ['all', 'All-Time'],
                ] as const
              ).map(([p, lbl]) => (
                <button
                  key={p}
                  type="button"
                  role="tab"
                  aria-selected={boardPeriod === p}
                  onClick={() => setBoardPeriod(p)}
                  className={`hl-tab${boardPeriod === p ? ' is-on' : ''}`}
                >
                  {lbl}
                </button>
              ))}
            </div>

            {boardLoading ? (
              <div className="flex justify-center py-6">
                <CatLoader size="sm" label="Loading scores…" />
              </div>
            ) : !leaderboard?.items?.length ? (
              <div className="hl-empty-box">
                <p className="hl-empty-copy">
                  No public high scores on this board yet. Finish a run &amp; opt into the public
                  leaderboard to claim #1!
                </p>
                <Link to="/profile/rewards" className="hl-empty-cta">
                  Leaderboard privacy →
                </Link>
              </div>
            ) : (
              <ol className="hl-board-list">
                {leaderboard.items.map((row) => {
                  const inner = (
                    <>
                      <span className={`hl-rank${row.rank <= 3 ? ` is-top-${row.rank}` : ''}`}>
                        #{row.rank}
                      </span>
                      <UserAvatar look={row.avatar} initials={row.handle} size={28} />
                      <span className="hl-player">
                        <strong>{row.handle}</strong>
                        <small>
                          {row.lines_cleared} lines · {row.questions_correct} MCQs
                        </small>
                      </span>
                      <span className="hl-score">{row.score.toLocaleString('en-IN')}</span>
                    </>
                  )
                  return (
                    <li key={row.handle + '-' + row.rank}>
                      {row.user_id ? (
                        <Link
                          to={`/creators/${encodeURIComponent(row.user_id)}`}
                          className="hl-board-row is-link"
                        >
                          {inner}
                        </Link>
                      ) : (
                        <div className="hl-board-row">{inner}</div>
                      )}
                    </li>
                  )
                })}
              </ol>
            )}

            {leaderboard?.placement && (
              <Link to="/profile/rewards" className="hl-placement">
                <span className="hl-placement-left">
                  <span className="hl-placement-rank">#{leaderboard.placement.rank}</span>
                  <span className="hl-placement-meta">
                    <strong>Your best</strong>
                    <small>
                      {leaderboard.placement.public
                        ? 'Public on board'
                        : 'Private · opt in on Rewards'}
                    </small>
                  </span>
                </span>
                <span className="hl-placement-val">
                  {leaderboard.placement.score.toLocaleString('en-IN')} pts
                </span>
              </Link>
            )}
          </section>

          <section className="finna-card">
            <span className="hl-eyebrow">How bank questions power your score</span>
            <h2 className="hl-title">Endless Synergy Loop</h2>
            <ul className="mt-3 space-y-2.5 text-sm leading-relaxed text-secondary">
              <li>
                <strong>🔥 Knowledge Multiplier (×1 → ×4):</strong> Every consecutive correct MCQ
                multiplies all row &amp; column blast points.
              </li>
              <li>
                <strong>🧱 Blessed Trays:</strong> Every 2 trays cleared triggers a fast Study Forge
                MCQ — answer right for clean small shapes; miss and 1 clearable stone block drops.
              </li>
              <li>
                <strong>⚡ Laser Clear:</strong> 3 correct MCQs charge a Cross-Laser that wipes an
                entire jammed row + column at once.
              </li>
              <li>
                <strong>🛡 3 Clutch Saves:</strong> If no piece fits, answer a Clutch Question to
                blast open a 3×3 crater and stay alive!
              </li>
            </ul>
            <div className="hl-card-foot mt-4">
              <Link to="/games" className="hl-foot-link">
                ← All games
              </Link>
              <Link to="/games/quest" className="hl-foot-link is-primary">
                Play Finna Quest RPG →
              </Link>
            </div>
          </section>
        </aside>
      </div>

      {/* Bank Question Forge / Reroll / Clutch Save Modal */}
      {qModal && (
        <div className="bp-modal-backdrop" role="presentation">
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="bp-q-title"
            className="bp-modal"
          >
            <span
              className={`bp-q-badge bp-q-badge--${
                qModal.purpose === 'clutch'
                  ? 'clutch'
                  : qModal.purpose === 'reroll'
                    ? 'reroll'
                    : 'forge'
              }`}
            >
              {qModal.purpose === 'clutch'
                ? `🛡 Clutch Save (${MAX_CLUTCH_SAVES - clutchSavesUsed} left)`
                : qModal.purpose === 'reroll'
                  ? '🔄 Answer to Reroll Tray'
                  : qModal.purpose === 'boost'
                    ? '📚 Study Boost · Charge Combo & Laser'
                    : '🔥 Study Forge · Refill Tray'}
            </span>

            <p className="text-xs font-semibold text-secondary">
              {qModal.question.source_appearance?.exam || 'Verified MPSC Bank Question'}
              {qModal.question.source_appearance?.year ? ` · ${qModal.question.source_appearance.year}` : ''}
            </p>

            <SourceQuestionContext
              direction={qModal.question.direction}
              passage={qModal.question.passage}
            />

            <h2 id="bp-q-title" className="bp-q-text">
              <SourceQuestionText
                text={qModal.question.question_markup || qModal.question.question}
              />
            </h2>

            <div className="bp-q-options">
              {qModal.question.options.map((opt, idx) => {
                const locked = qModal.chosen !== null
                const isCorrectOpt = locked && qModal.answerIndex === idx
                const isWrongPick = locked && qModal.chosen === idx && !qModal.correct
                return (
                  <button
                    key={idx}
                    type="button"
                    disabled={locked || qModal.submitting}
                    onClick={() => void handleAnswerQuestion(idx)}
                    className={`bp-q-opt${isCorrectOpt ? ' is-correct' : ''}${isWrongPick ? ' is-wrong' : ''}`}
                  >
                    <span className="bp-q-opt-letter">{LETTERS[idx]}</span>
                    <span className="min-w-0 flex-1">
                      <SourceQuestionText
                        text={qModal.question.options_markup?.[idx] || opt || ''}
                      />
                    </span>
                  </button>
                )
              })}
            </div>

            {qModal.correct !== null && (
              <>
                <div className={`bp-q-feedback ${qModal.correct ? 'is-ok' : 'is-bad'}`}>
                  <strong>
                    {qModal.correct
                      ? qModal.purpose === 'clutch'
                        ? '🛡 Clutch Save! Blasting open a 3×3 crater + blessed pieces!'
                        : '✓ Correct! Knowledge Combo boosted & blessed tray unlocked!'
                      : qModal.purpose === 'clutch'
                        ? '✕ Missed the Clutch Save — run complete.'
                        : '✕ Not quite — Combo reset & 1 stone block added. Learn this one!'}
                  </strong>
                  {qModal.explanation && <p className="mt-1.5">{qModal.explanation}</p>}
                </div>
                <div className="flex justify-end">
                  <button
                    type="button"
                    className="finna-btn"
                    onClick={handleContinueAfterQuestion}
                  >
                    {qModal.purpose === 'clutch' && !qModal.correct
                      ? 'See Final Score →'
                      : 'Back to Board →'}
                  </button>
                </div>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
