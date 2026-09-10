/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        wine: '#71211A',
        'wine-soft': '#9C3D3B',
        navy: '#1A2C52',
        blue: '#1A4E85',
        gold: '#EBAA35',
        charcoal: '#1D1D1B',
        secondary: '#526071',
        canvas: '#F4F6F9',
        border: '#DDE3EC',
        'dark-canvas': '#171717',
        'dark-surface': '#222222',
        'dark-border': '#3A3A3A',
      },
      fontFamily: { outfit: ['Outfit', 'system-ui', 'sans-serif'] },
      borderRadius: { control: '10px', container: '14px' },
      boxShadow: { panel: '0 12px 30px rgba(26, 44, 82, 0.08)' },
    },
  },
  plugins: [],
}
