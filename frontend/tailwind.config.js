export default {
  darkMode: 'class',
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          light: "#f3e8ff",
          DEFAULT: "#a855f7",     // light purple
          dark: "#7e22ce"
        },
        background: "#faf5ff",     // soft lavender
        foreground: "#1e1b4b",     // deep purple for text
      },
    },
  },
  plugins: [],
}
