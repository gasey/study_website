import { useEffect, useId, useState } from "react";
import { AVATAR_COLORS, type AvatarLook } from "../lib/avatar";

export type SpritePose = "idle" | "walk" | "attack" | "cheer";
export type SpriteFacing = "down" | "right" | "left";

export const DEFAULT_HERO_LOOK: AvatarLook = {
  skin: "#D9A47C",
  hair: "Short",
  hairC: "#1D1B18",
  top: "Teal",
  acc: "None",
  bg: "#D3EAEA",
  frame: "None",
};

/** Darken or lighten a #RRGGBB hex color for crisp 16-bit pixel shading. */
function shadeHex(hex: string, delta: number): string {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex || "");
  if (!m) return hex || "#1D1B18";
  const n = parseInt(m[1], 16);
  const clamp = (v: number) => Math.max(0, Math.min(255, v));
  const r = clamp(((n >> 16) & 255) + delta);
  const g = clamp(((n >> 8) & 255) + delta);
  const b = clamp((n & 255) + delta);
  return `#${((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1)}`;
}

function useSpriteFrame(pose: SpritePose, animate: boolean): number {
  const [frame, setFrame] = useState(0);
  useEffect(() => {
    if (!animate) {
      setFrame(0);
      return;
    }
    const ms = pose === "walk" ? 170 : pose === "attack" ? 140 : 420;
    const id = window.setInterval(() => setFrame((f) => (f + 1) % 4), ms);
    return () => window.clearInterval(id);
  }, [pose, animate]);
  return frame;
}

