import { useEffect, useRef, useState, type KeyboardEvent } from 'react'

export interface VaultSafeIllustrationProps {
  isOpen?: boolean
  spinning?: boolean
  size?: 'hero' | 'card' | 'mini'
  count?: number
  favoritesCount?: number
  tier?: 'bronze' | 'silver' | 'gold' | 'diamond'
  interactive?: boolean
  onToggle?: () => void
  label?: string
}

const TIER_GLOW: Record<
  NonNullable<VaultSafeIllustrationProps['tier']>,
  [string, string]
> = {
  bronze: ['#F59E0B', '#FDE68A'],
  silver: ['#38BDF8', '#E0F2FE'],
  gold: ['#F59E0B', '#FEF08A'],
  diamond: ['#818CF8', '#A5F3FC'],
}

/**
 * Interactive Icons8-inspired animated Bank Safe SVG guarded by our Ginger Tabby Cat,
 * with live cursor-tracking eyes, two floating fish treats, twinkling stars, and drifting
 * paw prints. Spins the combination wheel, retracts bolts, swings the 3D steel door open,
 * and reveals glowing saved question cards inside. Respects reduced motion.
 */
export default function VaultSafeIllustration({
  isOpen = false,
  spinning = false,
  size = 'hero',
  count = 0,
  favoritesCount = 0,
  tier = 'gold',
  interactive = true,
  onToggle,
  label,
}: VaultSafeIllustrationProps) {
  const stageRef = useRef<HTMLDivElement>(null)
  const [eye, setEye] = useState({ x: 0, y: 0 })
  const [glowA, glowB] = TIER_GLOW[tier]

  useEffect(() => {
    if (size === 'mini') return
    const onMove = (e: PointerEvent) => {
      const el = stageRef.current
      if (!el) return
      const rect = el.getBoundingClientRect()
      const cx = rect.left + rect.width / 2
      const cy = rect.top + rect.height * 0.22
      const dx = e.clientX - cx
      const dy = e.clientY - cy
      const angle = Math.atan2(dy, dx)
      const dist = Math.min(1, Math.hypot(dx, dy) / 260)
      setEye({ x: Math.cos(angle) * 3.1 * dist, y: Math.sin(angle) * 2.2 * dist })
    }
    window.addEventListener('pointermove', onMove, { passive: true })
    return () => window.removeEventListener('pointermove', onMove)
  }, [size])

  function onKey(e: KeyboardEvent<HTMLDivElement>) {
    if (!interactive || !onToggle) return
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onToggle()
    }
  }

  if (size === 'mini') {
    return (
      <span
        className={`vs-mini${isOpen ? ' is-open' : ''}${spinning ? ' is-spinning' : ''}`}
        aria-hidden="true"
      >
        <svg viewBox="0 0 48 52" width="24" height="24" fill="none">
          {/* Tiny ginger cat ears peeking on top of mini safe */}
          <path d="M15 11 L13 3 L21 8 Z" fill="#F97316" />
          <path d="M33 11 L35 3 L27 8 Z" fill="#F97316" />
          <ellipse cx="24" cy="11" rx="9" ry="5.5" fill="#FB923C" />
          <circle cx="21" cy="10" r="1.4" fill="#0F172A" />
          <circle cx="27" cy="10" r="1.4" fill="#0F172A" />
          <rect x="9" y="44" width="7" height="4" rx="1.5" fill="#263238" />
          <rect x="32" y="44" width="7" height="4" rx="1.5" fill="#263238" />
          <rect x="5" y="10" width="38" height="35" rx="6" fill="#455A64" />
          <rect x="9" y="14" width="30" height="27" rx="3.5" fill="#1E293B" />
          <rect
            x="14"
            y="18"
            width="16"
            height="19"
            rx="2"
            fill={glowA}
            className="vs-mini-loot"
          />
          <g className="vs-mini-door">
            <rect x="10" y="15" width="28" height="25" rx="3" fill="#607D8B" />
            <rect x="8" y="18" width="3.5" height="5" rx="1" fill="#F59E0B" />
            <rect x="8" y="32" width="3.5" height="5" rx="1" fill="#F59E0B" />
            <g className="vs-mini-dial">
              <circle cx="25" cy="27.5" r="7" fill="#CFD8DC" stroke="#37474F" strokeWidth="1.6" />
              <circle cx="25" cy="27.5" r="3" fill="#F59E0B" />
              <path d="M25 20.5v3.5M25 31v3.5M18 27.5h3.5M28.5 27.5H32" stroke="#37474F" strokeWidth="1.6" strokeLinecap="round" />
            </g>
          </g>
        </svg>
      </span>
    )
  }

  return (
    <div
      ref={stageRef}
      role={interactive && onToggle ? 'button' : undefined}
      tabIndex={interactive && onToggle ? 0 : undefined}
      aria-pressed={interactive && onToggle ? isOpen : undefined}
      aria-label={
        label ||
        (isOpen ? 'Close personal question safe' : 'Open personal question safe')
      }
      onClick={interactive ? onToggle : undefined}
      onKeyDown={onKey}
      className={`vs-stage vs-size-${size}${isOpen ? ' is-open' : ''}${spinning ? ' is-spinning' : ''}${interactive && onToggle ? ' is-clickable' : ''}`}
    >
      {/* Peeking Ginger Cat Guardian + Twin Floating Fish + Twinkling Stars & Paws */}
      <svg
        viewBox="0 0 260 92"
        className="vs-cat-topper"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id={`vs-gfur-${size}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#FDBA74" />
            <stop offset="52%" stopColor="#FB923C" />
            <stop offset="100%" stopColor="#EA580C" />
          </linearGradient>
          <linearGradient id={`vs-ft1-${size}`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#5EEAD4" />
            <stop offset="100%" stopColor="#0A7D8C" />
          </linearGradient>
          <linearGradient id={`vs-ft2-${size}`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#FDE047" />
            <stop offset="100%" stopColor="#F43F5E" />
          </linearGradient>
        </defs>

        {/* Floating Fish #1 (Teal fish left) */}
        <g className="cat-float-fish cat-fish-1">
          <g transform="translate(26 44) rotate(-14)">
            <path d="M0 0 L-10 -7 Q-7 0 -10 7 Z" fill="#0D9488" stroke="#134E4A" strokeWidth="1.3" />
            <ellipse cx="11" cy="0" rx="13" ry="8.2" fill={`url(#vs-ft1-${size})`} stroke="#134E4A" strokeWidth="1.4" />
            <circle cx="17.5" cy="-1.8" r="1.9" fill="#0F172A" />
            <circle cx="18.1" cy="-2.4" r="0.7" fill="#FFFFFF" />
            <circle cx="29" cy="-6" r="1.8" fill="#99F6E4" opacity="0.85" />
          </g>
        </g>

        {/* Floating Fish #2 (Golden-coral fish right) */}
        <g className="cat-float-fish cat-fish-2">
          <g transform="translate(234 38) scale(-1, 1) rotate(-10)">
            <path d="M0 0 L-10 -7 Q-7 0 -10 7 Z" fill="#FB7185" stroke="#881337" strokeWidth="1.3" />
            <ellipse cx="11" cy="0" rx="12.5" ry="8" fill={`url(#vs-ft2-${size})`} stroke="#881337" strokeWidth="1.4" />
            <path d="M6 -6.5 Q8.5 0 6 6.5" fill="none" stroke="#FFFFFF" strokeWidth="2" opacity="0.7" />
            <circle cx="17" cy="-1.6" r="1.9" fill="#0F172A" />
            <circle cx="17.6" cy="-2.2" r="0.7" fill="#FFFFFF" />
            <circle cx="28" cy="-5" r="1.7" fill="#FEF08A" opacity="0.9" />
          </g>
        </g>

        {/* Twinkling Stars & Drifting Paw Print */}
        <g className="cat-float-star cat-star-1">
          <path d="M62 24 Q62 16 54 16 Q62 16 62 8 Q62 16 70 16 Q62 16 62 24Z" fill="#F59E0B" />
        </g>
        <g className="cat-float-star cat-star-2">
          <path d="M200 22 Q200 15 193 15 Q200 15 200 8 Q200 15 207 15 Q200 15 200 22Z" fill="#FBBF24" />
        </g>
        <g className="cat-float-paw cat-pawprint-1" transform="translate(46 74) rotate(-20) scale(0.72)">
          <ellipse cx="0" cy="4" rx="5.5" ry="4.4" fill="#F97316" opacity="0.55" />
          <circle cx="-5.5" cy="-2.6" r="2.1" fill="#F97316" opacity="0.55" />
          <circle cx="-1" cy="-5.4" r="2.1" fill="#F97316" opacity="0.55" />
          <circle cx="3.4" cy="-5" r="2.1" fill="#F97316" opacity="0.55" />
          <circle cx="6.4" cy="-1" r="1.9" fill="#F97316" opacity="0.55" />
        </g>

        {/* Ginger Cat Peeking Happily Over the Safe */}
        <g className="vs-vault-cat">
          {/* Ears */}
          <g className="cat-ear-l">
            <path d="M95 54 L87 18 Q87 12 94 15 L120 38 Z" fill="#EA580C" stroke="#7C2D12" strokeWidth="2.2" strokeLinejoin="round" />
            <path d="M97 48 L93 25 L113 40 Z" fill="#FDA4AF" />
          </g>
          <g className="cat-ear-r">
            <path d="M165 54 L173 18 Q173 12 166 15 L140 38 Z" fill="#EA580C" stroke="#7C2D12" strokeWidth="2.2" strokeLinejoin="round" />
            <path d="M163 48 L167 25 L147 40 Z" fill="#FDA4AF" />
          </g>

          {/* Ginger Head */}
          <ellipse cx="130" cy="64" rx="42" ry="34" fill={`url(#vs-gfur-${size})`} stroke="#7C2D12" strokeWidth="2.2" />
          <ellipse cx="130" cy="76" rx="26" ry="17" fill="#FFF5E1" opacity="0.92" />
          {/* Tabby forehead stripes */}
          <path d="M121 32 Q123 41 120 45 M130 30 Q130 41 130 46 M139 32 Q137 41 140 45" fill="none" stroke="#C2410C" strokeWidth="3.6" strokeLinecap="round" opacity="0.82" />
          {/* Rosy cheeks */}
          <ellipse cx="104" cy="73" rx="6.5" ry="4" fill="#FB7185" opacity="0.55" />
          <ellipse cx="156" cy="73" rx="6.5" ry="4" fill="#FB7185" opacity="0.55" />

          {/* Eyes */}
          {spinning ? (
            <g stroke="#1E293B" strokeWidth="3" fill="none" strokeLinecap="round">
              <path d="M107 62 Q114 54 121 62" />
              <path d="M139 62 Q146 54 153 62" />
            </g>
          ) : (
            <g className="cat-eyes-blink">
              <ellipse cx="114" cy="61" rx="8.8" ry="9.5" fill="#FFFFFF" stroke="#1E293B" strokeWidth="1.8" />
              <g style={{ transform: `translate(${eye.x}px, ${eye.y}px)`, transition: 'transform 90ms ease-out' }}>
                <circle cx="114" cy="61" r="5.3" fill="#0F766E" />
                <circle cx="114" cy="61" r="3.4" fill="#0F172A" />
                <circle cx="112.2" cy="59" r="1.8" fill="#FFFFFF" />
              </g>
              <ellipse cx="146" cy="61" rx="8.8" ry="9.5" fill="#FFFFFF" stroke="#1E293B" strokeWidth="1.8" />
              <g style={{ transform: `translate(${eye.x}px, ${eye.y}px)`, transition: 'transform 90ms ease-out' }}>
                <circle cx="146" cy="61" r="5.3" fill="#0F766E" />
                <circle cx="146" cy="61" r="3.4" fill="#0F172A" />
                <circle cx="144.2" cy="59" r="1.8" fill="#FFFFFF" />
              </g>
            </g>
          )}

          {/* Nose & ":3" smile */}
          <path d="M126.5 70 Q130 68 133.5 70 L130 74 Z" fill="#FB7185" />
          <path d="M122 76 Q126 80.5 130 76 Q134 80.5 138 76" fill="none" stroke="#7C2D12" strokeWidth="2" strokeLinecap="round" />

          {/* Plump ginger paws gripping the top rim of the safe */}
          <g className="vs-cat-paws">
            <ellipse cx="97" cy="86" rx="13" ry="8.5" fill="#FDBA74" stroke="#7C2D12" strokeWidth="2" />
            <circle cx="93" cy="85" r="2" fill="#FDA4AF" />
            <circle cx="98" cy="84" r="2" fill="#FDA4AF" />
            <circle cx="102" cy="86" r="1.8" fill="#FDA4AF" />

            <ellipse cx="163" cy="86" rx="13" ry="8.5" fill="#FDBA74" stroke="#7C2D12" strokeWidth="2" />
            <circle cx="158" cy="86" r="1.8" fill="#FDA4AF" />
            <circle cx="162" cy="84" r="2" fill="#FDA4AF" />
            <circle cx="167" cy="85" r="2" fill="#FDA4AF" />
          </g>
        </g>
      </svg>

      {/* Safe Cabinet Back + Glowing Interior */}
      <div className="vs-cabinet">
        <svg viewBox="0 0 220 210" className="vs-svg-back" aria-hidden="true">
          <defs>
            <linearGradient id={`vs-body-${size}`} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#607D8B" />
              <stop offset="55%" stopColor="#455A64" />
              <stop offset="100%" stopColor="#37474F" />
            </linearGradient>
            <radialGradient id={`vs-glow-${size}`} cx="52%" cy="54%" r="54%">
              <stop offset="0%" stopColor={glowB} stopOpacity="0.95" />
              <stop offset="52%" stopColor={glowA} stopOpacity="0.45" />
              <stop offset="100%" stopColor="#0F172A" stopOpacity="0" />
            </radialGradient>
          </defs>

          <ellipse cx="110" cy="199" rx="78" ry="8" fill="rgba(15,23,42,0.22)" />
          <rect x="38" y="182" width="28" height="16" rx="5" fill="#263238" />
          <rect x="154" y="182" width="28" height="16" rx="5" fill="#263238" />
          <rect x="20" y="16" width="180" height="170" rx="22" fill={`url(#vs-body-${size})`} />
          <rect
            x="24"
            y="20"
            width="172"
            height="162"
            rx="19"
            fill="none"
            stroke="rgba(255,255,255,0.22)"
            strokeWidth="2"
          />

          <rect x="38" y="34" width="144" height="134" rx="12" fill="#0F172A" />
          <rect x="42" y="116" width="136" height="6" rx="2" fill="#1E293B" />
          <rect
            x="38"
            y="34"
            width="144"
            height="134"
            rx="12"
            fill={`url(#vs-glow-${size})`}
            className="vs-interior-glow"
          />

          {/* Stacked glowing Question Cards & Gold Star Treasures inside */}
          <g className="vs-loot-stack">
            <g transform="translate(64 46) rotate(-8)">
              <rect x="0" y="0" width="66" height="58" rx="8" fill="#FEF3C7" stroke="#F59E0B" strokeWidth="2" />
              <rect x="10" y="14" width="34" height="5" rx="2.5" fill="#B45309" />
              <rect x="10" y="25" width="44" height="4" rx="2" fill="#D97706" opacity="0.7" />
              <rect x="10" y="34" width="38" height="4" rx="2" fill="#D97706" opacity="0.55" />
            </g>
            <g transform="translate(88 52) rotate(5)">
              <rect x="0" y="0" width="72" height="60" rx="9" fill="#FFFFFF" stroke="#0A7D8C" strokeWidth="2.2" />
              <circle cx="16" cy="17" r="7" fill="#0A7D8C" />
              <text x="16" y="20.5" textAnchor="middle" fontSize="9.5" fontWeight="800" fill="#FFFFFF">Q</text>
              <rect x="28" y="13" width="32" height="4.5" rx="2" fill="#0F172A" opacity="0.75" />
              <rect x="28" y="21" width="24" height="3.5" rx="1.7" fill="#64748B" />
              <rect x="10" y="33" width="52" height="6" rx="3" fill="#DCFCE7" />
              <rect x="10" y="43" width="40" height="6" rx="3" fill="#E0F2FE" />
            </g>
            <g transform="translate(52 128)">
              <rect x="0" y="14" width="46" height="16" rx="5" fill="#F59E0B" />
              <rect x="6" y="6" width="42" height="14" rx="4" fill="#FBBF24" />
              <circle cx="88" cy="18" r="13" fill="#F59E0B" stroke="#FEF08A" strokeWidth="2" />
              <text x="88" y="22.5" textAnchor="middle" fontSize="13" fontWeight="900" fill="#78350F">★</text>
              <rect x="108" y="8" width="20" height="22" rx="4" fill="#14B8A6" />
              <text x="118" y="23" textAnchor="middle" fontSize="10" fontWeight="800" fill="#FFFFFF">✓</text>
            </g>
          </g>
        </svg>

        {/* 3D Hinged Safe Door */}
        <div className="vs-door-wrap" aria-hidden="true">
          <svg viewBox="0 0 156 146" className="vs-svg-door">
            <defs>
              <linearGradient id={`vs-door-${size}`} x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#78909C" />
                <stop offset="45%" stopColor="#546E7A" />
                <stop offset="100%" stopColor="#37474F" />
              </linearGradient>
              <linearGradient id={`vs-dial-${size}`} x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#ECEFF1" />
                <stop offset="100%" stopColor="#B0BEC5" />
              </linearGradient>
            </defs>

            <g className="vs-bolts">
              <rect x="136" y="34" width="16" height="14" rx="4" fill="#CFD8DC" stroke="#37474F" strokeWidth="1.5" />
              <rect x="136" y="98" width="16" height="14" rx="4" fill="#CFD8DC" stroke="#37474F" strokeWidth="1.5" />
            </g>

            <rect x="8" y="4" width="136" height="138" rx="14" fill={`url(#vs-door-${size})`} stroke="#263238" strokeWidth="2" />
            <rect x="16" y="12" width="120" height="122" rx="9" fill="none" stroke="rgba(255,255,255,0.22)" strokeWidth="1.8" />

            <rect x="3" y="24" width="11" height="26" rx="4" fill="#F59E0B" stroke="#78350F" strokeWidth="1.4" />
            <rect x="3" y="96" width="11" height="26" rx="4" fill="#F59E0B" stroke="#78350F" strokeWidth="1.4" />

            <circle cx="118" cy="26" r="5" fill={isOpen ? '#22C55E' : '#F59E0B'} />
            <circle cx="118" cy="26" r="2.2" fill="#FFFFFF" opacity="0.7" />

            <g className="vs-dial-wheel">
              <circle cx="78" cy="73" r="35" fill="#263238" opacity="0.45" />
              <circle cx="78" cy="73" r="31" fill={`url(#vs-dial-${size})`} stroke="#37474F" strokeWidth="2.5" />
              <circle cx="78" cy="73" r="24" fill="none" stroke="#455A64" strokeWidth="2.2" strokeDasharray="3 5" />
              <path
                d="M78 44v58M49 73h58M57.5 52.5l41 41M98.5 52.5l-41 41"
                stroke="#37474F"
                strokeWidth="4.2"
                strokeLinecap="round"
              />
              <circle cx="78" cy="73" r="13" fill="#F59E0B" stroke="#78350F" strokeWidth="2" />
              <circle cx="78" cy="73" r="5.5" fill="#FEF3C7" />
              <polygon points="78,39 73,47 83,47" fill="#EF4444" />
            </g>
          </svg>
        </div>

        {size !== 'card' && (
          <div className="vs-floating-badge">
            <span>{count} saved</span>
            {favoritesCount > 0 && <span className="vs-badge-star">★ {favoritesCount}</span>}
          </div>
        )}
      </div>

      {interactive && onToggle && size === 'hero' && (
        <span className="vs-tap-hint">
          {isOpen ? 'Vault unlocked · tap safe to lock' : 'Tap safe to crack open'}
        </span>
      )}
    </div>
  )
}
