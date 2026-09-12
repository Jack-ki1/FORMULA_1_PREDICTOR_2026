import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:5000', changeOrigin: true },
      '/dashboard': { target: 'http://localhost:5000', changeOrigin: true },
      '/standings': { target: 'http://localhost:5000', changeOrigin: true },
      '/h2h': { target: 'http://localhost:5000', changeOrigin: true },
      '/constructors': { target: 'http://localhost:5000', changeOrigin: true },
      '/analytics': { target: 'http://localhost:5000', changeOrigin: true },
      '/reports': { target: 'http://localhost:5000', changeOrigin: true },
      '/health': { target: 'http://localhost:5000', changeOrigin: true },
    }
  },
  build: { outDir: 'dist' }
})
