/**
 * Deterministic 6-slot subject chip palette & 2-letter monogram helpers.
 *
 * Ported from ShikshaCom's utils/subjectChips.js (§VII.19.8):
 * One deterministic hash maps any subject name to the exact same semantic
 * colour slot (0..5 → .finna-subj-chip--0..5) across /home, /exams, /bank,
 * /guides and /results.
 */
export const SUBJECT_SLOT_COUNT = 6

function hashString(name: string): number {
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = (hash * 31 + name.charCodeAt(i)) >>> 0
  }
  return hash
}

/** Deterministic slot index 0..5 for CSS classes `.finna-subj-chip--N`. */
export function subjectChipSlot(name: string | null | undefined): number {
  const normalized = (name || '').trim().toLowerCase()
  if (!normalized) return 0
  return hashString(normalized) % SUBJECT_SLOT_COUNT
}

/** Class name for a subject pill/monogram using tokenised light + night palettes. */
export function subjectChipClass(name: string | null | undefined): string {
  return `finna-subj-chip finna-subj-chip--${subjectChipSlot(name)}`
}

/** Two-letter square monogram for compact list rows (e.g. "Polity" -> "Po"). */
export function subjectInitials(name: string | null | undefined): string {
  const trimmed = (name || '').trim()
  if (!trimmed) return 'St'
  const words = trimmed.split(/\s+/).filter(Boolean)
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }
  return trimmed.slice(0, 1).toUpperCase() + (trimmed.slice(1, 2).toLowerCase() || '')
}
