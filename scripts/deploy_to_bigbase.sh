#!/usr/bin/env bash
# ============================================================================
# deploy_to_bigbase.sh — Set up env vars on BigBase server for bolão bot
#
# Prerequisites:
#   1. SSH access to the BigBase server
#   2. The server must have BigBase running (setup-vps.sh was run)
#
# Usage:
#   ./scripts/deploy_to_bigbase.sh <ssh-host>
#
# Example:
#   ./scripts/deploy_to_bigbase.sh root@123.456.789.0
#
# This script copies the .env file to /opt/bigbase/.env.bolao on the server
# and adds an EnvironmentFile directive to the bigbase systemd service.
# ============================================================================
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { printf "${GREEN}%s${NC}\n" "$1"; }
warn()  { printf "${YELLOW}WARNING: %s${NC}\n" "$1"; }
err()   { printf "${RED}ERROR: %s${NC}\n" "$1"; }

if [ $# -lt 1 ]; then
  echo "Usage: $0 <ssh-host>"
  echo "  Example: $0 root@YOUR_SERVER_IP"
  exit 1
fi

SSH_HOST="$1"

# ── Load local .env ────────────────────────────────────────────────
if [ ! -f ".env" ]; then
  err "No .env file found in the project root."
  err "Create one from .env.example and fill in the secrets."
  exit 1
fi

info "Deploying env vars to ${SSH_HOST}..."

# ── Copy .env to server ────────────────────────────────────────────
scp ".env" "${SSH_HOST}:/opt/bigbase/.env.bolao"

# ── Update systemd service to include the bolão env file ───────────
ssh "${SSH_HOST}" << 'SSHEOF'
set -euo pipefail

BOLAO_ENV_FILE="/opt/bigbase/.env.bolao"
SERVICE_FILE="/etc/systemd/system/bigbase.service"

if [ ! -f "$BOLAO_ENV_FILE" ]; then
  echo "ERROR: .env.bolao not found on server"
  exit 1
fi

# Check if .env.bolao is already referenced in the service file
if grep -q "\.env\.bolao" "$SERVICE_FILE"; then
  echo "→ .env.bolao already referenced in bigbase.service"
else
  echo "→ Adding EnvironmentFile for .env.bolao..."
  # Insert before the existing EnvironmentFile line, or at the end of [Service] section
  sed -i '/^EnvironmentFile/i EnvironmentFile=-/opt/bigbase/.env.bolao' "$SERVICE_FILE"
  systemctl daemon-reload
fi

# Restart BigBase to pick up new env vars
echo "→ Restarting BigBase service..."
systemctl restart bigbase
sleep 3

# Verify
if systemctl is-active --quiet bigbase; then
  echo "✓ BigBase restarted successfully"
else
  echo "✗ BigBase failed to restart — check journalctl -u bigbase -f"
  exit 1
fi

echo ""
echo "=== Env vars deployed ==="
echo "BigBase service now loads:"
echo "  /opt/bigbase/.env (original BigBase env)"
echo "  /opt/bigbase/.env.bolao (bolão secrets)"
echo ""
echo "Now push to main — BigBase will redeploy with the new env vars."
SSHEOF

info "Done! Push your code and the deployed app will have the secrets."
