import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getAccountSession } from '../lib/api'
import { deviceId } from '../lib/device'
import { reviewSession } from '../lib/review'
import { currentExamScope } from '../lib/examScope'
import {
  browseQuery,
  browseStoreKey,
  readBrowsePosition,
  writeBrowsePosition,
  clearBrowsePosition,
  restoreBrowseQuery,
  type BrowsePosition,
} from '../lib/browsePosition'

/** Restore after the matching question page arrives; capture scrolls and page exit. */
export function useBrowsePosition(
  collection: string,
  enabled: boolean,
  pending: boolean,
  questionIds: string[],
) {
  const [params, setParams] = useSearchParams()
  const [initializing, setInitializing] = useState(enabled),
    [message, setMessage] = useState('')
  const key = useRef(''),
    restore = useRef<BrowsePosition | null>(null),
    suppress = useRef(false)
  const query = browseQuery(params),
    ids = questionIds.join('|')
  const latest = useRef({ params, query, pending, questionIds })
  latest.current = { params, query, pending, questionIds }
  useEffect(() => {
    if (!enabled) {
      setInitializing(false)
      return
    }
    let live = true
    setInitializing(true)
    key.current = ''
    restore.current = null
    getAccountSession()
      .then((session) =>
        session.authenticated
          ? reviewSession()
          : { user_id: 'guest-' + deviceId() },
      )
      .then((session) => {
        if (!live) return
        key.current = browseStoreKey(
          session.user_id,
          collection,
          currentExamScope(),
        )
        const current = latest.current.params
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
            setMessage('Resumed your saved reading position.')
            if(browseQuery(current)!==saved.query){
              setParams((previous) => restoreBrowseQuery(previous, saved), {replace:true})
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
  useEffect(()=>{if(enabled&&initializing&&restore.current?.query===query)setInitializing(false)},[enabled,initializing,query])
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
        .map((id) => ({ id, el: document.getElementById('question-' + id) }))
        .filter((item) => item.el)
      const visible = cards.find((item) => {
        const r = item.el!.getBoundingClientRect()
        return r.bottom > 140 && r.top < window.innerHeight
      })
      const position: BrowsePosition = {
        query,
        questionId: visible?.id || null,
        top: visible?.el?.getBoundingClientRect().top || 140,
        savedAt: Date.now(),
      }
      // A tab's header may be in view. Retain an existing in-page anchor until the
      // student actually scrolls into questions, instead of overwriting it on mount.
      if (
        !visible &&
        readBrowsePosition(key.current, new URLSearchParams(query))?.query===query &&
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
  }, [enabled, initializing, pending, query, ids])
  function startAgain() {
    suppress.current = true
    restore.current = null
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
    setMessage('Reading position reset. Your answers and scores are kept.')
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
  return { initializing, message, startAgain }
}
