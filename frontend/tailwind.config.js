/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'sans-serif'] },
      colors: {
        sidebar: '#0b0f19',
        'sidebar-border': '#141b2d',
        'sidebar-muted': '#8892a4',
        'sidebar-input': '#141b2d',
        'sidebar-input-border': '#1e2a40',
      },
    },
  },
  plugins: [],
}
