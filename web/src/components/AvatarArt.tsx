import { useId } from "react";
import { AVATAR_COLORS, type AvatarLook } from "../lib/avatar";
/** Original v3 vector geometry, with instance-unique clipping. No external media. */
export default function AvatarArt({
  look,
  size = 36,
  label = "Avatar",
}: {
  look: AvatarLook;
  size?: number;
  label?: string;
}) {
  const clip = "avatar-" + useId().replace(/:/g, "");
  const c = look;
  return (
    <svg
      role="img"
      aria-label={label}
      viewBox="0 0 120 120"
      width={size}
      height={size}
      className="shrink-0"
      style={{ display: "block" }}
    >
      <defs>
        <clipPath id={clip}>
          <circle cx="60" cy="60" r="55" />
        </clipPath>
      </defs>
      <circle cx="60" cy="60" r="58" fill={c.bg} />
      <g clipPath={"url(#" + clip + ")"}>
        <rect
          x="30"
          y="80"
          width="60"
          height="50"
          rx="26"
          fill={AVATAR_COLORS[c.top] || "#C0462C"}
        />
        <AvatarFace look={c} />
      </g>
      {c.frame !== "None" && (
        <circle
          cx="60"
          cy="60"
          r="57"
          fill="none"
          stroke={AVATAR_COLORS[c.frame] || "#1D1B18"}
          strokeWidth="5"
        />
      )}
    </svg>
  );
}
export function UserAvatar({
  look,
  initials = "S",
  size = 36,
}: {
  look?: AvatarLook | null;
  initials?: string;
  size?: number;
}) {
  return look ? (
    <AvatarArt look={look} size={size} />
  ) : (
    <span
      aria-hidden="true"
      className="inline-flex shrink-0 items-center justify-center rounded-full border border-ink bg-[#F6DDD3] font-mono"
      style={{ width: size, height: size, fontSize: Math.max(10, size * 0.28) }}
    >
      {initials.slice(0, 2).toUpperCase()}
    </span>
  );
}

export function AvatarFace({ look: c }: { look: AvatarLook }) {
  return (
    <>
      <rect x="54" y="70" width="12" height="12" fill={c.skin} />
      <circle cx="60" cy="56" r="23" fill={c.skin} />
      {c.hair === "Short" && (
        <ellipse cx="60" cy="40" rx="26" ry="14" fill={c.hairC} />
      )}
      {c.hair === "Bun" && (
        <>
          <ellipse cx="60" cy="40" rx="26" ry="13" fill={c.hairC} />
          <circle cx="60" cy="22" r="10" fill={c.hairC} />
        </>
      )}
      {c.hair === "Long" && (
        <>
          <ellipse cx="60" cy="40" rx="27" ry="15" fill={c.hairC} />
          <rect x="33" y="40" width="10" height="38" rx="5" fill={c.hairC} />
          <rect x="77" y="40" width="10" height="38" rx="5" fill={c.hairC} />
        </>
      )}
      {c.hair === "Side part" && (
        <>
          <ellipse cx="56" cy="39" rx="27" ry="13" fill={c.hairC} />
          <rect x="34" y="38" width="9" height="18" rx="4" fill={c.hairC} />
        </>
      )}
      {c.hair === "Buzz" && (
        <ellipse cx="60" cy="39" rx="23" ry="9" fill={c.hairC} />
      )}
      <circle cx="52" cy="57" r="2.2" fill="#1D1B18" />
      <circle cx="68" cy="57" r="2.2" fill="#1D1B18" />
      <path
        d="M54 66 Q60 70 66 66"
        fill="none"
        stroke="#1D1B18"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      {c.acc === "Glasses" && (
        <g fill="none" stroke="#1D1B18" strokeWidth="2">
          <circle cx="51" cy="56" r="6.5" />
          <circle cx="69" cy="56" r="6.5" />
          <path d="M57.5 56H62.5" />
        </g>
      )}
      {c.acc === "Headphones" && (
        <>
          <path
            d="M34 56 A26 26 0 0 1 86 56"
            fill="none"
            stroke="#1D1B18"
            strokeWidth="4"
          />
          <rect x="30" y="50" width="9" height="16" rx="4" fill="#C0462C" />
          <rect x="81" y="50" width="9" height="16" rx="4" fill="#C0462C" />
        </>
      )}
    </>
  );
}
