/** Tokens transcribed from the design handoff, enhanced with CSS custom
 *  property channels so students can switch seamlessly between Warm Paper,
 *  Crisp Focus (Brilliant/Quizlet daylight), and Night Owl (dark study) themes.
 *  A colour names an AREA, never a state; vermilion is the brand mark only.
 *  @type {import('tailwindcss').Config} */
const rgb = (v) => `rgb(var(${v}) / <alpha-value>)`

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        paper: rgb('--ism-paper-rgb'),          // page background
        canvas: rgb('--ism-canvas-rgb'),        // secondary/mobile canvas
        card: rgb('--ism-card-rgb'),            // elevated card surface
        ink: rgb('--ism-ink-rgb'),              // primary text & action fill
        secondary: rgb('--ism-secondary-rgb'),
        muted: rgb('--ism-muted-rgb'),
        placeholder: rgb('--ism-placeholder-rgb'),
        hairline: rgb('--ism-hairline-rgb'),
        hairline2: rgb('--ism-hairline2-rgb'),
        // Brand mark only. Keep the exact handoff colour; primary buttons
        // and text use ink.
        vermilion: '#C0462C',

        // Area colours: mid / soft tint / dark ink.
        practice:  { DEFAULT: rgb('--ism-practice-rgb'), soft: rgb('--ism-practice-soft-rgb'), dark: rgb('--ism-practice-dark-rgb') },
        learn:     { DEFAULT: rgb('--ism-learn-rgb'), soft: rgb('--ism-learn-soft-rgb'), dark: rgb('--ism-learn-dark-rgb') },
        map:       { DEFAULT: rgb('--ism-map-rgb'), soft: rgb('--ism-map-soft-rgb'), dark: rgb('--ism-map-dark-rgb') },
        community: { DEFAULT: rgb('--ism-community-rgb'), soft: rgb('--ism-community-soft-rgb'), dark: rgb('--ism-community-dark-rgb') },
        exams:     { DEFAULT: rgb('--ism-exams-rgb'), soft: rgb('--ism-exams-soft-rgb'), dark: rgb('--ism-exams-dark-rgb') },
        rewards:   { DEFAULT: rgb('--ism-rewards-rgb'), soft: rgb('--ism-rewards-soft-rgb'), dark: rgb('--ism-rewards-dark-rgb') },

        // States always pair with a word or symbol, never colour alone.
        correct:   { DEFAULT: rgb('--ism-correct-rgb'), soft: rgb('--ism-correct-soft-rgb'), dark: rgb('--ism-correct-dark-rgb') },
        wrong:     { DEFAULT: rgb('--ism-wrong-rgb'), soft: rgb('--ism-wrong-soft-rgb'), dark: rgb('--ism-wrong-dark-rgb') },
        attention: { DEFAULT: rgb('--ism-ink-rgb'), soft: rgb('--ism-attention-soft-rgb'), dark: rgb('--ism-ink-rgb') },

        // Bank card & option states
        opt:      { bg: rgb('--ism-opt-bg-rgb'), border: rgb('--ism-opt-border-rgb'), muted: rgb('--ism-opt-muted-rgb') },
        keyed:    { DEFAULT: rgb('--ism-keyed-rgb'), soft: rgb('--ism-keyed-soft-rgb') },  // revealed correct
        mypick:   { DEFAULT: rgb('--ism-mypick-rgb'), soft: rgb('--ism-mypick-soft-rgb') },  // revealed wrong pick
        prov:     { DEFAULT: rgb('--ism-prov-rgb') },                   // non-official provenance
        link:     { DEFAULT: rgb('--ism-link-rgb') },                   // "View original ↗"
      },
      fontFamily: {
        display: ['Newsreader', 'Georgia', 'serif'],
        sans: ['"Public Sans"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
        paperdoc: ['"Times New Roman"', 'Times', 'serif'], // original-paper rendering
      },
      borderRadius: { card: '10px', panel: '8px', pill: '999px' },
      maxWidth: { shell: '100%' },
    },
  },
  plugins: [],
}
