#!/bin/bash
# =============================================================================
# Bruce AI - Oracle Cloud Free Tier Setup
# Run this on a fresh Ubuntu 22.04 ARM (Ampere A1) VM
#
# Oracle Always Free Tier: 4 ARM cores, 24GB RAM, 200GB storage
#
# Usage:
#   chmod +x oracle_setup.sh
#   ./oracle_setup.sh
# =============================================================================

set -euo pipefail

# -- Colors for output --------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[BRUCE]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# -- Pre-flight checks --------------------------------------------------------
if [[ $EUID -eq 0 ]]; then
    err "Do not run this script as root. Run as the 'ubuntu' user."
    exit 1
fi

ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" ]]; then
    warn "Expected aarch64 (ARM), detected $ARCH. Proceeding anyway."
fi

INSTALL_DIR="/opt/bruce"
BRUCE_USER="${USER}"

log "Starting Bruce AI deployment on Oracle Cloud Free Tier"
log "Architecture: $ARCH | User: $BRUCE_USER"
echo ""

# -- 1. System update ---------------------------------------------------------
log "Updating system packages..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    build-essential \
    curl \
    wget \
    git \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    jq \
    htop

# -- 2. Python 3.12 -----------------------------------------------------------
log "Installing Python 3.12..."
if ! command -v python3.12 &>/dev/null; then
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    sudo apt install -y python3.12 python3.12-venv python3.12-dev python3.12-distutils
    curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.12
else
    log "Python 3.12 already installed."
fi
python3.12 --version

# -- 3. Node.js 20 ------------------------------------------------------------
log "Installing Node.js 20 LTS..."
if ! command -v node &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
else
    log "Node.js already installed."
fi
node --version
npm --version

# -- 4. Ollama (ARM native) ---------------------------------------------------
log "Installing Ollama..."
if ! command -v ollama &>/dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
else
    log "Ollama already installed."
fi

log "Starting Ollama service..."
sudo systemctl enable ollama
sudo systemctl start ollama
sleep 3

log "Pulling Qwen2.5:7b model (this may take several minutes)..."
ollama pull qwen2.5:7b

# -- 5. Docker -----------------------------------------------------------------
log "Installing Docker..."
if ! command -v docker &>/dev/null; then
    sudo apt install -y docker.io docker-compose-v2
    sudo usermod -aG docker "$BRUCE_USER"
    sudo systemctl enable docker
    sudo systemctl start docker
else
    log "Docker already installed."
fi

# -- 6. Clone / Update Bruce --------------------------------------------------
log "Setting up Bruce at $INSTALL_DIR..."
if [[ -d "$INSTALL_DIR" ]]; then
    warn "$INSTALL_DIR already exists. Pulling latest..."
    cd "$INSTALL_DIR"
    git pull origin main || true
else
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown "$BRUCE_USER":"$BRUCE_USER" "$INSTALL_DIR"
    git clone https://github.com/Neopram/Bruce.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# -- 7. Python virtual environment --------------------------------------------
log "Creating Python virtual environment..."
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# -- 8. Environment file -------------------------------------------------------
if [[ ! -f "$INSTALL_DIR/.env" ]]; then
    log "Creating .env template..."
    cat > "$INSTALL_DIR/.env" << 'ENVEOF'
# Bruce AI Environment Configuration
# Fill in your actual values below

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# LLM
OLLAMA_HOST=http://localhost:11434
PRIMARY_MODEL=qwen2.5:7b

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
ENVEOF
    warn "Edit /opt/bruce/.env with your actual credentials before starting services!"
else
    log ".env already exists, skipping."
fi

# -- 9. Systemd services -------------------------------------------------------
log "Creating systemd service files..."

# Bruce Backend API
sudo tee /etc/systemd/system/bruce-backend.service > /dev/null << SVCEOF
[Unit]
Description=Bruce AI Backend
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=$BRUCE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=bruce-backend

[Install]
WantedBy=multi-user.target
SVCEOF

# Bruce Telegram Bot
sudo tee /etc/systemd/system/bruce-telegram.service > /dev/null << SVCEOF
[Unit]
Description=Bruce AI Telegram Bot
After=bruce-backend.service
Wants=bruce-backend.service

