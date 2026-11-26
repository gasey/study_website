/**
 * Pure-CSS Curled Cat Loader & Cat-Runner XP/Progress Bar
 * Inspired by Rplus's `[CSS] Cat loader` (codepen.io/Rplus/pen/PWZYRM)
 * and harmonized with Finna's warm ginger cat mascot.
 */

export function CatLoader({
  size = 'md',
  label,
  className = '',
}: {
  size?: 'sm' | 'md' | 'lg'
  label?: string
  className?: string
}) {
  return (
    <div
      className={`cat-loader-wrap cat-loader-wrap--${size} ${className}`.trim()}
      role={label ? 'status' : undefined}
      aria-live={label ? 'polite' : undefined}
    >
      <div className={`cat-loader cat-loader--${size}`} aria-hidden="true">
        <div className="cat-loader-track" />
        <div className="cat-loader-body">
          <div className="cat-loader-arc" />
        </div>
        <div className="cat-loader-tail">
          <div className="cat-loader-tail-arc" />
        </div>
        <div className="cat-loader-head">
          <div className="cat-loader-face">
            <span className="cat-loader-ear cat-loader-ear--l" />
            <span className="cat-loader-ear cat-loader-ear--r" />
            <span className="cat-loader-eye cat-loader-eye--l" />
            <span className="cat-loader-eye cat-loader-eye--r" />
            <span className="cat-loader-nose" />
          </div>
        </div>
      </div>
      {label && <span className="cat-loader-label">{label}</span>}
    </div>
  )
}

export function CatXpBar({
  value,
  max = 100,
  tone = 'xp',
  label,
  meta,
  showCat = true,
  className = '',
}: {
  value: number
  max?: number
  tone?: 'xp' | 'quest' | 'teal' | 'gold'
  label?: string
  meta?: string
  showCat?: boolean
  className?: string
}) {
  const safeMax = Math.max(1, max)
  const pct = Math.max(0, Math.min(100, Math.round((value / safeMax) * 100)))
  return (
    <div className={`cat-xp ${className}`.trim()}>
      {(label || meta) && (
        <div className="cat-xp-head">
          {label && <span className="cat-xp-label">{label}</span>}
          {meta && <span className="cat-xp-meta">{meta}</span>}
        </div>
      )}
      <div
        className={`cat-xp-track cat-xp-track--${tone}`}
        role="progressbar"
        aria-label={label || 'Progress'}
        aria-valuemin={0}
        aria-valuemax={safeMax}
        aria-valuenow={Math.min(safeMax, Math.max(0, Math.round(value)))}
      >
        <div className="cat-xp-fill" style={{ width: `${pct}%` }}>
          <span className="cat-xp-stripes" aria-hidden="true" />
        </div>
        {showCat && (
          <span
            className="cat-xp-runner"
            style={{ left: `clamp(10px, ${pct}%, calc(100% - 10px))` }}
            aria-hidden="true"
          >
            <span className="cat-xp-ear cat-xp-ear--l" />
            <span className="cat-xp-ear cat-xp-ear--r" />
            <span className="cat-xp-eyes" />
          </span>
        )}
      </div>
    </div>
  )
}
