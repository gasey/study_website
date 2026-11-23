import { useCallback, useEffect, useState } from 'react'
import { deviceId } from './device'
import { getProfile, type Question } from './api'

export type VaultItemKind = 'saved' | 'custom'
export type VaultQuestionType = 'mcq' | 'flashcard'
export type VaultDifficulty = 'easy' | 'medium' | 'hard' | 'trap'

export interface VaultItem {
  id: string
  kind: VaultItemKind
  canonical_question_id?: string | null
  folder: string
  subject: string
  question_type: VaultQuestionType
  question: string
  options: string[]
  answer_index: number | null
  answer_text: string
  explanation: string
  mnemonic: string
  image_url?: string | null
  image_alt: string
  difficulty: VaultDifficulty
  tags: string[]
  is_favorite: boolean
  mastery_box: 1 | 2 | 3 | 4
  review_count: number
  correct_count: number
  last_reviewed_at?: string | null
  next_review_at?: string | null
  source_meta?: {
    exam?: string | null
    year?: number | null
    qnum?: string | null
    paper_id?: string | null
  }
  created_at: string
  updated_at: string
}

export interface VaultSharePack {
  token: string
  title: string
  description: string
  mode: 'practice' | 'timed' | 'flashcards'
  duration_minutes: number
  items: VaultItem[]
  clones_count: number
  author_name?: string
  created_at: string
  path?: string
}

export interface VaultSummary {
  total: number
  saved: number
  custom: number
  favorites: number
  due: number
  mastered: number
}

export interface VaultTier {
  id: 'bronze' | 'silver' | 'gold' | 'diamond'
  label: string
  tagline: string
  percent: number
}

export const FREE_VAULT_LIMIT = 25
const STORAGE_KEY = 'finna.personal_vault.v1'
const PRO_PREVIEW_KEY = 'finna.personal_vault.pro_preview.v1'
const SHARES_KEY = 'finna.personal_vault.shares.v1'
const VAULT_EVENT = 'finna-vault-change'

const LEITNER_DAYS: Record<number, number> = { 1: 1, 2: 3, 3: 7, 4: 14 }
const HTTPS_IMAGE_RE = /^https:\/\/[^\s"'<>]{4,1000}$/i
const DATA_IMAGE_RE = /^data:image\/(?:png|jpeg|jpg|webp);base64,[A-Za-z0-9+/=]+$/i

export function isValidVaultImage(url?: string | null): boolean {
  if (!url) return false
  const trimmed = url.trim()
  if (trimmed.length > 680_000) return false
  return HTTPS_IMAGE_RE.test(trimmed) || DATA_IMAGE_RE.test(trimmed)
}

export function isVaultItemDue(item: VaultItem, nowMs = Date.now()): boolean {
  if (!item.next_review_at) return true
  const ts = Date.parse(item.next_review_at)
  return Number.isNaN(ts) || ts <= nowMs
}

export function computeVaultSummary(items: VaultItem[]): VaultSummary {
  const now = Date.now()
  let saved = 0
  let custom = 0
  let favorites = 0
  let due = 0
  let mastered = 0
  for (const item of items) {
    if (item.kind === 'custom') custom++
    else saved++
    if (item.is_favorite) favorites++
    if (item.mastery_box >= 3) mastered++
    if (isVaultItemDue(item, now)) due++
  }
  return { total: items.length, saved, custom, favorites, due, mastered }
}

export function computeVaultTier(items: VaultItem[]): VaultTier {
  if (!items.length) {
    return {
      id: 'bronze',
      label: 'Starter Safe',
      tagline: 'Save or craft your first questions to charge the vault.',
      percent: 8,
    }
  }
  const mastered = items.filter((i) => i.mastery_box >= 3).length
  const ratio = mastered / items.length
  const percent = Math.max(12, Math.min(100, Math.round(ratio * 100)))
  if (items.length >= 20 && ratio >= 0.75) {
    return {
      id: 'diamond',
      label: 'Diamond Vault',
      tagline: 'Battle-tested mastery across your personal bank.',
      percent,
    }
  }
  if (items.length >= 10 && ratio >= 0.5) {
    return {
      id: 'gold',
      label: 'Gold Vault',
      tagline: 'Strong recall — keep cracking due questions.',
      percent,
    }
  }
  if (items.length >= 4 && ratio >= 0.25) {
    return {
      id: 'silver',
      label: 'Silver Safe',
      tagline: 'Building momentum in your private revision safe.',
      percent,
    }
  }
  return {
    id: 'bronze',
    label: 'Bronze Safe',
    tagline: 'Drill saved questions to promote them into Box 3–4.',
    percent,
  }
}

export function pickRouletteItem(
  items: VaultItem[],
  excludeId?: string,
): VaultItem | null {
  if (!items.length) return null
  const pool = items.length > 1 && excludeId ? items.filter((i) => i.id !== excludeId) : items
  const now = Date.now()
  const weighted: VaultItem[] = []
  for (const item of pool) {
    const dueBonus = isVaultItemDue(item, now) ? 3 : 1
    const boxBonus = 5 - item.mastery_box
    const favBonus = item.is_favorite ? 1 : 0
    const weight = Math.max(1, dueBonus + boxBonus + favBonus)
    for (let k = 0; k < weight; k++) weighted.push(item)
  }
  return weighted[Math.floor(Math.random() * weighted.length)] ?? pool[0]
}

export function readLocalVault(): VaultItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? (parsed as VaultItem[]) : []
  } catch {
    return []
  }
}

