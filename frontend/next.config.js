/** @type {import('next').NextConfig} */
const nextConfig = {
  // Modo estricto de React: útil para desarrollo y debugging
  reactStrictMode: true,

  // Variables de entorno inyectadas al frontend en tiempo de build
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  },

  // Permite la nueva arquitectura de Next.js con carpeta /app
 // experimental: { appDir: true }


  // ✅ Preparamos para futuro uso con Docker sin activarlo aún
  // output: 'standalone' // lo habilitaremos más adelante en producción
};

module.exports = nextConfig;
