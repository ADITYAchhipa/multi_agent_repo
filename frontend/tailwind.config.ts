import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f7ff",
          100: "#e0effe",
          200: "#bae0fd",
          300: "#7cc5fb",
          400: "#36a4f7",
          500: "#1481ee",
          600: "#0969d6",
          700: "#0753ab",
          800: "#0b468c",
          900: "#0f3c73",
          DEFAULT: "#1481EE",
        },
        navy: {
          50: "#f4f6f9",
          100: "#e5e9f0",
          200: "#cad2e0",
          300: "#a0afc9",
          400: "#7087ad",
          500: "#4e6792",
          600: "#3d5178",
          700: "#324263",
          800: "#1e293b",
          900: "#0f172a",
          950: "#0b1120",
        },
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          '"Helvetica Neue"',
          "Arial",
          "sans-serif",
        ],
        mono: [
          '"SF Mono"',
          "Monaco",
          '"Cascadia Code"',
          '"Source Code Pro"',
          "Menlo",
          "Consolas",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
