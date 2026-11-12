import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// Dev: `npm run dev` proxies the API to the local FastAPI server (app/server.py). Production: the server serves dist/.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: { '/api': 'http://127.0.0.1:8765', '/files': 'http://127.0.0.1:8765' } },
})