/** 24×24 pixel-art RPG character sprite inspired by classic 16-bit RPG walk sheets. */
function PixelHeroBody({
  look,
  pose = "idle",
  facing = "down",
  frame = 0,
  fullBody = true,
}: {
  look: AvatarLook;
  pose?: SpritePose;
  facing?: SpriteFacing;
  frame?: number;
  fullBody?: boolean;
}) {
  const skin = look.skin || "#D9A47C";
  const skinShade = shadeHex(skin, -26);
  const hair = look.hairC || "#1D1B18";
  const hairHi = shadeHex(hair, 32);
  const top = AVATAR_COLORS[look.top] || "#C0462C";
  const topShade = shadeHex(top, -34);
  const topHi = shadeHex(top, 26);
  const outline = "#18181B";
  const pants = "#26334D";
  const boots = "#3F2A1D";

  const isWalk = pose === "walk";
  const isAttack = pose === "attack";
  const isCheer = pose === "cheer";
  const step = frame % 4; // 0: neutral, 1: left step, 2: neutral, 3: right step
  const bobY =
    isWalk
      ? step === 1 || step === 3
        ? -1
        : 0
      : isCheer
        ? step % 2 === 0
          ? -1
          : 0
        : step >= 2
          ? 0.5
          : 0;
  const lungeX = isAttack && step % 2 === 1 ? (facing === "left" ? -1.5 : 1.5) : 0;
  const eyeShift = facing === "right" ? 1 : facing === "left" ? -1 : 0;
  const blinking = pose === "idle" && step === 3;

  // Leg offsets for 4-frame RPG walk cycle
  const leftLegY = isWalk && step === 1 ? -1 : 0;
  const rightLegY = isWalk && step === 3 ? -1 : 0;
  const leftArmY = isCheer ? -4 : isWalk && step === 3 ? -1 : 0;
  const rightArmY = isCheer ? -4 : isAttack ? -2 : isWalk && step === 1 ? -1 : 0;

  return (
    <g
      shapeRendering="crispEdges"
      transform={`translate(${lungeX}, ${bobY})`}
    >
      {/* Ground drop shadow */}
      {fullBody && (
        <rect
          x="7"
          y="21"
          width="10"
          height="2"
          fill="rgba(15, 23, 42, 0.28)"
          transform={`translate(${-lungeX}, ${-bobY})`}
        />
      )}

      {/* Long hair back layer behind torso */}
      {look.hair === "Long" && (
        <>
          <rect x="6" y="7" width="12" height="10" fill={outline} />
          <rect x="7" y="8" width="10" height="8" fill={hair} />
        </>
      )}

      {/* Legs & Boots (full-body sprite mode) */}
      {fullBody && (
        <>
          {/* Left leg */}
          <g transform={`translate(0, ${leftLegY})`}>
            <rect x="8" y="17" width="3" height="4" fill={outline} />
            <rect x="9" y="17" width="2" height="2" fill={pants} />
            <rect x="8" y="19" width="3" height="2" fill={boots} />
          </g>
          {/* Right leg */}
          <g transform={`translate(0, ${rightLegY})`}>
            <rect x="13" y="17" width="3" height="4" fill={outline} />
            <rect x="13" y="17" width="2" height="2" fill={pants} />
            <rect x="13" y="19" width="3" height="2" fill={boots} />
          </g>
        </>
      )}

      {/* Torso / RPG Tunic */}
      <rect x="7" y="12" width="10" height={fullBody ? 6 : 11} fill={outline} />
      <rect x="8" y="13" width="8" height={fullBody ? 4 : 9} fill={top} />
      <rect x="8" y="13" width="8" height="1" fill={topHi} />
      <rect x="8" y="16" width="8" height="1" fill={topShade} />
      {/* RPG belt & gold buckle */}
      <rect x="8" y="16" width="8" height="1" fill="#292524" />
      <rect x="11" y="16" width="2" height="1" fill="#FBBF24" />
      {/* Collar V-neck */}
      <rect x="11" y="13" width="2" height="1" fill={skinShade} />

      {/* Left Arm */}
      <g transform={`translate(0, ${leftArmY})`}>
        <rect x="5" y="13" width="3" height="4" fill={outline} />
        <rect x="6" y="13" width="1" height="2" fill={topShade} />
        <rect x="6" y="15" width="1" height="1" fill={skin} />
      </g>

      {/* Right Arm (+ gleaming RPG blade/spark in attack pose) */}
      <g transform={`translate(0, ${rightArmY})`}>
        <rect x="16" y="13" width="3" height="4" fill={outline} />
        <rect x="17" y="13" width="1" height="2" fill={topShade} />
        <rect x="17" y="15" width="1" height="1" fill={skin} />
        {isAttack && (
          <g>
            <rect x="19" y="13" width="1" height="3" fill="#B45309" />
            <rect x="20" y="10" width="1" height="5" fill="#E2E8F0" />
            <rect x="21" y="9" width="1" height="4" fill="#38BDF8" />
            <rect x="22" y="8" width="1" height="2" fill="#FEF08A" />
          </g>
        )}
      </g>

      {/* Head Outline & Face */}
      <rect x="6" y="4" width="12" height="9" fill={outline} />
      <rect x="7" y="5" width="10" height="7" fill={skin} />
      <rect x="7" y="11" width="10" height="1" fill={skinShade} />
      {/* Rosy pixel cheeks */}
      <rect x="8" y="9" width="1" height="1" fill="#F472B6" opacity="0.55" />
      <rect x="15" y="9" width="1" height="1" fill="#F472B6" opacity="0.55" />

      {/* Eyes (blink on idle frame 3, shift when facing left/right) */}
      {blinking ? (
        <>
          <rect x={9 + eyeShift} y="9" width="2" height="1" fill={outline} />
          <rect x={13 + eyeShift} y="9" width="2" height="1" fill={outline} />
        </>
      ) : (
        <>
          <rect x={9 + eyeShift} y="8" width="2" height="2" fill={outline} />
          <rect x={9 + eyeShift} y="8" width="1" height="1" fill="#FFFFFF" />
          <rect x={13 + eyeShift} y="8" width="2" height="2" fill={outline} />
          <rect x={13 + eyeShift} y="8" width="1" height="1" fill="#FFFFFF" />
        </>
      )}

      {/* Pixel smile */}
      <rect x={11 + eyeShift} y="10" width="2" height="1" fill={isCheer ? "#991B1B" : skinShade} />

      {/* Hair Styles */}
      {look.hair === "Short" && (
        <>
          <rect x="6" y="3" width="12" height="3" fill={outline} />
          <rect x="7" y="4" width="10" height="2" fill={hair} />
          <rect x="8" y="3" width="3" height="1" fill={hair} />
          <rect x="12" y="3" width="3" height="1" fill={hairHi} />
          <rect x="7" y="6" width="1" height="2" fill={hair} />
          <rect x="16" y="6" width="1" height="2" fill={hair} />
        </>
      )}
      {look.hair === "Bun" && (
        <>
          <rect x="9" y="1" width="6" height="3" fill={outline} />
          <rect x="10" y="2" width="4" height="2" fill={hair} />
          <rect x="11" y="2" width="2" height="1" fill={hairHi} />
          <rect x="6" y="3" width="12" height="3" fill={outline} />
          <rect x="7" y="4" width="10" height="2" fill={hair} />
          <rect x="7" y="6" width="2" height="1" fill={hair} />
          <rect x="15" y="6" width="2" height="1" fill={hair} />
        </>
      )}
      {look.hair === "Long" && (
        <>
          <rect x="6" y="3" width="12" height="3" fill={outline} />
          <rect x="7" y="4" width="10" height="2" fill={hair} />
          <rect x="9" y="4" width="4" height="1" fill={hairHi} />
          <rect x="6" y="6" width="2" height="9" fill={hair} />
          <rect x="16" y="6" width="2" height="9" fill={hair} />
        </>
      )}
      {look.hair === "Side part" && (
        <>
          <rect x="6" y="3" width="12" height="3" fill={outline} />
          <rect x="7" y="4" width="10" height="2" fill={hair} />
          <rect x="7" y="6" width="4" height="1" fill={hair} />
          <rect x="7" y="7" width="2" height="1" fill={hair} />
          <rect x="11" y="4" width="4" height="1" fill={hairHi} />
        </>
      )}
      {look.hair === "Buzz" && (
        <>
          <rect x="7" y="4" width="10" height="2" fill={hair} />
          <rect x="9" y="4" width="3" height="1" fill={hairHi} />
        </>
      )}

      {/* Accessories */}
      {look.acc === "Glasses" && (
        <>
          <rect x={8 + eyeShift} y="7" width="4" height="3" fill="none" stroke="#18181B" strokeWidth="0.9" />
          <rect x={12 + eyeShift} y="7" width="4" height="3" fill="none" stroke="#18181B" strokeWidth="0.9" />
          <rect x={9 + eyeShift} y="8" width="1" height="1" fill="#BAE6FD" opacity="0.7" />
          <rect x={13 + eyeShift} y="8" width="1" height="1" fill="#BAE6FD" opacity="0.7" />
        </>
      )}
      {look.acc === "Headphones" && (
        <>
          <rect x="6" y="2" width="12" height="1" fill="#18181B" />
          <rect x="5" y="3" width="1" height="4" fill="#18181B" />
          <rect x="18" y="3" width="1" height="4" fill="#18181B" />
          <rect x="4" y="6" width="2" height="4" fill="#DC2626" />
          <rect x="18" y="6" width="2" height="4" fill="#DC2626" />
          <rect x="5" y="7" width="1" height="2" fill="#FCA5A5" />
          <rect x="18" y="7" width="1" height="2" fill="#FCA5A5" />
        </>
      )}

      {/* Victory sparkle */}
      {isCheer && (
        <>
          <rect x="3" y="4" width="2" height="2" fill="#FDE047" />
          <rect x="19" y="3" width="2" height="2" fill="#FDE047" />
        </>
      )}
    </g>
  );
}

