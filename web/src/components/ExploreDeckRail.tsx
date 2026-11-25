import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

export interface SpotlightItem {
  id: "stats" | "guides" | "chronicle" | "atlas" | "games" | "calendar";
  kind: string;
  meta: string;
  title: string;
  body: string;
  cta: string;
  to: string;
  accent: "teal" | "cobalt" | "terracotta" | "emerald" | "violet" | "amber";
  image: string;
  imageAlt: string;
}

const DEFAULT_SPOTLIGHTS: SpotlightItem[] = [
  {
    id: "stats",
    kind: "Stats",
    meta: "India & Global",
    title: "Rankings & Economic Survey",
    body: "Curated tables, state comparisons, and verified indicators built for quick GK revision.",
    cta: "Open Stats",
    to: "/stats",
    accent: "cobalt",
    image: "/images/discover/stats.jpg",
    imageAlt: "Parliament House in New Delhi",
  },
  {
    id: "guides",
    kind: "Guides",
    meta: "11 concept volumes",
    title: "Edited study concept books",
    body: "Polity, Computer, Science, Economy, Maths, English & Reasoning linked straight to bank questions.",
    cta: "Open Guides",
    to: "/guides",
    accent: "teal",
    image: "/images/discover/guides.jpg",
    imageAlt: "Classical university library reading room with wooden study tables and bookshelves",
  },
  {
    id: "chronicle",
    kind: "Chronicle",
    meta: "Timeline & dates",
    title: "History & polity timeline",
    body: "Step through eras, constitutional milestones, and linked past-paper questions by year.",
    cta: "Open Chronicle",
    to: "/chronicle",
    accent: "terracotta",
    image: "/images/discover/chronicle.jpg",
    imageAlt: "Qutub Minar sandstone monument in Delhi",
  },
  {
    id: "atlas",
    kind: "Atlas",
    meta: "Interactive map",
    title: "Geography layers & places",
    body: "Explore rivers, sanctuaries, passes, and Mizoram map chapters interactively.",
    cta: "Open Atlas",
    to: "/atlas",
    accent: "emerald",
    image: "/images/discover/atlas.jpg",
    imageAlt: "Brass compass resting on a vintage geographic map",
  },
  {
    id: "games",
    kind: "Finna Quest",
    meta: "16-Bit RPG & Daily 10-Q",
    title: "Battle Realm Guardians",
    body: "Ascend 12 floors with your custom pixel hero across curated general-knowledge realms.",
    cta: "Play Quest",
    to: "/games/quest",
    accent: "violet",
    image: "/images/discover/games.jpg",
    imageAlt: "Wooden chessboard viewed from above in warm light",
  },
  {
    id: "calendar",
    kind: "Calendar",
    meta: "Notices & plan",
    title: "Exam dates & schedule",
    body: "Track upcoming MPSC notices, personal targets, and daily review forecasts.",
    cta: "Open Calendar",
    to: "/calendar",
    accent: "amber",
    image: "/images/discover/calendar.jpg",
    imageAlt: "Fountain pen writing notes on ruled cream paper",
  },
];

const VISIBLE_COUNT = 3;
const SWIPE_THRESHOLD = 48;

/**
 * Unified Editorial Discovery Showcase with Real Photography.
 * Displays 3 cohesive feature cards simultaneously across every viewport:
 * - Wide desktop (>1440px): tall right-gutter rail (1 featured card + 2 matching compact cards).
 * - Standard desktop/laptop (900-1440px): full-width 3-column equal-height card showcase.
 * - Tablet (640-899px): 2 tall cards + 1 full-width horizontal card.
 * - Mobile (<640px): swipeable featured card + 2 compact horizontal cards.
 */
