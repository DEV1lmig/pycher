import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from 'tailwindcss';

export default defineConfig({

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
