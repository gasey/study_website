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
    fontSize: {
      xs: ['12px', { lineHeight: '1.4' }],
      sm: ['14px', { lineHeight: '1.5' }],
      base: ['16px', { lineHeight: '1.6' }],
      md: ['18px', { lineHeight: '1.65' }],
      lg: ['21px', { lineHeight: '1.35' }],
      xl: ['26px', { lineHeight: '1.25', letterSpacing: '-0.01em' }],
      '2xl': ['32px', { lineHeight: '1.15', letterSpacing: '-0.01em' }],
      '3xl': ['40px', { lineHeight: '1.1', letterSpacing: '-0.01em' }],
    },
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
        display: ['var(--font-ui)', 'Figtree', 'system-ui', 'sans-serif'],
        sans: ['var(--font-ui)', 'Figtree', 'system-ui', 'sans-serif'],
        reading: ['var(--font-reading)', 'Newsreader', 'Georgia', 'serif'],
        mono: ['var(--font-mono)', '"IBM Plex Mono"', 'ui-monospace', 'monospace'],
        paperdoc: ['var(--font-reading)', 'Newsreader', 'Georgia', 'serif'], // original-paper rendering
      },
      borderRadius: { card: '20px', panel: '18px', pill: '999px' },
      maxWidth: { shell: '1320px' },
    },
  },
  plugins: [],
}
