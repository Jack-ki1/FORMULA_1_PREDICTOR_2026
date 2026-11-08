import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Smoke tests render the real pages with MSW mock server handlers
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    env: { VITE_API_BASE: process.env.VITE_API_BASE ?? "http://127.0.0.1:8000" },
    setupFiles: ["./src/test/setup.ts"],
    testTimeout: 20000,
  },
});
