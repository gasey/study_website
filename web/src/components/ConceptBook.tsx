import { Link } from "react-router-dom";

export type BookTone =
  | "teal"
  | "cobalt"
  | "terracotta"
  | "emerald"
  | "plum"
  | "amber";

const BOOK_TONES: readonly BookTone[] = [
  "teal",
  "cobalt",
  "terracotta",
  "emerald",
  "plum",
  "amber",
];

/** Deterministic bookbinding tone from a stable slug/id or explicit index. */
export function bookToneFor(seed: string, fallbackIndex = 0): BookTone {
  const s = seed.toLowerCase();
  if (s.includes("polity") || s.includes("constitution") || s.includes("civic")) return "cobalt";
  if (s.includes("history") || s.includes("chronicle") || s.includes("mizo") || s.includes("culture")) return "terracotta";
  if (s.includes("geo") || s.includes("atlas") || s.includes("env") || s.includes("science")) return "emerald";
  if (s.includes("math") || s.includes("arith") || s.includes("reason") || s.includes("aptitude")) return "plum";
  if (s.includes("econ") || s.includes("stat") || s.includes("finna") || s.includes("quick")) return "amber";
  if (s.includes("english") || s.includes("grammar") || s.includes("tense") || s.includes("essay")) return "teal";
  let hash = fallbackIndex;
  for (let i = 0; i < s.length; i++) hash = (hash * 31 + s.charCodeAt(i)) >>> 0;
  return BOOK_TONES[hash % BOOK_TONES.length];
}

export function bookMonogram(title: string): string {
  const words = title.trim().split(/[\s&/-]+/).filter(Boolean);
  if (!words.length) return "BK";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

export interface ConceptBookProps {
  to: string;
  title: string;
  subtitle?: string;
  eyebrow?: string;
  meta: string;
  peekTitle?: string;
  peekNote?: string;
  tone?: BookTone;
  compact?: boolean;
}

/**
 * Tactile 3D Concept Book (inspired by vYaeadj, xrRPRL & oNxEBXj):
 * Hardcover front board with spine crease + gold/light rule + bookmark ribbon,
 * fanned cream paper pages peeking underneath on hover/focus, and a crisp
 * shelf shadow base. Respects prefers-reduced-motion.
 */
export default function ConceptBook({
  to,
  title,
  subtitle,
  eyebrow,
  meta,
  peekTitle,
  peekNote,
  tone,
  compact = false,
}: ConceptBookProps) {
  const resolvedTone = tone || bookToneFor(title);
  const code = bookMonogram(title);

  return (
    <Link
      to={to}
      className={`bk-book bk-tone-${resolvedTone}${compact ? " is-compact" : ""}`}
    >
      <span className="bk-stage" aria-hidden="true">
        {/* Back board & stacked cream pages (visible as front cover swings open) */}
        <span className="bk-back" />
        <span className="bk-leaf bk-leaf-2" />
        <span className="bk-leaf bk-leaf-1">
          <span className="bk-page-kicker">{peekTitle || "Inside"}</span>
          <span className="bk-page-lines">
            <span>{peekNote || subtitle || "Open volume to study"}</span>
          </span>
          <span className="bk-page-cta">Open →</span>
        </span>
        {/* Front hardcover board */}
        <span className="bk-cover">
          <span className="bk-spine" />
          <span className="bk-ribbon" />
          <span className="bk-cover-inner">
            <span className="bk-cover-top">
              <span className="bk-badge">{eyebrow || "Volume"}</span>
              <span className="bk-mono">{code}</span>
            </span>
            <span className="bk-cover-rule" />
            <span className="bk-cover-title">{title}</span>
            {subtitle && !compact && (
              <span className="bk-cover-sub">{subtitle}</span>
            )}
            <span className="bk-cover-foot">{meta}</span>
          </span>
        </span>
        {/* Right-side paper block edge */}
        <span className="bk-pages-edge" />
      </span>

      {/* Screen-reader + crisp below-book caption */}
      <span className="bk-caption">
        <strong>{title}</strong>
        <span>{meta}</span>
      </span>
    </Link>
  );
}
