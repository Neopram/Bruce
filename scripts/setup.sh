#!/usr/bin/env bash
# =============================================================================
# BruceWayneV1 - Development Setup Script
# Sets up the local development environment
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "\n${BLUE}[STEP]${NC} $1"
}

print_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ---------------------------------------------------------------------------
# Check prerequisites
# ---------------------------------------------------------------------------

print_step "Checking prerequisites..."

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "Python is not installed. Please install Python 3.10+."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    print_error "Python 3.10+ is required. Found: $PYTHON_VERSION"
    exit 1
fi
print_ok "Python $PYTHON_VERSION"

# Check Node.js version
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 20+."
    exit 1
fi

NODE_VERSION=$(node --version | sed 's/v//')
NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)

if [ "$NODE_MAJOR" -lt 20 ]; then
    print_error "Node.js 20+ is required. Found: $NODE_VERSION"
    exit 1
fi
print_ok "Node.js $NODE_VERSION"

# Check npm
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed."
    exit 1
fi
print_ok "npm $(npm --version)"

# Check Docker (optional)
if command -v docker &> /dev/null; then
    print_ok "Docker $(docker --version | awk '{print $3}' | sed 's/,//')"
else
    print_warn "Docker is not installed. Docker deployment will not be available."
fi

# ---------------------------------------------------------------------------
# Create Python virtual environment
# ---------------------------------------------------------------------------

print_step "Setting up Python virtual environment..."

if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    print_ok "Virtual environment created at ./venv"
else
    print_ok "Virtual environment already exists at ./venv"
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

print_ok "Virtual environment activated"

# ---------------------------------------------------------------------------
# Install Python dependencies
# ---------------------------------------------------------------------------

print_step "Installing Python dependencies..."

pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# Install development tools
pip install black flake8 isort pytest pytest-cov pytest-asyncio bandit --quiet

print_ok "Python dependencies installed"

# ---------------------------------------------------------------------------
# Install Node.js dependencies
# ---------------------------------------------------------------------------

print_step "Installing Node.js dependencies..."

npm ci --silent 2>/dev/null || npm install --silent

print_ok "Node.js dependencies installed"

# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------

print_step "Setting up environment configuration..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_ok "Created .env from .env.example"
        print_warn "Please edit .env with your actual configuration values."
    else
        cat > .env << 'ENVEOF'
# BruceWayneV1 Environment Configuration
# Copy this to .env and fill in your values

# Database
DATABASE_URL=postgresql://bruce:localpassword@localhost:5432/brucewayne
POSTGRES_PASSWORD=localpassword

# Redis
REDIS_URL=redis://localhost:6379/0

# Authentication
JWT_SECRET=dev-secret-change-in-production

# AI Keys
DEEPSEEK_API_KEY=your-api-key-here

# Application
ENVIRONMENT=development
LOG_LEVEL=debug
CORS_ORIGINS=*

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
ENVEOF
        print_ok "Created .env with default development values"
        print_warn "Please edit .env with your actual API keys and configuration."
    fi
else
    print_ok ".env file already exists"
fi

# ---------------------------------------------------------------------------
# Create necessary directories
# ---------------------------------------------------------------------------

print_step "Creating project directories..."

DIRS=(
    "logs"
    "data"
    "temp"
    "output"
    "snapshots"
    "meta_reports"
    "infrastructure/nginx/ssl"
)

for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        print_ok "Created $dir/"
    fi
done

# Create .gitkeep files so empty directories are tracked
for dir in logs temp output snapshots meta_reports; do
    if [ ! -f "$dir/.gitkeep" ]; then
        touch "$dir/.gitkeep"
    fi
done

print_ok "All directories ready"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}  BruceWayneV1 Setup Complete!${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo "  To start developing:"
echo ""
echo "    1. Activate the virtual environment:"
echo "       source venv/bin/activate    (Linux/macOS)"
echo "       venv\\Scripts\\activate       (Windows)"
echo ""
echo "    2. Edit .env with your configuration"
echo ""
echo "    3. Start the development servers:"
echo "       make dev"
echo ""
echo "    Or start individually:"
echo "       make dev-backend     (API on port 8000)"
echo "       make dev-frontend    (UI on port 3000)"
echo ""
echo "  Other useful commands:"
echo "    make test     - Run tests"
echo "    make lint     - Check code style"
echo "    make format   - Auto-format code"
echo "    make help     - Show all commands"
echo ""
