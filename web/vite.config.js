import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

// Version baked into the bundle at build time (CSP-safe — no inline script).
// BigBase serves `default-src 'self'` which blocks inline <script> and
// intercepts /api/*, so the version must live inside the JS bundle (served
// from same origin). Source of truth is the root VERSION file, which
// semantic-release writes BEFORE the web build runs in CI — so no off-by-one.
function appVersion() {
  if (process.env.APP_VERSION) return process.env.APP_VERSION
  try {
    const versionPath = fileURLToPath(new URL('../VERSION', import.meta.url))
    return readFileSync(versionPath, 'utf-8').trim()
  } catch {
    return 'dev'
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  define: {
    __APP_VERSION__: JSON.stringify(appVersion()),
  },
  server: {
    proxy: {
      '/api': {
        target: 'https://bigbase.click',
        changeOrigin: true,
        secure: true,
      },
    },
  },
})
