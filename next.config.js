/** @type {import('next').NextConfig} */
const nextConfig = {
  // ✅ CONFIGURAZIONE SEMPLIFICATA: Solo timeout estesi per evitare UND_ERR_CONNECT_TIMEOUT
  
  // 🔧 Headers di base per CORS e caching
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          // CORS permissivi per sviluppo
          {
            key: 'Access-Control-Allow-Origin',
            value: '*'
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS'
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization'
          },
          // Cache control per API
          {
            key: 'Cache-Control',
            value: 'no-cache, no-store, must-revalidate'
          }
        ]
      }
    ]
  },

  // 🔧 Configurazioni essenziali per stabilità
  compress: true,
  poweredByHeader: false,
  
  // 🔧 Configurazioni sperimentali minime
  experimental: {
    serverMinification: false
  }
}

module.exports = nextConfig 