import { useEffect, useState } from "react";

/**
 * Interactive Moonlit Forest & Campfire Medallion (inspired by xavier290/KKzREqy).
 * Clicking toggles the campfire between warm crackling flames (active focus)
 * and gentle rising smoke curls (resting/quiet mode).
 */
export function DeskForestPorthole({
  lit,
  onToggle,
  size = 196,
}: {
  lit: boolean;
  onToggle: () => void;
  size?: number;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={lit}
      aria-label={lit ? "Extinguish study campfire" : "Light study campfire"}
      title={lit ? "Click to dim campfire into calm smoke" : "Click to light the study campfire"}
      className={`dfp-porthole${lit ? " is-lit" : " is-smoke"}`}
      style={{ width: size, height: size }}
    >
      {/* Night sky & twinkling stars */}
      <span className="dfp-star dfp-star-1" aria-hidden="true" />
      <span className="dfp-star dfp-star-2" aria-hidden="true" />
      <span className="dfp-star dfp-star-3" aria-hidden="true" />
      <span className="dfp-star dfp-star-4" aria-hidden="true" />

      {/* Glowing cratered moon */}
      <span className="dfp-moon" aria-hidden="true">
        <i className="dfp-crater dfp-c1" />
        <i className="dfp-crater dfp-c2" />
        <i className="dfp-crater dfp-c3" />
      </span>

      {/* Layered pine forest + perched night owl + crossed wood logs (crisp self-contained SVG) */}
      <svg
        viewBox="0 0 200 200"
        className="dfp-svg"
        aria-hidden="true"
      >
        {/* Distant misty forest hills */}
        <path
          d="M-10 148 Q55 122 118 142 T210 138 L210 210 L-10 210 Z"
          fill="#0B2219"
        />
        {/* Pine trees silhouette */}
        <g fill="#061910">
          <polygon points="36,68 18,128 54,128" />
          <polygon points="36,88 14,142 58,142" />
          <rect x="33" y="138" width="6" height="16" fill="#23150B" />

          <polygon points="164,54 144,118 184,118" />
          <polygon points="164,78 139,136 189,136" />
          <rect x="161" y="134" width="6" height="18" fill="#23150B" />

          <polygon points="132,84 117,132 147,132" fill="#092115" />
          <polygon points="74,90 61,134 87,134" fill="#092115" />
        </g>

        {/* Ground mound */}
        <ellipse cx="106" cy="176" rx="116" ry="44" fill="#1E170A" />
        <ellipse cx="106" cy="184" rx="108" ry="38" fill="#161006" />

        {/* Cozy perched night owl on left branch */}
        <g transform="translate(8, 2)">
          <rect x="-4" y="128" width="54" height="6" rx="3" fill="#2A1C0E" />
          {/* Owl body & wings */}
          <ellipse cx="32" cy="112" rx="13" ry="17" fill="#5C3D18" />
          <ellipse cx="21" cy="114" rx="4.5" ry="11" fill="#442B0F" />
          <ellipse cx="43" cy="114" rx="4.5" ry="11" fill="#442B0F" />
          <ellipse cx="32" cy="116" rx="8" ry="10" fill="#785224" opacity="0.65" />
          {/* Owl eyes */}
          <circle cx="27" cy="105" r="4.2" fill="#D99B26" />
          <circle cx="37" cy="105" r="4.2" fill="#D99B26" />
          <circle cx="27" cy="105" r="2" fill="#0F172A" />
          <circle cx="37" cy="105" r="2" fill="#0F172A" />
          <circle cx="26.2" cy="104.2" r="0.8" fill="#FFFBEB" />
          <circle cx="36.2" cy="104.2" r="0.8" fill="#FFFBEB" />
          {/* Beak & feet */}
          <polygon points="30,108 34,108 32,112" fill="#F59E0B" />
          <rect x="27" y="126" width="3.5" height="3" rx="1" fill="#D97706" />
          <rect x="33.5" y="126" width="3.5" height="3" rx="1" fill="#D97706" />
        </g>

        {/* Crossed firewood logs for campfire */}
        <g transform="translate(108, 146)">
          <rect x="-24" y="8" width="48" height="9" rx="4.5" fill="#5A361E" transform="rotate(-14 0 12)" />
          <rect x="-24" y="8" width="48" height="9" rx="4.5" fill="#714426" transform="rotate(14 0 12)" />
          <rect x="-20" y="12" width="40" height="7" rx="3.5" fill="#452714" />
        </g>
      </svg>

      {/* Crackling campfire flames + rising embers (when lit) */}
      <div className="dfp-fire" aria-hidden="true">
        <span className="dfp-glow" />
        <div className="dfp-flame-wrap">
          <span className="dfp-flame dfp-f-red" />
          <span className="dfp-flame dfp-f-orange" />
          <span className="dfp-flame dfp-f-gold" />
          <span className="dfp-flame dfp-f-white" />
        </div>
        <span className="dfp-spark dfp-s1" />
        <span className="dfp-spark dfp-s2" />
      </div>

      {/* Gentle rising smoke curls (when dimmed/paused) */}
      <div className="dfp-smoke" aria-hidden="true">
        <i /><i /><i /><i /><i />
      </div>

      <span className="dfp-status-tag">{lit ? "Fire lit" : "Resting"}</span>
    </button>
  );
}

