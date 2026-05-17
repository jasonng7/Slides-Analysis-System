const backendBase = process.env.BACKEND_API_BASE_URL || "http://13.214.251.94";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: `${backendBase.replace(/\/$/, "")}/:path*`
      }
    ];
  }
};

export default nextConfig;
