import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getAccountSession } from '../lib/api'
import { deviceId } from '../lib/device'
import { reviewSession } from '../lib/review'
import { currentExamScope } from '../lib/examScope'
import {
  browseContext,
  browseQuery,
  browseStoreKey,
  checkpointStoreKey,
  readBrowsePosition,
  writeBrowsePosition,
  clearBrowsePosition,
  readBrowseCheckpoint,
  writeBrowseCheckpoint,
  clearBrowseCheckpoint,
  restoreBrowseQuery,
  type BrowseCheckpoint,
  type BrowsePosition,
} from '../lib/browsePosition'

/** Restore after the matching question page arrives; capture scrolls, checkpoints, and page exit. */
export function useBrowsePosition(
  collection: string,
  enabled: boolean,
  pending: boolean,
  questionIds: string[],
  baseOffset = 0,
) {
  const [params, setParams] = useSearchParams()
  const [initializing, setInitializing] = useState(enabled),
    [message, setMessage] = useState(''),
    [checkpoint, setCheckpoint] = useState<BrowseCheckpoint | null>(null),
    [currentIndex, setCurrentIndex] = useState<number>(baseOffset + 1),
    [currentQuestionId, setCurrentQuestionId] = useState<string | null>(questionIds[0] || null),
    [resumedIndex, setResumedIndex] = useState<number | null>(null)
  const key = useRef(''),
    cpKey = useRef(''),
    restore = useRef<BrowsePosition | null>(null),
    suppress = useRef(false)
  const query = browseQuery(params),
    contextKey = browseContext(params),
    ids = questionIds.join('|')
  const latest = useRef({ params, query, pending, questionIds, baseOffset })
  latest.current = { params, query, pending, questionIds, baseOffset }
  useEffect(() => {
    if (!enabled) {
      setInitializing(false)
      return
    }
    let live = true
    setInitializing(true)
    key.current = ''
    cpKey.current = ''
    restore.current = null
    setResumedIndex(null)
    getAccountSession()
      .then((session) =>
        session.authenticated
          ? reviewSession()
          : { user_id: 'guest-' + deviceId() },
      )
      .then((session) => {
        if (!live) return
        const scope = currentExamScope()
        key.current = browseStoreKey(session.user_id, collection, scope)
        cpKey.current = checkpointStoreKey(session.user_id, collection, scope)
        const current = latest.current.params
        setCheckpoint(readBrowseCheckpoint(cpKey.current, current))
        if (current.get('fresh') === '1')
          clearBrowsePosition(key.current, current)
        const saved =
          current.get('fresh') === '1'
            ? null
            : readBrowsePosition(key.current, current)
        if (saved) {
          const explicitOffset =
            current.has('offset') &&
            new URLSearchParams(saved.query).get('offset') !==
              current.get('offset')
          if (!explicitOffset) {
            restore.current = saved
            const savedOffset = Number(new URLSearchParams(saved.query).get('offset') || 0)
            const displayIdx = saved.questionIndex || (savedOffset > 0 ? savedOffset + 1 : null)
            setResumedIndex(displayIdx)
            setMessage(
              displayIdx
                ? `Resumed where you left off (#${displayIdx.toLocaleString('en-IN')}).`
                : 'Resumed your saved reading position.',
            )
            if (browseQuery(current) !== saved.query) {
              setParams((previous) => restoreBrowseQuery(previous, saved), {
                replace: true,
              })
              // Router search updates are navigation, not queued React state.
              // Wait for that URL before allowing the default-seed effect.
              return
            }
          }
        }
        setInitializing(false)
      })
      .catch(() => {
        if (live) {
          setInitializing(false)
          setMessage('Reading position could not be saved right now.')
        }
      })
    return () => {
      live = false
    }
  }, [collection, enabled])
  useEffect(() => {
    if (cpKey.current) setCheckpoint(readBrowseCheckpoint(cpKey.current, latest.current.params))
  }, [contextKey])
  useEffect(() => {
    if (enabled && initializing && restore.current?.query === query) setInitializing(false)
  }, [enabled, initializing, query])
  useEffect(() => {
    if (enabled && !initializing && params.get('fresh') === '1')
      setParams(
        (previous) => {
          const next = new URLSearchParams(previous)
          next.delete('fresh')
          return next
        },
        { replace: true },
      )
  }, [enabled, initializing, params.toString()])
  useEffect(() => {
    if (!enabled || initializing || pending || !key.current) return
    suppress.current = false
    let frame = 0,
      timer: number | undefined,
      stopped = false
    const saved = restore.current
    if (saved) {
      restore.current = null
      suppress.current = true
      frame = requestAnimationFrame(() => {
        if (stopped) return
        const target = saved.questionId
          ? document.getElementById('question-' + saved.questionId)
          : null
        if (target)
          window.scrollTo({
            top: Math.max(
              0,
              window.scrollY + target.getBoundingClientRect().top - saved.top,
            ),
            behavior: 'auto',
          })
        else
          document
            .getElementById('exam-question-browser')
            ?.scrollIntoView({ block: 'start' })
        suppress.current = false
      })
    }
    const capture = () => {
      if (suppress.current || stopped) return
      const current = latest.current
      if (current.pending || current.query !== query) return
      const cards = current.questionIds
        .map((id, idx) => ({ id, idx, el: document.getElementById('question-' + id) }))
        .filter((item) => item.el)
      const visible = cards.find((item) => {
        const r = item.el!.getBoundingClientRect()
        return r.bottom > 140 && r.top < window.innerHeight
      })
      const visibleGlobalIndex = visible ? current.baseOffset + visible.idx + 1 : current.baseOffset + 1
      setCurrentIndex(visibleGlobalIndex)
      setCurrentQuestionId(visible?.id || current.questionIds[0] || null)

      // Compute the real 25-aligned offset for the visible question so Continuous Scroll
      // resumes accurately on the exact question even if the user scrolled several pages deep.
      const saveParams = new URLSearchParams(current.query)
      if (visible) {
        const alignedOffset = Math.floor((current.baseOffset + visible.idx) / 25) * 25
        if (alignedOffset > 0) saveParams.set('offset', String(alignedOffset))
        else saveParams.delete('offset')
      }
      const saveQuery = browseQuery(saveParams)
      const position: BrowsePosition = {
        query: saveQuery,
        questionId: visible?.id || null,
        questionIndex: visibleGlobalIndex,
        top: visible?.el?.getBoundingClientRect().top || 140,
        savedAt: Date.now(),
      }
      // A tab's header may be in view. Retain an existing in-page anchor until the
      // student actually scrolls into questions, instead of overwriting it on mount.
      if (
        !visible &&
        readBrowsePosition(key.current, new URLSearchParams(query))?.query === query &&
        readBrowsePosition(key.current, new URLSearchParams(query))?.questionId
      )
        return
      if (writeBrowsePosition(key.current, position))
        setMessage('Reading position saved on this device.')
      else setMessage('This browser could not save your reading position.')
    }
    const schedule = () => {
      window.clearTimeout(timer)
      timer = window.setTimeout(capture, 200)
    }
    const hide = () => {
      if (document.visibilityState === 'hidden') capture()
    }
    window.addEventListener('scroll', schedule, { passive: true })
    window.addEventListener('pagehide', capture)
    document.addEventListener('visibilitychange', hide)
    timer = window.setTimeout(capture, 350)
    return () => {
      capture()
      stopped = true
      window.cancelAnimationFrame(frame)
      window.clearTimeout(timer)
      window.removeEventListener('scroll', schedule)
      window.removeEventListener('pagehide', capture)
      document.removeEventListener('visibilitychange', hide)
    }
  }, [enabled, initializing, pending, query, ids, baseOffset])

  function pinCheckpoint() {
    if (!cpKey.current) return
    const current = latest.current
    const cards = current.questionIds
      .map((id, idx) => ({ id, idx, el: document.getElementById('question-' + id) }))
      .filter((item) => item.el)
    const visible = cards.find((item) => {
      const r = item.el!.getBoundingClientRect()
      return r.bottom > 140 && r.top < window.innerHeight
    })
    const globalIdx = visible ? current.baseOffset + visible.idx + 1 : currentIndex
    const alignedOffset = Math.floor(Math.max(0, globalIdx - 1) / 25) * 25
    const cpParams = new URLSearchParams(current.query)
    if (alignedOffset > 0) cpParams.set('offset', String(alignedOffset))
    else cpParams.delete('offset')
    const nextCp: BrowseCheckpoint = {
      query: browseQuery(cpParams),
      questionId: visible?.id || currentQuestionId || null,
      questionIndex: globalIdx,
      top: visible?.el?.getBoundingClientRect().top || 140,
      savedAt: Date.now(),
    }
    if (writeBrowseCheckpoint(cpKey.current, nextCp)) {
      setCheckpoint(nextCp)
      setMessage(`Checkpoint pinned at #${globalIdx.toLocaleString('en-IN')}.`)
    }
  }

  function clearPinnedCheckpoint() {
    if (!cpKey.current) return
    clearBrowseCheckpoint(cpKey.current, latest.current.params)
    setCheckpoint(null)
    setMessage('Pinned checkpoint cleared.')
  }

  function jumpToCheckpoint() {
    if (!checkpoint) return
    restore.current = {
      query: checkpoint.query,
      questionId: checkpoint.questionId,
      questionIndex: checkpoint.questionIndex,
      top: checkpoint.top,
      savedAt: checkpoint.savedAt,
    }
    const targetEl = checkpoint.questionId
      ? document.getElementById('question-' + checkpoint.questionId)
      : null
    if (targetEl) {
      restore.current = null
      targetEl.scrollIntoView({
        block: 'start',
        behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
      })
      return
    }
    setParams((previous) => restoreBrowseQuery(previous, restore.current!), { replace: false })
  }

  function startAgain() {
    suppress.current = true
    restore.current = null
    setResumedIndex(null)
    if (key.current) clearBrowsePosition(key.current, params)
    setParams(
      (previous) => {
        const next = new URLSearchParams(previous)
        next.delete('offset')
        next.delete('resume_question')
        next.set('fresh', '1')
        return next
      },
      { replace: true },
    )
    setMessage('Jumped to start (#1). Your answers and scores are kept.')
    requestAnimationFrame(() =>
      document
        .getElementById('exam-question-browser')
        ?.scrollIntoView({
          block: 'start',
          behavior: window.matchMedia('(prefers-reduced-motion: reduce)')
            .matches
            ? 'auto'
            : 'smooth',
        }),
    )
  }

  return {
    initializing,
    message,
    startAgain,
    checkpoint,
    pinCheckpoint,
    clearPinnedCheckpoint,
    jumpToCheckpoint,
    currentIndex,
    currentQuestionId,
    resumedIndex,
  }
}
