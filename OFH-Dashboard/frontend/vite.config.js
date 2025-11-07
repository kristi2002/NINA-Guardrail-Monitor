import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // CDN configuration - set VITE_CDN_BASE_URL in environment for CDN deployment
  base: process.env.VITE_CDN_BASE_URL || '/',
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      },
      '/socket.io': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        ws: true,  // Enable WebSocket proxying
        secure: false,  // For local development
        rewrite: (path) => path,  // Keep the /socket.io path
        configure: (proxy, _options) => {
          // Handle proxy errors gracefully (connection resets are normal)
          proxy.on('error', (err, req, res) => {
            // ECONNRESET and ECONNREFUSED are common during development (server restarts, client disconnects)
            if (err.code === 'ECONNRESET' || err.code === 'ECONNREFUSED') {
              // Silently handle connection resets - these are normal
              return;
            }
            // Only log unexpected errors
            if (process.env.NODE_ENV === 'development') {
              console.warn('Socket.IO proxy error:', err.message || err.code);
            }
          });
          
          // Handle WebSocket-specific errors
          proxy.on('proxyReqWs', (proxyReq, req, socket) => {
            // Handle socket errors (connection resets during WebSocket upgrade)
            socket.on('error', (err) => {
              // ECONNRESET is normal when client disconnects or server restarts
              if (err.code !== 'ECONNRESET' && err.code !== 'EPIPE') {
                if (process.env.NODE_ENV === 'development') {
                  console.warn('Socket.IO WebSocket socket error:', err.message || err.code);
                }
              }
            });
          });
          
          // Handle WebSocket upgrade errors
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // Handle errors during HTTP upgrade to WebSocket
            proxyReq.on('error', (err) => {
              if (err.code !== 'ECONNRESET' && err.code !== 'ECONNREFUSED') {
                if (process.env.NODE_ENV === 'development') {
                  console.warn('Socket.IO proxy request error:', err.message || err.code);
                }
              }
            });
          });
        }
      }
    }
  },
  build: {
    // Optimize bundle size
    minify: 'esbuild', // Fast and efficient minification
    target: 'es2015', // Target modern browsers for smaller bundles
    rollupOptions: {
      output: {
        // Manual chunk splitting for better caching
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'chart-vendor': ['recharts'],
          'socket-vendor': ['socket.io-client']
        },
        // Optimize chunk file names
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]'
      }
    },
    // Increase chunk size warning limit (Vite default is 500KB)
    chunkSizeWarningLimit: 1000,
    // Enable source maps for production debugging (optional)
    sourcemap: false
  }
})

