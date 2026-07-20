import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://192.168.111.187:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://192.168.111.187:8000',
        ws: true,
      }
    }
  }
})
