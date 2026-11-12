import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'

// Dev: `npm run dev` proxies the API to the local FastAPI server (app/server.py). Production: the server serves dist/.
// M6 dev runs its server on RS_PORT (default 8775) so it never talks to production on 8765.
const api = `http://127.0.0.1:${process.env.RS_PORT ?? '8775'}`
// @m5 = the M5 checkpoint copy in this workspace. The poster editor imports its tested helpers unchanged.
const m5 = fileURLToPath(new URL('../../m5', import.meta.url))
const workspace = fileURLToPath(new URL('../..', import.meta.url))
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@m5': m5 } },
  server: { proxy: { '/api': api, '/files': api }, fs: { allow: [workspace] } },
})