/**
 * Live Antique Wood & Brass Analog Clock with Animated Turning Gears
 * (inspired by vuild/GXLXjQ "Grandmaster Chime").
 */
export function DeskBrassClock({ size = 84 }: { size?: number }) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(id);
  }, []);

  const secs = now.getSeconds();
  const mins = now.getMinutes();
  const hrs = now.getHours() % 12;

  const secDeg = secs * 6;
  const minDeg = mins * 6 + secs * 0.1;
  const hrDeg = hrs * 30 + mins * 0.5;

  const timeLabel = now.toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div
      className="dbc-clock"
      style={{ width: size, height: size }}
      role="img"
      aria-label={`Current study time ${timeLabel}`}
      title={`Local time · ${timeLabel}`}
    >
      <svg viewBox="0 0 120 120" className="dbc-svg">
        <defs>
          <radialGradient id="dbcBrass" cx="32%" cy="28%" r="72%">
            <stop offset="0%" stopColor="#FFF2B2" />
            <stop offset="35%" stopColor="#E6B95C" />
            <stop offset="75%" stopColor="#9B7228" />
            <stop offset="100%" stopColor="#5D4418" />
          </radialGradient>
          <linearGradient id="dbcFace" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#1E2025" />
            <stop offset="55%" stopColor="#121419" />
            <stop offset="100%" stopColor="#090A0D" />
          </linearGradient>
        </defs>

        {/* Outer walnut & antique brass bezel */}
        <circle cx="60" cy="60" r="57" fill="#5A3927" stroke="url(#dbcBrass)" strokeWidth="4" />
        <circle cx="60" cy="60" r="50" fill="url(#dbcFace)" stroke="#D9B166" strokeWidth="1.5" />

        {/* Subtle turning brass clockwork gears behind hands */}
        <g className="dbc-gear-lg" opacity="0.22">
          <circle cx="48" cy="66" r="16" fill="none" stroke="#E6B95C" strokeWidth="3.5" strokeDasharray="4 3" />
          <circle cx="48" cy="66" r="5" fill="#E6B95C" />
        </g>
        <g className="dbc-gear-sm" opacity="0.22">
          <circle cx="72" cy="54" r="10" fill="none" stroke="#E6B95C" strokeWidth="3" strokeDasharray="3.2 2.5" />
          <circle cx="72" cy="54" r="3" fill="#E6B95C" />
        </g>

        {/* Hour tick marks & cardinal brass numerals */}
        {Array.from({ length: 12 }, (_, i) => {
          const angle = (i * 30 * Math.PI) / 180;
          const isQuarter = i % 3 === 0;
          const r1 = isQuarter ? 41 : 43;
          const r2 = 47;
          return (
            <line
              key={i}
              x1={60 + Math.sin(angle) * r1}
              y1={60 - Math.cos(angle) * r1}
              x2={60 + Math.sin(angle) * r2}
              y2={60 - Math.cos(angle) * r2}
              stroke={isQuarter ? "#F8D77E" : "#A6894C"}
              strokeWidth={isQuarter ? 2.2 : 1.1}
              strokeLinecap="round"
            />
          );
        })}
        <text x="60" y="29" textAnchor="middle" fill="#F1C978" fontSize="9.5" fontWeight="700" fontFamily="serif">12</text>
        <text x="93" y="63.5" textAnchor="middle" fill="#F1C978" fontSize="9.5" fontWeight="700" fontFamily="serif">3</text>
        <text x="60" y="98" textAnchor="middle" fill="#F1C978" fontSize="9.5" fontWeight="700" fontFamily="serif">6</text>
        <text x="27" y="63.5" textAnchor="middle" fill="#F1C978" fontSize="9.5" fontWeight="700" fontFamily="serif">9</text>

        {/* Live Hour, Minute & Second hands */}
        <line
          x1="60"
          y1="60"
          x2="60"
          y2="34"
          stroke="url(#dbcBrass)"
          strokeWidth="3.2"
          strokeLinecap="round"
          transform={`rotate(${hrDeg} 60 60)`}
        />
        <line
          x1="60"
          y1="60"
          x2="60"
          y2="23"
          stroke="#F8E2A2"
          strokeWidth="2.1"
          strokeLinecap="round"
          transform={`rotate(${minDeg} 60 60)`}
        />
        <line
          x1="60"
          y1="68"
          x2="60"
          y2="20"
          stroke="#FFC83D"
          strokeWidth="1.1"
          strokeLinecap="round"
          transform={`rotate(${secDeg} 60 60)`}
        />
        <circle cx="60" cy="60" r="3.4" fill="url(#dbcBrass)" />
      </svg>
    </div>
  );
}
