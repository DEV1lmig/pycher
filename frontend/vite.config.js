import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from 'tailwindcss';

export default defineConfig({

  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': '/src',
      '@components': '/components',
      '@hooks': '/hooks',
      '@lib': '/lib',
      '@pages': '/pages',
      '@services': '/services',
      '@styles': '/styles',
      '@utils': '/utils',
      '@assets': '/assets',
      '@context': '/context',
      '@router': '/router',
      '@store': '/store',
    },
  },
});
