#!/usr/bin/env bash
# ============================================================================
# setup_server.sh — Configure Big Bolão on the BigBase server
#
# Creates /opt/bolao/.env with secrets and adds bolao.bigbase.click to Caddy.
# Does NOT touch the BigBase installation (/opt/bigbase/).
#
# Usage:
#   ./scripts/setup_server.sh root@YOUR_SERVER_IP
# ============================================================================
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { printf "${GREEN}%s${NC}\n" "$1"; }
warn()  { printf "${YELLOW}%s${NC}\n" "$1"; }
err()   { printf "${RED}%s${NC}\n" "$1"; }

[ $# -lt 1 ] && { echo "Usage: $0 <ssh-host>"; exit 1; }

SSH_HOST="$1"
cd "$(dirname "$0")/.."

[ ! -f ".env" ] && { err "No .env found in project root"; exit 1; }

info "=== Phase 1: Extract env vars ==="
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
"
scp /tmp/bolao.env "${SSH_HOST}:/tmp/bolao.env"
rm -f /tmp/bolao.env

info "=== Phase 2: Install on server ==="
ssh "${SSH_HOST}" << 'SSHEOF'
set -euo pipefail

BOLAO_DIR="/opt/bolao"

# ── 1. Create /opt/bolao/ with .env ───────────────────────────
echo "→ Creating ${BOLAO_DIR}..."
mkdir -p "$BOLAO_DIR"
cp /tmp/bolao.env "${BOLAO_DIR}/.env"
chmod 600 "${BOLAO_DIR}/.env"
rm -f /tmp/bolao.env
echo "  .env written with $(wc -l < "${BOLAO_DIR}/.env") vars"

# ── 2. Create symlink for latest build ────────────────────────
echo "→ Creating stable symlink..."
LATEST_PORT=$(sqlite3 /opt/bigbase/data/bigbase.db \
  "SELECT port FROM deployments WHERE url LIKE '%bolao%' ORDER BY created_at DESC LIMIT 1" 2>/dev/null || echo "")
if [ -n "$LATEST_PORT" ] && [ -d "/opt/bigbase/data/builds/${LATEST_PORT}/web/dist" ]; then
  ln -sfn "/opt/bigbase/data/builds/${LATEST_PORT}/web/dist" "${BOLAO_DIR}/current"
  echo "  Symlink: ${BOLAO_DIR}/current → builds/${LATEST_PORT}/web/dist"
else
  mkdir -p "${BOLAO_DIR}/current"
  echo "  Created empty current/ (will be symlinked after first deploy)"
fi

# ── 3. Install deploy hook (updates symlink after each deploy) ─
echo "→ Installing deploy hook..."
HOOK="${BOLAO_DIR}/post-deploy.sh"
cat > "$HOOK" << 'HOOK'
#!/usr/bin/env bash
# Post-deploy hook for Big Bolão — updates the stable symlink
set -euo pipefail
LATEST_PORT=$(sqlite3 /opt/bigbase/data/bigbase.db \
  "SELECT port FROM deployments WHERE url LIKE '%bolao%' ORDER BY created_at DESC LIMIT 1" 2>/dev/null || echo "")
if [ -n "$LATEST_PORT" ] && [ -d "/opt/bigbase/data/builds/${LATEST_PORT}/web/dist" ]; then
  ln -sfn "/opt/bigbase/data/builds/${LATEST_PORT}/web/dist" "/opt/bolao/current"
  echo "Symlinked /opt/bolao/current → builds/${LATEST_PORT}/web/dist"
fi
HOOK
chmod +x "$HOOK"

# ── 4. Configure Caddy ────────────────────────────────────────
echo "→ Configuring Caddy for bolao.bigbase.click..."
CADDYFILE="/etc/caddy/Caddyfile"

# Remove old bolão section
sed -i '/^# Big Bolão/,/^}/d' "$CADDYFILE" 2>/dev/null || true

cat >> "$CADDYFILE" << 'CADDYEOF'

# Big Bolão — Copa 2026
bolao.bigbase.click {
    handle {
        root * /opt/bolao/current
        try_files {path} /index.html
        file_server
    }

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

caddy reload --config "$CADDYFILE" 2>/dev/null || systemctl reload caddy 2>/dev/null || true
echo "  Caddy reloaded"

echo ""
echo "=== SETUP COMPLETE ==="
echo "  Env:     ${BOLAO_DIR}/.env"
echo "  SPA:     ${BOLAO_DIR}/current/  (symlink, updates on deploy)"
echo "  Caddy:   bolao.bigbase.click → static + /api/* → BigBase"
echo ""
echo "Now trigger a redeploy:"
echo "  python3 -m scripts.redeploy"
SSHEOF

info "=== Done ==="
