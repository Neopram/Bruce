#!/bin/bash
# =============================================================================
# Bruce AI - Health Monitor
# Checks all services, resources, and sends Telegram alerts if problems found
#
# Usage:
#   chmod +x monitor.sh
#   ./monitor.sh                    # Run once
#   ./monitor.sh --quiet            # Only output on errors
#   ./monitor.sh --no-alert         # Skip Telegram alerts
#
# Cron (run every 5 minutes):
#   */5 * * * * /opt/bruce/deploy/monitor.sh --quiet >> /var/log/bruce-monitor.log 2>&1
# =============================================================================

set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

QUIET=false
SEND_ALERTS=true
INSTALL_DIR="/opt/bruce"
PROBLEMS=()
WARNINGS=()

for arg in "$@"; do
    case "$arg" in
        --quiet)    QUIET=true ;;
        --no-alert) SEND_ALERTS=false ;;
    esac
done

log()  { [[ "$QUIET" == true ]] || echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; WARNINGS+=("$*"); }
err()  { echo -e "${RED}[FAIL]${NC} $*"; PROBLEMS+=("$*"); }

# -- Load .env for Telegram credentials ----------------------------------------
if [[ -f "$INSTALL_DIR/.env" ]]; then
    set -a
    source "$INSTALL_DIR/.env" 2>/dev/null || true
    set +a
fi

# -- Send Telegram alert -------------------------------------------------------
send_telegram_alert() {
    local message="$1"
    if [[ "$SEND_ALERTS" != true ]]; then
        return
    fi
    if [[ -z "${TELEGRAM_BOT_TOKEN:-}" || -z "${TELEGRAM_CHAT_ID:-}" ]]; then
        [[ "$QUIET" == true ]] || echo "Telegram credentials not configured, skipping alert."
        return
    fi
    if [[ "${TELEGRAM_BOT_TOKEN}" == "your_bot_token_here" ]]; then
        return
    fi

    curl -s -X POST \
        "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d "chat_id=${TELEGRAM_CHAT_ID}" \
        -d "parse_mode=HTML" \
        -d "text=${message}" \
        > /dev/null 2>&1 || true
}

# ==============================================================================
# CHECKS
# ==============================================================================

[[ "$QUIET" == true ]] || echo "=== Bruce AI Health Check - $(date '+%Y-%m-%d %H:%M:%S') ==="
echo ""

# -- 1. Systemd services -------------------------------------------------------
[[ "$QUIET" == true ]] || echo "--- Services ---"

SERVICES=("ollama" "bruce-backend" "bruce-telegram" "bruce-scheduler" "nginx")
for svc in "${SERVICES[@]}"; do
    STATUS=$(systemctl is-active "$svc" 2>/dev/null || echo "not-found")
    if [[ "$STATUS" == "active" ]]; then
        log "$svc is running"
    elif [[ "$svc" == "bruce-telegram" && "$STATUS" != "active" ]]; then
        # Telegram might be intentionally stopped
        warn "$svc is $STATUS (may need .env configuration)"
    else
        err "$svc is $STATUS"
    fi
done

# -- 2. Backend HTTP health check ----------------------------------------------
[[ "$QUIET" == true ]] || echo ""
[[ "$QUIET" == true ]] || echo "--- Backend API ---"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 http://localhost:8000/health 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" == "200" ]]; then
    log "Backend API responding (HTTP $HTTP_CODE)"
else
    err "Backend API not responding (HTTP $HTTP_CODE)"
fi

# -- 3. Ollama model check -----------------------------------------------------
[[ "$QUIET" == true ]] || echo ""
[[ "$QUIET" == true ]] || echo "--- Ollama ---"

if command -v ollama &>/dev/null; then
    MODELS=$(ollama list 2>/dev/null || echo "")
    if echo "$MODELS" | grep -q "qwen2.5:7b"; then
        log "qwen2.5:7b model is available"
    else
        err "qwen2.5:7b model not found. Run: ollama pull qwen2.5:7b"
    fi

    OLLAMA_HTTP=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:11434/api/tags 2>/dev/null || echo "000")
    if [[ "$OLLAMA_HTTP" == "200" ]]; then
        log "Ollama API responding"
    else
        err "Ollama API not responding on port 11434"
    fi
else
    err "Ollama not installed"
fi

# -- 4. Disk space -------------------------------------------------------------
[[ "$QUIET" == true ]] || echo ""
[[ "$QUIET" == true ]] || echo "--- Disk Space ---"

DISK_USAGE=$(df / --output=pcent 2>/dev/null | tail -1 | tr -d '% ')
if [[ -n "$DISK_USAGE" ]]; then
    if (( DISK_USAGE >= 90 )); then
        err "Disk usage critical: ${DISK_USAGE}%"
    elif (( DISK_USAGE >= 80 )); then
        warn "Disk usage high: ${DISK_USAGE}%"
    else
        log "Disk usage: ${DISK_USAGE}%"
    fi
