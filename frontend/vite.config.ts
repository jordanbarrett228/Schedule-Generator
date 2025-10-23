// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

export default defineConfig({
  plugins: [react()],
  base: './', // Use relative paths for Electron
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // <- match uvicorn host/port exactly
        changeOrigin: true,
        secure: false,
      },
    },
  },
})