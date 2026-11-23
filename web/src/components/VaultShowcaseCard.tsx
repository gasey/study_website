import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useVaultState } from '../lib/vault'
import VaultSafeIllustration from './VaultSafeIllustration'

export default function VaultShowcaseCard({
  compact = false,
}: {
  compact?: boolean
}) {
  const { summary, tier, effectivePro } = useVaultState()
  const [hovered, setHovered] = useState(false)

  return (
    <section
      aria-label="Personal Question Vault"
      className={`vs-showcase${compact ? ' is-compact' : ''}`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div className="vs-showcase-art">
        <VaultSafeIllustration
          size="card"
          isOpen={hovered || summary.total > 0}
          count={summary.total}
          favoritesCount={summary.favorites}
          tier={tier.id}
          interactive={false}
        />
      </div>

      <div className="vs-showcase-body">
        <div className="vs-showcase-top">
          <span className="vs-eyebrow">Personal Question Vault</span>
          <span className={`vs-tier-pill vs-tier-${tier.id}`}>{tier.label}</span>
          {effectivePro && <span className="vs-pro-pill">★ Pro Vault</span>}
        </div>
        <h2>Your Private Question Safe</h2>
        <p>
          Save tricky bank questions from anywhere, star Pro favorites, craft custom
          MCQs &amp; image flashcards, spin the dial for surprise drills, and share
          personal test packs.
        </p>

        <div className="vs-showcase-metrics">
          <span>
            <strong>{summary.total}</strong> in vault
          </span>
          <span>
            <strong>{summary.favorites}</strong> ★ favorites
          </span>
          <span>
            <strong>{summary.custom}</strong> ✦ crafted
          </span>
          <span>
            <strong>{summary.due}</strong> due today
          </span>
        </div>

        <div className="vs-showcase-actions">
          <Link to="/vault" className="cr-primary-btn">
            Open my Vault →
          </Link>
          <Link to="/vault?action=craft" className="finna-st-btn">
            ✦ Craft question
          </Link>
          <Link to="/vault?action=spin" className="finna-st-btn">
            🎡 Spin the dial
          </Link>
        </div>
      </div>
    </section>
  )
}
