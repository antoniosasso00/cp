/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://carbonpilot-backend:8000/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig 