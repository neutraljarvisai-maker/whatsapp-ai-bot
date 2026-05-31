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
          DEFAULT: '#0B0F14',
          alt: '#111827',
        },
        'vecta-cyan': {
          DEFAULT: '#00D1FF',
          accent: '#22D3EE',
        },
        'vecta-amber': '#F59E0B',
        'vecta-text': {
          primary: '#E5E7EB',
          secondary: '#9CA3AF',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