/** Crisp 16-bit Pixel RPG Avatar — renders either as a circular profile medallion (`badge`)
 *  or an animated full-body walking/battling RPG sprite (`sprite`). */
export default function AvatarArt({
  look,
  size = 36,
  label = "Avatar",
  variant = "badge",
  pose = "idle",
  facing = "down",
  animate = false,
}: {
  look: AvatarLook;
  size?: number;
  label?: string;
  variant?: "badge" | "sprite";
  pose?: SpritePose;
  facing?: SpriteFacing;
  animate?: boolean;
}) {
  const clip = "avatar-" + useId().replace(/:/g, "");
  const frame = useSpriteFrame(pose, animate);
  const c = look;

  if (variant === "sprite") {
    return (
      <svg
        role="img"
        aria-label={label}
        viewBox="0 0 24 24"
        width={size}
        height={size}
        className="shrink-0"
        style={{ display: "block", imageRendering: "pixelated" }}
      >
        <PixelHeroBody
          look={c}
          pose={pose}
          facing={facing}
          frame={frame}
          fullBody
        />
      </svg>
    );
  }

  return (
    <svg
      role="img"
      aria-label={label}
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className="shrink-0"
      style={{ display: "block", imageRendering: "pixelated" }}
    >
      <defs>
        <clipPath id={clip}>
          <circle cx="12" cy="12" r="10.8" />
        </clipPath>
      </defs>
      <circle cx="12" cy="12" r="11.4" fill={c.bg} />
      {/* Subtle 16-bit pixel sky highlight */}
      <g clipPath={"url(#" + clip + ")"} shapeRendering="crispEdges">
        <rect x="2" y="2" width="20" height="4" fill="#FFFFFF" opacity="0.22" />
        <g transform="translate(0, 1.5)">
          <PixelHeroBody
            look={c}
            pose={pose}
            facing={facing}
            frame={frame}
            fullBody={false}
          />
        </g>
      </g>
      {c.frame === "Orbit" && (
        <g fill="none" stroke="#5262AD">
          <circle cx="12" cy="12" r="11.2" strokeWidth="0.6" strokeDasharray="2 1.4" />
          <rect x="2" y="6" width="1.6" height="1.6" fill="#5262AD" stroke="#FFF" strokeWidth="0.3" />
          <rect x="20" y="16" width="1.6" height="1.6" fill="#FBBF24" stroke="#FFF" strokeWidth="0.3" />
        </g>
      )}
      {c.frame !== "None" && c.frame !== "Orbit" && (
        <circle
          cx="12"
          cy="12"
          r="11.2"
          fill="none"
          stroke={AVATAR_COLORS[c.frame] || "#1D1B18"}
          strokeWidth="1.2"
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

/** Backwards-compatible export for any preview using AvatarFace directly. */
export function AvatarFace({ look }: { look: AvatarLook }) {
  return (
    <g transform="scale(5)">
      <PixelHeroBody look={look} fullBody={false} />
    </g>
  );
}

/** 16-bit Pixel RPG Guardian & Boss Sprite for Finna Quest battle arenas. */
export function PixelGuardianSprite({
  realmId,
  isBoss = false,
  isFinalBoss = false,
  accent = "#0F766E",
  size = 76,
}: {
  realmId: string;
  isBoss?: boolean;
  isFinalBoss?: boolean;
  accent?: string;
  size?: number;
}) {
  const frame = useSpriteFrame("idle", true);
  const bobY = frame % 2 === 0 ? 0 : -1;
  const dark = shadeHex(accent, -45);
  const hi = shadeHex(accent, 40);

  return (
    <svg
      role="img"
      aria-label={isFinalBoss ? "Summit Sovereign Boss" : isBoss ? "Realm Boss" : "Realm Guardian"}
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className="shrink-0"
      style={{ display: "block", imageRendering: "pixelated" }}
    >
      <g shapeRendering="crispEdges">
        <rect x="5" y="21" width="14" height="2" fill="rgba(0,0,0,0.35)" />
        <g transform={`translate(0, ${bobY})`}>
          {isFinalBoss ? (
            /* Final Boss: Crowned Summit Sovereign */
            <>
              <rect x="7" y="1" width="2" height="3" fill="#FBBF24" />
              <rect x="11" y="0" width="2" height="4" fill="#FDE047" />
              <rect x="15" y="1" width="2" height="3" fill="#FBBF24" />
              <rect x="7" y="3" width="10" height="2" fill="#D97706" />
              <rect x="5" y="5" width="14" height="15" fill="#18181B" />
              <rect x="6" y="6" width="12" height="6" fill="#4C1D95" />
              <rect x="8" y="8" width="2" height="2" fill="#FDE047" />
              <rect x="14" y="8" width="2" height="2" fill="#FDE047" />
              <rect x="4" y="12" width="16" height="8" fill="#581C87" />
              <rect x="7" y="12" width="10" height="7" fill="#7C3AED" />
              <rect x="10" y="13" width="4" height="5" fill="#F59E0B" />
            </>
          ) : isBoss ? (
            /* Act Boss: 16-bit Pixel Dragon */
            <>
              <rect x="2" y="7" width="4" height="6" fill={dark} />
              <rect x="18" y="7" width="4" height="6" fill={dark} />
              <rect x="3" y="8" width="2" height="4" fill={hi} />
              <rect x="19" y="8" width="2" height="4" fill={hi} />
              <rect x="6" y="3" width="2" height="3" fill="#FDE047" />
              <rect x="16" y="3" width="2" height="3" fill="#FDE047" />
              <rect x="6" y="5" width="12" height="14" fill="#18181B" />
              <rect x="7" y="6" width="10" height="12" fill={accent} />
              <rect x="9" y="11" width="6" height="7" fill="#FDE68A" />
              <rect x="8" y="8" width="2" height="2" fill="#EF4444" />
              <rect x="14" y="8" width="2" height="2" fill="#EF4444" />
              <rect x="8" y="8" width="1" height="1" fill="#FEF08A" />
              <rect x="14" y="8" width="1" height="1" fill="#FEF08A" />
            </>
          ) : realmId === "computer" ? (
            /* Computer Realm: Pixel Cyber Bot */
            <>
              <rect x="11" y="2" width="2" height="3" fill="#38BDF8" />
              <rect x="6" y="5" width="12" height="14" fill="#18181B" />
              <rect x="7" y="6" width="10" height="7" fill="#334155" />
              <rect x="8" y="7" width="8" height="4" fill="#0F172A" />
              <rect x="9" y="8" width="2" height="2" fill="#38BDF8" />
              <rect x="13" y="8" width="2" height="2" fill="#38BDF8" />
              <rect x="7" y="13" width="10" height="5" fill={accent} />
              <rect x="9" y="15" width="6" height="2" fill="#BAE6FD" />
            </>
          ) : (
            /* Realm Guardian: Cute Armored Pixel Golem / Knight */
            <>
              <rect x="7" y="4" width="10" height="15" fill="#18181B" />
              <rect x="8" y="5" width="8" height="6" fill={accent} />
              <rect x="9" y="5" width="6" height="1" fill={hi} />
              <rect x="9" y="7" width="2" height="2" fill="#FEF08A" />
              <rect x="13" y="7" width="2" height="2" fill="#FEF08A" />
              <rect x="6" y="11" width="12" height="6" fill={dark} />
              <rect x="8" y="12" width="8" height="5" fill={accent} />
              <rect x="10" y="13" width="4" height="3" fill={hi} />
              <rect x="8" y="18" width="3" height="2" fill="#18181B" />
              <rect x="13" y="18" width="3" height="2" fill="#18181B" />
            </>
          )}
        </g>
      </g>
    </svg>
  );
}
