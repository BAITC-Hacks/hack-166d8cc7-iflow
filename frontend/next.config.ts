import type { NextConfig } from 'next';
const backend = (process.env.BACKEND_INTERNAL_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');
const config: NextConfig = {
  output: 'standalone',
  devIndicators: false,
  async rewrites() {
    return [{ source: '/backend/:path*', destination: `${backend}/:path*` }];
  },
};
export default config;
