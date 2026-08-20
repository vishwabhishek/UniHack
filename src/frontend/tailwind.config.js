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
        pim: {
          darkest: '#070A0F',
          surface: '#0B0F17',
          panel: '#111827',
          card: '#151D2C',
          cardHover: '#1B2436',
          border: '#1E293B',
          borderSubtle: '#293548',
          borderHighlight: '#3B82F6',
          textMuted: '#64748B',
          textSecondary: '#94A3B8',
          textPrimary: '#F1F5F9',
          accent: '#2563EB',
          accentHover: '#1D4ED8',
          accentLight: '#3B82F6',
          amber: '#F59E0B',
          amberDark: '#D97706',
          amberBg: '#451A03',
          emerald: '#10B981',
          emeraldDark: '#059669',
          emeraldBg: '#022C22',
          rose: '#F43F5E',
          roseDark: '#E11D48',
          roseBg: '#4C0519',
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'monospace'],
      },
      boxShadow: {
        'pim-sm': '0 1px 2px 0 rgba(0, 0, 0, 0.4)',
        'pim-panel': '0 4px 20px -2px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(30, 41, 59, 0.8)',
        'pim-active': '0 0 0 1px rgba(59, 130, 246, 0.5), 0 4px 12px -2px rgba(37, 99, 235, 0.2)',
      }
    },
  },
  plugins: [],
}
