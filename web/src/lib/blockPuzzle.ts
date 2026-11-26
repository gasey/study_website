import type { AvatarLook } from './avatar'

export const BOARD_SIZE = 8
export const MAX_CLUTCH_SAVES = 3
export const LASER_CHARGE_COST = 3

export type BlockColor = 'gk' | 'english' | 'math' | 'reasoning' | 'mizo' | 'stone'
export type CellValue = BlockColor | null
export type Board = CellValue[][]
export type BlockMode = 'endless' | 'daily'
export type BoardPeriod = 'week' | 'daily' | 'all'

export interface PieceSpec {
  id: string
  uid: string
  tier: 'clean' | 'standard' | 'heavy'
  color: Exclude<BlockColor, 'stone'>
  /** Relative [row, col] offsets starting from (0,0) */
  cells: readonly (readonly [number, number])[]
  rows: number
  cols: number
}

const COLORS: readonly Exclude<BlockColor, 'stone'>[] = [
  'gk',
  'english',
  'math',
  'reasoning',
  'mizo',
]

export const SUBJECT_SCOPES = [
  { id: 'all', label: 'All MPSC Core', apiSubject: undefined },
  { id: 'gk-gs', label: 'GK & GS', apiSubject: 'gk-gs' },
  { id: 'english', label: 'English', apiSubject: 'english' },
  { id: 'mathematics', label: 'Maths', apiSubject: 'mathematics' },
  { id: 'reasoning-and-aptitude', label: 'Reasoning', apiSubject: 'reasoning-and-aptitude' },
  { id: 'mizo', label: 'Mizo', apiSubject: 'mizo' },
  { id: 'computer-science', label: 'Computer', apiSubject: 'computer-science' },
  { id: 'science', label: 'Science', apiSubject: 'science' },
] as const

interface RawShape {
  id: string
  tier: 'clean' | 'standard' | 'heavy'
  cells: readonly (readonly [number, number])[]
}

const SHAPES: readonly RawShape[] = [
  // Clean / blessed tier
  { id: 'dot', tier: 'clean', cells: [[0, 0]] },
  { id: 'h2', tier: 'clean', cells: [[0, 0], [0, 1]] },
  { id: 'v2', tier: 'clean', cells: [[0, 0], [1, 0]] },
  { id: 'h3', tier: 'clean', cells: [[0, 0], [0, 1], [0, 2]] },
  { id: 'v3', tier: 'clean', cells: [[0, 0], [1, 0], [2, 0]] },
  { id: 'sq2', tier: 'clean', cells: [[0, 0], [0, 1], [1, 0], [1, 1]] },
  { id: 'l3a', tier: 'clean', cells: [[0, 0], [1, 0], [1, 1]] },
  { id: 'l3b', tier: 'clean', cells: [[0, 0], [0, 1], [1, 0]] },
  // Standard tier
  { id: 'h4', tier: 'standard', cells: [[0, 0], [0, 1], [0, 2], [0, 3]] },
  { id: 'v4', tier: 'standard', cells: [[0, 0], [1, 0], [2, 0], [3, 0]] },
  { id: 't4', tier: 'standard', cells: [[0, 0], [0, 1], [0, 2], [1, 1]] },
  { id: 'l4', tier: 'standard', cells: [[0, 0], [1, 0], [2, 0], [2, 1]] },
  { id: 'j4', tier: 'standard', cells: [[0, 1], [1, 1], [2, 1], [2, 0]] },
  { id: 's4', tier: 'standard', cells: [[0, 1], [0, 2], [1, 0], [1, 1]] },
  { id: 'z4', tier: 'standard', cells: [[0, 0], [0, 1], [1, 1], [1, 2]] },
  { id: 'rect23', tier: 'standard', cells: [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2]] },
  // Heavy tier
  { id: 'h5', tier: 'heavy', cells: [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4]] },
  { id: 'v5', tier: 'heavy', cells: [[0, 0], [1, 0], [2, 0], [3, 0], [4, 0]] },
  { id: 'sq3', tier: 'heavy', cells: [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]] },
  { id: 'bigL', tier: 'heavy', cells: [[0, 0], [1, 0], [2, 0], [2, 1], [2, 2]] },
]

