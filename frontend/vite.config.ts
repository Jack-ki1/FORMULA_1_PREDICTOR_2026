import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
// PWA/service-worker plugin intentionally disabled (was `vite-plugin-pwa`'s VitePWA()).
// It auto-registers a service worker on every page load with no update-prompt UI, which
// caches the app shell + JS/CSS and stale-while-revalidates /api/v1/races and
// /api/v1/standings for 5 minutes. During active development this reliably serves users
// (including you, mid-testing) an old build or stale API data after a fresh deploy — the
// exact "changes aren't showing up" / "not displaying things" symptom. Re-add deliberately,
// later, once the app is stable and you want real offline support, with an explicit
// "new version available, reload?" prompt (registerType: 'prompt') instead of silent
// autoUpdate.

export default defineConfig({
  plugins: [
    react(),
  ],
  // Decoupled: frontend on 5178, backend on 5000. Vite proxies /api → backend for dev.
  // Note: 5178 avoids conflict with parallel workspace's 5173; use --port 5173 if free.
  // Vitest: without this, `vitest run` exits 1 with "No test files found",
  // which fails the CI frontend job even though nothing is wrong.
  test: {
    environment: 'node',
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    passWithNoTests: true,
  },
  server: {
    host: '127.0.0.1',
    port: 5178,
    proxy: {
      '/api': { target: 'http://localhost:5000', changeOrigin: true },
      '/health': { target: 'http://localhost:5000', changeOrigin: true },
      '/metrics': { target: 'http://localhost:5000', changeOrigin: true },
      '/docs': { target: 'http://localhost:5000', changeOrigin: true },
      '/redoc': { target: 'http://localhost:5000', changeOrigin: true },
      '/openapi.json': { target: 'http://localhost:5000', changeOrigin: true },
    },
  },
  // GitHub Pages deployment: base path set via VITE_BASE_PATH env var
  // Default to '/' for local development, override for GH Pages subpath
  base: process.env.VITE_BASE_PATH || '/',
  build: { outDir: 'dist' },
})
