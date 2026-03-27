import type { NextConfig } from "next"

const isDevelopment = process.env.NODE_ENV === "development"

const nextConfig: NextConfig = {
  skipTrailingSlashRedirect: true,

  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },

      // Google Drive
      {
        protocol: "https",
        hostname: "drive.google.com",
      },

      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com",
      },
    ],
  },

  async rewrites() {
    if (!isDevelopment) {
      return []
    }

    return {
      beforeFiles: [
        {
          source: "/api/system/plans/admin",
          destination: "http://127.0.0.1:8000/api/system/plans/admin/",
        },
        {
          source: "/api/system/plans/admin/",
          destination: "http://127.0.0.1:8000/api/system/plans/admin/",
        },
        {
          source: "/ws/system/notifications",
          destination: "http://127.0.0.1:8000/ws/system/notifications/",
        },
        {
          source: "/ws/system/notifications/",
          destination: "http://127.0.0.1:8000/ws/system/notifications/",
        },
        {
          source: "/api/:path*",
          destination: "http://127.0.0.1:8000/api/:path*",
        },
        {
          source: "/ws/:path*",
          destination: "http://127.0.0.1:8000/ws/:path*",
        },
      ],
    }
  },
}

export default nextConfig