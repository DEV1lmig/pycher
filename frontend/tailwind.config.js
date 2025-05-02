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
          DEFAULT: '#8363f2', // Purple
          light: '#9880f2',   // Light Purple
          opaque: '#6653c4', // Darker Purple
        },
        secondary: '#f2d231', // Yellow
        tertiary: '#a5a5a5',  // Grey
        blue: '#00B4D8',
        dark: {
          DEFAULT: '#070113', // Dark Purple
          light: '#302640',   // Lighter Dark Purple
          background: '#0e051f', // Background Dark
        },
        orange: '#FBC465', // Orange

      },
    },
  },
  plugins: [tailwindcssAnimate],
}
