import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  compiler: {
    removeConsole: process.env.NODE_ENV === "production",
  },
  images: {
    domains: ['localhost'],
    unoptimized: process.env.NODE_ENV === "development",
    localPatterns: [
        {
          pathname: '/assets/images/**',
          search: '',
        },
      ],
  },
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['@heroicons/react', '@mui/material'],
  }
};

export default nextConfig;
