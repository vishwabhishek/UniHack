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
        bg: 'var(--bg)',
        'surface-1': 'var(--surface-1)',
        'surface-2': 'var(--surface-2)',
        'surface-glass': 'var(--surface-glass)',
        border: 'var(--border)',
        'border-strong': 'var(--border-strong)',
        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        'text-muted': 'var(--text-muted)',
        cyan: {
          DEFAULT: 'var(--cyan)',
          bg: 'var(--cyan-bg)',
        },
        amber: {
          DEFAULT: 'var(--amber)',
          bg: 'var(--amber-bg)',
        },
        green: {
          DEFAULT: 'var(--green)',
          bg: 'var(--green-bg)',
        },
        red: {
          DEFAULT: 'var(--red)',
          bg: 'var(--red-bg)',
        },
        'gray-chip': 'var(--gray-chip)',
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
    },
  },
  plugins: [],
}
