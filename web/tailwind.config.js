/** Tokens transcribed from the design handoff. Colours, type and shape are
 *  final per the handoff — do not improvise values. Two rules worth keeping
 *  in mind while using these: a colour names an AREA, never a state; and
 *  vermilion is the brand mark only, never a button.
 *  @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#F4EFE4',          // page background (warm paper)
        canvas: '#E9E1D2',         // mobile canvas
        card: '#FFFFFF',
        ink: '#1D1B18',            // text and primary buttons
        secondary: '#49443B',
        muted: '#6B6457',
        placeholder: '#7A7366',
        hairline: '#E4DBC9',
        hairline2: '#DCD3C2',
        vermilion: '#C0462C',      // brand mark ONLY

        // Area colours: mid / soft tint / dark ink.
        // Text in an area colour uses `dark`; `DEFAULT` is for dots, bars,
        // borders and swatches only.
        practice:  { DEFAULT: '#2D5BD0', soft: '#E3E9F8', dark: '#1F44A6' },
        learn:     { DEFAULT: '#7B45B8', soft: '#EEE6F7', dark: '#5E2F98' },
        map:       { DEFAULT: '#0E8287', soft: '#DCEFEF', dark: '#08605F' },
        community: { DEFAULT: '#B23A9A', soft: '#F5E1F0', dark: '#86226F' },
        exams:     { DEFAULT: '#B26B00', soft: '#F7EAD0', dark: '#7E4A00' },
        rewards:   { DEFAULT: '#8A8A12', soft: '#ECEDCF', dark: '#545A06' },

        // States always pair with a symbol (✓ × !), never colour alone.
        correct:   { DEFAULT: '#2E7D46', soft: '#DCEFE1', dark: '#1F6234' },
        wrong:     { DEFAULT: '#C0392B', soft: '#F8DEDA', dark: '#9E2A1F' },
        attention: { DEFAULT: '#1D1B18', soft: '#EDE5D4', dark: '#1D1B18' },
      },
      fontFamily: {
        display: ['Newsreader', 'Georgia', 'serif'],
        sans: ['"Public Sans"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
        paperdoc: ['"Times New Roman"', 'Times', 'serif'], // original-paper rendering
      },
      borderRadius: { card: '10px', panel: '8px', pill: '999px' },
      maxWidth: { shell: '1240px' },
    },
  },
  plugins: [],
}
