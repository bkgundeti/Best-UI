// vite.config.js

export default {
  server: {
    proxy: {
      '/chat': 'http://localhost:5000',
      '/upload': 'http://localhost:5000',
      '/history': 'http://localhost:5000',
      '/login': 'http://localhost:5000',
      '/clear_chat': 'http://localhost:5000'
    }
  },
  build: {
    outDir: 'dist'
  }
};
