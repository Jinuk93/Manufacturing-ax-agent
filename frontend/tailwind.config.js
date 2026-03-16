/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Palantir 디자인 토큰 (ui-ux-design.md 섹션 14-2)
        black:  '#090C10',
        dg1:    '#0F1318',
        dg2:    '#161B22',
        dg3:    '#1E2530',
        dg4:    '#252D3A',
        gray5:  '#D8DFE8',
        gray4:  '#A8B3C0',
        gray3:  '#6B7788',
        blue3:  '#2D72D2',
        blue4:  '#4C90F0',
        green5: '#72CA9B',
        yellow5:'#FBB360',
        red3:   '#C53030',
        red5:   '#F17474',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
