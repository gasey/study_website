import { AvatarFace } from "./AvatarArt";
import type { AvatarLook } from "../lib/avatar";
import * as React from "react";

export interface SceneMember {
  avatar?: AvatarLook | null;
  ini: string;
  name: string;
  here: boolean;
  body: string;
  skin: string;
  hair: string;
  arm: string;
}

const ACCENT = {
  plum: "#7C3AED",
  blue: "#2563EB",
  teal: "#0A7D8C",
  coral: "#EA580C",
  emerald: "#059669",
  amber: "#D97706",
  rose: "#C2410C",
};

export default function DeskScene({
  active,
  pick,
  members,
  focus,
  pickMember,
  invite,
  personal = false,
}: {
  active: string;
  pick: (key: string) => void;
  members: (SceneMember | null)[];
  focus: string;
  pickMember: (id: string) => void;
  invite: () => void;
  personal?: boolean;
}) {
  const h = (
    tag: string,
    props: Record<string, unknown> | null,
    ...children: React.ReactNode[]
  ) => React.createElement(tag, props, ...children);

  const an = (
    name: string,
    dur: string,
    origin?: string,
    delay?: string,
    timing?: string,
  ) => ({
    animation:
      name +
      " " +
      dur +
      " " +
      (timing || "ease-in-out") +
      " " +
      (delay || "0s") +
      " infinite",
    transformBox: "fill-box",
    transformOrigin: origin || "center",
  });

  const tag = (
    key: string,
    label: string,
    x: number,
    y: number,
    color: string,
    on: boolean,
    pulse: boolean,
  ) => {
    const w = Math.max(72, label.length * 6.8 + 30);
    return h(
      "g",
      { key: "t" + key, className: "desk-svg-tag" + (on ? " is-on" : "") },
      h("rect", {
        x: x - w / 2,
        y: y + 2,
        width: w,
        height: 24,
        rx: 12,
        fill: "rgba(15,23,42,0.14)",
        opacity: on ? 0.28 : 0.12,
      }),
      h("rect", {
        x: x - w / 2,
        y,
        width: w,
        height: 24,
        rx: 12,
        fill: on ? color : "var(--desk-tag-bg, #FFFFFF)",
        stroke: on ? color : "var(--desk-tag-border, rgba(15,23,42,0.16))",
        strokeWidth: on ? 1.5 : 1,
      }),
      pulse && !on
        ? h("circle", {
            cx: x - w / 2 + 12,
            cy: y + 12,
            r: 5,
            fill: color,
            opacity: 0.35,
            "data-anim": 1,
            style: an("ism-pulse", "2.1s"),
          })
        : null,
      h("circle", {
        cx: x - w / 2 + 12,
        cy: y + 12,
        r: 3.8,
        fill: on ? "#FFFFFF" : color,
      }),
      h(
        "text",
        {
          x: x + 6,
          y: y + 15.5,
          textAnchor: "middle",
          fontSize: 11,
          fontWeight: 700,
          fill: on ? "#FFFFFF" : "var(--desk-tag-ink, #0F172A)",
        },
        label,
      ),
    );
  };

  const hot = (key: string, label: string, kids: React.ReactNode[]) =>
    h(
      "g",
      {
        key,
        role: "button",
        tabIndex: 0,
        className: "desk-svg-hot",
        "aria-label": label,
        onKeyDown: (e: React.KeyboardEvent) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            pick(key);
          }
        },
        onClick: () => pick(key),
        style: { cursor: "pointer" },
      },
      ...kids,
    );

  const SEATS = [150, 280, 410, 550, 680, 810];

  const chairs = SEATS.map((cx, i) =>
    h("rect", {
      key: "ch" + i,
      x: cx - 38,
      y: 146,
      width: 76,
      height: 108,
      rx: 16,
      fill: members[i] ? "var(--desk-chair, #334155)" : "var(--desk-chair-empty, rgba(148,163,184,0.12))",
      stroke: members[i] ? "var(--desk-chair-stroke, #1E293B)" : "var(--desk-chair-dash, rgba(100,116,139,0.45))",
      strokeWidth: 1.5,
      strokeDasharray: members[i] ? null : "6 5",
    }),
  );

  const bodies = SEATS.map((cx, i) => {
    const m = members[i];
    if (!m) return null;
    const d = i * 0.65 + "s";
    return h(
      "g",
      {
        key: "p" + i,
        opacity: m.here ? 1 : 0.34,
        onClick: () => pickMember(m.ini),
        style: { cursor: "pointer", transition: "opacity 350ms ease" },
      },
      h(
        "g",
        { "data-anim": 1, style: an("ism-breathe", "4.2s", "center", d) },
        h("rect", {
          x: cx - 33,
          y: 192,
          width: 66,
          height: 74,
          rx: 28,
          fill: m.body,
        }),
        m.avatar
          ? h(
              "g",
              { transform: `translate(${cx - 60} 108)` },
              <AvatarFace look={m.avatar} />,
            )
          : h(
              "g",
              null,
              h("circle", { cx, cy: 164, r: 23, fill: m.skin }),
              h("ellipse", { cx, cy: 150, rx: 24, ry: 12.5, fill: m.hair }),
              i % 2
                ? h("circle", { cx: cx + 18, cy: 144, r: 7.5, fill: m.hair })
                : h("rect", {
                    x: cx - 24,
                    y: 146,
                    width: 7.5,
                    height: 23,
                    rx: 4,
                    fill: m.hair,
                  }),
              h("circle", { cx: cx - 7.5, cy: 167, r: 2, fill: "#1E293B" }),
              h("circle", { cx: cx + 7.5, cy: 167, r: 2, fill: "#1E293B" }),
            ),
      ),
    );
  });

  const arms = SEATS.map((cx, i) => {
    const m = members[i];
    if (!m) return null;
    return h(
      "g",
      {
        key: "a" + i,
        opacity: m.here ? 1 : 0.34,
        onClick: () => pickMember(m.ini),
        style: { cursor: "pointer" },
      },
      h("rect", {
        x: cx - 40,
        y: 237,
        width: 30,
        height: 13,
        rx: 6.5,
        fill: m.arm,
      }),
      h("rect", {
        x: cx + 10,
        y: 237,
        width: 30,
        height: 13,
        rx: 6.5,
        fill: m.arm,
        "data-anim": m.here ? 1 : null,
        style: m.here
          ? an("ism-write", "2.6s", "left center", i * 0.45 + "s")
          : null,
      }),
    );
  });

  const names = SEATS.map((cx, i) => {
    const m = members[i];
    if (!m) {
      if (personal && i > 1) return null;
      return h(
        "g",
        { key: "n" + i, onClick: invite, style: { cursor: "pointer" } },
        tag(
          "inv" + i,
          personal ? "+ Study partner" : "+ Invite",
          cx,
          184,
          ACCENT.teal,
          false,
          i === 1,
        ),
      );
    }
    return h(
      "g",
      {
        key: "n" + i,
        onClick: () => pickMember(m.ini),
        style: { cursor: "pointer" },
      },
      tag(
        "m" + i,
        m.here ? m.name : m.name + " · away",
        cx,
        106,
        m.body,
        focus === m.ini,
        false,
      ),
    );
  });

  return h(
    "svg",
    {
      viewBox: "0 0 960 364",
      width: "100%",
      role: "group",
      "aria-label":
        "Interactive study desk diagram. Use the labelled content tabs below for the same actions.",
      style: { display: "block" },
    },
    h(
      "defs",
      null,
      h(
        "linearGradient",
        { id: "deskWallGrad", x1: "0", y1: "0", x2: "0", y2: "1" },
        h("stop", { offset: "0%", stopColor: "var(--desk-wall-top, #F1F5F9)" }),
        h("stop", { offset: "100%", stopColor: "var(--desk-wall-bot, #E2E8F0)" }),
      ),
      h(
        "linearGradient",
        { id: "deskFloorGrad", x1: "0", y1: "0", x2: "0", y2: "1" },
        h("stop", { offset: "0%", stopColor: "var(--desk-floor-top, #CBD5E1)" }),
        h("stop", { offset: "100%", stopColor: "var(--desk-floor-bot, #E2E8F0)" }),
      ),
      h(
        "radialGradient",
        { id: "deskLampCone", cx: "50%", cy: "0%", r: "85%" },
        h("stop", { offset: "0%", stopColor: "var(--desk-lamp-a, rgba(251,191,36,0.34))" }),
        h("stop", { offset: "60%", stopColor: "var(--desk-lamp-b, rgba(251,191,36,0.10))" }),
        h("stop", { offset: "100%", stopColor: "rgba(251,191,36,0)" }),
      ),
      h(
        "linearGradient",
        { id: "deskWoodTop", x1: "0", y1: "0", x2: "1", y2: "0" },
        h("stop", { offset: "0%", stopColor: "var(--desk-wood-1, #B07D56)" }),
        h("stop", { offset: "50%", stopColor: "var(--desk-wood-2, #C5936B)" }),
        h("stop", { offset: "100%", stopColor: "var(--desk-wood-1, #A6734D)" }),
      ),
      h(
        "linearGradient",
        { id: "deskWindowSky", x1: "0", y1: "0", x2: "0", y2: "1" },
        h("stop", { offset: "0%", stopColor: "var(--desk-sky-top, #BAE6FD)" }),
        h("stop", { offset: "100%", stopColor: "var(--desk-sky-bot, #E0F2FE)" }),
      ),
    ),

    // Studio wall & floor
    h("rect", { x: 0, y: 0, width: 960, height: 304, fill: "url(#deskWallGrad)" }),
    h("rect", { x: 0, y: 304, width: 960, height: 60, fill: "url(#deskFloorGrad)" }),
    h("line", {
      x1: 0,
      y1: 304,
      x2: 960,
      y2: 304,
      stroke: "var(--desk-horizon, rgba(15,23,42,0.14))",
      strokeWidth: 1.5,
    }),

    // Forest & hills window behind center-right (wood frame + pines + moon/clouds)
    h("rect", {
      x: 562,
      y: 22,
      width: 174,
      height: 102,
      rx: 12,
      fill: "url(#deskWindowSky)",
      stroke: "var(--desk-wood-edge, #6B442A)",
      strokeWidth: 4,
    }),
    // Distant hills & forest pines visible through window
    h("path", { d: "M565 110 Q608 82 652 104 T733 98 L733 122 L565 122 Z", fill: "#1B4332", opacity: 0.72 }),
    h("polygon", { points: "588,78 577,114 599,114", fill: "#0F2E22", opacity: 0.85 }),
    h("polygon", { points: "612,86 603,116 621,116", fill: "#143B2B", opacity: 0.85 }),
    h("polygon", { points: "706,74 694,114 718,114", fill: "#0F2E22", opacity: 0.85 }),
    h("circle", { cx: 688, cy: 46, r: 10, fill: "#FEF3C7", opacity: 0.82 }),
    h("circle", { cx: 602, cy: 48, r: 8, fill: "rgba(255,255,255,0.45)" }),
    h("circle", { cx: 614, cy: 46, r: 10, fill: "rgba(255,255,255,0.45)" }),
    h("line", { x1: 649, y1: 22, x2: 649, y2: 124, stroke: "var(--desk-wood-edge, #6B442A)", strokeWidth: 3 }),
    h("line", { x1: 562, y1: 73, x2: 736, y2: 73, stroke: "var(--desk-wood-edge, #6B442A)", strokeWidth: 3 }),

    // Warm pendant lamp cone
    h("path", {
      d: "M438 62 L522 62 L760 286 L200 286 Z",
      fill: "url(#deskLampCone)",
      "data-anim": 1,
      style: an("ism-glow", "5.2s"),
    }),
    h("line", {
      x1: 480,
      y1: 0,
      x2: 480,
      y2: 34,
      stroke: "var(--desk-lamp-wire, #334155)",
      strokeWidth: 2.5,
    }),
    h("path", {
      d: "M450 34 L510 34 L528 62 L432 62 Z",
      fill: "#0A7D8C",
      stroke: "var(--desk-lamp-wire, #1E293B)",
      strokeWidth: 1.5,
    }),
    h("ellipse", { cx: 480, cy: 62, rx: 32, ry: 5, fill: "#FDE68A", opacity: 0.9 }),

    // Wall corkboard — Mistakes wall
    hot("mistakes", "Mistakes wall", [
      h("rect", {
        key: "b",
        x: 34,
        y: 20,
        width: 158,
        height: 82,
        rx: 10,
        fill: "var(--desk-board, #D6B28D)",
        stroke: "var(--desk-board-frame, #8C5E3C)",
        strokeWidth: 2.5,
      }),
      h("rect", { key: "s1", x: 48, y: 30, width: 34, height: 28, rx: 3, fill: "#FEF3C7", transform: "rotate(-4 65 44)" }),
      h("rect", { key: "s2", x: 92, y: 28, width: 34, height: 28, rx: 3, fill: "#FFEDD5", transform: "rotate(3 109 42)" }),
      h("rect", { key: "s3", x: 138, y: 32, width: 34, height: 28, rx: 3, fill: "#DBEAFE", transform: "rotate(-3 155 46)" }),
      h("rect", { key: "s4", x: 68, y: 64, width: 34, height: 26, rx: 3, fill: "#D1FAE5", transform: "rotate(2 85 77)" }),
      h("rect", { key: "s5", x: 114, y: 64, width: 34, height: 26, rx: 3, fill: "#EDE9FE", transform: "rotate(-3 131 77)" }),
      tag("mistakes", "Mistakes", 252, 48, ACCENT.rose, active === "mistakes", true),
    ]),

    // Antique wood & brass pendulum wall clock — Focus session
    hot("session", "Focus sessions", [
      h(
        "g",
        {
          key: "pend",
          "data-anim": 1,
          style: an("ism-sway", "2.4s", "892px 84px"),
        },
        h("line", { x1: 892, y1: 84, x2: 892, y2: 120, stroke: "#D4A446", strokeWidth: 2.6 }),
        h("circle", { cx: 892, cy: 124, r: 8, fill: "#E6B95C", stroke: "#8A621C", strokeWidth: 1.5 }),
      ),
      h("rect", {
        key: "case",
        x: 862,
        y: 26,
        width: 60,
        height: 66,
        rx: 14,
        fill: "#653E28",
        stroke: "#D4A446",
        strokeWidth: 2,
      }),
      h("circle", {
        key: "c",
        cx: 892,
        cy: 58,
        r: 25,
        fill: "#151922",
        stroke: "#E6B95C",
        strokeWidth: 2,
      }),
      h("circle", { key: "r", cx: 892, cy: 58, r: 19, fill: "none", stroke: "rgba(230,185,92,0.38)", strokeDasharray: "2 5" }),
      h("line", {
        key: "hh",
        x1: 892,
        y1: 58,
        x2: 903,
        y2: 64,
        stroke: "#F8D77E",
        strokeWidth: 2.6,
        strokeLinecap: "round",
      }),
      h(
        "g",
        {
          key: "mh",
          "data-anim": 1,
          style: {
            animation: "ism-spin 12s linear infinite",
            transformOrigin: "892px 58px",
            transformBox: "view-box",
          },
        },
        h("line", {
          x1: 892,
          y1: 58,
          x2: 892,
          y2: 40,
          stroke: "#FFC83D",
          strokeWidth: 2.2,
          strokeLinecap: "round",
        }),
      ),
      h("circle", { key: "d", cx: 892, cy: 58, r: 3, fill: "#FFC83D" }),
      tag("session", "Focus timer", 792, 46, ACCENT.amber, active === "session", true),
    ]),

    // Potted desk plant (left corner ambiance)
    h("rect", { x: 26, y: 268, width: 28, height: 36, rx: 6, fill: "#C2410C" }),
    h("ellipse", { cx: 40, cy: 256, rx: 14, ry: 20, fill: "#059669", transform: "rotate(-18 40 256)" }),
    h("ellipse", { cx: 46, cy: 252, rx: 12, ry: 18, fill: "#10B981", transform: "rotate(18 46 252)" }),

    ...chairs,
    ...bodies,

    // Long studio desk surface + legs + soft floor shadow
    h("ellipse", { cx: 480, cy: 334, rx: 390, ry: 11, fill: "rgba(15,23,42,0.14)" }),
    h("rect", { x: 96, y: 274, width: 14, height: 58, rx: 4, fill: "var(--desk-leg, #5C3D28)" }),
    h("rect", { x: 850, y: 274, width: 14, height: 58, rx: 4, fill: "var(--desk-leg, #5C3D28)" }),
    h("rect", { x: 70, y: 244, width: 820, height: 15, rx: 6, fill: "url(#deskWoodTop)" }),
    h("rect", { x: 70, y: 257, width: 820, height: 16, rx: 3, fill: "var(--desk-wood-edge, #7A5236)" }),

    ...arms,

    // Stacked notebooks — Notes
    hot("notes", "Notes", [
      h("rect", { key: "n1", x: 188, y: 234, width: 52, height: 10, rx: 3, fill: "#F59E0B" }),
      h("rect", { key: "n2", x: 192, y: 224, width: 46, height: 10, rx: 3, fill: "#7C3AED" }),
      h("rect", { key: "n3", x: 186, y: 214, width: 50, height: 10, rx: 3, fill: "#0A7D8C" }),
      tag("notes", "Notes", 214, 286, ACCENT.amber, active === "notes", true),
    ]),

    // Ribbons book — Bookmarks
    hot("bookmarks", "Bookmarks", [
      h("rect", { key: "bk", x: 318, y: 226, width: 52, height: 18, rx: 4, fill: "#0A7D8C" }),
      h("rect", { key: "pg", x: 322, y: 229, width: 44, height: 3, rx: 1.5, fill: "#F8FAFC" }),
      h("rect", { key: "r1", x: 329, y: 255, width: 5, height: 20, rx: 2, fill: "#EA580C", "data-anim": 1, style: an("ism-sway", "3s", "top center") }),
      h("rect", { key: "r2", x: 341, y: 255, width: 5, height: 15, rx: 2, fill: "#F59E0B", "data-anim": 1, style: an("ism-sway", "3s", "top center", ".5s") }),
      h("rect", { key: "r3", x: 353, y: 255, width: 5, height: 23, rx: 2, fill: "#7C3AED", "data-anim": 1, style: an("ism-sway", "3s", "top center", "1s") }),
      tag("bookmarks", "Bookmarks", 344, 286, ACCENT.teal, active === "bookmarks", true),
    ]),

    // Studio laptop — Practice / Desk set
    hot("practice", "Desk set", [
      h("rect", { key: "sc", x: 448, y: 196, width: 64, height: 44, rx: 6, fill: "#0F172A", stroke: "#334155", strokeWidth: 1.5 }),
      h("rect", { key: "b1", x: 456, y: 205, width: 36, height: 5, rx: 2.5, fill: "#38BDF8", "data-anim": 1, style: an("ism-blink", "2.4s") }),
      h("rect", { key: "b2", x: 456, y: 215, width: 48, height: 5, rx: 2.5, fill: "#34D399", "data-anim": 1, style: an("ism-blink", "2.4s", "center", ".6s") }),
      h("rect", { key: "b3", x: 456, y: 225, width: 26, height: 5, rx: 2.5, fill: "#FBBF24", "data-anim": 1, style: an("ism-blink", "2.4s", "center", "1.2s") }),
      h("rect", { key: "bs", x: 440, y: 240, width: 80, height: 6, rx: 3, fill: "#475569" }),
      tag("practice", personal ? "Practice" : "Desk set", 480, 286, ACCENT.blue, active === "practice", true),
    ]),

    // Flashcards — Saved / Shared Qs
    hot("shared", personal ? "Saved questions" : "Shared questions", [
      h("rect", { key: "q1", x: 592, y: 214, width: 44, height: 28, rx: 4, fill: "#FFFFFF", stroke: "#CBD5E1", transform: "rotate(-8 614 228)" }),
      h("rect", { key: "q2", x: 594, y: 212, width: 44, height: 28, rx: 4, fill: "#FFEDD5", stroke: "#FDBA74", transform: "rotate(5 616 226)" }),
      h("rect", { key: "q3", x: 593, y: 213, width: 44, height: 28, rx: 4, fill: "#FFFFFF", stroke: "#94A3B8" }),
      h(
        "text",
        {
          key: "qt",
          x: 615,
          y: 232,
          textAnchor: "middle",
          fontSize: 15,
          fontWeight: 800,
          fill: ACCENT.coral,
        },
        "Q?",
      ),
      tag("shared", personal ? "Saved Qs" : "Shared Qs", 615, 286, ACCENT.coral, active === "shared", true),
    ]),

    // Progress clipboard — Progress
    hot("progress", "Progress", [
      h("rect", { key: "cb", x: 724, y: 196, width: 42, height: 48, rx: 6, fill: "#FFFFFF", stroke: "#94A3B8" }),
      h("rect", { key: "cl", x: 737, y: 191, width: 16, height: 7, rx: 2.5, fill: "#334155" }),
      h("rect", { key: "g1", x: 731, y: 222, width: 7, height: 16, rx: 2, fill: "#10B981" }),
      h("rect", { key: "g2", x: 742, y: 211, width: 7, height: 27, rx: 2, fill: "#2563EB" }),
      h("rect", { key: "g3", x: 753, y: 217, width: 7, height: 21, rx: 2, fill: "#F97316" }),
      tag("progress", "Progress", 745, 286, ACCENT.emerald, active === "progress", true),
    ]),

    // Ceramic coffee mug + animated steam
    h("rect", { x: 856, y: 227, width: 18, height: 17, rx: 4, fill: "#F8FAFC", stroke: "#94A3B8" }),
    h("path", { d: "M874 231 q6 0 6 5 q0 5 -6 5", fill: "none", stroke: "#94A3B8", strokeWidth: 2 }),
    h("path", {
      d: "M861 221 q-4 -6 0 -12 q4 -6 0 -12",
      stroke: "var(--desk-steam, #94A3B8)",
      fill: "none",
      strokeWidth: 2,
      strokeLinecap: "round",
      "data-anim": 1,
      style: an("ism-steam", "2.8s"),
    }),
    h("path", {
      d: "M869 221 q-4 -6 0 -12 q4 -6 0 -12",
      stroke: "var(--desk-steam, #94A3B8)",
      fill: "none",
      strokeWidth: 2,
      strokeLinecap: "round",
      "data-anim": 1,
      style: an("ism-steam", "2.8s", "center", "1.4s"),
    }),

    ...names,
  );
}
