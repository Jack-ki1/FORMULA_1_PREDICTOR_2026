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
        description: 'AI-powered Formula 1 predictions — Monte Carlo, Elo H2H, tire strategy, now on a single port 5000 at /app.',
        theme_color: '#E10600',
        background_color: '#F4F5F7',
        display: 'standalone',
        start_url: '/app/',
        scope: '/app/',
        icons: [
          { src: '/app/pwa-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: '/app/pwa-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
        ],
      },
      workbox: {
        // Keep shell offline, but predictions need network (no offline POST)
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
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
  // Single-port model: Flask (5000) is the only browsable server. Vite is used
  // only to `npm run build` → frontend/dist, which Flask serves at /app on the
  // same port (see dashboard/app.py). No Vite dev server on 5173 — legacy
  // Jinja at / and API at /api/v1/* keep precedence on 5000.
  base: '/app/',
  build: { outDir: 'dist' },
})
