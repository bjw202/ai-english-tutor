import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable React strict mode for better development experience
  reactStrictMode: true,

  // Configure image domains (if needed for future)
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },

  // Experimental features for Next.js 15
  experimental: {
    // Optimize package imports
    optimizePackageImports: ["@/components"],
  },

  // Environment variables accessible to the client
  env: {
    BACKEND_URL: process.env.BACKEND_URL || "http://localhost:8000",
  },
};

export default nextConfig;