function writeLocalVault(items: VaultItem[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  } catch {
    // Ignore storage quota issues gracefully.
  }
  window.dispatchEvent(new CustomEvent(VAULT_EVENT))
}

export function readProPreview(): boolean {
  try {
    return localStorage.getItem(PRO_PREVIEW_KEY) === '1'
  } catch {
    return false
  }
}

export function setProPreview(enabled: boolean) {
  try {
    if (enabled) localStorage.setItem(PRO_PREVIEW_KEY, '1')
    else localStorage.removeItem(PRO_PREVIEW_KEY)
  } catch {
    // ignore
  }
  window.dispatchEvent(new CustomEvent(VAULT_EVENT))
}

function readLocalShares(): Record<string, VaultSharePack> {
  try {
    const raw = localStorage.getItem(SHARES_KEY)
    return raw ? (JSON.parse(raw) as Record<string, VaultSharePack>) : {}
  } catch {
    return {}
  }
}

function writeLocalShare(pack: VaultSharePack) {
  try {
    const all = readLocalShares()
    all[pack.token] = pack
    localStorage.setItem(SHARES_KEY, JSON.stringify(all))
  } catch {
    // ignore
  }
}

function genId(prefix: string): string {
  return `${prefix}_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`
}

async function vaultFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const r = await fetch(`/api/vault${path}`, {
      credentials: 'include',
      ...init,
      headers: {
        'Content-Type': 'application/json',
        'x-device-id': deviceId(),
        ...(init?.headers || {}),
      },
    })
    if (!r.ok) return null
    return (await r.json()) as T
  } catch {
    return null
  }
}

export function isQuestionInLocalVault(canonicalId: string): boolean {
  return readLocalVault().some((i) => i.canonical_question_id === canonicalId)
}