fi

# Check /opt/bruce size
BRUCE_SIZE=$(du -sh "$INSTALL_DIR" 2>/dev/null | cut -f1 || echo "N/A")
log "Bruce install size: $BRUCE_SIZE"

# -- 5. Memory usage -----------------------------------------------------------
[[ "$QUIET" == true ]] || echo ""
[[ "$QUIET" == true ]] || echo "--- Memory ---"

MEM_TOTAL=$(free -m 2>/dev/null | awk '/^Mem:/{print $2}')
MEM_USED=$(free -m 2>/dev/null | awk '/^Mem:/{print $3}')
MEM_AVAIL=$(free -m 2>/dev/null | awk '/^Mem:/{print $7}')
SWAP_USED=$(free -m 2>/dev/null | awk '/^Swap:/{print $3}')

if [[ -n "$MEM_TOTAL" && -n "$MEM_USED" ]]; then
    MEM_PCT=$(( MEM_USED * 100 / MEM_TOTAL ))
    if (( MEM_PCT >= 95 )); then
        err "Memory critical: ${MEM_USED}MB / ${MEM_TOTAL}MB (${MEM_PCT}%)"
    elif (( MEM_PCT >= 85 )); then
        warn "Memory high: ${MEM_USED}MB / ${MEM_TOTAL}MB (${MEM_PCT}%)"
    else
        log "Memory: ${MEM_USED}MB / ${MEM_TOTAL}MB (${MEM_PCT}%) | Available: ${MEM_AVAIL}MB"
    fi
    log "Swap used: ${SWAP_USED}MB"
fi

# -- 6. CPU load ---------------------------------------------------------------
[[ "$QUIET" == true ]] || echo ""
[[ "$QUIET" == true ]] || echo "--- CPU ---"

LOAD_1=$(cat /proc/loadavg 2>/dev/null | awk '{print $1}')
NPROC=$(nproc 2>/dev/null || echo 4)
if [[ -n "$LOAD_1" ]]; then
    LOAD_INT=${LOAD_1%.*}
    if (( LOAD_INT >= NPROC * 2 )); then
        err "CPU load very high: $LOAD_1 (${NPROC} cores)"
    elif (( LOAD_INT >= NPROC )); then
        warn "CPU load high: $LOAD_1 (${NPROC} cores)"
    else
        log "CPU load: $LOAD_1 (${NPROC} cores)"
    fi
fi

# -- 7. Recent service crashes -------------------------------------------------
[[ "$QUIET" == true ]] || echo ""
[[ "$QUIET" == true ]] || echo "--- Recent Errors ---"

for svc in bruce-backend bruce-telegram bruce-scheduler; do
    ERRORS=$(journalctl -u "$svc" --since "1 hour ago" --priority=err --no-pager -q 2>/dev/null | wc -l)
    if (( ERRORS > 0 )); then
        warn "$svc has $ERRORS error(s) in the last hour"
    else
        log "$svc: no errors in the last hour"
    fi
done

# ==============================================================================
# SUMMARY AND ALERTS
# ==============================================================================

echo ""
echo "=== Summary ==="

if [[ ${#PROBLEMS[@]} -eq 0 && ${#WARNINGS[@]} -eq 0 ]]; then
    log "All checks passed. Bruce is healthy."
    exit 0
fi

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}Warnings: ${#WARNINGS[@]}${NC}"
    for w in "${WARNINGS[@]}"; do
        echo "  - $w"
    done
fi

if [[ ${#PROBLEMS[@]} -gt 0 ]]; then
    echo -e "${RED}Problems: ${#PROBLEMS[@]}${NC}"
    for p in "${PROBLEMS[@]}"; do
        echo "  - $p"
    done

    # Build Telegram alert message
    ALERT_MSG="<b>Bruce AI Alert</b>%0A%0A"
    ALERT_MSG+="<b>Problems (${#PROBLEMS[@]}):</b>%0A"
    for p in "${PROBLEMS[@]}"; do
        ALERT_MSG+="- ${p}%0A"
    done
    if [[ ${#WARNINGS[@]} -gt 0 ]]; then
        ALERT_MSG+="%0A<b>Warnings (${#WARNINGS[@]}):</b>%0A"
        for w in "${WARNINGS[@]}"; do
            ALERT_MSG+="- ${w}%0A"
        done
    fi
    ALERT_MSG+="%0AServer: $(hostname) | $(date '+%H:%M:%S')"

    send_telegram_alert "$ALERT_MSG"
    [[ "$QUIET" == true ]] || echo ""
    [[ "$QUIET" == true ]] || echo "Telegram alert sent (if configured)."

    exit 1
fi

exit 0