[Service]
Type=simple
User=$BRUCE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/python -m modules.telegram_bot
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=bruce-telegram

[Install]
WantedBy=multi-user.target
SVCEOF

# Bruce Scheduler
sudo tee /etc/systemd/system/bruce-scheduler.service > /dev/null << SVCEOF
[Unit]
Description=Bruce AI Scheduler
After=bruce-backend.service
Wants=bruce-backend.service

[Service]
Type=simple
User=$BRUCE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/python -c "import asyncio; from modules.scheduler import start_scheduler; asyncio.run(start_scheduler())"
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=bruce-scheduler

[Install]
WantedBy=multi-user.target
SVCEOF

# -- 10. Nginx reverse proxy ---------------------------------------------------
log "Setting up Nginx reverse proxy..."
sudo apt install -y nginx

sudo tee /etc/nginx/sites-available/bruce > /dev/null << 'NGINXEOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
NGINXEOF

sudo ln -sf /etc/nginx/sites-available/bruce /etc/nginx/sites-enabled/bruce
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

# -- 11. Firewall (Oracle Cloud + UFW) -----------------------------------------
log "Configuring firewall..."
sudo apt install -y iptables-persistent || true

# Oracle Cloud uses iptables by default; open ports there too
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
sudo netfilter-persistent save 2>/dev/null || true

# Also configure UFW as a secondary layer
if command -v ufw &>/dev/null; then
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 8000/tcp
    echo "y" | sudo ufw enable || true
fi

# -- 12. Enable and start services --------------------------------------------
log "Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable bruce-backend bruce-telegram bruce-scheduler

# Start backend first, give it time to initialize
sudo systemctl start bruce-backend
sleep 5

# Check if .env has real tokens before starting telegram
if grep -q "your_bot_token_here" "$INSTALL_DIR/.env" 2>/dev/null; then
    warn "Telegram bot NOT started - update .env with real TELEGRAM_BOT_TOKEN first."
    warn "Then run: sudo systemctl start bruce-telegram"
else
    sudo systemctl start bruce-telegram
fi

sudo systemctl start bruce-scheduler

# -- 13. Swap file (recommended for 7B model) ---------------------------------
log "Setting up swap space..."
if [[ ! -f /swapfile ]]; then
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    log "4GB swap file created."
else
    log "Swap file already exists."
fi

# -- Summary -------------------------------------------------------------------
echo ""
echo "============================================================================="
log "Bruce AI deployment complete!"
echo "============================================================================="
echo ""
echo "  Public IP:       $(curl -s --connect-timeout 5 ifconfig.me 2>/dev/null || echo 'N/A')"
echo "  Backend API:     http://$(curl -s --connect-timeout 5 ifconfig.me 2>/dev/null || echo 'YOUR_IP'):8000"
echo "  Nginx proxy:     http://$(curl -s --connect-timeout 5 ifconfig.me 2>/dev/null || echo 'YOUR_IP')"
echo "  Ollama:          http://localhost:11434"
echo ""
echo "  Config file:     $INSTALL_DIR/.env"
echo "  Logs:            journalctl -u bruce-backend -f"
echo ""
echo "  Services:"
echo "    bruce-backend   $(systemctl is-active bruce-backend 2>/dev/null || echo 'unknown')"
echo "    bruce-telegram  $(systemctl is-active bruce-telegram 2>/dev/null || echo 'unknown')"
echo "    bruce-scheduler $(systemctl is-active bruce-scheduler 2>/dev/null || echo 'unknown')"
echo "    ollama          $(systemctl is-active ollama 2>/dev/null || echo 'unknown')"
echo "    nginx           $(systemctl is-active nginx 2>/dev/null || echo 'unknown')"
echo ""
echo "  Next steps:"
echo "    1. Edit /opt/bruce/.env with your Telegram tokens"
echo "    2. sudo systemctl restart bruce-telegram"
echo "    3. Open Oracle Cloud Console > Networking > Security Lists"
echo "       and add ingress rules for ports 80 and 443"
echo "============================================================================="
