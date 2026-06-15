import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8001/:path*",
      },
      {
        source: "/storage/:path*",
        destination: "http://localhost:8001/storage/:path*",
      },
    ];
  },
};

export default nextConfig;
