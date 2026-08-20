/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        canvas: '#0B0E13',
        surface: {
          1: '#12161D',
          2: '#1A1F29',
          3: '#232935'
        },
        border: {
          line: '#232935',
          subtle: '#1C212B',
          glow: 'rgba(69, 224, 214, 0.3)'
        },
        content: {
          primary: '#E7EAF0',
          secondary: '#8B93A3',
          muted: '#525B6C'
        },
        signal: {
          cyan: '#45E0D6',
          amber: '#E8A33D',
          green: '#3DDC84',
          red: '#EF5A5A',
          blue: '#3B82F6'
        }
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', '"Inter"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', '"JetBrains Mono"', 'monospace']
      },
      boxShadow: {
        'glow-cyan': '0 0 24px -4px rgba(69, 224, 214, 0.25)',
        'glow-amber': '0 0 24px -4px rgba(232, 163, 61, 0.25)',
        'glow-green': '0 0 24px -4px rgba(61, 220, 132, 0.25)',
        'glass-card': '0 16px 40px -8px rgba(0, 0, 0, 0.6)'
      }
    },
  },
  plugins: [],
}
