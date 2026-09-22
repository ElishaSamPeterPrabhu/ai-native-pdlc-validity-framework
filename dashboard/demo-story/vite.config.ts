import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    rollupOptions: {
      input: {
        main: 'index.html',
        rolling3d: 'rolling-3d.html',
        rolling3dPhysics: 'rolling-3d-physics.html',
        rolling3dPhysicsBoost: 'rolling-3d-physics-boost.html',
      },
    },
  },
});
