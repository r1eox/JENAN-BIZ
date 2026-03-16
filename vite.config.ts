import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
  ],
  server: {
    watch: {
      // Prevent Tailwind's own CSS output from triggering a re-scan loop
      ignored: ['**/.git/**', '**/node_modules/**', '**/dist/**'],
    },
  },
  css: {
    devSourcemap: false,
  },
})
