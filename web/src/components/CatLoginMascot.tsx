import { useEffect, useRef, useState } from 'react'

export type CatMood = 'idle' | 'email' | 'password' | 'peek' | 'happy' | 'error'

export const CAT_MOOD_TEXT: Record<CatMood, string> = {
  idle: 'Tap the cat to say hi',
  email: 'Reading along…',
  password: 'Not peeking at your password!',
  peek: 'Just a tiny peek!',
  happy: 'Purrfect! Ready to study',
  error: 'Oops — check those details',
}

export interface CatLoginMascotProps {
  mood: CatMood
  /** 0..1 reading progress along the email input so eyes follow typing. */
  emailProgress?: number
  onPet?: () => void
  /** Hide inline pill when the parent renders the mood pill perched on the card top edge. */
  hidePill?: boolean
}

/**
 * Interactive Ginger Tabby Cat Mascot for Finna Sign-In / Join.
 * Eyes follow the pointer / email typing progress; paws cover eyes on password;
 * one paw lowers on Show ("peek"); happy arc eyes on submit or tap; frown on error.
 */
export default function CatLoginMascot({
  mood,
  emailProgress = 0,
  onPet,
  hidePill = false,
}: CatLoginMascotProps) {
  const stageRef = useRef<HTMLDivElement>(null)
  const [eyeOffset, setEyeOffset] = useState({ x: 0, y: 0 })
  const [petted, setPetted] = useState(false)

  // Track mouse pointer smoothly when not covering eyes
  useEffect(() => {
    if (mood === 'password') return
    const onMove = (e: PointerEvent) => {
      const el = stageRef.current
      if (!el) return
      const rect = el.getBoundingClientRect()
      const cx = rect.left + rect.width / 2
      const cy = rect.top + rect.height * 0.56
      const dx = e.clientX - cx
      const dy = e.clientY - cy
      const angle = Math.atan2(dy, dx)
      const dist = Math.min(1, Math.hypot(dx, dy) / 220)
      setEyeOffset({
        x: Math.cos(angle) * 5.2 * dist,
        y: Math.sin(angle) * 3.8 * dist,
      })
    }
    window.addEventListener('pointermove', onMove, { passive: true })
    return () => window.removeEventListener('pointermove', onMove)
  }, [mood])

  const pupilX =
    mood === 'email'
      ? -5.5 + Math.min(1, Math.max(0, emailProgress)) * 11
      : mood === 'peek'
        ? 1.5
        : eyeOffset.x
  const pupilY =
    mood === 'email' ? 4.2 : mood === 'peek' ? 3.5 : eyeOffset.y

  const headTilt =
    mood === 'email'
      ? -4 + Math.min(1, Math.max(0, emailProgress)) * 8
      : mood === 'peek'
        ? -5
        : 0

  const effectiveMood: CatMood = petted ? 'happy' : mood

  function handlePet() {
    setPetted(true)
    onPet?.()
    window.setTimeout(() => setPetted(false), 1200)
  }

  return (
    <div
      ref={stageRef}
      className={`cat-stage cat-mood-${effectiveMood}`}
      onClick={handlePet}
      role="button"
      tabIndex={0}
      aria-label="Finna ginger study cat mascot — tap to pet"
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          handlePet()
        }
      }}
    >
      <svg viewBox="40 14 260 190" className="cat-svg" aria-hidden="true">
        <defs>
          <radialGradient id="cat-aura" cx="50%" cy="62%" r="48%">
            <stop offset="0%" stopColor="#FFE7A3" stopOpacity="0.8" />
            <stop offset="55%" stopColor="#FFC83D" stopOpacity="0.22" />
            <stop offset="100%" stopColor="#FFC83D" stopOpacity="0" />
          </radialGradient>
          {/* Ginger Tabby Fur */}
          <linearGradient id="cat-ginger-fur" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#FDBA74" />
            <stop offset="48%" stopColor="#FB923C" />
            <stop offset="100%" stopColor="#EA580C" />
          </linearGradient>
          <linearGradient id="cat-ginger-ear" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#F97316" />
            <stop offset="100%" stopColor="#C2410C" />
          </linearGradient>
          <linearGradient id="cat-ginger-paw" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#FDBA74" />
            <stop offset="65%" stopColor="#FB923C" />
            <stop offset="100%" stopColor="#FFF3D6" />
          </linearGradient>
        </defs>

        {/* Warm Finna yellow aura */}
        <ellipse cx="170" cy="120" rx="124" ry="66" fill="url(#cat-aura)" />

        {/* Swaying ginger striped tail */}
        <path
          className="cat-tail"
          d="M226 164 C262 164, 280 130, 262 106 C254 95, 243 102, 248 113 C254 128, 244 146, 224 150"
          fill="none"
          stroke="#EA580C"
          strokeWidth="13"
          strokeLinecap="round"
        />
        <path
          className="cat-tail"
          d="M254 134 L264 138 M257 118 L266 116"
          fill="none"
          stroke="#9A3412"
          strokeWidth="3.5"
          strokeLinecap="round"
          opacity="0.7"
        />

        {/* Ginger body + warm cream chest bib */}
        <ellipse cx="170" cy="178" rx="66" ry="34" fill="#F97316" stroke="#7C2D12" strokeWidth="2.4" />
        <ellipse cx="170" cy="178" rx="34" ry="22" fill="#FFF3D6" />
        {/* Finna blue collar + yellow bell */}
        <path d="M132 158 Q170 172 208 158" fill="none" stroke="#1F4BE0" strokeWidth="8" strokeLinecap="round" />
        <circle cx="170" cy="168" r="7.5" fill="#FFC83D" stroke="#7C2D12" strokeWidth="1.8" />
        <circle cx="170" cy="170" r="2" fill="#7C2D12" />

        {/* Animated Ginger Cat Head */}
        <g className="cat-head" style={{ transform: `rotate(${headTilt}deg)` }}>
          {/* Left Ear */}
          <g className="cat-ear-l">
            <path
              d="M114 86 L104 30 Q104 22 113 26 L152 58 Z"
              fill="url(#cat-ginger-ear)"
              stroke="#7C2D12"
              strokeWidth="2.6"
              strokeLinejoin="round"
            />
            <path d="M116 76 L111 40 L141 62 Z" fill="#FDA4AF" />
          </g>

          {/* Right Ear */}
          <g className="cat-ear-r">
            <path
              d="M226 86 L236 30 Q236 22 227 26 L188 58 Z"
              fill="url(#cat-ginger-ear)"
              stroke="#7C2D12"
              strokeWidth="2.6"
              strokeLinejoin="round"
            />
            <path d="M224 76 L229 40 L199 62 Z" fill="#FDA4AF" />
          </g>

          {/* Ginger Head Base */}
          <ellipse
            cx="170"
            cy="108"
            rx="64"
            ry="53"
            fill="url(#cat-ginger-fur)"
            stroke="#7C2D12"
            strokeWidth="2.6"
          />

          {/* Cream lower muzzle / cheeks patch (classic ginger tabby!) */}
          <ellipse cx="170" cy="126" rx="40" ry="27" fill="#FFF5E1" opacity="0.92" />

          {/* Bold Marmalade Tabby Forehead M-Stripes */}
          <path
            d="M156 58 Q159 72 154 78 M170 55 Q170 72 170 80 M184 58 Q181 72 186 78"
            fill="none"
            stroke="#C2410C"
            strokeWidth="5"
            strokeLinecap="round"
            opacity="0.82"
          />
          {/* Cheek ginger tabby stripes */}
          <path d="M109 106 L124 109 M111 116 L125 117" stroke="#C2410C" strokeWidth="3.4" strokeLinecap="round" opacity="0.72" />
          <path d="M231 106 L216 109 M229 116 L215 117" stroke="#C2410C" strokeWidth="3.4" strokeLinecap="round" opacity="0.72" />

          {/* Rosy blush cheeks */}
          <ellipse cx="130" cy="122" rx="10" ry="6" fill="#FB7185" opacity="0.52" />
          <ellipse cx="210" cy="122" rx="10" ry="6" fill="#FB7185" opacity="0.52" />

          {/* Expressive Eyes */}
          {effectiveMood === 'happy' ? (
            <g stroke="#1E293B" strokeWidth="3.6" fill="none" strokeLinecap="round">
              <path d="M134 104 Q145 92 156 104" />
              <path d="M184 104 Q195 92 206 104" />
            </g>
          ) : (
            <g className="cat-eyes-blink">
              {/* Left Eye */}
              <ellipse cx="145" cy="103" rx="13.5" ry="14.5" fill="#FFFFFF" stroke="#1E293B" strokeWidth="2.2" />
              <g style={{ transform: `translate(${pupilX}px, ${pupilY}px)`, transition: 'transform 90ms ease-out' }}>
                <circle cx="145" cy="103" r="8.2" fill="#0F766E" />
                <circle cx="145" cy="103" r="5.4" fill="#0F172A" />
                <circle cx="142.2" cy="99.6" r="2.8" fill="#FFFFFF" />
                <circle cx="147.8" cy="106.2" r="1.4" fill="#FFFFFF" />
              </g>

              {/* Right Eye */}
              <ellipse cx="195" cy="103" rx="13.5" ry="14.5" fill="#FFFFFF" stroke="#1E293B" strokeWidth="2.2" />
              <g style={{ transform: `translate(${pupilX}px, ${pupilY}px)`, transition: 'transform 90ms ease-out' }}>
                <circle cx="195" cy="103" r="8.2" fill="#0F766E" />
                <circle cx="195" cy="103" r="5.4" fill="#0F172A" />
                <circle cx="192.2" cy="99.6" r="2.8" fill="#FFFFFF" />
                <circle cx="197.8" cy="106.2" r="1.4" fill="#FFFFFF" />
              </g>
            </g>
          )}

          {/* Cute Pink Nose & ":3" Smile */}
          <path d="M165 117 Q170 114 175 117 L170 123 Z" fill="#FB7185" stroke="#7C2D12" strokeWidth="1.4" strokeLinejoin="round" />
          {effectiveMood === 'error' ? (
            <path d="M162 132 Q170 125 178 132" fill="none" stroke="#7C2D12" strokeWidth="2.4" strokeLinecap="round" />
          ) : (
            <path
              d="M158 126 Q164 133 170 126 Q176 133 182 126"
              fill="none"
              stroke="#7C2D12"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Delicate Whiskers */}
          <g stroke="#7C2D12" strokeWidth="1.6" strokeLinecap="round" opacity="0.7">
            <line x1="94" y1="110" x2="122" y2="114" />
            <line x1="92" y1="120" x2="121" y2="120" />
            <line x1="96" y1="130" x2="123" y2="126" />
            <line x1="246" y1="110" x2="218" y2="114" />
            <line x1="248" y1="120" x2="219" y2="120" />
            <line x1="244" y1="130" x2="217" y2="126" />
          </g>
        </g>

        {/* Left Ginger Paw with Cream Mitt & Pink Toe Beans */}
        <g className="cat-paw cat-paw-l">
          <ellipse cx="124" cy="170" rx="22" ry="16" fill="url(#cat-ginger-paw)" stroke="#7C2D12" strokeWidth="2.5" />
          <ellipse cx="124" cy="173" rx="8" ry="5.5" fill="#FDA4AF" />
          <circle cx="114" cy="165" r="3.4" fill="#FDA4AF" />
          <circle cx="124" cy="162" r="3.4" fill="#FDA4AF" />
          <circle cx="134" cy="165" r="3.4" fill="#FDA4AF" />
        </g>

        {/* Right Ginger Paw with Cream Mitt & Pink Toe Beans */}
        <g className="cat-paw cat-paw-r">
          <ellipse cx="216" cy="170" rx="22" ry="16" fill="url(#cat-ginger-paw)" stroke="#7C2D12" strokeWidth="2.5" />
          <ellipse cx="216" cy="173" rx="8" ry="5.5" fill="#FDA4AF" />
          <circle cx="206" cy="165" r="3.4" fill="#FDA4AF" />
          <circle cx="216" cy="162" r="3.4" fill="#FDA4AF" />
          <circle cx="226" cy="165" r="3.4" fill="#FDA4AF" />
        </g>
      </svg>

      {!hidePill && <span className="cat-mood-pill">{CAT_MOOD_TEXT[effectiveMood]}</span>}
    </div>
  )
}
