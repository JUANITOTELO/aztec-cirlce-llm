/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        dummyDark: '#121316',
        dummyPanel: '#1A1C23',
        dummyBorder: '#2D3139',
        dummyAccent: '#3B82F6',
        dummyAccentHover: '#2563EB',
        dummyHighlight: '#10B981'
      }
    },
  },
  plugins: [],
};
