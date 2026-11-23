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
  },
  {
    id: "guides",
    kind: "Guides",
    meta: "Free reading room",
    title: "Edited study concept books",
    body: "Polity Codex, grammar guides, and exam walkthroughs linked straight to bank questions.",
    cta: "Open Guides",
    to: "/guides",
    accent: "teal",
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
  },
  {
    id: "games",
    kind: "Games",
    meta: "Timed drills",
    title: "Fast recall & streak games",
    body: "Warm up with Daily Five and quick-fire rounds that build XP without pressure.",
    cta: "Play Games",
    to: "/games",
    accent: "violet",
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
  },
];

/** Crisp lightweight SVG visual previews for each Finna feature (light + night safe). */
function FeatureArt({ id }: { id: SpotlightItem["id"] }) {
  switch (id) {
    case "stats":
      return (
        <svg viewBox="0 0 220 76" className="ed-art-svg" aria-hidden="true">
          <defs>
            <linearGradient id="ed-g-stats" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#2563EB" stopOpacity="0.22" />
              <stop offset="100%" stopColor="#60A5FA" stopOpacity="0.06" />
            </linearGradient>
          </defs>
          <rect width="220" height="76" rx="10" fill="url(#ed-g-stats)" />
          <line x1="16" y1="58" x2="204" y2="58" stroke="#2563EB" strokeOpacity="0.25" strokeWidth="1" />
          <rect x="26" y="38" width="16" height="20" rx="4" fill="#60A5FA" fillOpacity="0.7" />
          <rect x="52" y="28" width="16" height="30" rx="4" fill="#3B82F6" fillOpacity="0.85" />
          <rect x="78" y="34" width="16" height="24" rx="4" fill="#60A5FA" fillOpacity="0.7" />
          <rect x="104" y="18" width="16" height="40" rx="4" fill="#2563EB" />
          <rect x="130" y="24" width="16" height="34" rx="4" fill="#3B82F6" fillOpacity="0.85" />
          <path d="M34 33 L60 22 L86 28 L112 13 L138 19 L174 11" fill="none" stroke="#1D4ED8" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="174" cy="11" r="4" fill="#2563EB" />
          <rect x="160" y="26" width="44" height="22" rx="6" fill="#2563EB" fillOpacity="0.16" />
          <text x="182" y="40" textAnchor="middle" fontSize="9.5" fontWeight="800" fill="#1D4ED8">TOP #1</text>
        </svg>
      );
    case "guides":
      return (
        <svg viewBox="0 0 220 76" className="ed-art-svg" aria-hidden="true">
          <defs>
            <linearGradient id="ed-g-guides" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#0A7D8C" stopOpacity="0.24" />
              <stop offset="100%" stopColor="#2DD4BF" stopOpacity="0.06" />
            </linearGradient>
          </defs>
          <rect width="220" height="76" rx="10" fill="url(#ed-g-guides)" />
          {/* Open book spread */}
          <path d="M40 16 C65 12, 92 15, 110 22 L110 62 C92 56, 65 53, 40 57 Z" fill="#FCF9F2" stroke="#0A7D8C" strokeWidth="1.5" />
          <path d="M180 16 C155 12, 128 15, 110 22 L110 62 C128 56, 155 53, 180 57 Z" fill="#F5EFE2" stroke="#0A7D8C" strokeWidth="1.5" />
          <path d="M154 14 L154 33 L160 28 L166 33 L166 14 Z" fill="#F59E0B" />
          <line x1="52" y1="28" x2="96" y2="28" stroke="#0A7D8C" strokeOpacity="0.55" strokeWidth="2.2" strokeLinecap="round" />
          <line x1="52" y1="36" x2="92" y2="36" stroke="#0A7D8C" strokeOpacity="0.32" strokeWidth="1.8" strokeLinecap="round" />
          <line x1="52" y1="44" x2="86" y2="44" stroke="#0A7D8C" strokeOpacity="0.32" strokeWidth="1.8" strokeLinecap="round" />
          <line x1="122" y1="34" x2="148" y2="34" stroke="#0A7D8C" strokeOpacity="0.45" strokeWidth="2" strokeLinecap="round" />
          <line x1="122" y1="42" x2="164" y2="42" stroke="#0A7D8C" strokeOpacity="0.3" strokeWidth="1.8" strokeLinecap="round" />
          <line x1="122" y1="49" x2="156" y2="49" stroke="#0A7D8C" strokeOpacity="0.3" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "chronicle":
      return (
        <svg viewBox="0 0 220 76" className="ed-art-svg" aria-hidden="true">
          <defs>
            <linearGradient id="ed-g-chrono" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#C2410C" stopOpacity="0.22" />
              <stop offset="100%" stopColor="#FB923C" stopOpacity="0.06" />
            </linearGradient>
          </defs>
          <rect width="220" height="76" rx="10" fill="url(#ed-g-chrono)" />
          <path d="M22 44 C64 44, 72 26, 110 38 C148 50, 158 24, 198 28" fill="none" stroke="#C2410C" strokeWidth="2.4" strokeLinecap="round" />
          <circle cx="42" cy="42" r="5.5" fill="#C2410C" />
          <circle cx="110" cy="38" r="7" fill="#EA580C" stroke="#FFF7ED" strokeWidth="2" />
          <circle cx="176" cy="29" r="5.5" fill="#C2410C" />
          <text x="42" y="61" textAnchor="middle" fontSize="9.5" fontWeight="800" fill="#9A3412">1857</text>
          <text x="110" y="22" textAnchor="middle" fontSize="10" fontWeight="800" fill="#C2410C">1947</text>
          <text x="176" y="48" textAnchor="middle" fontSize="9.5" fontWeight="800" fill="#9A3412">1950</text>
        </svg>
      );
    case "atlas":
      return (
        <svg viewBox="0 0 220 76" className="ed-art-svg" aria-hidden="true">
          <defs>
            <linearGradient id="ed-g-atlas" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#059669" stopOpacity="0.22" />
              <stop offset="100%" stopColor="#34D399" stopOpacity="0.06" />
            </linearGradient>
          </defs>
          <rect width="220" height="76" rx="10" fill="url(#ed-g-atlas)" />
          {/* Topographic contours */}
          <path d="M12 56 Q62 24 112 46 T210 26" fill="none" stroke="#059669" strokeOpacity="0.35" strokeWidth="1.6" />
          <path d="M12 66 Q72 36 122 56 T210 42" fill="none" stroke="#059669" strokeOpacity="0.22" strokeWidth="1.4" />
          <circle cx="110" cy="38" r="22" fill="none" stroke="#059669" strokeOpacity="0.25" strokeDasharray="4 3" />
          {/* Map pin */}
          <path d="M110 15 C101 15 95 21 95 29 C95 40 110 53 110 53 C110 53 125 40 125 29 C125 21 119 15 110 15 Z" fill="#059669" />
          <circle cx="110" cy="29" r="5" fill="#ECFDF5" />
          <circle cx="48" cy="34" r="3.5" fill="#10B981" />
          <circle cx="174" cy="32" r="3.5" fill="#10B981" />
        </svg>
      );
    case "games":
      return (
        <svg viewBox="0 0 220 76" className="ed-art-svg" aria-hidden="true">
          <defs>
            <linearGradient id="ed-g-games" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#7C3AED" stopOpacity="0.22" />
              <stop offset="100%" stopColor="#A78BFA" stopOpacity="0.06" />
            </linearGradient>
          </defs>
          <rect width="220" height="76" rx="10" fill="url(#ed-g-games)" />
          <circle cx="68" cy="38" r="22" fill="#7C3AED" fillOpacity="0.16" stroke="#7C3AED" strokeWidth="2.2" />
          <polygon points="63,29 79,38 63,47" fill="#7C3AED" />
          <rect x="108" y="20" width="90" height="14" rx="7" fill="#7C3AED" fillOpacity="0.18" />
          <rect x="108" y="20" width="64" height="14" rx="7" fill="#7C3AED" />
          <rect x="108" y="42" width="76" height="12" rx="6" fill="#A78BFA" fillOpacity="0.35" />
          <text x="116" y="30" fontSize="8.5" fontWeight="800" fill="#FFFFFF">DAILY 5 · XP</text>
        </svg>
      );
    case "calendar":
      return (
        <svg viewBox="0 0 220 76" className="ed-art-svg" aria-hidden="true">
          <defs>
            <linearGradient id="ed-g-cal" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#B45309" stopOpacity="0.22" />
              <stop offset="100%" stopColor="#FBBF24" stopOpacity="0.06" />
            </linearGradient>
          </defs>
          <rect width="220" height="76" rx="10" fill="url(#ed-g-cal)" />
          <rect x="44" y="13" width="132" height="52" rx="9" fill="#FCF9F2" stroke="#D97706" strokeWidth="1.5" />
          <rect x="44" y="13" width="132" height="15" rx="8" fill="#D97706" />
          <circle cx="66" cy="39" r="3.5" fill="#D97706" fillOpacity="0.35" />
          <circle cx="88" cy="39" r="3.5" fill="#10B981" />
          <circle cx="110" cy="39" r="5" fill="#D97706" />
          <circle cx="132" cy="39" r="3.5" fill="#D97706" fillOpacity="0.35" />
          <circle cx="154" cy="39" r="3.5" fill="#10B981" />
          <circle cx="66" cy="54" r="3.5" fill="#D97706" fillOpacity="0.25" />
          <circle cx="88" cy="54" r="3.5" fill="#D97706" fillOpacity="0.25" />
          <circle cx="110" cy="54" r="3.5" fill="#10B981" />
          <circle cx="132" cy="54" r="3.5" fill="#D97706" fillOpacity="0.25" />
          <circle cx="154" cy="54" r="3.5" fill="#D97706" fillOpacity="0.25" />
        </svg>
      );
  }
}

const STACK_POSES = [
  { y: 0, s: 1, r: 0, o: 1 },
  { y: -11, s: 0.955, r: -1.9, o: 1 },
  { y: -20, s: 0.912, r: 1.5, o: 0.94 },
  { y: -28, s: 0.875, r: -1.1, o: 0 },
];

const DRAG_THRESHOLD = 82;
const DRAG_START_PX = 6;

/**
 * Outer-Margin Feature Spotlight Deck with Custom Illustrated Visual Art.
 * Inspired by ShikshaCom draggable noticeboard stack, Nidal95/RNNgWNM card
 * carousel, and hexagoncircle/wvmjomb calm visual reel.
 * Sits OUTSIDE the 1320px homepage margin on desktop so Calendar stays at top.
 */
export default function ExploreDeckRail({
  exclude = [],
  interval = 6200,
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

  const [order, setOrder] = useState<string[]>(() => items.map((i) => i.id));
  const [exiting, setExiting] = useState<{ id: string; from: number } | null>(
    null,
  );
  const [drag, setDrag] = useState<{ x: number; y: number } | null>(null);
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

  function toggleCollapsed(next: boolean) {
    setCollapsed(next);
    try {
      sessionStorage.setItem("finna_ed_collapsed", next ? "1" : "0");
    } catch {
      /* ignore */
    }
  }

  const ptrRef = useRef<{ x: number; y: number; moved: boolean } | null>(null);
  const exitTimerRef = useRef<number | null>(null);
  const orderRef = useRef(order);
  orderRef.current = order;

  const findItem = useCallback(
    (id: string) => items.find((i) => i.id === id),
    [items],
  );

  const step = useCallback(
    (dir: 1 | -1 = 1, fromX = 0) => {
      if (count < 2) return;
      const leaving = dir >= 0 ? orderRef.current[0] : null;
      setOrder((prev) => {
        const next = prev.slice();
        if (dir >= 0) {
          const head = next.shift();
          if (head) next.push(head);
        } else {
          const tail = next.pop();
          if (tail) next.unshift(tail);
        }
        return next;
      });
      setExiting(leaving ? { id: leaving, from: fromX } : null);
      setDrag(null);
    },
    [count],
  );

  useEffect(() => {
    if (!exiting) return;
    if (exitTimerRef.current !== null) window.clearTimeout(exitTimerRef.current);
    exitTimerRef.current = window.setTimeout(() => setExiting(null), 420);
    return () => {
      if (exitTimerRef.current !== null)
        window.clearTimeout(exitTimerRef.current);
    };
  }, [exiting]);

  const bringToFront = useCallback((id: string) => {
    setOrder((prev) => {
      const idx = prev.indexOf(id);
      if (idx <= 0) return prev;
      return prev.slice(idx).concat(prev.slice(0, idx));
    });
    setExiting(null);
    setDrag(null);
  }, []);

  useEffect(() => {
    if (
      paused ||
      drag ||
      count < 2 ||
      (typeof window !== "undefined" &&
        window.matchMedia?.("(prefers-reduced-motion: reduce)").matches)
    ) {
      return;
    }
    const t = window.setTimeout(() => step(1, 0), interval);
    return () => window.clearTimeout(t);
  }, [order, paused, drag, interval, count, step]);

  useEffect(() => {
    const onVis = () => setPaused(document.hidden);
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, []);

  function onPointerDown(e: React.PointerEvent<HTMLElement>) {
    if (count < 2 || e.button > 0) return;
    if ((e.target as HTMLElement)?.closest("a,button")) return;
    ptrRef.current = { x: e.clientX, y: e.clientY, moved: false };
    e.currentTarget.setPointerCapture?.(e.pointerId);
  }

  function onPointerMove(e: React.PointerEvent<HTMLElement>) {
    const p = ptrRef.current;
    if (!p) return;
    const dx = e.clientX - p.x;
    const dy = e.clientY - p.y;
    if (!p.moved && Math.abs(dx) < DRAG_START_PX && Math.abs(dy) < DRAG_START_PX)
      return;
    p.moved = true;
    setDrag({ x: dx, y: dy });
  }

  function onPointerUp(e: React.PointerEvent<HTMLElement>) {
    const p = ptrRef.current;
    ptrRef.current = null;
    try {
      e.currentTarget.releasePointerCapture?.(e.pointerId);
    } catch {
      /* ignore */
    }
    if (!p || !p.moved) {
      setDrag(null);
      return;
    }
    const dx = e.clientX - p.x;
    if (Math.abs(dx) > DRAG_THRESHOLD) step(1, dx);
    else setDrag(null);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (e.key === "ArrowRight") {
      e.preventDefault();
      step(1, 0);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      step(-1, 0);
    }
  }

  const activeId = order[0];
  const activeIndex = Math.max(
    0,
    items.findIndex((i) => i.id === activeId),
  );

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
          <span className="ed-reopen-sub">Stats · Guides · Atlas</span>
        </button>
      </aside>
    );
  }

  return (
    <aside
      className={`ed-rail${compact ? " is-compact" : ""}${paused ? " is-held" : ""}`}
      aria-label="Explore more study features"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocusCapture={() => setPaused(true)}
      onBlurCapture={() => setPaused(false)}
    >
      <div className="ed-rail-head">
        <div>
          <span className="ed-eyebrow">Discover</span>
          <h2>{heading}</h2>
        </div>
        <div className="ed-head-right">
          <span className="ed-count">
            <b>{activeIndex + 1}</b> / {count}
          </span>
          <button
            type="button"
            className="ed-collapse-btn"
            aria-label="Minimize discovery deck"
            title="Minimize"
            onClick={() => toggleCollapsed(true)}
          >
            −
          </button>
        </div>
      </div>

      {/* Draggable / auto-turning illustrated feature stack */}
      <div
        className="ed-stack"
        tabIndex={0}
        role="group"
        aria-roledescription="Feature spotlight stack"
        aria-label="Finna study features"
        onKeyDown={onKeyDown}
      >
        {exiting && (
          <ExitingCard item={findItem(exiting.id)} from={exiting.from} />
        )}

        {order.map((id, idx) => {
          const item = findItem(id);
          if (!item || idx > STACK_POSES.length - 1) return null;
          const isFront = idx === 0;
          const pose = STACK_POSES[Math.min(idx, STACK_POSES.length - 1)];
          const style: React.CSSProperties =
            isFront && drag
              ? {
                  transform: `translate(${drag.x}px, ${drag.y * 0.28}px) rotate(${drag.x * 0.045}deg)`,
                  opacity: 1,
                  zIndex: 30,
                }
              : {
                  transform: `translateY(${pose.y}px) scale(${pose.s}) rotate(${pose.r}deg)`,
                  opacity: pose.o,
                  zIndex: 30 - idx,
                };

          return (
            <article
              key={id}
              className={`ed-card ed-tone-${item.accent}${isFront ? " is-front" : ""}${isFront && drag ? " is-dragging" : ""}`}
              style={style}
              aria-hidden={isFront ? undefined : "true"}
              onPointerDown={isFront ? onPointerDown : undefined}
              onPointerMove={isFront ? onPointerMove : undefined}
              onPointerUp={isFront ? onPointerUp : undefined}
              onPointerCancel={isFront ? onPointerUp : undefined}
            >
              <div className="ed-card-kind">
                <b>{item.kind}</b>
                <i aria-hidden="true" />
                <span>{item.meta}</span>
              </div>
              <div className="ed-card-art">
                <FeatureArt id={item.id} />
              </div>
              <h3>{item.title}</h3>
              <p>{item.body}</p>
              <Link
                to={item.to}
                className="ed-card-go"
                tabIndex={isFront ? 0 : -1}
                draggable={false}
              >
                {item.cta} →
              </Link>
            </article>
          );
        })}
      </div>

      {/* Controls & filling progress markers */}
      <div className="ed-controls">
        <div className="ed-nav-group">
          <button
            type="button"
            className="ed-nav-btn"
            aria-label="Previous feature"
            onClick={() => step(-1, 0)}
          >
            ‹
          </button>
          <button
            type="button"
            className="ed-nav-btn"
            aria-label="Next feature"
            onClick={() => step(1, 0)}
          >
            ›
          </button>
        </div>
        <div className="ed-marks">
          {items.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`ed-mark${item.id === activeId ? " is-on" : ""}`}
              style={{ ["--ed-dur" as string]: `${interval}ms` }}
              aria-label={`Show ${item.kind}: ${item.title}`}
              aria-current={item.id === activeId ? "true" : undefined}
              onClick={() => bringToFront(item.id)}
            />
          ))}
        </div>
      </div>

      {/* Calm scrollable feature preview strip (desktop hover / mobile quick tap) */}
      <nav aria-label="Quick feature shortcuts" className="ed-pill-list">
        {items.map((item) => (
          <Link
            key={item.id}
            to={item.to}
            onMouseEnter={() => bringToFront(item.id)}
            className={`ed-mini-pill ed-tone-${item.accent}${item.id === activeId ? " is-active" : ""}`}
          >
            <span className="ed-mini-dot" aria-hidden="true" />
            <span>{item.kind}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
}

function ExitingCard({
  item,
  from,
}: {
  item: SpotlightItem | undefined;
  from: number;
}) {
  const [gone, setGone] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setGone(true));
    return () => cancelAnimationFrame(id);
  }, []);
  if (!item) return null;
  const dir = from >= 0 ? 1 : -1;
  return (
    <article
      className={`ed-card ed-tone-${item.accent}${gone ? " is-gone" : ""}`}
      aria-hidden="true"
      style={{
        zIndex: 40,
        pointerEvents: "none",
        transform: gone
          ? `translate(${dir * 340}px, 24px) rotate(${dir * 13}deg)`
          : `translate(${from}px, 0px) rotate(${from * 0.045}deg)`,
        opacity: gone ? 0 : 1,
      }}
    >
      <div className="ed-card-kind">
        <b>{item.kind}</b>
        <i aria-hidden="true" />
        <span>{item.meta}</span>
      </div>
      <div className="ed-card-art">
        <FeatureArt id={item.id} />
      </div>
      <h3>{item.title}</h3>
      <p>{item.body}</p>
      <span className="ed-card-go">{item.cta} →</span>
    </article>
  );
}
