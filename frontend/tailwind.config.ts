import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef8ff",
          100: "#cfe9ff",
          200: "#a0d3ff",
          300: "#6bb9ff",
          400: "#469eff",
          500: "#2a83f5",
          600: "#1a65d1",
          700: "#144fa7",
          800: "#133f82",
          900: "#102f60",
        },
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;

