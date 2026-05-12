/** @type {import('next').NextConfig} */
// Force rebuild - v1.0.1
const nextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  optimizeFonts: false,
  basePath: process.env.NODE_ENV === "production" ? "/NEXUS-MIND" : "",
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: "pk_live_Y2xlcmsuOTA3LWJvdC5naXRodWIuaW8k",
  },
};

module.exports = nextConfig;
