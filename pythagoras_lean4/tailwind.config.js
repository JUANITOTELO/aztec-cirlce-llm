/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        lean: {
          bg: '#0f172a',
          panel: '#1e293b',
          border: '#334155',
          accent: '#38bdf8',
          purple: '#c084fc',
          green: '#4ade80',
          amber: '#fbbf24',
          rose: '#fb7185'
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace']
      }
    }
  },
  plugins: []
};