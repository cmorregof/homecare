import type { Config } from "tailwindcss";

/**
 * Design tokens ported from the reference visual language
 * (proyecto_daniela @ 1aa2b0a — salud-cardiaca-web/src/styles/global.css:1-29).
 *
 * Two deliberate departures from the reference, both documented below:
 *
 * 1. PRIMARY IS BLUE, NOT RED. The reference sets --primary #D32F2F and
 *    --danger #C62828 — effectively the same hue. That is harmless there
 *    because the reference product has no risk tiers. Here red *means*
 *    critical, so a red primary would collapse the distinction between
 *    signal and chrome. The reference's --accent (#1976D2) is promoted to
 *    primary and red is reserved entirely for risk.
 *
 * 2. RISK IS A FOUR-TIER SCALE. `risk.high` and `risk.critical` are both
 *    dark reds (1.57:1 luminance contrast against each other, and closer
 *    still under deuteranopia). Colour alone cannot carry the distinction,
 *    so the risk badge differentiates on fill, weight and icon as well.
 *    See components/risk/risk-badge.tsx.
 */
const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // --- Surfaces and text (reference global.css:7-11) ---
        canvas: "#F6F7FB", // reference --bg (renamed: `bg-bg` reads badly)
        surface: "#FFFFFF", // reference --surface
        ink: "#1F2937", // reference --text (was #102027)
        muted: "#6B7280", // reference --muted
        border: "#E5E7EB", // reference --border

        // --- Status (reference global.css:12-14) ---
        success: "#2E7D32", // reference --success
        warning: "#ED6C02", // reference --warning (was #b7791f)
        danger: "#C62828", // reference --danger  (was #b42318)

        // --- Brand: the reference's --accent, promoted to primary ---
        brand: {
          DEFAULT: "#1976D2", // reference --accent (global.css:6)
          dark: "#0D47A1", // derived — not in the reference
          light: "#BBDEFB", // derived — not in the reference
          soft: "#EFF6FF", // derived — not in the reference
        },

        // --- Risk tiers: red reserved exclusively for these ---
        risk: {
          low: "#2E7D32", // reference --success
          moderate: "#ED6C02", // reference --warning
          high: "#C62828", // reference --danger
          critical: "#9A0007", // reference --primary-dark (global.css:3)
        },

        /**
         * @deprecated Legacy accent, 16 usages across 15 files. Aliased to
         * `brand` so existing markup keeps rendering unchanged while blocks
         * 3-4 migrate it. Remove once no `*-clinical` classes remain.
         */
        clinical: "#1976D2",
      },

      // --- Radii (reference global.css:16-19) ---
      borderRadius: {
        sm: "6px", // --radius-sm
        md: "10px", // --radius-md
        lg: "16px", // --radius-lg
        xl: "24px", // --radius-xl
      },

      // --- Shadows (reference global.css:21-23) ---
      boxShadow: {
        sm: "0 1px 2px rgba(15, 23, 42, 0.06)",
        md: "0 4px 12px rgba(15, 23, 42, 0.06)",
        lg: "0 16px 40px rgba(15, 23, 42, 0.08)",
      },

      // --- Type (reference global.css:25-27; base 14px, system stack) ---
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Oxygen",
          "Ubuntu",
          "Cantarell",
          "sans-serif",
        ],
      },

      /**
       * Every step is a size the reference actually uses. Line heights 1.6
       * and 1.05 are taken from it verbatim; the rest interpolate.
       */
      fontSize: {
        xs: ["12px", "1.4"],
        sm: ["13px", "1.5"],
        base: ["14px", "1.6"],
        lg: ["16px", "1.6"],
        xl: ["18px", "1.5"],
        "2xl": ["24px", "1.3"],
        "3xl": ["28px", "1.2"],
        "4xl": ["30px", "1.15"],
        "5xl": ["44px", "1.05"],
      },
    },
  },
  plugins: [],
};

export default config;