export async function saveBankQuestionToVault(
  q: Question,
  opts?: {
    folder?: string
    mnemonic?: string
    difficulty?: VaultDifficulty
    is_favorite?: boolean
  },
): Promise<{ item: VaultItem; synced: boolean }> {
  const nowIso = new Date().toISOString()
  const existing = readLocalVault()
  const match = existing.find((i) => i.canonical_question_id === q.id)
  const subject =
    q.taxonomy_topic ||
    q.taxonomy_subject ||
    q.source_appearance?.exam ||
    'General'

  const draft: VaultItem = match
    ? {
        ...match,
        folder: opts?.folder?.trim() || match.folder,
        mnemonic: opts?.mnemonic !== undefined ? opts.mnemonic.trim() : match.mnemonic,
        difficulty: opts?.difficulty || match.difficulty,
        is_favorite:
          opts?.is_favorite !== undefined ? opts.is_favorite : match.is_favorite,
        updated_at: nowIso,
      }
    : {
        id: genId('vlt'),
        kind: 'saved',
        canonical_question_id: q.id,
        folder: opts?.folder?.trim() || 'Saved Bank',
        subject,
        question_type: q.type === 'descriptive' ? 'flashcard' : 'mcq',
        question: q.question,
        options: (q.options || []).filter((o): o is string => typeof o === 'string'),
        answer_index: null,
        answer_text: '',
        explanation: '',
        mnemonic: opts?.mnemonic?.trim() || '',
        image_url: q.figure_image_url || null,
        image_alt: q.figure_image_url ? 'Question diagram' : '',
        difficulty: opts?.difficulty || 'medium',
        tags: [subject].filter(Boolean),
        is_favorite: Boolean(opts?.is_favorite),
        mastery_box: 1,
        review_count: 0,
        correct_count: 0,
        last_reviewed_at: null,
        next_review_at: null,
        source_meta: {
          exam: q.source_appearance?.exam ?? null,
          year: q.source_appearance?.year ?? q.last_year ?? null,
          qnum: q.source_appearance?.qnum ?? null,
          paper_id: q.source_appearance?.paper_id ?? null,
        },
        created_at: nowIso,
        updated_at: nowIso,
      }

  const next = match
    ? existing.map((i) => (i.id === match.id ? draft : i))
    : [draft, ...existing]
  writeLocalVault(next)

  const remote = await vaultFetch<{ item: VaultItem }>('/items', {
    method: 'POST',
    body: JSON.stringify({
      kind: 'saved',
      canonical_question_id: q.id,
      folder: draft.folder,
      subject: draft.subject,
      question_type: draft.question_type,
      question: draft.question,
      options: draft.options,
      answer_index: draft.answer_index,
      answer_text: draft.answer_text,
      explanation: draft.explanation,
      mnemonic: draft.mnemonic,
      image_url: isValidVaultImage(draft.image_url) ? draft.image_url : null,
      image_alt: draft.image_alt,
      difficulty: draft.difficulty,
      tags: draft.tags,
      is_favorite: draft.is_favorite,
      source_meta: draft.source_meta || {},
    }),
  })
  if (remote?.item) {
    const merged = readLocalVault().map((i) =>
      i.canonical_question_id === q.id ? remote.item : i,
    )
    writeLocalVault(merged)
    return { item: remote.item, synced: true }
  }
  return { item: draft, synced: false }
}

export async function removeBankQuestionFromVault(canonicalId: string): Promise<void> {
  const existing = readLocalVault()
  const target = existing.find((i) => i.canonical_question_id === canonicalId)
  if (!target) return
  writeLocalVault(existing.filter((i) => i.id !== target.id))
  await vaultFetch(`/items/${encodeURIComponent(target.id)}`, { method: 'DELETE' })
}

export interface CraftQuestionInput {
  folder: string
  subject: string
  question_type: VaultQuestionType
  question: string
  options: string[]
  answer_index: number | null
  answer_text: string
  explanation: string
  mnemonic: string
  image_url?: string | null
  image_alt: string
  difficulty: VaultDifficulty
  tags: string[]
  is_favorite: boolean
}

