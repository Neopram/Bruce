#!/bin/bash
# Generate self-signed SSL certificates for Bruce AI development
# Usage: bash scripts/generate_ssl.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SSL_DIR="$PROJECT_ROOT/infrastructure/nginx/ssl"

DAYS_VALID=365
KEY_SIZE=2048
COUNTRY="US"
STATE="California"
LOCALITY="San Francisco"
ORG="BruceAI"
CN="localhost"

echo "============================================================"
echo " Bruce AI -- Self-Signed SSL Certificate Generator"
echo "============================================================"
echo ""

# Create output directory
mkdir -p "$SSL_DIR"
echo "[1/3] Created directory: $SSL_DIR"

# Generate private key
openssl genrsa -out "$SSL_DIR/privkey.pem" "$KEY_SIZE" 2>/dev/null
echo "[2/3] Generated private key: $SSL_DIR/privkey.pem ($KEY_SIZE-bit RSA)"

# Generate self-signed certificate
openssl req -new -x509 \
    -key "$SSL_DIR/privkey.pem" \
    -out "$SSL_DIR/fullchain.pem" \
    -days "$DAYS_VALID" \
    -subj "/C=$COUNTRY/ST=$STATE/L=$LOCALITY/O=$ORG/CN=$CN" \
    -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1" \
    2>/dev/null
echo "[3/3] Generated self-signed certificate: $SSL_DIR/fullchain.pem (valid $DAYS_VALID days)"

echo ""
echo "============================================================"
echo " SSL files created:"
echo "   Private key  : $SSL_DIR/privkey.pem"
echo "   Certificate  : $SSL_DIR/fullchain.pem"
echo "============================================================"
echo ""
echo " These certificates are for DEVELOPMENT ONLY."
echo " Browsers will show a security warning -- this is expected."
echo ""
echo " For production, use Let's Encrypt (free, auto-renewing):"
echo "   1. Install certbot:  sudo apt install certbot python3-certbot-nginx"
echo "   2. Obtain certs:     sudo certbot --nginx -d yourdomain.com"
echo "   3. Auto-renew:       sudo certbot renew --dry-run"
echo "   4. Certs stored at:  /etc/letsencrypt/live/yourdomain.com/"
echo ""
echo " Or use the Nginx proxy manager with built-in Let's Encrypt support."
echo "============================================================"
