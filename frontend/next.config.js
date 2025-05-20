/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/v1/:path*',
        destination: 'http://backend:8000/v1/:path*',
      },
    ]
  },
}

module.exports = nextConfig 