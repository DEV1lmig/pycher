/** @type {import('tailwindcss').Config} */
import tailwindcssAnimate from "tailwindcss-animate";

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      animation: {
        'scroll-line': 'scroll-line 1.5s infinite ease-in-out', 
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
      scale: {
        101: '1.01',
        102: '1.02',
        103: '1.03',
        104: '1.04',
      },
      keyframes: {
        'scroll-line': {
          '0%': { height: '8%', opacity: '1' }, 
          '50%': { height: '0%', opacity: '0' },  
          '100%': { height: '8%', opacity: '1' },
        },
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
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
        red: '#FF6F61',
        dark: {
          DEFAULT: '#160f30', // Dark Purple
          light: '#302640',   // Lighter Dark Purple
          background: '#0e0f2d', // Background Dark
        },
        orange: '#FBC465', // Orange
      },
    },
  },
  plugins: [tailwindcssAnimate],
};