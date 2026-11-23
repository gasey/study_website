import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import type { Question } from '../lib/api'
import {
  isQuestionInLocalVault,
  removeBankQuestionFromVault,
  saveBankQuestionToVault,
} from '../lib/vault'
import VaultSafeIllustration from './VaultSafeIllustration'

export default function SaveToVaultButton({
  question,
  compact = false,
}: {
  question: Question
  compact?: boolean
}) {
  const [saved, setSaved] = useState(() => isQuestionInLocalVault(question.id))
  const [busy, setBusy] = useState(false)
  const [justSaved, setJustSaved] = useState(false)

  useEffect(() => {
    setSaved(isQuestionInLocalVault(question.id))
    const sync = () => setSaved(isQuestionInLocalVault(question.id))
    window.addEventListener('finna-vault-change', sync)
    return () => window.removeEventListener('finna-vault-change', sync)
  }, [question.id])

  async function toggle() {
    if (busy) return
    setBusy(true)
    try {
      if (saved) {
        await removeBankQuestionFromVault(question.id)
        setSaved(false)
        setJustSaved(false)
      } else {
        await saveBankQuestionToVault(question)
        setSaved(true)
        setJustSaved(true)
        window.setTimeout(() => setJustSaved(false), 1800)
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <span className="vs-save-wrap">
      <button
        type="button"
        disabled={busy}
        aria-pressed={saved}
        onClick={() => void toggle()}
        className={`vs-save-btn${saved ? ' is-saved' : ''}${compact ? ' is-compact' : ''}`}
        title={saved ? 'Saved in your Personal Vault (click to remove)' : 'Save to your Personal Question Vault'}
      >
        <VaultSafeIllustration size="mini" isOpen={saved} spinning={justSaved} interactive={false} />
        <span>{saved ? 'In Vault' : 'Save to Vault'}</span>
      </button>
      {justSaved && (
        <Link to="/vault" className="vs-save-toast-link">
          Open Vault →
        </Link>
      )}
    </span>
  )
}
