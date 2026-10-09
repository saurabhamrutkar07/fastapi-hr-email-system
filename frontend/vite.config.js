import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(),tailwindcss()],
  server: {
    // Backend CORS, allows FRONTEND_URL (default http:/localhost:3000)
    port: 3000,
    strictPort: true
  }
})
