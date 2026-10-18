import type { ReactNode } from 'react'

/** Primitives extracted from the prototype. Every screen composes these
 *  rather than re-deriving padding and radii, which is how a design drifts.
 *  Values come from the markup, not the handoff README — see
 *  docs/DESIGN-FIDELITY.md for where the two disagree. */

/** Filled pill button. The primary action everywhere; always ink, never
 *  vermilion — vermilion is the brand mark only. (markup line 49) */
export function PillButton({
  children,
  onClick,
  tone = 'ink',
  disabled,
}: {
  children: ReactNode
  onClick?: () => void
  tone?: 'ink' | 'quiet'
  disabled?: boolean
}) {
  const tones = {
    ink: 'bg-ink text-paper',
    quiet: 'border border-hairline bg-[#F7F3EA] text-ink',
  }
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`whitespace-nowrap rounded-pill px-4 py-[9px] text-[14px] font-semibold disabled:opacity-40 ${tones[tone]}`}
    >
      {children}
    </button>
  )
}

/** Outlined pill, used for provenance and other metadata that must not read
 *  as an action. (markup line 411) */
export function OutlinePill({
  children,
  colorClass,
}: {
  children: ReactNode
  colorClass: string
}) {
  return (
    <span
      className={`shrink-0 rounded-pill border px-2 py-[2px] font-mono text-[10px] uppercase tracking-[0.06em] ${colorClass}`}
    >
      {children}
    </span>
  )
}

/** Solid chip — topic tags and the repeat badge. (markup lines 410, 412) */
export function Chip({
  children,
  className = '',
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <span
      className={`shrink-0 rounded-pill px-[9px] py-[3px] font-mono text-[10px] uppercase tracking-[0.06em] ${className}`}
    >
      {children}
    </span>
  )
}

/** Small count badge, e.g. unread inbox. mono 11px on #B0412A. (line 48) */
export function CountBadge({ children }: { children: ReactNode }) {
  return (
    <span className="rounded-pill bg-mypick px-1.5 py-px font-mono text-[11px] text-[#FBF8F1]">
      {children}
    </span>
  )
}

/** 14px square checkbox, 3px radius, solid ink when on. (markup line 396) */
export function Checkbox({
  on,
  label,
  onClick,
  disabled,
}: {
  on: boolean
  label: ReactNode
  onClick?: () => void
  disabled?: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-pressed={on}
      className="flex w-full items-center gap-2.5 py-1.5 text-left text-[14px] disabled:text-muted"
    >
      <span
        className={`h-[14px] w-[14px] shrink-0 rounded-[3px] border ${
          disabled ? 'border-hairline2' : 'border-ink'
        } ${on ? 'bg-ink' : 'bg-transparent'}`}
      />
      <span>{label}</span>
    </button>
  )
}

/** Group heading used in rails and menu columns: mono 11px, wide tracking,
 *  underlined with 1px ink. (markup lines 393 and 58) */
export function GroupTitle({ children }: { children: ReactNode }) {
  return (
    <div className="mb-1.5 border-b border-ink pb-1.5 font-mono text-[11px] uppercase tracking-[0.1em] text-muted">
      {children}
    </div>
  )
}

/** White surface card: 14px radius, hairline border, the same faint shadow
 *  the prototype uses on the bank article and the filter rail. */
export function Card({
  children,
  className = '',
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <div
      className={`rounded-[14px] border border-hairline bg-card shadow-[0_1px_2px_rgba(29,27,24,.05)] ${className}`}
    >
      {children}
    </div>
  )
}

/** Shown wherever today's data cannot honestly support a control. Preferred
 *  over hiding the feature or shipping a control that returns nothing —
 *  see CLAUDE.md, "Build with the data that exists". */
export function NotYet({ children }: { children: ReactNode }) {
  return <p className="py-1.5 text-[13px] leading-snug text-muted">{children}</p>
}

/** 36px avatar circle with initials. (markup line 50) */
export function Avatar({ initials }: { initials: string }) {
  return (
    <span className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-full border border-ink bg-[#F6DDD3] font-mono text-[12px] font-medium">
      {initials}
    </span>
  )
}
