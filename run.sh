#!/usr/bin/env bash
# Lancamento em um comando: valida env, sobe a agenda no BigBase e roda o bot.
# Uso:  ./run.sh           (seed + bot)
#       ./run.sh --no-seed (so o bot)
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  echo "❌ Falta o arquivo .env. Copie de .env.example e preencha." >&2
  exit 1
fi

# venv
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

if [[ "${1:-}" != "--no-seed" ]]; then
  echo "▶ Subindo agenda + resultados R1 + palpites historicos..."
  python -m scripts.seed_bigbase
fi

echo "▶ Iniciando o bot (long polling). Ctrl+C para parar."
exec python -m bolao.bot
