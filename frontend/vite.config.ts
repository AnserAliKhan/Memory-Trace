import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // Cloudflare Pages sets these at build time; empty for local builds.
  // Read by EnvBanner to label preview / UAT deployments.
  define: {
    __APP_BRANCH__: JSON.stringify(process.env.CF_PAGES_BRANCH ?? ''),
    __APP_COMMIT__: JSON.stringify(process.env.CF_PAGES_COMMIT_SHA ?? ''),
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
