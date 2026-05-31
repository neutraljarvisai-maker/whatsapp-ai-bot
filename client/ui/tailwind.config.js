/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'vecta-cyan': {
          DEFAULT: '#00d4ff',
          glow: 'rgba(0, 212, 255, 0.5)',
        },
        'vecta-amber': {
          DEFAULT: '#ffbf00',
          warning: 'rgba(255, 191, 0, 0.5)',
        },
        'vecta-green': {
          DEFAULT: '#39ff14',
          status: 'rgba(57, 255, 20, 0.5)',
        },
        'vecta-bg': {
          matte: '#0a0a0a',
          metallic: '#1a1c1e',
        }
      },
      backgroundImage: {
        'vecta-gradient': 'radial-gradient(circle, #1a1c1e 0%, #0a0a0a 100%)',
      }
    },
  },
  plugins: [],
}
