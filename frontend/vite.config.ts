import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In dev, proxy API calls to the local FastAPI server (uvicorn main:app --port 8000)
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:8000", "/health": "http://127.0.0.1:8000" } },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          recharts: ["recharts"],
          "framer-motion": ["framer-motion"],
        },
      },
    },
  },
});
