import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Прокси для локальной разработки: /api → FastAPI на :8000
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
