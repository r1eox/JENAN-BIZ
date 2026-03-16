import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  // Use /JENAN-BIZ/ base when building for GitHub Pages, / for local dev
  base: process.env.GITHUB_ACTIONS ? '/JENAN-BIZ/' : '/',
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
