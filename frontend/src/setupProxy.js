const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // When running locally (npm start), use localhost
  // When running in Docker, use the backend service name
  const target = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  
  console.log('Proxy target:', target);
  
  app.use(
    '/api',
    createProxyMiddleware({
      target: target,
      changeOrigin: true,
      secure: false,
      logLevel: 'debug',
      onError: (err, req, res) => {
        console.error('Proxy error:', err.message);
        res.status(500).send('Proxy error: ' + err.message);
      },
      onProxyReq: (proxyReq, req, res) => {
        console.log('Proxying request to:', target);
      }
    })
  );
};
