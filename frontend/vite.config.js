import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from 'tailwindcss';

export default defineConfig({

  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': '/app/src',
      '@components': '/app/src/components',
      '@hooks': '/app/src/hooks',
      '@lib': '/app/src/lib',
      '@pages': '/app/src/pages',
      '@services': '/app/src/services',
      '@styles': '/app/src/styles',
      '@utils': '/app/src/utils',
      '@assets': '/app/src/assets',
      '@context': '/app/src/context',
      '@router': '/app/src/router',
      '@store': '/app/src/store',
    },
  },
});
