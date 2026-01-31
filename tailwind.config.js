/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./templates/**/*.html",
    "./**/*.py"
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(214, 32%, 91%)",
        input: "hsl(214, 32%, 91%)",
        ring: "hsl(214, 32%, 91%)",
        background: "#ffffff",
        foreground: "#111827",
        muted: {
          DEFAULT: "hsl(215, 16%, 92%)",
          foreground: "hsl(215, 16%, 47%)",
        },
        card: {
          DEFAULT: "#ffffff",
          foreground: "#111827",
        },
      },
      borderRadius: {
        lg: "12px",
        md: "10px",
        sm: "8px",
      },
      boxShadow: {
        sm: "0 1px 2px rgba(0,0,0,0.05)",
        base: "0 1px 3px rgba(0,0,0,0.1)",
        card: "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
      },
    },
  },
  plugins: [],
};