export async function craftVaultQuestion(
  input: CraftQuestionInput,
): Promise<{ item: VaultItem; synced: boolean }> {
  const nowIso = new Date().toISOString()
  const safeImage = isValidVaultImage(input.image_url)
    ? input.image_url!.trim()
    : null
  const draft: VaultItem = {
    id: genId('vlt'),
    kind: 'custom',
    canonical_question_id: null,
    folder: input.folder.trim() || 'My Crafted',
    subject: input.subject.trim() || 'General',
    question_type: input.question_type,
    question: input.question.trim(),
    options: input.options.map((o) => o.trim()).filter(Boolean),
    answer_index: input.question_type === 'mcq' ? input.answer_index : null,
    answer_text: input.answer_text.trim(),
    explanation: input.explanation.trim(),
    mnemonic: input.mnemonic.trim(),
    image_url: safeImage,
    image_alt: input.image_alt.trim(),
    difficulty: input.difficulty,
    tags: input.tags
      .map((t) => t.trim().replace(/^#/, ''))
      .filter(Boolean)
      .slice(0, 12),
    is_favorite: input.is_favorite,
    mastery_box: 1,
    review_count: 0,
    correct_count: 0,
    last_reviewed_at: null,
    next_review_at: null,
    created_at: nowIso,
    updated_at: nowIso,
  }

  writeLocalVault([draft, ...readLocalVault()])

  const remote = await vaultFetch<{ item: VaultItem }>('/items', {
    method: 'POST',
    body: JSON.stringify({
      kind: 'custom',
      folder: draft.folder,
      subject: draft.subject,
      question_type: draft.question_type,
      question: draft.question,
      options: draft.options,
      answer_index: draft.answer_index,
      answer_text: draft.answer_text,
      explanation: draft.explanation,
      mnemonic: draft.mnemonic,
      image_url: draft.image_url,
      image_alt: draft.image_alt,
      difficulty: draft.difficulty,
      tags: draft.tags,
      is_favorite: draft.is_favorite,
    }),
  })

  if (remote?.item) {
    writeLocalVault(
      readLocalVault().map((i) => (i.id === draft.id ? remote.item : i)),
    )
    return { item: remote.item, synced: true }
  }
  return { item: draft, synced: false }
}

export async function updateVaultItem(
  itemId: string,
  patch: Partial<VaultItem> & { clear_image?: boolean },
): Promise<VaultItem | null> {
  const existing = readLocalVault()
  const target = existing.find((i) => i.id === itemId)
  if (!target) return null
  const updated: VaultItem = {
    ...target,
    ...patch,
    image_url: patch.clear_image
      ? null
      : patch.image_url !== undefined
        ? patch.image_url
        : target.image_url,
    updated_at: new Date().toISOString(),
  }
  writeLocalVault(existing.map((i) => (i.id === itemId ? updated : i)))
  const remote = await vaultFetch<{ item: VaultItem }>(
    `/items/${encodeURIComponent(itemId)}`,
    {
      method: 'PATCH',
      body: JSON.stringify(patch),
    },
  )
  if (remote?.item) {
    writeLocalVault(
      readLocalVault().map((i) => (i.id === itemId ? remote.item : i)),
    )
    return remote.item
  }
  return updated
}

export async function deleteVaultItem(itemId: string): Promise<void> {
  writeLocalVault(readLocalVault().filter((i) => i.id !== itemId))
  await vaultFetch(`/items/${encodeURIComponent(itemId)}`, { method: 'DELETE' })
}

export async function recordVaultReview(
  itemId: string,
  correct: boolean,
): Promise<VaultItem | null> {
  const existing = readLocalVault()
  const target = existing.find((i) => i.id === itemId)
  if (!target) return null
  const nextBox = (correct ? Math.min(4, target.mastery_box + 1) : 1) as 1 | 2 | 3 | 4
  const now = new Date()
  const nextDue = new Date(now.getTime() + LEITNER_DAYS[nextBox] * 86_400_000)
  const updated: VaultItem = {
    ...target,
    mastery_box: nextBox,
    review_count: target.review_count + 1,
    correct_count: target.correct_count + (correct ? 1 : 0),
    last_reviewed_at: now.toISOString(),
    next_review_at: nextDue.toISOString(),
    updated_at: now.toISOString(),
  }
  writeLocalVault(existing.map((i) => (i.id === itemId ? updated : i)))
  const remote = await vaultFetch<{ item: VaultItem }>(
    `/items/${encodeURIComponent(itemId)}/review`,
    {
      method: 'POST',
      body: JSON.stringify({ correct }),
    },
  )
  if (remote?.item) {
    writeLocalVault(
      readLocalVault().map((i) => (i.id === itemId ? remote.item : i)),
    )
    return remote.item
  }
  return updated
}

export async function createVaultSharePack(payload: {
  title: string
  description: string
  mode: 'practice' | 'timed' | 'flashcards'
  duration_minutes: number
  items: VaultItem[]
}): Promise<VaultSharePack> {
  const remote = await vaultFetch<{
    share: Omit<VaultSharePack, 'items'> & { item_count: number; path: string }
  }>('/shares', {
    method: 'POST',
    body: JSON.stringify({
      title: payload.title,
      description: payload.description,
      mode: payload.mode,
      duration_minutes: payload.duration_minutes,
      item_ids: payload.items.map((i) => i.id),
    }),
  })
  const pack: VaultSharePack = {
    token: remote?.share?.token || genId('vsh'),
    title: payload.title,
    description: payload.description,
    mode: payload.mode,
    duration_minutes: payload.duration_minutes,
    items: payload.items,
    clones_count: remote?.share?.clones_count ?? 0,
    created_at: remote?.share?.created_at || new Date().toISOString(),
    path: remote?.share?.path,
  }
  writeLocalShare(pack)
  return pack
}

export async function loadVaultSharePack(token: string): Promise<VaultSharePack | null> {
  const remote = await vaultFetch<{ share: VaultSharePack }>(
    `/shares/${encodeURIComponent(token)}`,
  )
  if (remote?.share) return remote.share
  return readLocalShares()[token] ?? null
}

export async function cloneVaultSharePack(
  pack: VaultSharePack,
): Promise<{ cloned: number; folder: string }> {
  const remote = await vaultFetch<{ cloned: number; folder: string }>(
    `/shares/${encodeURIComponent(pack.token)}/clone`,
    { method: 'POST' },
  )
  const folder = pack.title.slice(0, 60) || 'Shared Pack'
  const existing = readLocalVault()
  const nowIso = new Date().toISOString()
  const clonedItems: VaultItem[] = pack.items.map((item) => ({
    ...item,
    id: genId('vlt'),
    folder,
    mastery_box: 1,
    review_count: 0,
    correct_count: 0,
    last_reviewed_at: null,
    next_review_at: null,
    created_at: nowIso,
    updated_at: nowIso,
  }))
  writeLocalVault([...clonedItems, ...existing])
  return remote || { cloned: clonedItems.length, folder }
}

export function importVaultItemsFromJson(rawJson: string): {
  imported: number
  error?: string
} {
  try {
    const parsed = JSON.parse(rawJson)
    const list = Array.isArray(parsed)
      ? parsed
      : Array.isArray(parsed?.items)
        ? parsed.items
        : null
    if (!list || !list.length) {
      return { imported: 0, error: 'No valid questions found in that Vault pack.' }
    }
    const nowIso = new Date().toISOString()
    const fresh: VaultItem[] = []
    for (const raw of list.slice(0, 100)) {
      if (!raw || typeof raw.question !== 'string' || raw.question.trim().length < 3) {
        continue
      }
      fresh.push({
        id: genId('vlt'),
        kind: raw.kind === 'saved' ? 'saved' : 'custom',
        canonical_question_id: raw.canonical_question_id || null,
        folder: String(raw.folder || 'Imported Pack').slice(0, 60),
        subject: String(raw.subject || 'General').slice(0, 80),
        question_type: raw.question_type === 'flashcard' ? 'flashcard' : 'mcq',
        question: raw.question.trim().slice(0, 4000),
        options: Array.isArray(raw.options)
          ? raw.options.map((o: unknown) => String(o).trim()).filter(Boolean).slice(0, 6)
          : [],
        answer_index:
          typeof raw.answer_index === 'number' ? raw.answer_index : null,
        answer_text: String(raw.answer_text || '').slice(0, 2000),
        explanation: String(raw.explanation || '').slice(0, 4000),
        mnemonic: String(raw.mnemonic || '').slice(0, 1000),
        image_url: isValidVaultImage(raw.image_url) ? raw.image_url : null,
        image_alt: String(raw.image_alt || '').slice(0, 200),
        difficulty: ['easy', 'medium', 'hard', 'trap'].includes(raw.difficulty)
          ? raw.difficulty
          : 'medium',
        tags: Array.isArray(raw.tags)
          ? raw.tags.map((t: unknown) => String(t).trim()).filter(Boolean).slice(0, 12)
          : [],
        is_favorite: Boolean(raw.is_favorite),
        mastery_box: 1,
        review_count: 0,
        correct_count: 0,
        last_reviewed_at: null,
        next_review_at: null,
        created_at: nowIso,
        updated_at: nowIso,
      })
    }
    if (!fresh.length) {
      return { imported: 0, error: 'Pack did not contain readable questions.' }
    }
    writeLocalVault([...fresh, ...readLocalVault()])
    return { imported: fresh.length }
  } catch {
    return { imported: 0, error: 'Invalid JSON format. Paste a Finna Vault pack.' }
  }
}

/** Compress an uploaded image File safely to a compact JPEG data URL (no SVG/HTML). */
export async function compressImageFileToDataUrl(file: File): Promise<string> {
  if (!/^image\/(png|jpeg|jpg|webp)$/i.test(file.type)) {
    throw new Error('Please choose a PNG, JPEG, or WebP image.')
  }
  const objectUrl = URL.createObjectURL(file)
  try {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const el = new Image()
      el.onload = () => resolve(el)
      el.onerror = () => reject(new Error('Could not read that image file.'))
      el.src = objectUrl
    })
    const maxDim = 960
    const scale = Math.min(1, maxDim / Math.max(img.width || 1, img.height || 1))
    const w = Math.max(1, Math.round(img.width * scale))
    const h = Math.max(1, Math.round(img.height * scale))
    const canvas = document.createElement('canvas')
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('Image processing unavailable in this browser.')
    ctx.drawImage(img, 0, 0, w, h)
    const dataUrl = canvas.toDataURL('image/jpeg', 0.78)
    if (dataUrl.length > 650_000) {
      return canvas.toDataURL('image/jpeg', 0.55)
    }
    return dataUrl
  } finally {
    URL.revokeObjectURL(objectUrl)
  }
}

