/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: { ink: "rgb(var(--ink) / <alpha-value>)", edge: "rgb(var(--edge) / <alpha-value>)", fg: "rgb(var(--fg) / <alpha-value>)", mute: "rgb(var(--mute) / <alpha-value>)", f1red: "rgb(var(--accent) / <alpha-value>)", glow: "rgb(var(--accent2) / <alpha-value>)", violet: "#7c4dff" },
      borderRadius: { sm: "calc(var(--r) * 0.5)", DEFAULT: "calc(var(--r) * 0.5)", md: "calc(var(--r) * 0.75)", lg: "var(--r)", xl: "calc(var(--r) * 1.5)", "2xl": "calc(var(--r) * 2)", full: "9999px" },
      fontFamily: { sans: ["Inter Variable", "Inter", "system-ui", "sans-serif"] },
      keyframes: { shimmer: { "100%": { transform: "translateX(100%)" } } },
    },
  },
  plugins: [],
};
