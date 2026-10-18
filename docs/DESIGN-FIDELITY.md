# Design fidelity — values extracted from the prototype

**The prototype markup is authoritative, not the handoff README.** The README
in `docs/design/README.md` gives a tidy summary of the tokens; where it
disagrees with `docs/design/India Study Map v3.dc.html`, the markup wins. It
disagrees in several places, listed below, and building from the README alone
produces something that looks close but reads wrong.

Extract values from the prototype with `grep`/`sed` before building a screen.
Do not eyeball them, and do not carry a value over from another screen
assuming it is shared.

## README vs. markup — known disagreements

| Thing | README | Markup (use this) |
|---|---|---|
| Card radius | 10px | **14px** (bank article) |
| Option button radius | 8px | **6px** |
| Correct state | `#2E7D46` / `#DCEFE1` | **`#3D7344`** border / **`#E3ECDD`** bg |
| Wrong state | `#C0392B` / `#F8DEDA` | **`#B0412A`** border / **`#F5E1D8`** bg |
| Option resting bg | `#FFFFFF` | **`#FBF8F1`**, border `#DCD3C2` |
| State indicator | symbols `✓ × !` | **words**: "Correct", "Answer", "Your pick" |

The README is still right about the six area colours, the three fonts, and
the "a colour names an area, never a state" rule.

## Bank question card (`v3.dc.html` line 407)

```
article  bg #FFFFFF · border 1px #E4DBC9 · radius 14px
         box-shadow 0 1px 2px rgba(29,27,24,.05) · padding 20px 22px
         margin-bottom 12px
```

Header row (`display:flex; flex-wrap; gap 6px 12px; align-items:center`):

1. **Topic chip** — mono 10px, uppercase, tracking .06em, padding 3px 9px,
   radius 999px, per-topic background and colour (see palette below).
2. **`Q{n} · {source}`** — mono 11px, `#6B6457`.
3. **Provenance pill** — mono 10px, uppercase, padding 2px 8px, radius 999px,
   **outlined**: `1px solid {provColor}`, text the same colour, no fill.
   `Official key` → `#3D7344`; anything else → `#2F5E8C`.
4. **Repeat badge**, only when `seen.length > 1` — mono 10px, uppercase,
   padding 3px 9px, radius 999px, **solid dark**: bg `#1D1B18`,
   text `#F4EFE4`. Copy: `Asked {n}× · {comma-separated years}`.
5. **`View original ↗`** — mono 11px, weight 500, `#33609E`,
   pushed right with `margin-left:auto`.

Question stem: Newsreader 21px, line-height 1.35, margin `10px 0 14px`,
`text-wrap: pretty`.

Options: `grid-template-columns: repeat(auto-fit, minmax(220px, 1fr))`,
gap 8px. Each is a button — flex, gap 12px, padding 11px 14px, radius 6px,
font-size 15px, with the letter in mono 12px at a fixed 16px width.

**Options are answered inline on the bank list**, not only on a detail page.
The list header says "Tap an option to check it". After a pick the card
reveals an explanation underneath.

### Option states (from `opts()`, line 2603)

| State | bg | border | text | mark |
|---|---|---|---|---|
| resting | `#FBF8F1` | `#DCD3C2` | `#1D1B18` | — |
| revealed · correct | `#E3ECDD` | `#3D7344` | `#1D1B18` | `Correct` if you picked it, else `Answer` |
| revealed · your wrong pick | `#F5E1D8` | `#B0412A` | `#1D1B18` | `Your pick` |
| revealed · other | `#FBF8F1` | `#DCD3C2` | `#6B6457` | — |

Cursor is `pointer` before reveal, `default` after; options stop responding
once revealed.

## Topic palette (`const TOPIC`, line 2369)

`[colour, background]` pairs, keyed by topic name:

| Topic | colour | bg |
|---|---|---|
| Current affairs | saffron | — |
| Polity | blue | — |
| Science | green | — |
| English | plum | — |
| Mizoram | teal | — |

The literal hex values live in the `H` object in the prototype; read them
there rather than guessing. Note this palette is topic-specific and is **not**
the six area colours.

## What our data does not have yet

The prototype's cards show a **topic chip** and a **discussion count**. Our
`subject`/`topic` columns are NULL by design until classification runs, and
discussion is milestone 4. Render those slots only when the data exists —
do not invent a placeholder topic, and do not fall back to the old `'gk'`.

## Naming — "module" is dead, and "exam" means two things

The prototype still uses the old vocabulary. The schema and UI moved on, and
the overlap is a real trap: the prototype's `exam` screen is **the timed
paper**, not an exam's landing page.

| Prototype screen | What it actually is | Schema | Our file |
|---|---|---|---|
| `modules` | the launcher, "Exams & tools" | `collections` | `screens/Exams.tsx` |
| `module` | one exam's landing page | one `collection` | `screens/ExamPage.tsx` |
| `exam` | **the timed paper itself** | `collection_papers.as_mock` | `screens/MockRunner.tsx` |

Schema v3 says it outright: *"Collections (UI: 'Exams & tools'; formerly
'modules')"*. Do not name anything new `module`, and do not assume a file
called `Exam*` is the timed paper — check which of the three it is.

Routes: `/exams` → launcher, `/exams/:id` → exam page, and the mock runner
is entered from there.

## Deliberate divergences from the handoff

Changes we have made on purpose. Everything else follows the prototype.

| Token | Handoff | Ours | Why |
|---|---|---|---|
| brand vermilion | `#C0462C` | `#D9461C` (mark) + `#962F15` (text) | was RGB-distance 23 from the wrong-answer state; see DECISIONS #8 |

Known and **not** changed: `placeholder #7A7366` sits at 4.10 contrast,
just under AA for body text. Left alone pending a design pass, since
placeholder styling is a system-wide call rather than a component fix.
