/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#0f1115',
        panel: '#171a21',
        border: '#262b36',
        accent: '#6366f1',
      },
    },
  },
  plugins: [],
}
