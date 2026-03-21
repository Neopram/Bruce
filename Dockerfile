# Etapa 1: Construcción de la app
FROM node:20-alpine AS builder

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar package.json y lock para caché de dependencias
COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./

# Instalar dependencias (usa pnpm, yarn o npm según corresponda)
RUN npm install

# Copiar todo el proyecto
COPY . .

# Construir la app de producción
RUN npm run build

---

# Etapa 2: Servidor para producción (Next.js optimizado)
FROM node:20-alpine AS runner

WORKDIR /app

# Importar solo los archivos necesarios del builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.js ./next.config.js
COPY --from=builder /app/tailwind.config.js ./tailwind.config.js
COPY --from=builder /app/postcss.config.js ./postcss.config.js
COPY --from=builder /app/tsconfig.json ./tsconfig.json

# Exponer el puerto estándar
EXPOSE 3000

# Arrancar el servidor optimizado de Next.js
CMD ["npm", "start"]
