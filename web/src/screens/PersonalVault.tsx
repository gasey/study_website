import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
} from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import VaultSafeIllustration from '../components/VaultSafeIllustration'
import {
  FREE_VAULT_LIMIT,
  cloneVaultSharePack,
  compressImageFileToDataUrl,
  craftVaultQuestion,
  createVaultSharePack,
  deleteVaultItem,
  formatVaultQuizText,
  importVaultItemsFromJson,
  isValidVaultImage,
  isVaultItemDue,
  loadVaultSharePack,
  pickRouletteItem,
  recordVaultReview,
  updateVaultItem,
  useVaultState,
  type CraftQuestionInput,
  type VaultDifficulty,
  type VaultItem,
  type VaultQuestionType,
  type VaultSharePack,
} from '../lib/vault'

type Compartment = 'all' | 'favorites' | 'custom' | 'saved' | 'due'
type TestMode = 'practice' | 'timed' | 'flashcards'

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']
const DIFFICULTIES: { id: VaultDifficulty; label: string }[] = [
  { id: 'easy', label: 'Easy' },
  { id: 'medium', label: 'Medium' },
  { id: 'hard', label: 'Hard' },
  { id: 'trap', label: 'Trap!' },
]
const BOX_LABELS: Record<number, string> = {
  1: 'Box 1 · Shaky',
  2: 'Box 2 · Learning',
  3: 'Box 3 · Solid',
  4: 'Box 4 · Locked In',
}

const EMPTY_CRAFT: CraftQuestionInput = {
  folder: 'High-Yield',
  subject: 'General Studies',
  question_type: 'mcq',
  question: '',
  options: ['', '', '', ''],
  answer_index: 0,
  answer_text: '',
  explanation: '',
  mnemonic: '',
  image_url: '',
  image_alt: '',
  difficulty: 'medium',
  tags: [],
  is_favorite: false,
}