const CLEAN_SHAPES = SHAPES.filter((s) => s.tier === 'clean')
const STANDARD_SHAPES = SHAPES.filter((s) => s.tier === 'standard')
const HEAVY_SHAPES = SHAPES.filter((s) => s.tier === 'heavy')

export function hashSeed(str: string): number {
  let h = 2166136261 >>> 0
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

export function createRng(seed: string | number): () => number {
  let a = typeof seed === 'number' ? seed >>> 0 : hashSeed(seed)
  return () => {
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

export function createEmptyBoard(): Board {
  return Array.from({ length: BOARD_SIZE }, () =>
    Array.from({ length: BOARD_SIZE }, () => null),
  )
}

export function cloneBoard(board: Board): Board {
  return board.map((row) => [...row])
}

let pieceUidCounter = 0

function buildPiece(raw: RawShape, rng: () => number): PieceSpec {
  const maxR = Math.max(...raw.cells.map(([r]) => r))
  const maxC = Math.max(...raw.cells.map(([, c]) => c))
  const color = COLORS[Math.floor(rng() * COLORS.length)]
  return {
    id: raw.id,
    uid: `${raw.id}_${++pieceUidCounter}`,
    tier: raw.tier,
    color,
    cells: raw.cells,
    rows: maxR + 1,
    cols: maxC + 1,
  }
}

export function dealTray(
  rng: () => number,
  bias: 'blessed' | 'normal' | 'tough' = 'normal',
): PieceSpec[] {
  const out: PieceSpec[] = []
  for (let i = 0; i < 3; i++) {
    const roll = rng()
    let pool: readonly RawShape[]
    if (bias === 'blessed') {
      pool = roll < 0.78 ? CLEAN_SHAPES : STANDARD_SHAPES
    } else if (bias === 'tough') {
      pool = roll < 0.25 ? CLEAN_SHAPES : roll < 0.65 ? STANDARD_SHAPES : HEAVY_SHAPES
    } else {
      pool = roll < 0.48 ? CLEAN_SHAPES : roll < 0.86 ? STANDARD_SHAPES : HEAVY_SHAPES
    }
    const shape = pool[Math.floor(rng() * pool.length)]
    out.push(buildPiece(shape, rng))
  }
  return out
}

export function canPlace(board: Board, piece: PieceSpec, row: number, col: number): boolean {
  for (const [dr, dc] of piece.cells) {
    const r = row + dr
    const c = col + dc
    if (r < 0 || r >= BOARD_SIZE || c < 0 || c >= BOARD_SIZE) return false
    if (board[r][c] !== null) return false
  }
  return true
}

export function previewClearLines(
  board: Board,
  piece: PieceSpec,
  row: number,
  col: number,
): { rows: number[]; cols: number[] } {
  if (!canPlace(board, piece, row, col)) return { rows: [], cols: [] }
  const next = cloneBoard(board)
  for (const [dr, dc] of piece.cells) {
    next[row + dr][col + dc] = piece.color
  }
  const rows: number[] = []
  const cols: number[] = []
  for (let r = 0; r < BOARD_SIZE; r++) {
    if (next[r].every((cell) => cell !== null)) rows.push(r)
  }
  for (let c = 0; c < BOARD_SIZE; c++) {
    let full = true
    for (let r = 0; r < BOARD_SIZE; r++) {
      if (next[r][c] === null) {
        full = false
        break
      }
    }
    if (full) cols.push(c)
  }
  return { rows, cols }
}

export function placePiece(board: Board, piece: PieceSpec, row: number, col: number): {
  board: Board
  clearedRows: number[]
  clearedCols: number[]
  totalLines: number
  cellsPlaced: number
} {
  const next = cloneBoard(board)
  for (const [dr, dc] of piece.cells) {
    next[row + dr][col + dc] = piece.color
  }
  const clearedRows: number[] = []
  const clearedCols: number[] = []
  for (let r = 0; r < BOARD_SIZE; r++) {
    if (next[r].every((cell) => cell !== null)) clearedRows.push(r)
  }
  for (let c = 0; c < BOARD_SIZE; c++) {
    let full = true
    for (let r = 0; r < BOARD_SIZE; r++) {
      if (next[r][c] === null) {
        full = false
        break
      }
    }
    if (full) clearedCols.push(c)
  }
  for (const r of clearedRows) {
    for (let c = 0; c < BOARD_SIZE; c++) next[r][c] = null
  }
  for (const c of clearedCols) {
    for (let r = 0; r < BOARD_SIZE; r++) next[r][c] = null
  }
  return {
    board: next,
    clearedRows,
    clearedCols,
    totalLines: clearedRows.length + clearedCols.length,
    cellsPlaced: piece.cells.length,
  }
}

export function applyLaserClear(board: Board, row: number, col: number): {
  board: Board
  clearedCells: number
} {
  const next = cloneBoard(board)
  let clearedCells = 0
  for (let c = 0; c < BOARD_SIZE; c++) {
    if (next[row][c] !== null) {
      next[row][c] = null
      clearedCells++
    }
  }
  for (let r = 0; r < BOARD_SIZE; r++) {
    if (next[r][col] !== null) {
      next[r][col] = null
      clearedCells++
    }
  }
  return { board: next, clearedCells }
}

/** Clears the densest 3x3 region on the board to rescue a jammed run on a Clutch Save. */
export function applyClutchBlast(board: Board): {
  board: Board
  origin: [number, number]
  clearedCells: number
} {
  let bestR = 2
  let bestC = 2
  let bestCount = -1
  for (let r = 0; r <= BOARD_SIZE - 3; r++) {
    for (let c = 0; c <= BOARD_SIZE - 3; c++) {
      let count = 0
      for (let dr = 0; dr < 3; dr++) {
        for (let dc = 0; dc < 3; dc++) {
          if (board[r + dr][c + dc] !== null) count++
        }
      }
      if (count > bestCount) {
        bestCount = count
        bestR = r
        bestC = c
      }
    }
  }
  const next = cloneBoard(board)
  let clearedCells = 0
  for (let dr = 0; dr < 3; dr++) {
    for (let dc = 0; dc < 3; dc++) {
      if (next[bestR + dr][bestC + dc] !== null) {
        next[bestR + dr][bestC + dc] = null
        clearedCells++
      }
    }
  }
  return { board: next, origin: [bestR, bestC], clearedCells }
}

/** Drops 1 clearable stone cell into an open square as gentle risk-reward on a wrong MCQ. */
export function addStoneBlock(board: Board, rng: () => number): Board {
  const open: [number, number][] = []
  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      if (board[r][c] === null) open.push([r, c])
    }
  }
  if (!open.length) return board
  const [r, c] = open[Math.floor(rng() * open.length)]
  const next = cloneBoard(board)
  next[r][c] = 'stone'
  return next
}

export function pieceFitsAnywhere(board: Board, piece: PieceSpec): boolean {
  for (let r = 0; r <= BOARD_SIZE - piece.rows; r++) {
    for (let c = 0; c <= BOARD_SIZE - piece.cols; c++) {
      if (canPlace(board, piece, r, c)) return true
    }
  }
  return false
}

export function anyPieceFits(board: Board, tray: (PieceSpec | null)[]): boolean {
  return tray.some((p) => p !== null && pieceFitsAnywhere(board, p))
}

export function knowledgeMultiplier(streak: number): number {
  if (streak >= 10) return 4
  if (streak >= 7) return 3
  if (streak >= 4) return 2.5
  if (streak >= 2) return 2
  if (streak >= 1) return 1.5
  return 1
}

export function scorePlacement(
  cellsPlaced: number,
  totalLines: number,
  knowledgeStreak: number,
  clearStreak: number,
): number {
  const mult = knowledgeMultiplier(knowledgeStreak)
  const base = cellsPlaced * 10
  const linePoints = totalLines > 0 ? Math.round(totalLines * totalLines * 120 * mult) : 0
  const streakBonus = totalLines > 0 && clearStreak > 1 ? clearStreak * 60 : 0
  return base + linePoints + streakBonus
}

export function todayIstDate(): string {
  return new Date(Date.now() + 5.5 * 3600_000).toISOString().slice(0, 10)
}

// Lightweight Web Audio synth SFX (zero external assets)
class BlockSfx {
  private ctx: AudioContext | null = null
  muted = false

  private tone(freq: number, dur: number, type: OscillatorType = 'triangle', gain = 0.08, delay = 0) {
    if (this.muted || typeof window === 'undefined') return
    try {
      const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
      if (!Ctx) return
      if (!this.ctx) this.ctx = new Ctx()
      if (this.ctx.state === 'suspended') void this.ctx.resume()
      const now = this.ctx.currentTime + delay
      const osc = this.ctx.createOscillator()
      const g = this.ctx.createGain()
      osc.type = type
      osc.frequency.setValueAtTime(freq, now)
      g.gain.setValueAtTime(gain, now)
      g.gain.exponentialRampToValueAtTime(0.001, now + dur)
      osc.connect(g)
      g.connect(this.ctx.destination)
      osc.start(now)
      osc.stop(now + dur + 0.02)
    } catch {
      /* audio blocked */
    }
  }

  place() {
    this.tone(240, 0.06, 'triangle', 0.09)
    this.tone(360, 0.05, 'sine', 0.05, 0.02)
  }

  clear(lines: number) {
    const notes = [440, 554, 659, 880, 1046]
    const count = Math.min(notes.length, Math.max(2, lines + 1))
    for (let i = 0; i < count; i++) {
      this.tone(notes[i], 0.14, 'triangle', 0.09, i * 0.055)
    }
  }

  correct() {
    this.tone(523, 0.1, 'triangle', 0.09, 0)
    this.tone(659, 0.1, 'triangle', 0.09, 0.07)
    this.tone(784, 0.16, 'sine', 0.1, 0.14)
  }

  wrong() {
    this.tone(210, 0.14, 'sawtooth', 0.05, 0)
    this.tone(165, 0.18, 'sawtooth', 0.05, 0.09)
  }

  laser() {
    this.tone(880, 0.09, 'sawtooth', 0.06, 0)
    this.tone(440, 0.14, 'triangle', 0.08, 0.05)
    this.tone(660, 0.16, 'sine', 0.08, 0.1)
  }
}

export const blockSfx = new BlockSfx()

// Backend API client
export interface BlockRunStart {
  run_id: string
  mode: BlockMode
  daily_date: string | null
  daily_seed: string | null
  subject_scope: string
}

export interface BlockRunProgressBody {
  score: number
  lines_cleared: number
  pieces_placed: number
  questions_answered: number
  questions_correct: number
  best_streak: number
  max_combo: number
  clutch_saves_used: number
}

export interface BlockRunResult {
  run_id: string
  status: 'active' | 'finished'
  score: number
  lines_cleared: number
  xp_awarded: number
  is_new_best: boolean
}

export interface BlockLeaderboardRow {
  rank: number
  handle: string
  score: number
  lines_cleared: number
  questions_correct: number
  best_streak: number
  level: number
  avatar?: AvatarLook | null
  profile_public: boolean
  user_id?: string | null
}

export interface BlockLeaderboardData {
  period: BoardPeriod
  today_ist: string
  total: number
  items: BlockLeaderboardRow[]
  placement: {
    rank: number
    score: number
    lines_cleared: number
    questions_correct: number
    public: boolean
  } | null
}

export interface MyBlockStats {
  best_endless: number
  best_daily_today: number
  best_lines: number
  total_runs: number
  total_lines: number
  total_questions_correct: number
  today_ist: string
}

async function blocksFetch<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch('/api/blocks' + path, {
    method: body !== undefined ? 'POST' : 'GET',
    credentials: 'same-origin',
    headers: {
      Accept: 'application/json',
      ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  })
  if (!res.ok) throw new Error(`Blocks API ${res.status}`)
  return (await res.json()) as T
}

export const startBlockRun = (mode: BlockMode, subject_scope: string) =>
  blocksFetch<BlockRunStart>('/runs', { mode, subject_scope })

export const checkpointBlockRun = (runId: string, body: BlockRunProgressBody) =>
  blocksFetch<BlockRunResult>(`/runs/${encodeURIComponent(runId)}/checkpoint`, body)

export const finishBlockRun = (runId: string, body: BlockRunProgressBody) =>
  blocksFetch<BlockRunResult>(`/runs/${encodeURIComponent(runId)}/finish`, body)

export const getBlockLeaderboard = (period: BoardPeriod) =>
  blocksFetch<BlockLeaderboardData>(`/leaderboard?period=${encodeURIComponent(period)}&limit=15`)

export const getMyBlockStats = () => blocksFetch<MyBlockStats>('/me')
