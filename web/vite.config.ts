import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

// The database is localhost-only on the server, so there is no local
// Postgres to run the API against. Dev proxies /api to the deployed service
// instead; set API_TARGET=http://localhost:8000 if you tunnel the DB and run
// uvicorn locally.
const API_TARGET = process.env.API_TARGET ?? 'https://study.hawayu.in'

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  server: {
    proxy: {
      '/api': { target: API_TARGET, changeOrigin: true, secure: true },
    },
  },
})
