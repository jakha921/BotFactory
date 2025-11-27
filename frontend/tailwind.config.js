/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        // Apple HIG "Zinc" (Neutral) Palette
        gray: {
          50: '#fafafa',
          100: '#f4f4f5',
          200: '#e4e4e7',
          300: '#d4d4d8',
          400: '#a1a1aa',
          500: '#71717a',
          600: '#52525b',
          700: '#3f3f46',
          800: '#27272a',
          900: '#18181b',
          950: '#09090b', // True dark (Zinc 950)
        },
        primary: {
          DEFAULT: '#6366f1', // Indigo 500
          dark: '#4f46e5',    // Indigo 600
          light: '#818cf8',   // Indigo 400
        },
        surface: {
          light: '#ffffff',
          dark: '#18181b', // Zinc 900
        }
      }
    }
  }
};


