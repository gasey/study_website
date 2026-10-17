import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  server: {
    // FastAPI runs on :8000 in dev; Caddy does the same routing in production.
    proxy: { '/api': 'http://localhost:8000' },
  },
})
