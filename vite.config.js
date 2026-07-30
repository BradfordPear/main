import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// GitHub Pages serves a project repo at https://<user>.github.io/<repo>/
// This repo is `bradfordpear/main`, so the base path is `/main/`.
// Override with the DETHRONE_BASE env var if you rename the repo or use a custom domain.
const base = process.env.DETHRONE_BASE ?? '/main/'

export default defineConfig({
  base,
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'icons/icon-192.png', 'icons/icon-512.png'],
      manifest: {
        name: 'Dethrone',
        short_name: 'Dethrone',
        description: 'A single-phone, pass-around social debate party game.',
        theme_color: '#0e0e12',
        background_color: '#0e0e12',
        display: 'standalone',
        orientation: 'portrait',
        start_url: '.',
        scope: '.',
        icons: [
          { src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,ico,json,woff2}'],
      },
    }),
  ],
})