export default function PersonalVault() {
  const { token: shareToken } = useParams()
  const [params, setParams] = useSearchParams()
  const {
    items,
    summary,
    tier,
    serverPro,
    proPreview,
    effectivePro,
    toggleProPreview,
  } = useVaultState()

  // Safe door & interactive states
  const [safeOpen, setSafeOpen] = useState(true)
  const [spinning, setSpinning] = useState(false)
  const [compartment, setCompartment] = useState<Compartment>('all')
  const [folderFilter, setFolderFilter] = useState('all')
  const [difficultyFilter, setDifficultyFilter] = useState<'all' | VaultDifficulty>('all')
  const [query, setQuery] = useState('')
  const [notice, setNotice] = useState('')
  const [peekIds, setPeekIds] = useState<Record<string, boolean>>({})
  const [lightboxImg, setLightboxImg] = useState<{ url: string; alt: string } | null>(null)

  // Inline note editing
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null)
  const [noteDraft, setNoteDraft] = useState('')

  // Question Crafter modal
  const [craftOpen, setCraftOpen] = useState(false)
  const [editingItemId, setEditingItemId] = useState<string | null>(null)
  const [craft, setCraft] = useState<CraftQuestionInput>(EMPTY_CRAFT)
  const [tagsText, setTagsText] = useState('')
  const [craftError, setCraftError] = useState('')
  const [uploadingImg, setUploadingImg] = useState(false)

  // Spin-the-dial roulette modal
  const [rouletteItem, setRouletteItem] = useState<VaultItem | null>(null)
  const [roulettePick, setRoulettePick] = useState<number | null>(null)
  const [rouletteFlipped, setRouletteFlipped] = useState(false)

  // Test & Flashcard Studio
  const [testOpen, setTestOpen] = useState(false)
  const [testSetupMode, setTestSetupMode] = useState<TestMode>('practice')
  const [testMinutes, setTestMinutes] = useState(10)
  const [testActive, setTestActive] = useState(false)
  const [testItems, setTestItems] = useState<VaultItem[]>([])
  const [testIdx, setTestIdx] = useState(0)
  const [testAnswers, setTestAnswers] = useState<Record<string, number | boolean>>({})
  const [testFlipped, setTestFlipped] = useState(false)
  const [testSubmitted, setTestSubmitted] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState(600)
  const [streak, setStreak] = useState(0)

  // Share & Import/Export modal
  const [shareOpen, setShareOpen] = useState(false)
  const [shareTitle, setShareTitle] = useState('My Finna Revision Pack')
  const [shareDesc, setShareDesc] = useState('')
  const [shareMode, setShareMode] = useState<TestMode>('practice')
  const [shareDuration, setShareDuration] = useState(10)
  const [createdShare, setCreatedShare] = useState<VaultSharePack | null>(null)
  const [importJson, setImportJson] = useState('')
  const [importMsg, setImportMsg] = useState('')
  const [copiedText, setCopiedText] = useState('')

  // Viewing a shared link (/vault/share/:token)
  const [sharedPack, setSharedPack] = useState<VaultSharePack | null>(null)
  const [sharedLoading, setSharedLoading] = useState(false)

  const spinTimer = useRef<number | null>(null)

  useEffect(() => {
    return () => {
      if (spinTimer.current) window.clearTimeout(spinTimer.current)
    }
  }, [])

  // Handle deep-link quick actions (?action=craft or ?action=spin)
  useEffect(() => {
    const action = params.get('action')
    if (!action) return
    if (action === 'craft') {
      setCraftOpen(true)
      setEditingItemId(null)
      setCraft(EMPTY_CRAFT)
      setTagsText('')
    } else if (action === 'spin') {
      triggerSpin()
    }
    const next = new URLSearchParams(params)
    next.delete('action')
    setParams(next, { replace: true })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params])

  // Load shared pack if on /vault/share/:token
  useEffect(() => {
    if (!shareToken) {
      setSharedPack(null)
      return
    }
    let live = true
    setSharedLoading(true)
    void loadVaultSharePack(shareToken).then((pack) => {
      if (live) {
        setSharedPack(pack)
        setSharedLoading(false)
      }
    })
    return () => {
      live = false
    }
  }, [shareToken])

  // Timed mock countdown
  useEffect(() => {
    if (!testActive || testSetupMode !== 'timed' || testSubmitted) return
    const timer = window.setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          setTestSubmitted(true)
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => window.clearInterval(timer)
  }, [testActive, testSetupMode, testSubmitted])

  const folders = useMemo(() => {
    const map = new Map<string, number>()
    for (const item of items) {
      const f = item.folder || 'General'
      map.set(f, (map.get(f) || 0) + 1)
    }
    return [...map.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
  }, [items])

  const filteredItems = useMemo(() => {
    const needle = query.trim().toLowerCase()
    const now = Date.now()
    return items.filter((item) => {
      if (compartment === 'favorites' && !item.is_favorite) return false
      if (compartment === 'custom' && item.kind !== 'custom') return false
      if (compartment === 'saved' && item.kind !== 'saved') return false
      if (compartment === 'due' && !isVaultItemDue(item, now)) return false
      if (folderFilter !== 'all' && (item.folder || 'General') !== folderFilter) return false
      if (difficultyFilter !== 'all' && item.difficulty !== difficultyFilter) return false
      if (!needle) return true
      const hay = [
        item.question,
        item.subject,
        item.folder,
        item.mnemonic,
        item.explanation,
        ...item.tags,
      ]
        .join(' ')
        .toLowerCase()
      return hay.includes(needle)
    })
  }, [items, compartment, folderFilter, difficultyFilter, query])

  function flash(msg: string) {
    setNotice(msg)
    window.setTimeout(() => {
      setNotice((cur) => (cur === msg ? '' : cur))
    }, 3400)
  }

  function triggerSpin() {
    if (!items.length) {
      flash('Save or craft at least one question first to spin the Vault dial!')
      return
    }
    setSafeOpen(false)
    setSpinning(true)
    if (spinTimer.current) window.clearTimeout(spinTimer.current)
    spinTimer.current = window.setTimeout(() => {
      setSpinning(false)
      setSafeOpen(true)
      const picked = pickRouletteItem(items, rouletteItem?.id)
      setRouletteItem(picked)
      setRoulettePick(null)
      setRouletteFlipped(false)
    }, 640)
  }

  function openCrafterForNew() {
    setEditingItemId(null)
    setCraft({
      ...EMPTY_CRAFT,
      folder: folderFilter !== 'all' ? folderFilter : 'High-Yield',
    })
    setTagsText('')
    setCraftError('')
    setCraftOpen(true)
  }

  function openCrafterForEdit(item: VaultItem) {
    setEditingItemId(item.id)
    setCraft({
      folder: item.folder,
      subject: item.subject,
      question_type: item.question_type,
      question: item.question,
      options: item.options.length >= 2 ? [...item.options] : ['', '', '', ''],
      answer_index: item.answer_index ?? 0,
      answer_text: item.answer_text || '',
      explanation: item.explanation || '',
      mnemonic: item.mnemonic || '',
      image_url: item.image_url || '',
      image_alt: item.image_alt || '',
      difficulty: item.difficulty,
      tags: item.tags || [],
      is_favorite: item.is_favorite,
    })
    setTagsText((item.tags || []).join(', '))
    setCraftError('')
    setCraftOpen(true)
  }

  async function handleImageFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadingImg(true)
    setCraftError('')
    try {
      const dataUrl = await compressImageFileToDataUrl(file)
      setCraft((prev) => ({
        ...prev,
        image_url: dataUrl,
        image_alt: prev.image_alt || file.name.replace(/\.[^.]+$/, ''),
      }))
    } catch (err) {
      setCraftError(err instanceof Error ? err.message : 'Could not attach image.')
    } finally {
      setUploadingImg(false)
      e.target.value = ''
    }
  }

  async function submitCraft(e: FormEvent) {
    e.preventDefault()
    setCraftError('')
    if (!effectivePro) {
      setCraftError(
        'Custom question crafting is a Pro Vault feature. Enable "Preview Pro" above to try it locally, or upgrade to Pro.',
      )
      return
    }
    if (craft.question.trim().length < 3) {
      setCraftError('Write a question prompt (at least 3 characters).')
      return
    }
    const cleanOpts = craft.options.map((o) => o.trim()).filter(Boolean)
    if (craft.question_type === 'mcq' && cleanOpts.length < 2) {
      setCraftError('Add at least 2 answer choices for an MCQ.')
      return
    }
    if (
      craft.image_url?.trim() &&
      !isValidVaultImage(craft.image_url.trim())
    ) {
      setCraftError('Image must be a valid https:// URL or uploaded PNG/JPEG/WebP.')
      return
    }
    const parsedTags = tagsText
      .split(/[,\n]+/)
      .map((s) => s.trim().replace(/^#/, ''))
      .filter(Boolean)

    if (editingItemId) {
      await updateVaultItem(editingItemId, {
        ...craft,
        options: craft.question_type === 'mcq' ? cleanOpts : [],
        answer_index:
          craft.question_type === 'mcq'
            ? Math.min(craft.answer_index ?? 0, cleanOpts.length - 1)
            : null,
        tags: parsedTags,
        image_url: craft.image_url?.trim() || null,
        clear_image: !craft.image_url?.trim(),
      })
      flash('Updated question in your Vault.')
    } else {
      await craftVaultQuestion({
        ...craft,
        options: craft.question_type === 'mcq' ? cleanOpts : [],
        answer_index:
          craft.question_type === 'mcq'
            ? Math.min(craft.answer_index ?? 0, cleanOpts.length - 1)
            : null,
        tags: parsedTags,
      })
      setSafeOpen(true)
      flash('Crafted and locked into your Personal Vault!')
    }
    setCraftOpen(false)
  }

  async function toggleFavorite(item: VaultItem) {
    if (!item.is_favorite && !effectivePro) {
      flash('★ Starring Favorites in the Gold Vault is a Pro feature — toggle Preview Pro to try it!')
      return
    }
    await updateVaultItem(item.id, { is_favorite: !item.is_favorite })
  }

  function startTestFrom(sourceItems: VaultItem[], mode: TestMode, minutes = 10) {
    if (!sourceItems.length) {
      flash('No questions in this selection yet. Save or craft some first!')
      return
    }
    setTestItems(sourceItems)
    setTestSetupMode(mode)
    setTestMinutes(minutes)
    setSecondsLeft(minutes * 60)
    setTestIdx(0)
    setTestAnswers({})
    setTestFlipped(false)
    setTestSubmitted(false)
    setStreak(0)
    setTestActive(true)
    setTestOpen(true)
  }

  async function answerTestMcq(item: VaultItem, optionIdx: number) {
    if (testSubmitted) return
    if (testSetupMode === 'practice' && testAnswers[item.id] !== undefined) return
    setTestAnswers((prev) => ({ ...prev, [item.id]: optionIdx }))
    if (testSetupMode === 'practice' && item.answer_index !== null) {
      const ok = optionIdx === item.answer_index
      setStreak((s) => (ok ? s + 1 : 0))
      if (items.some((x) => x.id === item.id)) {
        await recordVaultReview(item.id, ok)
      }
    }
  }

  async function gradeFlashcard(item: VaultItem, ok: boolean) {
    setTestAnswers((prev) => ({ ...prev, [item.id]: ok }))
    setStreak((s) => (ok ? s + 1 : 0))
    if (items.some((x) => x.id === item.id)) {
      await recordVaultReview(item.id, ok)
    }
    if (testIdx < testItems.length - 1) {
      setTestIdx((i) => i + 1)
      setTestFlipped(false)
    } else {
      setTestSubmitted(true)
    }
  }

  async function submitTimedTest() {
    setTestSubmitted(true)
    for (const item of testItems) {
      const ans = testAnswers[item.id]
      if (
        typeof ans === 'number' &&
        item.answer_index !== null &&
        items.some((x) => x.id === item.id)
      ) {
        await recordVaultReview(item.id, ans === item.answer_index)
      }
    }
  }

  async function handleCreateShare(e: FormEvent) {
    e.preventDefault()
    const pool = filteredItems.length ? filteredItems : items
    if (!pool.length) return
    const pack = await createVaultSharePack({
      title: shareTitle.trim() || 'My Finna Vault Pack',
      description: shareDesc.trim(),
      mode: shareMode,
      duration_minutes: shareDuration,
      items: pool.slice(0, 60),
    })
    setCreatedShare(pack)
    flash('Shareable Vault pack created!')
  }

  async function copyToClipboard(text: string, label: string) {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedText(label)
      window.setTimeout(() => setCopiedText(''), 2000)
    } catch {
      flash('Could not access clipboard — copy manually.')
    }
  }

  function downloadVaultJson() {
    const pool = filteredItems.length ? filteredItems : items
    const blob = new Blob(
      [JSON.stringify({ app: 'finna-vault', exported_at: new Date().toISOString(), items: pool }, null, 2)],
      { type: 'application/json' },
    )
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `finna-vault-${pool.length}-questions.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const testScore = useMemo(() => {
    let correct = 0
    let graded = 0
    for (const item of testItems) {
      const ans = testAnswers[item.id]
      if (typeof ans === 'boolean') {
        graded++
        if (ans) correct++
      } else if (typeof ans === 'number' && item.answer_index !== null) {
        graded++
        if (ans === item.answer_index) correct++
      }
    }
    return { correct, graded }
  }, [testItems, testAnswers])

  // Render Shared Pack Landing View (/vault/share/:token)
  if (shareToken) {
    return (
      <div className="vs-page" data-screen="vault-share">
        <div className="vs-share-banner">
          <Link to="/vault" className="gd-back-link">
            ← Open My Personal Vault
          </Link>
          {sharedLoading && <p className="text-sm text-secondary">Unlocking shared Vault pack…</p>}
          {!sharedLoading && !sharedPack && (
            <div className="at-card">
              <h1>Shared Vault pack not found</h1>
              <p className="text-sm text-secondary">
                This share link may have expired or only exists on the device that created it.
              </p>
              <Link to="/vault" className="cr-primary-btn">
                Go to My Vault →
              </Link>
            </div>
          )}
          {sharedPack && (
            <section className="vs-hero">
              <VaultSafeIllustration
                size="hero"
                isOpen
                count={sharedPack.items.length}
                tier="gold"
                interactive={false}
              />
              <div className="vs-hero-copy">
                <span className="vs-eyebrow">Shared Vault Test Pack</span>
                <h1>{sharedPack.title}</h1>
                <p>
                  {sharedPack.description ||
                    `Curated by ${sharedPack.author_name || 'a Finna learner'} · ${sharedPack.items.length} questions · ${sharedPack.mode} mode.`}
                </p>
                <div className="vs-hero-actions">
                  <button
                    type="button"
                    className="cr-primary-btn"
                    onClick={() =>
                      startTestFrom(
                        sharedPack.items,
                        sharedPack.mode,
                        sharedPack.duration_minutes,
                      )
                    }
                  >
                    ▶ Take this {sharedPack.mode === 'timed' ? `${sharedPack.duration_minutes}m test` : 'drill'}
                  </button>
                  <button
                    type="button"
                    className="finna-st-btn"
                    onClick={async () => {
                      const res = await cloneVaultSharePack(sharedPack)
                      flash(`Cloned ${res.cloned} questions into "${res.folder}"!`)
                    }}
                  >
                    ⬇ Save Pack to My Vault
                  </button>
                </div>
                {notice && <p role="status" className="vs-notice">{notice}</p>}
              </div>
            </section>
          )}
        </div>
        {testOpen && renderTestModal()}
      </div>
    )
  }

  function renderTestModal() {
    const cur = testItems[testIdx]
    const mins = Math.floor(secondsLeft / 60)
    const secs = String(secondsLeft % 60).padStart(2, '0')

    return (
      <div className="vs-modal-backdrop" role="dialog" aria-modal="true" aria-label="Vault Test Studio">
        <div className="vs-modal vs-modal--wide">
          <div className="vs-modal-head">
            <div>
              <span className="vs-eyebrow">Vault Test Studio</span>
              <h2>
                {!testActive
                  ? 'Launch a Personal Test'
                  : testSubmitted
                    ? 'Vault Run Complete'
                    : `${testSetupMode === 'timed' ? 'Timed Mock' : testSetupMode === 'flashcards' ? '3D Flashcards' : 'Quick Drill'} · ${testIdx + 1} / ${testItems.length}`}
              </h2>
            </div>
            <div className="vs-modal-head-right">
              {testActive && !testSubmitted && testSetupMode === 'timed' && (
                <span className={`vs-timer-pill${secondsLeft < 60 ? ' is-low' : ''}`}>
                  ⏱ {mins}:{secs}
                </span>
              )}
              {testActive && !testSubmitted && streak >= 2 && (
                <span className="vs-streak-pill">🔥 {streak} streak</span>
              )}
              <button
                type="button"
                className="finna-st-btn"
                onClick={() => {
                  setTestOpen(false)
                  setTestActive(false)
                }}
              >
                Close ✕
              </button>
            </div>
          </div>

          {!testActive ? (
            <div className="vs-test-setup">
              <p className="text-sm text-secondary">
                Choose how you want to drill the{' '}
                <strong>{filteredItems.length || items.length}</strong> questions
                currently in view. Every answer updates your Leitner mastery box!
              </p>
              <div className="vs-mode-grid">
                {(
                  [
                    ['practice', '⚡ Quick Drill', 'Instant answer feedback, streak fire & Leitner updates.'],
                    ['timed', '⏱ Timed Mock', 'Real exam countdown, question palette & final score sheet.'],
                    ['flashcards', '🃏 3D Flashcards', 'Tap to flip each card & self-grade Got it / Shaky.'],
                  ] as const
                ).map(([m, title, desc]) => (
                  <button
                    key={m}
                    type="button"
                    className={`vs-mode-card${testSetupMode === m ? ' is-active' : ''}`}
                    onClick={() => setTestSetupMode(m)}
                  >
                    <strong>{title}</strong>
                    <span>{desc}</span>
                  </button>
                ))}
              </div>
              {testSetupMode === 'timed' && (
                <div className="vs-duration-row">
                  <span>Timer:</span>
                  {[5, 10, 15, 30].map((m) => (
                    <button
                      key={m}
                      type="button"
                      className={`av-cat-pill${testMinutes === m ? ' is-active' : ''}`}
                      onClick={() => setTestMinutes(m)}
                    >
                      {m} min
                    </button>
                  ))}
                </div>
              )}
              <div className="vs-modal-actions">
                <button
                  type="button"
                  className="cr-primary-btn"
                  onClick={() =>
                    startTestFrom(
                      filteredItems.length ? filteredItems : items,
                      testSetupMode,
                      testMinutes,
                    )
                  }
                >
                  Start now ({(filteredItems.length || items.length)} questions) →
                </button>
              </div>
            </div>
          ) : testSubmitted ? (
            <div className="vs-test-summary">
              <div className="vs-score-ring">
                <strong>
                  {testScore.graded > 0
                    ? `${Math.round((testScore.correct / testScore.graded) * 100)}%`
                    : '✓'}
                </strong>
                <span>
                  {testScore.correct} / {testScore.graded || testItems.length} right
                </span>
              </div>
              <p className="text-sm text-secondary">
                Your Vault Leitner boxes have been updated so shaky questions stay front
                and center next time you spin the dial.
              </p>
              <div className="vs-review-list">
                {testItems.map((it, idx) => {
                  const ans = testAnswers[it.id]
                  const ok =
                    typeof ans === 'boolean'
                      ? ans
                      : typeof ans === 'number' && it.answer_index !== null
                        ? ans === it.answer_index
                        : null
                  return (
                    <div key={it.id} className="vs-review-row">
                      <span className={`vs-dot ${ok === true ? 'is-ok' : ok === false ? 'is-miss' : ''}`}>
                        {idx + 1}
                      </span>
                      <div className="min-w-0 flex-1">
                        <strong>{it.question}</strong>
                        {it.answer_index !== null && it.options[it.answer_index] && (
                          <p className="text-xs text-secondary">
                            Answer: {LETTERS[it.answer_index]}. {it.options[it.answer_index]}
                          </p>
                        )}
                        {it.answer_text && (
                          <p className="text-xs text-secondary">Answer: {it.answer_text}</p>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
              <div className="vs-modal-actions">
                <button
                  type="button"
                  className="cr-primary-btn"
                  onClick={() => startTestFrom(testItems, testSetupMode, testMinutes)}
                >
                  ↻ Run again
                </button>
                <button
                  type="button"
                  className="finna-st-btn"
                  onClick={() => {
                    setTestOpen(false)
                    setTestActive(false)
                  }}
                >
                  Back to Vault
                </button>
              </div>
            </div>
          ) : cur ? (
            <div className="vs-test-runner">
              {testSetupMode === 'flashcards' ? (
                <div className="vs-flashcard-stage">
                  <button
                    type="button"
                    className={`vs-flashcard${testFlipped ? ' is-flipped' : ''}`}
                    onClick={() => setTestFlipped((f) => !f)}
                  >
                    <div className="vs-fc-face vs-fc-front">
                      <span className="vs-eyebrow">
                        {cur.subject} · {cur.folder} · Tap to flip
                      </span>
                      {cur.image_url && (
                        <img
                          src={cur.image_url}
                          alt={cur.image_alt || 'Question figure'}
                          className="vs-fc-img"
                        />
                      )}
                      <h3>{cur.question}</h3>
                      {cur.options.length > 0 && (
                        <ul className="vs-fc-opts">
                          {cur.options.map((o, i) => (
                            <li key={i}>
                              <strong>{LETTERS[i]}.</strong> {o}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                    <div className="vs-fc-face vs-fc-back">
                      <span className="vs-eyebrow">Answer &amp; Memory Hook</span>
                      {cur.answer_index !== null && cur.options[cur.answer_index] ? (
                        <h3>
                          {LETTERS[cur.answer_index]}. {cur.options[cur.answer_index]}
                        </h3>
                      ) : (
                        <h3>{cur.answer_text || 'Check explanation / source paper'}</h3>
                      )}
                      {cur.explanation && <p>{cur.explanation}</p>}
                      {cur.mnemonic && (
                        <div className="vs-sticky-note">
                          <strong>💡 Mnemonic:</strong> {cur.mnemonic}
                        </div>
                      )}
                    </div>
                  </button>
                  <div className="vs-modal-actions">
                    <button
                      type="button"
                      className="finna-st-btn"
                      onClick={() => void gradeFlashcard(cur, false)}
                    >
                      ↻ Shaky (Box 1)
                    </button>
                    <button
                      type="button"
                      className="cr-primary-btn"
                      onClick={() => void gradeFlashcard(cur, true)}
                    >
                      ✓ Got it! (Level up)
                    </button>
                  </div>
                </div>
              ) : (
                <div className="vs-drill-card">
                  <div className="vs-card-badges">
                    <span className="finna-st-pill finna-st-pill--teal">{cur.subject}</span>
                    <span className="vs-box-pill">{BOX_LABELS[cur.mastery_box]}</span>
                  </div>
                  {cur.image_url && (
                    <img
                      src={cur.image_url}
                      alt={cur.image_alt || 'Question image'}
                      className="vs-drill-img"
                    />
                  )}
                  <h3>{cur.question}</h3>
                  {cur.options.length > 0 ? (
                    <div className="vs-opt-list">
                      {cur.options.map((opt, idx) => {
                        const chosen = testAnswers[cur.id]
                        const revealed = testSetupMode === 'practice' && chosen !== undefined
                        const isPicked = chosen === idx
                        const isRight = cur.answer_index === idx
                        let cls = 'vs-opt-btn'
                        if (revealed && isRight) cls += ' is-correct'
                        else if (revealed && isPicked && !isRight) cls += ' is-wrong'
                        else if (isPicked) cls += ' is-picked'
                        return (
                          <button
                            key={idx}
                            type="button"
                            className={cls}
                            onClick={() => void answerTestMcq(cur, idx)}
                          >
                            <span className="vs-opt-letter">{LETTERS[idx]}</span>
                            <span>{opt}</span>
                          </button>
                        )
                      })}
                    </div>
                  ) : (
                    <div className="vs-open-answer">
                      <button
                        type="button"
                        className="finna-st-btn"
                        onClick={() => setTestFlipped((f) => !f)}
                      >
                        {testFlipped ? 'Hide answer' : 'Reveal answer'}
                      </button>
                      {testFlipped && (
                        <div className="vs-sticky-note">
                          <strong>Answer:</strong> {cur.answer_text || cur.explanation || 'Self-review item'}
                        </div>
                      )}
                    </div>
                  )}

                  {testSetupMode === 'practice' && testAnswers[cur.id] !== undefined && (
                    <div className="vs-drill-feedback">
                      {cur.explanation && <p>{cur.explanation}</p>}
                      {cur.mnemonic && (
                        <div className="vs-sticky-note">
                          <strong>💡 Memory Hook:</strong> {cur.mnemonic}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="vs-runner-nav">
                    <button
                      type="button"
                      className="finna-st-btn"
                      disabled={testIdx === 0}
                      onClick={() => {
                        setTestIdx((i) => Math.max(0, i - 1))
                        setTestFlipped(false)
                      }}
                    >
                      ← Prev
                    </button>
                    <div className="vs-runner-dots">
                      {testItems.map((it, idx) => (
                        <button
                          key={it.id}
                          type="button"
                          className={`vs-nav-dot${idx === testIdx ? ' is-cur' : ''}${testAnswers[it.id] !== undefined ? ' is-ans' : ''}`}
                          onClick={() => {
                            setTestIdx(idx)
                            setTestFlipped(false)
                          }}
                        >
                          {idx + 1}
                        </button>
                      ))}
                    </div>
                    {testIdx < testItems.length - 1 ? (
                      <button
                        type="button"
                        className="cr-primary-btn"
                        onClick={() => {
                          setTestIdx((i) => i + 1)
                          setTestFlipped(false)
                        }}
                      >
                        Next →
                      </button>
                    ) : (
                      <button
                        type="button"
                        className="cr-primary-btn"
                        onClick={() => void submitTimedTest()}
                      >
                        Finish &amp; Score ✓
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    )
  }

  return (
    <div className="vs-page" data-screen="vault">
      {/* HERO: Animated Opening Bank Safe + Vault Controls */}
      <header className="vs-hero">
        <VaultSafeIllustration
          size="hero"
          isOpen={safeOpen}
          spinning={spinning}
          count={summary.total}
          favoritesCount={summary.favorites}
          tier={tier.id}
          onToggle={() => setSafeOpen((v) => !v)}
        />

        <div className="vs-hero-copy">
          <div className="vs-hero-pills">
            <span className="vs-eyebrow">Personal Question Vault</span>
            <span className={`vs-tier-pill vs-tier-${tier.id}`}>{tier.label}</span>
            {serverPro ? (
              <span className="vs-pro-pill">★ Pro Unlocked</span>
            ) : proPreview ? (
              <span className="vs-pro-pill">★ Pro Preview (Local)</span>
            ) : (
              <Link to="/plans" className="vs-upgrade-pill">
                Upgrade to Pro ★
              </Link>
            )}
          </div>

          <h1>Your Private Question Safe</h1>
          <p>
            Stash tricky bank questions from any section, lock your Pro ★ Favorites in the
            gold tray, craft custom MCQs &amp; image flashcards, spin the combination dial
            for surprise drills, and share personal test packs.
          </p>

          {/* Mastery Progress Gauge */}
          <div className="vs-mastery-bar-wrap">
            <div className="vs-mastery-meta">
              <span>Vault Mastery · {summary.mastered}/{summary.total} locked in (Box 3–4)</span>
              <strong>{tier.percent}%</strong>
            </div>
            <div className="vs-mastery-track" role="progressbar" aria-valuenow={tier.percent} aria-valuemin={0} aria-valuemax={100}>
              <div className="vs-mastery-fill" style={{ width: `${tier.percent}%` }} />
            </div>
            <span className="vs-mastery-sub">{tier.tagline}</span>
          </div>

          {/* Primary Actions */}
          <div className="vs-hero-actions">
            <button type="button" className="cr-primary-btn" onClick={openCrafterForNew}>
              ✦ Craft Question {!effectivePro ? '(Pro)' : ''}
            </button>
            <button
              type="button"
              className="finna-st-btn"
              onClick={() => {
                setTestActive(false)
                setTestOpen(true)
              }}
            >
              ▶ Start Test / Flashcards
            </button>
            <button type="button" className="finna-st-btn" onClick={triggerSpin}>
              🎡 Spin the Dial
            </button>
            <button
              type="button"
              className="finna-st-btn"
              onClick={() => {
                setCreatedShare(null)
                setImportMsg('')
                setShareOpen(true)
              }}
            >
              ↗ Share &amp; Backup
            </button>
          </div>

          {!serverPro && (
            <div className="vs-pro-strip">
              <span>
                Free Safe: up to {FREE_VAULT_LIMIT} saved bank questions + drills.{' '}
                <strong>Pro</strong> unlocks ★ Gold Favorites, unlimited Crafted Questions
                with images &amp; Shareable Test Packs.
              </span>
              <button
                type="button"
                className="vs-preview-btn"
                onClick={toggleProPreview}
              >
                {proPreview ? 'Exit Pro Preview' : 'Try Pro Preview locally'}
              </button>
            </div>
          )}
        </div>
      </header>

      {notice && (
        <p role="status" className="vs-notice">
          {notice}
        </p>
      )}

      {/* Vault Stats Row */}
      <section className="vs-stats-strip" aria-label="Vault counts">
        <button
          type="button"
          className={`vs-stat-tile${compartment === 'all' ? ' is-active' : ''}`}
          onClick={() => setCompartment('all')}
        >
          <strong>{summary.total}</strong>
          <span>Total Stored</span>
        </button>
        <button
          type="button"
          className={`vs-stat-tile vs-stat-gold${compartment === 'favorites' ? ' is-active' : ''}`}
          onClick={() => setCompartment('favorites')}
        >
          <strong>★ {summary.favorites}</strong>
          <span>Gold Favorites</span>
        </button>
        <button
          type="button"
          className={`vs-stat-tile vs-stat-teal${compartment === 'custom' ? ' is-active' : ''}`}
          onClick={() => setCompartment('custom')}
        >
          <strong>✦ {summary.custom}</strong>
          <span>My Crafted</span>
        </button>
        <button
          type="button"
          className={`vs-stat-tile${compartment === 'saved' ? ' is-active' : ''}`}
          onClick={() => setCompartment('saved')}
        >
          <strong>📚 {summary.saved}</strong>
          <span>Saved from Bank</span>
        </button>
        <button
          type="button"
          className={`vs-stat-tile vs-stat-amber${compartment === 'due' ? ' is-active' : ''}`}
          onClick={() => setCompartment('due')}
        >
          <strong>🔥 {summary.due}</strong>
          <span>Due for Review</span>
        </button>
      </section>

      {/* Search, Folder Shelves & Difficulty Toolbar */}
      <section className="vs-toolbar" aria-label="Filter Vault questions">
        <input
          type="search"
          aria-label="Search personal vault"
          placeholder="Search questions, mnemonics, tags, or subjects…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="vs-search-input"
        />

        <div className="vs-filter-row">
          <div className="av-cat-strip" role="group" aria-label="Vault folders">
            <button
              type="button"
              className={`av-cat-pill${folderFilter === 'all' ? ' is-active' : ''}`}
              onClick={() => setFolderFilter('all')}
            >
              All folders ({items.length})
            </button>
            {folders.map(([name, count]) => (
              <button
                key={name}
                type="button"
                className={`av-cat-pill${folderFilter === name ? ' is-active' : ''}`}
                onClick={() => setFolderFilter(name)}
              >
                📁 {name} ({count})
              </button>
            ))}
          </div>

          <select
            aria-label="Filter by difficulty"
            value={difficultyFilter}
            onChange={(e) => setDifficultyFilter(e.target.value as 'all' | VaultDifficulty)}
            className="vs-select"
          >
            <option value="all">All difficulty</option>
            {DIFFICULTIES.map((d) => (
              <option key={d.id} value={d.id}>
                {d.label}
              </option>
            ))}
          </select>
        </div>
      </section>

      {/* Vault Contents Grid */}
      {!safeOpen ? (
        <div className="vs-locked-state">
          <p>
            Your safe door is shut. Tap the safe above (or click below) to spin the dial and
            open your <strong>{summary.total}</strong> questions.
          </p>
          <button type="button" className="cr-primary-btn" onClick={() => setSafeOpen(true)}>
            🔓 Unlock &amp; Open Vault
          </button>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="vs-empty-card">
          <h3>
            {items.length === 0
              ? 'Your Safe is ready for its first question'
              : 'No Vault questions match those filters'}
          </h3>
          <p>
            {items.length === 0
              ? 'Save any question from the Question Bank, Subjects, or Exams using the "Save to Vault" button — or craft your own custom MCQ/flashcard with an image right here.'
              : 'Clear your search or switch compartments to see the rest of your safe.'}
          </p>
          <div className="vs-hero-actions">
            <button type="button" className="cr-primary-btn" onClick={openCrafterForNew}>
              ✦ Craft your first question
            </button>
            <Link to="/bank" className="finna-st-btn">
              Browse Question Bank →
            </Link>
            {items.length > 0 && (
              <button
                type="button"
                className="finna-st-btn"
                onClick={() => {
                  setCompartment('all')
                  setFolderFilter('all')
                  setDifficultyFilter('all')
                  setQuery('')
                }}
              >
                Reset filters
              </button>
            )}
          </div>
        </div>
      ) : (
        <section className="vs-grid" aria-label="Stored Vault questions">
          {filteredItems.map((item) => {
            const peeking = Boolean(peekIds[item.id])
            const due = isVaultItemDue(item)
            return (
              <article
                key={item.id}
                className={`vs-item-card${item.is_favorite ? ' is-fav' : ''}${item.kind === 'custom' ? ' is-custom' : ''}`}
              >
                <div className="vs-item-top">
                  <div className="vs-card-badges">
                    <span className="vs-kind-badge">
                      {item.kind === 'custom' ? '✦ Crafted' : '📚 Bank'}
                    </span>
                    <span className="finna-st-pill finna-st-pill--teal">
                      {item.subject}
                    </span>
                    <span className="vs-folder-badge">📁 {item.folder}</span>
                    <span className={`vs-diff-badge is-${item.difficulty}`}>
                      {item.difficulty}
                    </span>
                    <span className={`vs-box-pill${due ? ' is-due' : ''}`}>
                      {BOX_LABELS[item.mastery_box]}
                    </span>
                  </div>
                  <button
                    type="button"
                    aria-pressed={item.is_favorite}
                    aria-label={item.is_favorite ? 'Remove from favorites' : 'Star as Pro favorite'}
                    className={`vs-star-btn${item.is_favorite ? ' is-on' : ''}`}
                    onClick={() => void toggleFavorite(item)}
                  >
                    {item.is_favorite ? '★' : '☆'}
                  </button>
                </div>

                {item.image_url && (
                  <button
                    type="button"
                    className="vs-item-img-btn"
                    onClick={() =>
                      setLightboxImg({
                        url: item.image_url!,
                        alt: item.image_alt || 'Vault question image',
                      })
                    }
                  >
                    <img
                      src={item.image_url}
                      alt={item.image_alt || 'Vault question diagram'}
                      loading="lazy"
                    />
                    <span className="vs-img-zoom">🔍 Tap to enlarge</span>
                  </button>
                )}

                <h3 className="vs-item-q">{item.question}</h3>

                {item.options.length > 0 && (
                  <ul className="vs-item-opts">
                    {item.options.map((opt, idx) => (
                      <li
                        key={idx}
                        className={
                          peeking && item.answer_index === idx ? 'is-answer' : ''
                        }
                      >
                        <strong>{LETTERS[idx]}.</strong> {opt}
                      </li>
                    ))}
                  </ul>
                )}

                {peeking && (
                  <div className="vs-peek-box">
                    {item.answer_index !== null && item.options[item.answer_index] && (
                      <p>
                        <strong>Answer:</strong> {LETTERS[item.answer_index]}.{' '}
                        {item.options[item.answer_index]}
                      </p>
                    )}
                    {item.answer_text && (
                      <p>
                        <strong>Answer:</strong> {item.answer_text}
                      </p>
                    )}
                    {item.explanation && <p>{item.explanation}</p>}
                  </div>
                )}

                {/* Editable Personal Mnemonic / Trap Sticky Note */}
                {editingNoteId === item.id ? (
                  <div className="vs-note-editor">
                    <textarea
                      rows={2}
                      value={noteDraft}
                      onChange={(e) => setNoteDraft(e.target.value)}
                      placeholder="Write your memory hook, formula trick, or trap warning…"
                    />
                    <div className="vs-note-editor-actions">
                      <button
                        type="button"
                        className="cr-primary-btn"
                        onClick={async () => {
                          await updateVaultItem(item.id, { mnemonic: noteDraft })
                          setEditingNoteId(null)
                          flash('Memory hook saved.')
                        }}
                      >
                        Save note
                      </button>
                      <button
                        type="button"
                        className="finna-st-btn"
                        onClick={() => setEditingNoteId(null)}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : item.mnemonic ? (
                  <div className="vs-sticky-note">
                    <strong>💡 Memory Hook:</strong> {item.mnemonic}
                  </div>
                ) : null}

                {item.tags.length > 0 && (
                  <div className="vs-tag-list">
                    {item.tags.map((tag) => (
                      <span key={tag}>#{tag}</span>
                    ))}
                  </div>
                )}

                <div className="vs-item-actions">
                  <button
                    type="button"
                    className="finna-st-btn"
                    onClick={() =>
                      setPeekIds((prev) => ({ ...prev, [item.id]: !prev[item.id] }))
                    }
                  >
                    {peeking ? 'Hide answer' : '👁 Peek answer'}
                  </button>
                  <button
                    type="button"
                    className="finna-st-btn"
                    onClick={() => {
                      setEditingNoteId(item.id)
                      setNoteDraft(item.mnemonic || '')
                    }}
                  >
                    💡 {item.mnemonic ? 'Edit hook' : 'Add hook'}
                  </button>
                  {item.kind === 'custom' && (
                    <button
                      type="button"
                      className="finna-st-btn"
                      onClick={() => openCrafterForEdit(item)}
                    >
                      ✎ Edit
                    </button>
                  )}
                  {item.canonical_question_id && (
                    <Link
                      to={`/bank/${encodeURIComponent(item.canonical_question_id)}`}
                      className="finna-st-btn"
                    >
                      Source ↗
                    </Link>
                  )}
                  <button
                    type="button"
                    className="finna-st-btn"
                    onClick={() =>
                      void copyToClipboard(
                        formatVaultQuizText(item.subject, [item]),
                        item.id,
                      )
                    }
                  >
                    {copiedText === item.id ? 'Copied ✓' : '↗ Share'}
                  </button>
                  <button
                    type="button"
                    className="vs-danger-btn"
                    onClick={() => void deleteVaultItem(item.id)}
                  >
                    Remove
                  </button>
                </div>
              </article>
            )
          })}
        </section>
      )}

      {/* QUESTION CRAFTER MODAL (with Images!) */}
      {craftOpen && (
        <div className="vs-modal-backdrop" role="dialog" aria-modal="true" aria-label="Craft personal question">
          <form className="vs-modal vs-modal--wide" onSubmit={(e) => void submitCraft(e)}>
            <div className="vs-modal-head">
              <div>
                <span className="vs-eyebrow">Pro Vault Question Crafter</span>
                <h2>{editingItemId ? 'Edit Crafted Question' : 'Craft a Personal Question'}</h2>
              </div>
              <button type="button" className="finna-st-btn" onClick={() => setCraftOpen(false)}>
                Close ✕
              </button>
            </div>

            {!effectivePro && (
              <div className="vs-pro-strip">
                <span>
                  Crafting personal questions with images is a <strong>Pro</strong> feature.
                </span>
                <button type="button" className="vs-preview-btn" onClick={toggleProPreview}>
                  Enable Pro Preview
                </button>
              </div>
            )}

            {craftError && <p role="alert" className="vs-error-box">{craftError}</p>}

            <div className="vs-form-grid">
              <label className="vs-field">
                <span>Question type</span>
                <select
                  value={craft.question_type}
                  onChange={(e) =>
                    setCraft((p) => ({
                      ...p,
                      question_type: e.target.value as VaultQuestionType,
                    }))
                  }
                >
                  <option value="mcq">Multiple Choice (MCQ)</option>
                  <option value="flashcard">Flashcard / Short Answer</option>
                </select>
              </label>

              <label className="vs-field">
                <span>Folder / Shelf</span>
                <input
                  value={craft.folder}
                  onChange={(e) => setCraft((p) => ({ ...p, folder: e.target.value }))}
                  placeholder="e.g. High-Yield Polity"
                />
              </label>

              <label className="vs-field">
                <span>Subject</span>
                <input
                  value={craft.subject}
                  onChange={(e) => setCraft((p) => ({ ...p, subject: e.target.value }))}
                  placeholder="e.g. Indian Polity, Maths"
                />
              </label>

              <label className="vs-field">
                <span>Difficulty</span>
                <select
                  value={craft.difficulty}
                  onChange={(e) =>
                    setCraft((p) => ({
                      ...p,
                      difficulty: e.target.value as VaultDifficulty,
                    }))
                  }
                >
                  {DIFFICULTIES.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <label className="vs-field">
              <span>Question prompt *</span>
              <textarea
                required
                rows={3}
                value={craft.question}
                onChange={(e) => setCraft((p) => ({ ...p, question: e.target.value }))}
                placeholder="Write your question, formula prompt, or tricky exam stem…"
              />
            </label>

            {/* Image Attachment Studio */}
            <div className="vs-img-studio">
              <div className="vs-img-studio-head">
                <strong>🖼 Attach Image / Diagram (optional)</strong>
                <label className="finna-st-btn vs-upload-label">
                  {uploadingImg ? 'Processing…' : 'Upload Photo / Diagram'}
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    onChange={(e) => void handleImageFile(e)}
                    hidden
                  />
                </label>
              </div>
              <input
                type="url"
                value={craft.image_url?.startsWith('data:') ? '' : craft.image_url || ''}
                onChange={(e) => setCraft((p) => ({ ...p, image_url: e.target.value }))}
                placeholder="Or paste an https:// image URL…"
                className="vs-input"
              />
              {craft.image_url && isValidVaultImage(craft.image_url) && (
                <div className="vs-img-preview">
                  <img src={craft.image_url} alt={craft.image_alt || 'Preview'} />
                  <button
                    type="button"
                    className="vs-danger-btn"
                    onClick={() => setCraft((p) => ({ ...p, image_url: '', image_alt: '' }))}
                  >
                    Remove image
                  </button>
                </div>
              )}
            </div>

            {craft.question_type === 'mcq' ? (
              <div className="vs-opts-editor">
                <span className="vs-field-title">Answer choices (click letter to mark correct)</span>
                {craft.options.map((opt, idx) => (
                  <div key={idx} className="vs-opt-edit-row">
                    <button
                      type="button"
                      className={`vs-opt-pick${craft.answer_index === idx ? ' is-correct' : ''}`}
                      onClick={() => setCraft((p) => ({ ...p, answer_index: idx }))}
                      title="Mark as correct answer"
                    >
                      {LETTERS[idx]} {craft.answer_index === idx ? '✓' : ''}
                    </button>
                    <input
                      value={opt}
                      onChange={(e) => {
                        const next = [...craft.options]
                        next[idx] = e.target.value
                        setCraft((p) => ({ ...p, options: next }))
                      }}
                      placeholder={`Option ${LETTERS[idx]}`}
                    />
                  </div>
                ))}
                {craft.options.length < 6 && (
                  <button
                    type="button"
                    className="finna-st-btn"
                    onClick={() => setCraft((p) => ({ ...p, options: [...p.options, ''] }))}
                  >
                    + Add option
                  </button>
                )}
              </div>
            ) : (
              <label className="vs-field">
                <span>Flashcard Back / Answer</span>
                <textarea
                  rows={2}
                  value={craft.answer_text}
                  onChange={(e) => setCraft((p) => ({ ...p, answer_text: e.target.value }))}
                  placeholder="Write the exact answer, formula, or key points…"
                />
              </label>
            )}

            <div className="vs-form-grid">
              <label className="vs-field">
                <span>Explanation</span>
                <textarea
                  rows={2}
                  value={craft.explanation}
                  onChange={(e) => setCraft((p) => ({ ...p, explanation: e.target.value }))}
                  placeholder="Why is this the right answer?"
                />
              </label>
              <label className="vs-field">
                <span>💡 Personal Mnemonic / Trap Warning</span>
                <textarea
                  rows={2}
                  value={craft.mnemonic}
                  onChange={(e) => setCraft((p) => ({ ...p, mnemonic: e.target.value }))}
                  placeholder="Memory hook or exam trap to watch out for…"
                />
              </label>
            </div>

            <div className="vs-form-grid">
              <label className="vs-field">
                <span>Tags (comma separated)</span>
                <input
                  value={tagsText}
                  onChange={(e) => setTagsText(e.target.value)}
                  placeholder="article-368, trap, formula"
                />
              </label>
              <label className="vs-check-field">
                <input
                  type="checkbox"
                  checked={craft.is_favorite}
                  onChange={(e) => setCraft((p) => ({ ...p, is_favorite: e.target.checked }))}
                />
                <span>★ Star in Gold Favorites compartment</span>
              </label>
            </div>

            <div className="vs-modal-actions">
              <button type="submit" className="cr-primary-btn">
                🔐 {editingItemId ? 'Save changes' : 'Lock into Vault'}
              </button>
              <button type="button" className="finna-st-btn" onClick={() => setCraftOpen(false)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* SPIN THE DIAL ROULETTE MODAL */}
      {rouletteItem && (
        <div className="vs-modal-backdrop" role="dialog" aria-modal="true" aria-label="Vault Roulette Pull">
          <div className="vs-modal">
            <div className="vs-modal-head">
              <div>
                <span className="vs-eyebrow">🎡 Combination Dial Surprise Pull</span>
                <h2>{rouletteItem.subject} · {BOX_LABELS[rouletteItem.mastery_box]}</h2>
              </div>
              <button type="button" className="finna-st-btn" onClick={() => setRouletteItem(null)}>
                Close ✕
              </button>
            </div>

            {rouletteItem.image_url && (
              <img
                src={rouletteItem.image_url}
                alt={rouletteItem.image_alt || 'Question figure'}
                className="vs-drill-img"
              />
            )}
            <h3 className="vs-item-q">{rouletteItem.question}</h3>

            {rouletteItem.options.length > 0 ? (
              <div className="vs-opt-list">
                {rouletteItem.options.map((opt, idx) => {
                  const picked = roulettePick === idx
                  const revealed = roulettePick !== null
                  const right = rouletteItem.answer_index === idx
                  let cls = 'vs-opt-btn'
                  if (revealed && right) cls += ' is-correct'
                  else if (revealed && picked && !right) cls += ' is-wrong'
                  return (
                    <button
                      key={idx}
                      type="button"
                      className={cls}
                      onClick={async () => {
                        if (roulettePick !== null) return
                        setRoulettePick(idx)
                        if (rouletteItem.answer_index !== null) {
                          await recordVaultReview(
                            rouletteItem.id,
                            idx === rouletteItem.answer_index,
                          )
                        }
                      }}
                    >
                      <span className="vs-opt-letter">{LETTERS[idx]}</span>
                      <span>{opt}</span>
                    </button>
                  )
                })}
              </div>
            ) : (
              <div>
                <button
                  type="button"
                  className="finna-st-btn"
                  onClick={() => setRouletteFlipped((v) => !v)}
                >
                  {rouletteFlipped ? 'Hide answer' : 'Reveal answer'}
                </button>
                {rouletteFlipped && (
                  <div className="vs-sticky-note">
                    <strong>Answer:</strong> {rouletteItem.answer_text || rouletteItem.explanation}
                  </div>
                )}
              </div>
            )}

            {roulettePick !== null && (rouletteItem.explanation || rouletteItem.mnemonic) && (
              <div className="vs-drill-feedback">
                {rouletteItem.explanation && <p>{rouletteItem.explanation}</p>}
                {rouletteItem.mnemonic && (
                  <div className="vs-sticky-note">
                    <strong>💡 Hook:</strong> {rouletteItem.mnemonic}
                  </div>
                )}
              </div>
            )}

            <div className="vs-modal-actions">
              <button type="button" className="cr-primary-btn" onClick={triggerSpin}>
                🎡 Spin again
              </button>
              <button type="button" className="finna-st-btn" onClick={() => setRouletteItem(null)}>
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SHARE & PORTABLE BACKUP MODAL */}
      {shareOpen && (
        <div className="vs-modal-backdrop" role="dialog" aria-modal="true" aria-label="Share and backup Vault">
          <div className="vs-modal">
            <div className="vs-modal-head">
              <div>
                <span className="vs-eyebrow">Share &amp; Portable Packs</span>
                <h2>Share Your Vault Questions</h2>
              </div>
              <button type="button" className="finna-st-btn" onClick={() => setShareOpen(false)}>
                Close ✕
              </button>
            </div>

            <form onSubmit={(e) => void handleCreateShare(e)} className="vs-share-form">
              <label className="vs-field">
                <span>Pack title</span>
                <input
                  required
                  value={shareTitle}
                  onChange={(e) => setShareTitle(e.target.value)}
                />
              </label>
              <label className="vs-field">
                <span>Short note (optional)</span>
                <input
                  value={shareDesc}
                  onChange={(e) => setShareDesc(e.target.value)}
                  placeholder="e.g. Top 15 Polity traps for Sunday revision"
                />
              </label>
              <div className="vs-form-grid">
                <label className="vs-field">
                  <span>Default mode</span>
                  <select
                    value={shareMode}
                    onChange={(e) => setShareMode(e.target.value as TestMode)}
                  >
                    <option value="practice">Quick Drill</option>
                    <option value="timed">Timed Mock</option>
                    <option value="flashcards">3D Flashcards</option>
                  </select>
                </label>
                <label className="vs-field">
                  <span>Timer (minutes)</span>
                  <input
                    type="number"
                    min={1}
                    max={120}
                    value={shareDuration}
                    onChange={(e) => setShareDuration(Number(e.target.value) || 10)}
                  />
                </label>
              </div>
              <button type="submit" className="cr-primary-btn" disabled={!items.length}>
                Generate Share Link ({filteredItems.length || items.length} questions)
              </button>
            </form>

            {createdShare && (
              <div className="vs-share-result">
                <strong>Shareable link ready:</strong>
                <code>{`${window.location.origin}/vault/share/${createdShare.token}`}</code>
                <div className="vs-hero-actions">
                  <button
                    type="button"
                    className="finna-st-btn"
                    onClick={() =>
                      void copyToClipboard(
                        `${window.location.origin}/vault/share/${createdShare.token}`,
                        'share-url',
                      )
                    }
                  >
                    {copiedText === 'share-url' ? 'Copied link ✓' : 'Copy link'}
                  </button>
                  <a
                    className="finna-st-btn"
                    target="_blank"
                    rel="noreferrer"
                    href={`https://wa.me/?text=${encodeURIComponent(
                      `Try my Finna Vault Pack "${createdShare.title}" (${createdShare.items.length} Qs):\n${window.location.origin}/vault/share/${createdShare.token}`,
                    )}`}
                  >
                    WhatsApp ↗
                  </a>
                </div>
              </div>
            )}

            <div className="vs-backup-box">
              <strong>Portable Backup &amp; Friend Pack Import</strong>
              <div className="vs-hero-actions">
                <button
                  type="button"
                  className="finna-st-btn"
                  disabled={!items.length}
                  onClick={downloadVaultJson}
                >
                  ⬇ Export JSON Pack
                </button>
                <button
                  type="button"
                  className="finna-st-btn"
                  disabled={!items.length}
                  onClick={() =>
                    void copyToClipboard(
                      formatVaultQuizText(shareTitle, filteredItems.length ? filteredItems : items),
                      'quiz-text',
                    )
                  }
                >
                  {copiedText === 'quiz-text' ? 'Quiz copied ✓' : '📋 Copy as Text Quiz'}
                </button>
              </div>
              <textarea
                rows={3}
                value={importJson}
                onChange={(e) => setImportJson(e.target.value)}
                placeholder="Paste a friend's exported Finna Vault JSON pack here to import…"
                className="vs-input"
              />
              <button
                type="button"
                className="finna-st-btn"
                disabled={!importJson.trim()}
                onClick={() => {
                  const res = importVaultItemsFromJson(importJson)
                  if (res.error) setImportMsg(res.error)
                  else {
                    setImportMsg(`Imported ${res.imported} questions into your Vault!`)
                    setImportJson('')
                  }
                }}
              >
                ⬆ Import JSON Pack
              </button>
              {importMsg && <p className="text-xs text-secondary">{importMsg}</p>}
            </div>
          </div>
        </div>
      )}

      {/* TEST STUDIO MODAL */}
      {testOpen && renderTestModal()}

      {/* IMAGE LIGHTBOX */}
      {lightboxImg && (
        <div
          className="vs-modal-backdrop"
          role="dialog"
          aria-modal="true"
          onClick={() => setLightboxImg(null)}
        >
          <div className="vs-lightbox" onClick={(e) => e.stopPropagation()}>
            <img src={lightboxImg.url} alt={lightboxImg.alt} />
            <button type="button" className="cr-primary-btn" onClick={() => setLightboxImg(null)}>
              Close image
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
