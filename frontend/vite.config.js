import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from 'tailwindcss';

export default defineConfig({
  server: {
    host: '0.0.0.0',
    watch: {
      usePolling: true,
      interval: 1000, // Adjust the polling interval as needed
    },
  },
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': '/src',
      '@components': '/src/components',
      '@hooks': '/src/hooks',
      '@lib': '/src/lib',
      '@pages': '/src/pages',
      '@services': '/src/services',
      '@styles': '/src/styles',
      '@utils': '/src/utils',
      '@assets': '/src/assets',
      '@context': '/src/context',
      '@router': '/src/router',
      '@store': '/src/store',
    },
  },
});
