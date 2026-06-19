#!/usr/bin/env bash
# ============================================================================
# setup_server.sh — One-time server setup for Big Bolão
#
# Configures Caddy to serve the Vue SPA + proxy /api to BigBase,
# and adds the bot's env vars to the BigBase server.
#
# Usage:
#   ./scripts/setup_server.sh root@YOUR_SERVER_IP
#
# Prerequisites:
#   1. BigBase already running on the server (setup-vps.sh was run)
#   2. bolao.bigbase.click DNS points to the server
# ============================================================================
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { printf "${GREEN}%s${NC}\n" "$1"; }
warn()  { printf "${YELLOW}%s${NC}\n" "$1"; }
err()   { printf "${RED}%s${NC}\n" "$1"; }

[ $# -lt 1 ] && { echo "Usage: $0 <ssh-host>"; exit 1; }

SSH_HOST="$1"
cd "$(dirname "$0")/.."

[ ! -f ".env" ] && { err "No .env found"; exit 1; }

info "=== Phase 1: Upload env vars ==="
python3 -c "
import os
from dotenv import load_dotenv; load_dotenv(override=True)
keys = ['TELEGRAM_TOKEN','GRUPO_CHAT_ID','ADMIN_IDS',
        'BIGBASE_URL','BIGBASE_EMAIL','BIGBASE_PASSWORD',
        'APIFOOTBALL_KEY','APIFOOTBALL_LEAGUE_ID','APIFOOTBALL_SEASON',
        'RESULTS_PROVIDER','TIMEZONE','BOLAO_WEB_URL']
with open('/tmp/bolao.env','w') as f:
    for k in keys:
        v = os.environ.get(k,'')
        if v: f.write(f'{k}={v}\n')
        else: warn(f'  {k} is empty!')
"
scp /tmp/bolao.env "${SSH_HOST}:/tmp/bolao.env"
rm -f /tmp/bolao.env

info "=== Phase 2: Server configuration ==="
ssh "${SSH_HOST}" << 'SSHEOF'
set -euo pipefail

# ── 1. Merge env vars ─────────────────────────────────────────
echo "→ Merging env vars..."
MAIN_ENV="/opt/bigbase/.env"
[ -f "$MAIN_ENV" ] && cp "$MAIN_ENV" "${MAIN_ENV}.bak.$(date +%Y%m%d-%H%M%S)"

while IFS='=' read -r key value; do
  [ -z "$key" ] || [ -z "$value" ] && continue
  if grep -q "^${key}=" "$MAIN_ENV" 2>/dev/null; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$MAIN_ENV"
  else
    echo "${key}=${value}" >> "$MAIN_ENV"
  fi
done < /tmp/bolao.env
rm -f /tmp/bolao.env
chmod 600 "$MAIN_ENV"

# ── 2. Create stable symlink to latest build ──────────────────
echo "→ Creating stable symlink..."
LATEST=$(sqlite3 /opt/bigbase/data/bigbase.db \
  "SELECT port FROM deployments WHERE url LIKE '%bolao%' ORDER BY created_at DESC LIMIT 1" 2>/dev/null || echo "")
if [ -n "$LATEST" ] && [ -d "/opt/bigbase/data/builds/${LATEST}/web/dist" ]; then
  ln -sfn "/opt/bigbase/data/builds/${LATEST}/web/dist" "/opt/bigbase/bolao-current"
  echo "  Symlink: /opt/bigbase/bolao-current → builds/${LATEST}/web/dist"
else
  echo "  WARNING: No build with web/dist found. Create the directory first, or it'll be created on first deploy."
  mkdir -p /opt/bigbase/bolao-current
fi

# ── 3. Update Caddy config ────────────────────────────────────
echo "→ Configuring Caddy..."
CADDYFILE="/etc/caddy/Caddyfile"

# Remove old bolao section if it exists
sed -i '/^# Big Bolão/,/^}/d' "$CADDYFILE" 2>/dev/null || true

cat >> "$CADDYFILE" << 'CADDYEOF'

# Big Bolão — Vue SPA + API proxy to BigBase
bolao.bigbase.click {
    # Serve Vue SPA
    handle {
        root * /opt/bigbase/bolao-current
        try_files {path} /index.html
        file_server
    }

    # Proxy API calls to BigBase
    handle /api/* {
        reverse_proxy 127.0.0.1:8080 {
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
    }
}
CADDYEOF

# ── 4. Reload Caddy ───────────────────────────────────────────
echo "→ Reloading Caddy..."
caddy reload --config "$CADDYFILE" 2>/dev/null || systemctl reload caddy 2>/dev/null || true

# ── 5. Create deploy hook to update symlink on each deploy ────
echo "→ Creating deploy hook..."
HOOK_SCRIPT="/opt/bigbase/update-bolao-symlink.sh"
cat > "$HOOK_SCRIPT" << 'HOOK'
#!/usr/bin/env bash
# Called by BigBase deploy system after each deploy
# Updates the stable symlink to point to the latest build's web/dist
set -euo pipefail
LATEST_PORT=$(sqlite3 /opt/bigbase/data/bigbase.db \
  "SELECT port FROM deployments WHERE url LIKE '%bolao%' ORDER BY created_at DESC LIMIT 1" 2>/dev/null || echo "")
if [ -n "$LATEST_PORT" ] && [ -d "/opt/bigbase/data/builds/${LATEST_PORT}/web/dist" ]; then
  ln -sfn "/opt/bigbase/data/builds/${LATEST_PORT}/web/dist" "/opt/bigbase/bolao-current"
  echo "Symlink updated to build ${LATEST_PORT}"
fi
HOOK
chmod +x "$HOOK_SCRIPT"

# ── 6. Restart BigBase ────────────────────────────────────────
echo "→ Restarting BigBase..."
systemctl restart bigbase
sleep 5

if systemctl is-active --quiet bigbase; then
  echo "✓ BigBase restarted OK"
else
  err "BigBase failed to restart — check journalctl -u bigbase -f"
  exit 1
fi

echo ""
echo "=== SERVER SETUP COMPLETE ==="
echo "  Env vars added to /opt/bigbase/.env"
echo "  Caddy configured for bolao.bigbase.click"
echo "  Deploy hook at ${HOOK_SCRIPT}"
echo ""
echo "Next: trigger a redeploy from your machine:"
echo "  python3 -m scripts.redeploy"
SSHEOF

info "=== DONE ==="
