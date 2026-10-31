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
const H = {
  plum: ["#8A4A86"],
  blue: ["#2D5BD0"],
  teal: ["#1F7F86"],
  verm: ["#C0462C"],
  green: ["#3F8350"],
};
export default function DeskScene({
  active,
  pick,
  members,
  focus,
  pickMember,
  invite,
}: {
  active: string;
  pick: (key: string) => void;
  members: (SceneMember | null)[];
  focus: string;
  pickMember: (id: string) => void;
  invite: () => void;
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
    const w = label.length * 7 + 30;
    return h(
      "g",
      { key: "t" + key },
      pulse && !on
        ? h("circle", {
            cx: x - w / 2 + 12,
            cy: y + 11,
            r: 4,
            fill: color,
            "data-anim": 1,
            style: an("ism-pulse", "1.8s"),
          })
        : null,
      h("rect", {
        x: x - w / 2,
        y,
        width: w,
        height: 22,
        rx: 11,
        fill: on ? color : "#FBF8F1",
        stroke: on ? color : "#1D1B18",
      }),
      h("circle", {
        cx: x - w / 2 + 12,
        cy: y + 11,
        r: 4,
        fill: on ? "#FBF8F1" : color,
      }),
      h(
        "text",
        {
          x: x + 7,
          y: y + 15,
          textAnchor: "middle",
          fontFamily: "IBM Plex Mono, monospace",
          fontSize: 11,
          fill: on ? "#FBF8F1" : "#1D1B18",
        },
        label,
      ),
    );
  };
  const hot = (key: string, kids: React.ReactNode[]) =>
    h(
      "g",
      {
        key,
        role: "button",
        tabIndex: 0,
        "aria-label": key === "session" ? "Focus sessions" : key,
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
      x: cx - 42,
      y: 140,
      width: 84,
      height: 116,
      rx: 12,
      fill: members[i] ? "#6E4630" : "none",
      stroke: members[i] ? "none" : "#8A5A3B",
      strokeWidth: 2,
      strokeDasharray: members[i] ? null : "6 5",
    }),
  );
  const bodies = SEATS.map((cx, i) => {
    const m = members[i];
    if (!m) return null;
    const d = i * 0.7 + "s";
    return h(
      "g",
      {
        key: "p" + i,
        opacity: m.here ? 1 : 0.28,
        onClick: () => pickMember(m.ini),
        style: { cursor: "pointer", transition: "opacity 400ms" },
      },
      h(
        "g",
        { "data-anim": 1, style: an("ism-breathe", "4s", "center", d) },
        h("rect", {
          x: cx - 34,
          y: 190,
          width: 68,
          height: 76,
          rx: 30,
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
              h("circle", { cx, cy: 164, r: 24, fill: m.skin }),
              h("ellipse", { cx, cy: 150, rx: 25, ry: 13, fill: m.hair }),
              i % 2
                ? h("circle", { cx: cx + 19, cy: 144, r: 8, fill: m.hair })
                : h("rect", {
                    x: cx - 25,
                    y: 146,
                    width: 8,
                    height: 24,
                    rx: 4,
                    fill: m.hair,
                  }),
              h("circle", { cx: cx - 8, cy: 167, r: 2, fill: "#1D1B18" }),
              h("circle", { cx: cx + 8, cy: 167, r: 2, fill: "#1D1B18" }),
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
        opacity: m.here ? 1 : 0.28,
        onClick: () => pickMember(m.ini),
        style: { cursor: "pointer" },
      },
      h("rect", {
        x: cx - 42,
        y: 236,
        width: 32,
        height: 14,
        rx: 7,
        fill: m.arm,
      }),
      h("rect", {
        x: cx + 10,
        y: 236,
        width: 32,
        height: 14,
        rx: 7,
        fill: m.arm,
        "data-anim": m.here ? 1 : null,
        style: m.here
          ? an("ism-write", "2.4s", "left center", i * 0.5 + "s")
          : null,
      }),
    );
  });
  const names = SEATS.map((cx, i) => {
    const m = members[i];
    if (!m)
      return h(
        "g",
        { key: "n" + i, onClick: invite, style: { cursor: "pointer" } },
        tag("inv", "+ Invite", cx, 188, "#1D1B18", false, true),
      );
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
        110,
        m.body,
        focus === m.ini,
        false,
      ),
    );
  });
  return h(
    "svg",
    {
      viewBox: "0 0 960 400",
      width: "100%",
      role: "group",
      "aria-label":
        "Interactive study desk. Use the labelled content tabs below for the same actions.",
      style: { display: "block" },
    },
    h("rect", { x: 0, y: 0, width: 960, height: 332, fill: "#EFE6D3" }),
    h("rect", { x: 0, y: 332, width: 960, height: 68, fill: "#E1D2B6" }),
    h("line", { x1: 0, y1: 332, x2: 960, y2: 332, stroke: "#1D1B18" }),
    h("ellipse", {
      cx: 480,
      cy: 240,
      rx: 430,
      ry: 120,
      fill: "#F6E7C6",
      "data-anim": 1,
      style: an("ism-glow", "5s"),
    }),
    h("line", {
      x1: 480,
      y1: 0,
      x2: 480,
      y2: 40,
      stroke: "#1D1B18",
      strokeWidth: 2,
    }),
    h("path", {
      d: "M452 40 L508 40 L528 68 L432 68 Z",
      fill: "#D8A33A",
      stroke: "#1D1B18",
      strokeWidth: 1.5,
    }),
    hot("mistakes", [
      h("rect", {
        key: "b",
        x: 36,
        y: 18,
        width: 150,
        height: 78,
        rx: 4,
        fill: "#C9A27A",
        stroke: "#8A5A3B",
        strokeWidth: 3,
      }),
      h("rect", {
        key: "s1",
        x: 50,
        y: 28,
        width: 34,
        height: 30,
        fill: "#F6E7C6",
        transform: "rotate(-5 67 43)",
      }),
      h("rect", {
        key: "s2",
        x: 92,
        y: 26,
        width: 34,
        height: 30,
        fill: "#F6DDD3",
        transform: "rotate(4 109 41)",
      }),
      h("rect", {
        key: "s3",
        x: 136,
        y: 30,
        width: 34,
        height: 30,
        fill: "#DAE3F1",
        transform: "rotate(-3 153 45)",
      }),
      h("rect", {
        key: "s4",
        x: 70,
        y: 62,
        width: 32,
        height: 26,
        fill: "#DCEBD9",
        transform: "rotate(3 86 75)",
      }),
      h("rect", {
        key: "s5",
        x: 114,
        y: 62,
        width: 32,
        height: 26,
        fill: "#EEDDEC",
        transform: "rotate(-4 130 75)",
      }),
      tag(
        "mistakes",
        "Mistakes wall",
        264,
        46,
        "#9A5B34",
        active === "mistakes",
        true,
      ),
    ]),
    hot("session", [
      h("circle", {
        key: "c",
        cx: 890,
        cy: 56,
        r: 26,
        fill: "#FBF8F1",
        stroke: "#1D1B18",
        strokeWidth: 2,
      }),
      h("line", {
        key: "hh",
        x1: 890,
        y1: 56,
        x2: 902,
        y2: 63,
        stroke: "#1D1B18",
        strokeWidth: 3,
        strokeLinecap: "round",
      }),
      h(
        "g",
        {
          key: "mh",
          "data-anim": 1,
          style: {
            animation: "ism-spin 12s linear infinite",
            transformOrigin: "890px 56px",
            transformBox: "view-box",
          },
        },
        h("line", {
          x1: 890,
          y1: 56,
          x2: 890,
          y2: 37,
          stroke: "#8A4A86",
          strokeWidth: 2.5,
          strokeLinecap: "round",
        }),
      ),
      h("circle", { key: "d", cx: 890, cy: 56, r: 3, fill: "#1D1B18" }),
      tag(
        "session",
        "Focus session",
        790,
        45,
        H.plum[0],
        active === "session",
        true,
      ),
    ]),
    ...chairs,
    ...bodies,
    h("rect", {
      x: 70,
      y: 244,
      width: 820,
      height: 14,
      rx: 4,
      fill: "#9A6A48",
    }),
    h("rect", { x: 70, y: 258, width: 820, height: 16, fill: "#7A5236" }),
    h("rect", { x: 96, y: 274, width: 14, height: 58, fill: "#6E4630" }),
    h("rect", { x: 850, y: 274, width: 14, height: 58, fill: "#6E4630" }),
    ...arms,
    hot("notes", [
      h("rect", {
        key: "n1",
        x: 191,
        y: 234,
        width: 50,
        height: 10,
        rx: 2,
        fill: "#D8A33A",
      }),
      h("rect", {
        key: "n2",
        x: 195,
        y: 224,
        width: 44,
        height: 10,
        rx: 2,
        fill: "#8A4A86",
      }),
      h("rect", {
        key: "n3",
        x: 189,
        y: 214,
        width: 48,
        height: 10,
        rx: 2,
        fill: "#33609E",
      }),
      tag("notes", "Notes", 215, 290, "#B7791A", active === "notes", true),
    ]),
    hot("bookmarks", [
      h("rect", {
        key: "bk",
        x: 320,
        y: 226,
        width: 50,
        height: 18,
        rx: 2,
        fill: "#1F7F86",
      }),
      h("rect", {
        key: "pg",
        x: 323,
        y: 228,
        width: 44,
        height: 3,
        fill: "#FBF8F1",
      }),
      h("rect", {
        key: "r1",
        x: 330,
        y: 256,
        width: 5,
        height: 20,
        fill: "#C0462C",
        "data-anim": 1,
        style: an("ism-sway", "3s", "top center"),
      }),
      h("rect", {
        key: "r2",
        x: 342,
        y: 256,
        width: 5,
        height: 15,
        fill: "#D8A33A",
        "data-anim": 1,
        style: an("ism-sway", "3s", "top center", ".5s"),
      }),
      h("rect", {
        key: "r3",
        x: 354,
        y: 256,
        width: 5,
        height: 24,
        fill: "#8A4A86",
        "data-anim": 1,
        style: an("ism-sway", "3s", "top center", "1s"),
      }),
      tag(
        "bookmarks",
        "Bookmarks",
        345,
        290,
        H.teal[0],
        active === "bookmarks",
        true,
      ),
    ]),
    hot("practice", [
      h("rect", {
        key: "sc",
        x: 450,
        y: 198,
        width: 60,
        height: 42,
        rx: 3,
        fill: "#1D1B18",
      }),
      h("rect", {
        key: "b1",
        x: 457,
        y: 206,
        width: 34,
        height: 5,
        rx: 2,
        fill: "#D8A33A",
        "data-anim": 1,
        style: an("ism-blink", "2.4s"),
      }),
      h("rect", {
        key: "b2",
        x: 457,
        y: 216,
        width: 46,
        height: 5,
        rx: 2,
        fill: "#5E9BD6",
        "data-anim": 1,
        style: an("ism-blink", "2.4s", "center", ".6s"),
      }),
      h("rect", {
        key: "b3",
        x: 457,
        y: 226,
        width: 24,
        height: 5,
        rx: 2,
        fill: "#6DBB7E",
        "data-anim": 1,
        style: an("ism-blink", "2.4s", "center", "1.2s"),
      }),
      h("rect", {
        key: "bs",
        x: 442,
        y: 240,
        width: 76,
        height: 6,
        rx: 2,
        fill: "#49443B",
      }),
      tag(
        "practice",
        "Desk set",
        480,
        290,
        H.blue[0],
        active === "practice",
        true,
      ),
    ]),
    hot("shared", [
      h("rect", {
        key: "q1",
        x: 592,
        y: 214,
        width: 44,
        height: 28,
        rx: 2,
        fill: "#FBF8F1",
        stroke: "#1D1B18",
        transform: "rotate(-8 614 228)",
      }),
      h("rect", {
        key: "q2",
        x: 594,
        y: 212,
        width: 44,
        height: 28,
        rx: 2,
        fill: "#F6DDD3",
        stroke: "#1D1B18",
        transform: "rotate(5 616 226)",
      }),
      h("rect", {
        key: "q3",
        x: 593,
        y: 213,
        width: 44,
        height: 28,
        rx: 2,
        fill: "#FBF8F1",
        stroke: "#1D1B18",
      }),
      h(
        "text",
        {
          key: "qt",
          x: 615,
          y: 232,
          textAnchor: "middle",
          fontFamily: "Newsreader, serif",
          fontSize: 16,
          fill: "#C0462C",
        },
        "Q?",
      ),
      tag(
        "shared",
        "Shared Qs",
        615,
        290,
        H.verm[0],
        active === "shared",
        true,
      ),
    ]),
    hot("progress", [
      h("rect", {
        key: "cb",
        x: 724,
        y: 196,
        width: 42,
        height: 48,
        rx: 3,
        fill: "#FBF8F1",
        stroke: "#1D1B18",
      }),
      h("rect", {
        key: "cl",
        x: 737,
        y: 191,
        width: 16,
        height: 7,
        rx: 2,
        fill: "#1D1B18",
      }),
      h("rect", {
        key: "g1",
        x: 731,
        y: 222,
        width: 7,
        height: 16,
        fill: "#3F8350",
      }),
      h("rect", {
        key: "g2",
        x: 742,
        y: 212,
        width: 7,
        height: 26,
        fill: "#33609E",
      }),
      h("rect", {
        key: "g3",
        x: 753,
        y: 218,
        width: 7,
        height: 20,
        fill: "#C0462C",
      }),
      tag(
        "progress",
        "Progress",
        745,
        290,
        H.green[0],
        active === "progress",
        true,
      ),
    ]),
    h("rect", {
      x: 858,
      y: 228,
      width: 18,
      height: 16,
      rx: 3,
      fill: "#FBF8F1",
      stroke: "#1D1B18",
    }),
    h("path", {
      d: "M863 222 q-4 -6 0 -12 q4 -6 0 -12",
      stroke: "#8C826F",
      fill: "none",
      strokeWidth: 2,
      strokeLinecap: "round",
      "data-anim": 1,
      style: an("ism-steam", "2.8s"),
    }),
    h("path", {
      d: "M871 222 q-4 -6 0 -12 q4 -6 0 -12",
      stroke: "#8C826F",
      fill: "none",
      strokeWidth: 2,
      strokeLinecap: "round",
      "data-anim": 1,
      style: an("ism-steam", "2.8s", "center", "1.4s"),
    }),
    ...names,
  );
}