export function formatVaultQuizText(title: string, items: VaultItem[]): string {
  const lines = [`🔐 Finna Vault Pack: ${title} (${items.length} questions)`, '']
  items.slice(0, 15).forEach((item, idx) => {
    lines.push(`Q${idx + 1}. ${item.question}`)
    item.options.forEach((opt, oi) => {
      lines.push(`  ${String.fromCharCode(65 + oi)}) ${opt}`)
    })
    lines.push('')
  })
  return lines.join('\n').trim()
}

export function useVaultState() {
  const [items, setItems] = useState<VaultItem[]>(() => readLocalVault())
  const [serverPro, setServerPro] = useState(false)
  const [proPreview, setProPreviewState] = useState<boolean>(() => readProPreview())
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    setItems(readLocalVault())
    setProPreviewState(readProPreview())
    const [remote, profile] = await Promise.all([
      vaultFetch<{ is_pro: boolean; items: VaultItem[] }>(''),
      getProfile().catch(() => null),
    ])
    const profilePro =
      profile?.plan_code === 'pro' || profile?.role === 'owner'
    if (remote) {
      setServerPro(Boolean(remote.is_pro || profilePro))
      if (remote.items.length > 0) {
        const localOnly = readLocalVault().filter(
          (l) => !remote.items.some((r) => r.id === l.id),
        )
        const combined = [...remote.items, ...localOnly]
        setItems(combined)
      }
    } else if (profilePro) {
      setServerPro(true)
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    void refresh()
    const onChange = () => {
      setItems(readLocalVault())
      setProPreviewState(readProPreview())
    }
    window.addEventListener(VAULT_EVENT, onChange)
    window.addEventListener('ism-auth-change', () => void refresh())
    return () => {
      window.removeEventListener(VAULT_EVENT, onChange)
    }
  }, [refresh])

  const effectivePro = serverPro || proPreview
  const summary = computeVaultSummary(items)
  const tier = computeVaultTier(items)

  return {
    items,
    summary,
    tier,
    serverPro,
    proPreview,
    effectivePro,
    loading,
    refresh,
    toggleProPreview: () => setProPreview(!readProPreview()),
  }
}