export default function ExploreDeckRail({
  exclude = [],
  interval = 7500,
  heading = "Also on Finna",
  compact = false,
}: {
  exclude?: string[];
  interval?: number;
  heading?: string;
  compact?: boolean;
}) {
  const items = DEFAULT_SPOTLIGHTS.filter((item) => !exclude.includes(item.id));
  const count = items.length;

  const [startIndex, setStartIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return (
        typeof sessionStorage !== "undefined" &&
        sessionStorage.getItem("finna_ed_collapsed") === "1"
      );
    } catch {
      return false;
    }
  });

  const touchStartX = useRef<number | null>(null);

  function toggleCollapsed(next: boolean) {
    setCollapsed(next);
    try {
      sessionStorage.setItem("finna_ed_collapsed", next ? "1" : "0");
    } catch {
      /* ignore */
    }
  }

  const step = useCallback(
    (dir: 1 | -1) => {
      if (count < 2) return;
      setStartIndex((prev) => (prev + dir + count) % count);
    },
    [count],
  );

  const jumpTo = useCallback(
    (id: string) => {
      const idx = items.findIndex((item) => item.id === id);
      if (idx >= 0) setStartIndex(idx);
    },
    [items],
  );

  useEffect(() => {
    if (
      paused ||
      collapsed ||
      count <= 1 ||
      (typeof window !== "undefined" &&
        window.matchMedia?.("(prefers-reduced-motion: reduce)").matches)
    ) {
      return;
    }
    const timer = window.setTimeout(() => step(1), interval);
    return () => window.clearTimeout(timer);
  }, [startIndex, paused, collapsed, interval, count, step]);

  useEffect(() => {
    const onVis = () => setPaused(document.hidden);
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, []);

  function onKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (e.key === "ArrowRight") {
      e.preventDefault();
      step(1);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      step(-1);
    }
  }

  function onTouchStart(e: React.TouchEvent<HTMLDivElement>) {
    touchStartX.current = e.touches[0]?.clientX ?? null;
  }

  function onTouchEnd(e: React.TouchEvent<HTMLDivElement>) {
    if (touchStartX.current === null) return;
    const endX = e.changedTouches[0]?.clientX ?? touchStartX.current;
    const dx = endX - touchStartX.current;
    touchStartX.current = null;
    if (Math.abs(dx) >= SWIPE_THRESHOLD) {
      step(dx < 0 ? 1 : -1);
    }
  }

  if (count === 0) return null;

  if (collapsed) {
    return (
      <aside
        className="ed-rail ed-rail--collapsed"
        aria-label="Explore more study features"
      >
        <button
          type="button"
          className="ed-reopen-btn"
          onClick={() => toggleCollapsed(false)}
        >
          <span>✦ Discover</span>
          <span className="ed-reopen-sub">Stats · Guides · Atlas · Games</span>
        </button>
      </aside>
    );
  }

  const visibleCount = Math.min(VISIBLE_COUNT, count);
  const visibleItems: SpotlightItem[] = Array.from(
    { length: visibleCount },
    (_, offset) => items[(startIndex + offset) % count],
  );
  const visibleIds = new Set(visibleItems.map((i) => i.id));
  const activeId = visibleItems[0]?.id;

  return (
    <aside
      className={`ed-rail${compact ? " is-compact" : ""}${paused ? " is-held" : ""}`}
      aria-label="Explore more study features"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocusCapture={() => setPaused(true)}
      onBlurCapture={() => setPaused(false)}
    >
      {/* Unified Header with Inline Stepper & Minimize */}
      <div className="ed-rail-head">
        <div className="ed-head-titles">
          <span className="ed-eyebrow">Discover</span>
          <h2>{heading}</h2>
        </div>
        <div className="ed-head-right">
          {count > 1 && (
            <div className="ed-stepper" role="group" aria-label="Cycle features">
              <button
                type="button"
                className="ed-step-btn"
                aria-label="Previous feature"
                onClick={() => step(-1)}
              >
                ‹
              </button>
              <span className="ed-count" aria-live="polite">
                <b>{startIndex + 1}</b>/{count}
              </span>
              <button
                type="button"
                className="ed-step-btn"
                aria-label="Next feature"
                onClick={() => step(1)}
              >
                ›
              </button>
            </div>
          )}
          <button
            type="button"
            className="ed-collapse-btn"
            aria-label="Minimize discovery panel"
            title="Minimize"
            onClick={() => toggleCollapsed(true)}
          >
            −
          </button>
        </div>
      </div>

      {/* Unified 3-Card Showcase Stage */}
      <div
        className="ed-unified-grid"
        tabIndex={0}
        role="region"
        aria-label="Finna study features"
        onKeyDown={onKeyDown}
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
      >
        {visibleItems.map((item, idx) => {
          const isPrimary = idx === 0;
          return (
            <Link
              key={item.id}
              to={item.to}
              className={`ed-tile ed-tone-${item.accent}${isPrimary ? " is-primary" : " is-secondary"}`}
            >
              <div className="ed-tile-media">
                <img
                  src={item.image}
                  alt={item.imageAlt}
                  loading={isPrimary ? "eager" : "lazy"}
                  decoding="async"
                  draggable={false}
                  className="ed-photo-img"
                />
                <div className="ed-photo-scrim" aria-hidden="true" />
                <div className="ed-photo-badge">
                  <b>{item.kind}</b>
                  <i aria-hidden="true" />
                  <span>{item.meta}</span>
                </div>
              </div>
              <div className="ed-tile-body">
                <div className="ed-tile-kicker">
                  <b>{item.kind}</b>
                  <span>{item.meta}</span>
                </div>
                <h3>{item.title}</h3>
                <p>{item.body}</p>
                <span className="ed-tile-cta">
                  {item.cta} <span aria-hidden="true">→</span>
                </span>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Clean Single-Row Feature Index Bar */}
      <div className="ed-index-bar" role="tablist" aria-label="Jump to Finna feature">
        {items.map((item) => {
          const isActive = item.id === activeId;
          const isShown = visibleIds.has(item.id);
          return (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => jumpTo(item.id)}
              className={`ed-index-tab ed-tone-${item.accent}${isActive ? " is-active" : isShown ? " is-shown" : ""}`}
            >
              <span className="ed-mini-dot" aria-hidden="true" />
              <span>{item.kind}</span>
            </button>
          );
        })}
      </div>
    </aside>
  );
}
