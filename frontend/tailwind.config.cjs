module.exports = {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0b1220',
        surface: '#0f172a',
        ink: '#e6edf3',
        accent: {
          DEFAULT: '#22d3ee',
          600: '#06b6d4',
          700: '#0891b2'
        },
        teal: {
          DEFAULT: '#2dd4bf'
        }
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
        arabic: ['"IBM Plex Sans Arabic"', '"Noto Naskh Arabic"', 'Tahoma', 'sans-serif']
      },
      boxShadow: {
        glow: '0 10px 40px -10px rgba(34, 211, 238, 0.45)',
        soft: '0 8px 30px -12px rgba(2, 6, 23, 0.25)'
      },
      backgroundImage: {
        'mesh-hero': 'radial-gradient(at 20% 10%, rgba(34,211,238,0.18) 0px, transparent 50%), radial-gradient(at 80% 0%, rgba(45,212,191,0.18) 0px, transparent 50%), radial-gradient(at 50% 100%, rgba(99,102,241,0.10) 0px, transparent 50%)'
      }
    }
  },
  plugins: []
}
