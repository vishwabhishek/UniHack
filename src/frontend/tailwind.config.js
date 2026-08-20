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
          bg: '#080C14',
          darkest: '#0B0F19',
          surface: '#0F1626',
          panel: '#131D31',
          card: '#16233B',
          cardHover: '#1B2A47',
          border: 'rgba(255, 255, 255, 0.08)',
          borderHighlight: 'rgba(56, 189, 248, 0.3)',
          text: '#F1F5F9',
          textSecondary: '#94A3B8',
          textMuted: '#64748B',
          cyan: '#06B6D4',
          blue: '#3B82F6',
          indigo: '#6366F1',
          violet: '#8B5CF6',
          emerald: '#10B981',
          amber: '#F59E0B',
          rose: '#F43F5E'
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace']
      },
      boxShadow: {
        'glow-cyan': '0 0 20px -3px rgba(6, 182, 212, 0.3)',
        'glow-blue': '0 0 20px -3px rgba(59, 130, 246, 0.3)',
        'glow-emerald': '0 0 20px -3px rgba(16, 185, 129, 0.3)',
        'glow-violet': '0 0 20px -3px rgba(139, 92, 246, 0.3)',
        'glow-amber': '0 0 20px -3px rgba(245, 158, 11, 0.3)',
        'glow-rose': '0 0 20px -3px rgba(244, 63, 94, 0.3)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)'
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'mesh-glow': 'radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.15) 0px, transparent 50%), radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.15) 0px, transparent 50%), radial-gradient(at 50% 100%, rgba(6, 182, 212, 0.1) 0px, transparent 50%)'
      }
    },
  },
  plugins: [],
}
