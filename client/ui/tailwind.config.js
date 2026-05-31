/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'vecta-bg': {
          DEFAULT: '#000000',
          alt: '#05070A',
        },
        'vecta-panel': {
          DEFAULT: 'rgba(11, 15, 20, 0.8)', // Glassy base
          solid: '#0B0F14',
        },
        'vecta-cyan': {
          DEFAULT: '#00D1FF',
          accent: '#22D3EE',
          dim: 'rgba(0, 209, 255, 0.2)',
        },
        'vecta-amber': '#F59E0B',
        'vecta-text': {
          primary: '#E5E7EB',
          secondary: '#9CA3AF',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
