import type { Config } from "tailwindcss";

// Mundo "institucional sobrio juridico": papel quente, tinta navy, serif de display.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "hsl(var(--primary) / <alpha-value>)",
          hover: "hsl(var(--primary-hover) / <alpha-value>)",
          foreground: "hsl(var(--primary-foreground) / <alpha-value>)",
          ink: "hsl(var(--primary-ink) / <alpha-value>)",
        },
        accent: "hsl(var(--accent) / <alpha-value>)",
        background: "hsl(var(--background) / <alpha-value>)",
        surface: "hsl(var(--surface) / <alpha-value>)",
        foreground: "hsl(var(--foreground) / <alpha-value>)",
        "foreground-muted": "hsl(var(--foreground-muted) / <alpha-value>)",
        card: "hsl(var(--card) / <alpha-value>)",
        border: "hsl(var(--border) / <alpha-value>)",
        muted: "hsl(var(--muted) / <alpha-value>)",
        ring: "hsl(var(--ring) / <alpha-value>)",
        score: {
          high: "hsl(var(--score-high) / <alpha-value>)",
          mid: "hsl(var(--score-mid) / <alpha-value>)",
          low: "hsl(var(--score-low) / <alpha-value>)",
        },
        success: "hsl(var(--success) / <alpha-value>)",
        warning: "hsl(var(--warning) / <alpha-value>)",
        danger: "hsl(var(--danger) / <alpha-value>)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "Georgia", "Cambria", "serif"],
      },
      borderRadius: {
        DEFAULT: "var(--radius)",
        lg: "calc(var(--radius) + 0.25rem)",
      },
      boxShadow: {
        card: "0 1px 2px hsl(216 42% 13% / 0.05), 0 14px 30px -18px hsl(216 42% 13% / 0.20)",
        lift: "0 2px 4px hsl(216 42% 13% / 0.06), 0 22px 44px -22px hsl(216 42% 13% / 0.28)",
      },
      letterSpacing: {
        tightest: "-0.04em",
      },
    },
  },
  plugins: [],
};

export default config;
