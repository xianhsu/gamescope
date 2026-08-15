/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Standalone output keeps the production Docker image small.
  output: "standalone",
  // Article thumbnails come from arbitrary news domains; use plain <img> to avoid
  // per-domain allowlisting. (Documented trade-off: no next/image optimization.)
  images: { unoptimized: true },
};

export default nextConfig;
