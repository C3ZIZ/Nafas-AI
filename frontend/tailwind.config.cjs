/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}'
  ],
  safelist: [
    'bg-emerald-50', 'text-emerald-700', 'border-emerald-200',
    'bg-indigo-50', 'text-indigo-700', 'border-indigo-200',
    'bg-rose-50', 'text-rose-700', 'border-rose-200',
    'bg-blue-50', 'text-blue-700', 'border-blue-200',
    'bg-violet-50', 'text-violet-700', 'border-violet-200',
    'bg-amber-50', 'text-amber-700', 'border-amber-200',
    'bg-stone-50', 'text-stone-600', 'border-stone-200',
    'bg-teal-50', 'text-teal-700', 'border-teal-200'
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
          DEFAULT: '#0d9488'
        },
        ink: {
          DEFAULT: '#1c1917',
          muted:   '#57534e',
          subtle:  '#78716c'
        },
        surface: {
          DEFAULT: '#ffffff',
          alt:     '#fafaf9',
          sunken:  '#f5f5f4'
        },
        line: {
          DEFAULT: '#e7e5e4',
          strong:  '#d6d3d1'
        }
      },
      fontFamily: {
        sans: [
          '"IBM Plex Sans"',
          '"IBM Plex Sans Arabic"',
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'sans-serif'
        ],
        arabic: ['"IBM Plex Sans Arabic"', '"IBM Plex Sans"', 'Tahoma', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace']
      },
      fontSize: {
        '2xs': ['0.6875rem', { lineHeight: '1rem' }]
      },
      borderRadius: {
        xl: '0.75rem',
        '2xl': '1rem',
        '3xl': '1.25rem'
      },
      boxShadow: {
        card:    '0 1px 0 0 rgba(28,25,23,0.04), 0 1px 2px 0 rgba(28,25,23,0.04)',
        soft:    '0 4px 16px -4px rgba(28,25,23,0.08), 0 2px 4px -2px rgba(28,25,23,0.04)',
        ring:    '0 0 0 4px rgba(13,148,136,0.12)'
      },
      transitionTimingFunction: {
        'out-quint': 'cubic-bezier(0.22, 1, 0.36, 1)'
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: 0, transform: 'translateY(6px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' }
        }
      },
      animation: {
        'fade-up': 'fade-up 0.4s cubic-bezier(0.22, 1, 0.36, 1) both'
      }
    }
  },
  plugins: []
}
