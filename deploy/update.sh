#!/bin/bash
# =============================================================================
# Bruce AI - Update Script
# Pull latest code and restart all services
#
# Usage:
#   chmod +x update.sh
#   ./update.sh
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[BRUCE]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }

INSTALL_DIR="/opt/bruce"

if [[ ! -d "$INSTALL_DIR" ]]; then
    err "Bruce not found at $INSTALL_DIR. Run oracle_setup.sh first."
    exit 1
fi

cd "$INSTALL_DIR"

# -- Save current commit for rollback info ------------------------------------
OLD_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
log "Current version: $OLD_COMMIT"

# -- Pull latest code ---------------------------------------------------------
log "Pulling latest code from main..."
git stash --include-untracked 2>/dev/null || true
if ! git pull origin main; then
    err "Git pull failed. Check for conflicts."
    git stash pop 2>/dev/null || true
    exit 1
fi
git stash pop 2>/dev/null || true

NEW_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
log "Updated to: $NEW_COMMIT"

if [[ "$OLD_COMMIT" == "$NEW_COMMIT" ]]; then
    log "Already up to date. Restarting services anyway."
fi

# -- Update Python dependencies ------------------------------------------------
log "Updating Python dependencies..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# -- Restart services ----------------------------------------------------------
log "Restarting Bruce services..."
sudo systemctl daemon-reload
sudo systemctl restart bruce-backend
sleep 3

# Only restart telegram if it was running
if systemctl is-active --quiet bruce-telegram; then
    sudo systemctl restart bruce-telegram
    log "Telegram bot restarted."
else
    warn "Telegram bot was not running, skipping restart."
fi

sudo systemctl restart bruce-scheduler

# -- Verify services are running -----------------------------------------------
sleep 5
echo ""
FAIL=0
for svc in bruce-backend bruce-scheduler ollama nginx; do
    STATUS=$(systemctl is-active "$svc" 2>/dev/null || echo "inactive")
    if [[ "$STATUS" == "active" ]]; then
        log "$svc: ${GREEN}active${NC}"
    else
        err "$svc: $STATUS"
        FAIL=1
    fi
done

# Check telegram separately (might be intentionally stopped)
TEL_STATUS=$(systemctl is-active bruce-telegram 2>/dev/null || echo "inactive")
if [[ "$TEL_STATUS" == "active" ]]; then
    log "bruce-telegram: ${GREEN}active${NC}"
else
    warn "bruce-telegram: $TEL_STATUS (check .env if this is unexpected)"
fi

# -- Health check --------------------------------------------------------------
log "Running health check..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:8000/health 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" == "200" ]]; then
    log "Backend health check: OK (HTTP $HTTP_CODE)"
else
    warn "Backend health check returned HTTP $HTTP_CODE"
    FAIL=1
fi

echo ""
if [[ $FAIL -eq 0 ]]; then
    log "Update complete! $OLD_COMMIT -> $NEW_COMMIT"
else
    err "Update finished with warnings. Check logs: journalctl -u bruce-backend -n 50"
fi
