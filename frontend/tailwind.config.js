/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'glass-bg': 'rgba(17, 25, 40, 0.75)',
        'glass-border': 'rgba(255, 255, 255, 0.125)',
      },
    },
  },
  plugins: [],
}
