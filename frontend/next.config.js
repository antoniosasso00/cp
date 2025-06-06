/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  experimental: {
    serverComponentsExternalPackages: [],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
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