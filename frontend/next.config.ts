import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  basePath: "/BOQ-2.0",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
