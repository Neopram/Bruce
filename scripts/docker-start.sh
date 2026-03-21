#!/usr/bin/env bash
###############################################################################
# Bruce AI - Docker Start Script
# Starts all services, pulls Ollama models, and verifies health.
###############################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"
OLLAMA_MODEL="${OLLAMA_MODEL:-mistral}"

log()   { echo -e "${CYAN}[Bruce AI]${NC} $*"; }
ok()    { echo -e "${GREEN}[  OK  ]${NC} $*"; }
warn()  { echo -e "${YELLOW}[ WARN ]${NC} $*"; }
fail()  { echo -e "${RED}[ FAIL ]${NC} $*"; }

# ── Pre-flight checks ────────────────────────────────────────────────────
check_prerequisites() {
    log "Checking prerequisites..."

    if ! command -v docker &>/dev/null; then
        fail "Docker is not installed. Please install Docker first."
        exit 1
    fi
    ok "Docker found: $(docker --version)"

    if ! docker compose version &>/dev/null; then
        fail "Docker Compose V2 is not available."
        exit 1
    fi
    ok "Docker Compose found: $(docker compose version --short)"

    if ! docker info &>/dev/null 2>&1; then
        fail "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    ok "Docker daemon is running"
}

# ── Start infrastructure services first ───────────────────────────────────
start_services() {
    log "Starting Bruce AI services..."
    cd "${PROJECT_DIR}"

    # Start infrastructure first (postgres, redis, ollama)
    log "Starting infrastructure (postgres, redis, ollama)..."
    docker compose -f "${COMPOSE_FILE}" up -d postgres redis ollama
    ok "Infrastructure services started"

    # Wait for postgres and redis to be healthy
    log "Waiting for PostgreSQL to be ready..."
    local retries=30
    while [ $retries -gt 0 ]; do
        if docker compose -f "${COMPOSE_FILE}" exec -T postgres pg_isready -U bruce -d bruce_ai &>/dev/null; then
            ok "PostgreSQL is ready"
            break
        fi
        retries=$((retries - 1))
        sleep 2
    done
    if [ $retries -eq 0 ]; then
        fail "PostgreSQL failed to start within 60 seconds"
        docker compose -f "${COMPOSE_FILE}" logs postgres
        exit 1
    fi

    log "Waiting for Redis to be ready..."
    retries=15
    while [ $retries -gt 0 ]; do
        if docker compose -f "${COMPOSE_FILE}" exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
            ok "Redis is ready"
            break
        fi
        retries=$((retries - 1))
        sleep 2
    done
    if [ $retries -eq 0 ]; then
        fail "Redis failed to start"
        exit 1
    fi
}

# ── Pull Ollama model if not present ──────────────────────────────────────
ensure_ollama_model() {
    log "Checking Ollama for '${OLLAMA_MODEL}' model..."

    # Wait for Ollama to be responsive
    local retries=20
    while [ $retries -gt 0 ]; do
        if docker compose -f "${COMPOSE_FILE}" exec -T ollama curl -sf http://localhost:11434/api/tags &>/dev/null; then
            break
        fi
        retries=$((retries - 1))
        sleep 3
    done
    if [ $retries -eq 0 ]; then
        warn "Ollama is not responding. Model pull will be skipped."
        return
    fi

    # Check if model exists
    local models
    models=$(docker compose -f "${COMPOSE_FILE}" exec -T ollama curl -sf http://localhost:11434/api/tags 2>/dev/null || echo '{}')

    if echo "${models}" | grep -q "\"${OLLAMA_MODEL}"; then
        ok "Model '${OLLAMA_MODEL}' is already available"
    else
        log "Pulling '${OLLAMA_MODEL}' model (this may take a while)..."
        docker compose -f "${COMPOSE_FILE}" exec -T ollama ollama pull "${OLLAMA_MODEL}"
        if [ $? -eq 0 ]; then
            ok "Model '${OLLAMA_MODEL}' pulled successfully"
        else
            warn "Failed to pull model '${OLLAMA_MODEL}'. You can pull it later with:"
            warn "  docker compose exec ollama ollama pull ${OLLAMA_MODEL}"
        fi
    fi
}

# ── Start application services ────────────────────────────────────────────
start_app_services() {
    log "Starting application services..."
    docker compose -f "${COMPOSE_FILE}" up -d bruce-backend bruce-frontend telegram-bot nginx
    ok "Application services started"
}

# ── Wait for health checks ───────────────────────────────────────────────
wait_for_health() {
    log "Waiting for services to become healthy..."

    # Wait for backend
    local retries=30
    while [ $retries -gt 0 ]; do
        if curl -sf http://localhost:8000/health &>/dev/null; then
            ok "Backend is healthy"
            break
        fi
        retries=$((retries - 1))
        sleep 3
    done
    if [ $retries -eq 0 ]; then
        warn "Backend health check timed out"
    fi

    # Wait for frontend
    retries=20
    while [ $retries -gt 0 ]; do
        if curl -sf http://localhost:3000 &>/dev/null; then
            ok "Frontend is healthy"
            break
        fi
        retries=$((retries - 1))
        sleep 3
    done
    if [ $retries -eq 0 ]; then
        warn "Frontend health check timed out"
    fi

    # Check nginx
    retries=10
    while [ $retries -gt 0 ]; do
        if curl -sf http://localhost/health &>/dev/null; then
            ok "Nginx proxy is healthy"
            break
        fi
        retries=$((retries - 1))
        sleep 2
    done
    if [ $retries -eq 0 ]; then
        warn "Nginx health check timed out"
    fi
}

# ── Print status ─────────────────────────────────────────────────────────
print_status() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}          Bruce AI - Service Status                       ${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    docker compose -f "${COMPOSE_FILE}" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "  Frontend:   ${GREEN}http://localhost${NC}       (via nginx)"
    echo -e "  Backend:    ${GREEN}http://localhost/api${NC}   (via nginx)"
    echo -e "  API Docs:   ${GREEN}http://localhost/docs${NC}"
    echo -e "  Ollama:     ${GREEN}http://localhost:11434${NC}"
    echo -e "  PostgreSQL: ${GREEN}localhost:5432${NC}"
    echo -e "  Redis:      ${GREEN}localhost:6379${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    ok "Bruce AI is running!"
}

# ── Main ─────────────────────────────────────────────────────────────────
main() {
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║       Bruce AI - Docker Deployment            ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════╝${NC}"
    echo ""

    check_prerequisites
    start_services
    ensure_ollama_model
    start_app_services
    wait_for_health
    print_status
}

main "$@"
