import { defineConfig, Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { spawn, ChildProcess } from 'child_process';
import path from 'path';

function phpBackendPlugin(): Plugin {
  let phpProcess: ChildProcess | null = null;

  return {
    name: 'php-backend-launcher',
    configureServer(server) {
      if (process.env.VITEST || process.env.NODE_ENV === 'test') {
        return;
      }
      const backendPort = process.env.PHP_PORT || '8000';
      const backendEntry = path.resolve(__dirname, 'backend/index.php');
      const migrateScript = path.resolve(__dirname, 'backend/migrate_and_seed.php');

      try {
        const mig = spawn('php', [migrateScript], { stdio: 'inherit' });
        mig.on('close', (code) => {
          if (code === 0) {
            console.log(`\n🚀 [Vite:PHP] Spawning PHP SQLite Backend on http://127.0.0.1:${backendPort}...`);
            phpProcess = spawn('php', ['-S', `127.0.0.1:${backendPort}`, backendEntry], {
              stdio: 'inherit',
            });

            phpProcess.on('error', (err) => {
              console.warn('⚠️ [Vite:PHP] Failed to spawn PHP backend:', err.message);
            });
          }
        });
      } catch (err: any) {
        console.warn('⚠️ [Vite:PHP] PHP runner error:', err.message);
      }

      const cleanUp = () => {
        if (phpProcess) {
          console.log('\n🛑 [Vite:PHP] Stopping PHP backend process...');
          phpProcess.kill();
          phpProcess = null;
        }
      };

      process.on('exit', cleanUp);
      process.on('SIGINT', () => {
        cleanUp();
        process.exit();
      });
      process.on('SIGTERM', () => {
        cleanUp();
        process.exit();
      });
      server.httpServer?.on('close', cleanUp);
    },
  };
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), phpBackendPlugin()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: process.env.NODE_ENV === 'development',
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['react', 'react-dom'],
          'db': ['dexie', 'dexie-react-hooks'],
          'ui': ['lucide-react'],
        },
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
});
