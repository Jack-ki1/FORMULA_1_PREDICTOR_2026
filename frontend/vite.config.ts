import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'robots.txt', 'apple-touch-icon.png'],
      manifest: {
        name: 'F1 Predictor 2026',
        short_name: 'F1 Predictor',
        description: 'AI-powered Formula 1 predictions — Monte Carlo, Elo H2H, tire strategy. Frontend on 5178, API on 5000.',
        theme_color: '#E10600',
        background_color: '#F4F5F7',
        display: 'standalone',
        start_url: '/',
        scope: '/',
        icons: [
          { src: '/pwa-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: '/pwa-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,svg,woff2}'],
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.startsWith('/api/v1/races') || url.pathname.startsWith('/api/v1/standings'),
            handler: 'StaleWhileRevalidate',
            options: { cacheName: 'f1-api-cache', expiration: { maxEntries: 50, maxAgeSeconds: 300 } },
          },
        ],
      },
    }),
  ],
  // Decoupled: frontend on 5178, backend on 5000. Vite proxies /api → backend for dev.
  // Note: 5178 avoids conflict with parallel workspace's 5173; use --port 5173 if free.
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
  base: '/',
  build: { outDir: 'dist' },
})
