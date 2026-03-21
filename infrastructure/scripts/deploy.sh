
#!/bin/bash
echo "🚀 Iniciando despliegue de OKK Gorilla Bot..."
docker-compose down
docker-compose pull
docker-compose up -d --build
echo "✅ Despliegue completo."
