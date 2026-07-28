/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,css}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // ── KnowledgeHub AI Signature Palette ──
        // Deep Warm Graphite surfaces (warm-tinted near-black)
        graphite: {
          50:  '#f9f8f7',
          100: '#f0ede8',
          200: '#e2dbd4',
          300: '#c9bfb4',
          400: '#a89a8a',
          500: '#8a7a6a',
          600: '#6e6055',
          700: '#564c42',
          800: '#3c342c',
          850: '#2a2420',
          900: '#1c1813',
          925: '#161210',
          950: '#0f0d0a',
        },
        // Burnt Copper — the ONE signature accent
        copper: {
          50:  '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#f97316',
          600: '#ea580c',
          700: '#c2410c',
          800: '#9a3412',
          900: '#7c2d12',
          950: '#431407',
        },
        // Warm neutral surfaces for cards/sidebar
        warm: {
          50:  '#fafaf9',
          100: '#f5f5f4',
          200: '#e7e5e4',
          300: '#d6d3d1',
          400: '#a8a29e',
          500: '#78716c',
          600: '#57534e',
          700: '#44403c',
          800: '#292524',
          850: '#1f1c1a',
          900: '#161412',
          950: '#0e0c0a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        serif: ['Georgia', 'Cambria', 'Times New Roman', 'serif'],
      },
      boxShadow: {
        'lift':     '0 2px 8px 0 rgba(0,0,0,0.35), 0 1px 2px 0 rgba(0,0,0,0.25)',
        'lift-md':  '0 4px 16px 0 rgba(0,0,0,0.40), 0 2px 4px 0 rgba(0,0,0,0.30)',
        'lift-lg':  '0 8px 32px 0 rgba(0,0,0,0.50), 0 4px 8px 0 rgba(0,0,0,0.35)',
        'copper':   '0 2px 12px 0 rgba(194,65,12,0.20)',
        'inset-sm': 'inset 0 1px 0 0 rgba(255,255,255,0.04)',
        'paper':    '0 1px 3px 0 rgba(0,0,0,0.30), 0 0 0 1px rgba(255,255,255,0.03)',
      },
      keyframes: {
        'fade-up': {
          '0%':   { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-left': {
          '0%':   { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        'shimmer': {
          '100%': { transform: 'translateX(100%)' },
        },
      },
      animation: {
        'fade-up':    'fade-up 0.20s ease-out forwards',
        'fade-in':    'fade-in 0.18s ease-out forwards',
        'slide-left': 'slide-left 0.22s ease-out forwards',
        'shimmer':    'shimmer 1.8s infinite',
      },
    },
  },
  plugins: [],
}
