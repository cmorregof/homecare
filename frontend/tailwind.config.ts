import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#102027",
        clinical: "#0f766e",
        warning: "#b7791f",
        danger: "#b42318",
      },
    },
  },
  plugins: [],
};

export default config;
