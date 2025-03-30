// filepath: /home/dev1mig/Documents/projects/pycher/frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
import tailwindcssAnimate from "tailwindcss-animate";

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
      colors: {
        primary: {
          DEFAULT: '#5f2dee', // Purple
          light: '#9880f2',   // Light Purple
        },
        secondary: '#f2d231', // Yellow
        dark: {
          DEFAULT: '#160f30', // Dark Purple
          light: '#312a56',   // Lighter Dark Purple
          background: '#0e0f2d', // Background Dark
        },
      },
    },
  },
  plugins: [tailwindcssAnimate],
}
