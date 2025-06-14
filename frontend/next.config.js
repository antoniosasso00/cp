/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  experimental: {
    serverComponentsExternalPackages: [],
  },
  // 🔧 FIX TIMEOUT: Configurazione proxy con timeout esteso per algoritmi 2L
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ]
  },
  // 🚀 NUOVO: Configurazione server per timeout estesi
  serverRuntimeConfig: {
    // Timeout per richieste API proxy (10 minuti per algoritmi complessi)
    apiTimeout: 600000, // 10 minuti in millisecondi
  },
  // 🔧 FIX: Headers personalizzati per timeout
  async headers() {
    return [
      {
        source: '/api/batch_nesting/:path*',
        headers: [
          {
            key: 'X-Timeout',
            value: '600000', // 10 minuti per endpoint nesting
          },
        ],
      },
    ]
  },
  webpack: (config, { isServer }) => {
    // Escludi canvas e konva dal server-side rendering
    if (isServer) {
      config.externals.push('canvas', 'konva')
    }
    
    // Configura fallback per moduli Node.js
    config.resolve.fallback = {
      ...config.resolve.fallback,
      canvas: false,
      fs: false,
    }
    
    return config
  },
}

module.exports = nextConfig 