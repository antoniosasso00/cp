/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/v1/:path*',
      },
    ]
  },
  async redirects() {
    return [
      // 🔄 REDIRECT LEGACY /admin/* → Dashboard (v1.4.3-sidebar-roles)
      {
        source: '/admin',
        destination: '/dashboard',
        permanent: true,
      },
      {
        source: '/admin/:path*',
        destination: '/dashboard/:path*',
        permanent: true,
      },
      // 🔄 REDIRECT specifici per vecchi percorsi admin
      {
        source: '/admin/odl',
        destination: '/dashboard/shared/odl',
        permanent: true,
      },
      {
        source: '/admin/tools',
        destination: '/dashboard/management/tools',
        permanent: true,
      },
      {
        source: '/admin/catalog',
        destination: '/dashboard/shared/catalog',
        permanent: true,
      },
      {
        source: '/admin/system-logs',
        destination: '/dashboard/admin/system-logs',
        permanent: true,
      },
      {
        source: '/admin/settings',
        destination: '/dashboard/admin/settings',
        permanent: true,
      },
      // 🔄 REDIRECT per navigazione semplificata
      {
        source: '/odl',
        destination: '/dashboard/shared/odl',
        permanent: true,
      },
      {
        source: '/nesting',
        destination: '/dashboard/curing/nesting',
        permanent: true,
      },
      {
        source: '/autoclavi',
        destination: '/dashboard/curing/autoclavi',
        permanent: true,
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