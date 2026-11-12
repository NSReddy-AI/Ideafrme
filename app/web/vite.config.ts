import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// Dev: `npm run dev` proxies the API to the local FastAPI server (app/server.py). Production: the server serves dist/.
// M6 dev runs its server on RS_PORT (default 8775) so it never talks to production on 8765.
const api = `http://127.0.0.1:${process.env.RS_PORT ?? '8775'}`
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: { '/api': api, '/files': api } },
})
