import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8085',
        changeOrigin: true,
      },
      '/manifest.json': {
        target: 'http://localhost:8085',
        changeOrigin: true,
      },
      '/sw.js': {
        target: 'http://localhost:8085',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../static_dist',
    emptyOutDir: true,
  },
})
