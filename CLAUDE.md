# Big Bolão — Claude Code Context

## Project Overview

Telegram bot + Vue SPA bolão (football pool) for Copa do Mundo 2026.

- **Bot**: `bolao/` — python-telegram-bot, BigBase as backend
- **Web SPA**: `web/` — Vue 3 + Vite, served by `app.py`
- **Hosted**: `bolao.bigbase.click`

## MCP Servers

Two MCP servers are configured in `.pi/mcp.json` (git-ignored, per-developer).

### BigBase MCP — `mcp({ connect: "bigbase" })`

**Auth:** Bearer JWT — must be set before Pi starts:

```bash
# Generate token (expires in 24h)
export BIGBASE_MCP_TOKEN=$(python3 -c "
import httpx
r = httpx.post('https://bigbase.click/api/auth/login', json={
    'email': 'bolao-bot@bigbase.local',
    'password': 'bolao-bot-secure-password-2026',
})
print(r.json()['token'])
")
```

| Tool                | What it does                          | When to use                             |
| ------------------- | ------------------------------------- | --------------------------------------- |
| `ping`              | Health check                          | Verify MCP is alive                     |
| `list_services`     | Browse BigBase service catalog        | Understand platform capabilities        |
| `get_service_docs`  | Docs for a specific service           | Before integrating a BigBase feature    |
| `list_frameworks`   | Supported frameworks (Vue, etc.)      | Verify framework compatibility          |
| `get_code_example`  | Code snippets for a service+framework | Scaffold integration code               |
| `list_repos`        | List git repos on BigBase             | Find the repo ID for deploy             |
| `deploy_site`       | Deploy a repo/branch                  | **Inspection only — see WARNING below** |
| `get_deploy_status` | Check deploy progress                 | After triggering deploy                 |
| `get_deploy_logs`   | Debug failed builds                   | When deploy fails                       |
| `deploy_guide`      | Full deploy workflow                  | First-time deploy setup                 |

**Code areas it maps to:**

- `app.py` + BigBase entry point → `ping`, `deploy_site`
- `bolao/bigbase.py` (BigBase client) → `get_code_example`, `get_service_docs`
- CI/CD (`scripts/redeploy.py`, `.github/workflows/ci-cd.yml`) → `deploy_site`, `get_deploy_status`

### New Relic MCP — `mcp({ connect: "newrelic" })`

**Auth:** User API Key (NRAK-...) — hardcoded in `.pi/mcp.json`. Requires Pi restart to appear.

| Tool category | What it does                           | When to use                        |
| ------------- | -------------------------------------- | ---------------------------------- |
| `discovery`   | Find entities (apps, hosts, services)  | Check if app is reporting          |
| `alerting`    | Query/manage alert conditions          | Investigate production issues      |
| `data-access` | NRQL queries for metrics, logs, events | Debug bot performance, error rates |

**Code areas it maps to:**

- `bolao/bigbase.py` (DB latency) → NRQL queries, error analytics
- `bolao/handlers.py` (bot command failures) → error tracking, transaction traces
- `app.py` (HTTP server) → APM transaction monitoring
- BigBase VPS (`scripts/setup_server.sh`) → Infrastructure monitoring (CPU, memory, disk)

**Quick NRQL examples (via `ssh root@bigbase.click`):**

```bash
# Last 30 min of system metrics
newrelic nrql query --accountId 8192379 \
  --query "SELECT * FROM SystemSample SINCE 30 MINUTES AGO"

# Errors in the last hour
newrelic nrql query --accountId 8192379 \
  --query "SELECT count(*) FROM TransactionError SINCE 1 HOUR AGO"
```

## Deploy to BigBase

### Preferred: redeploy script (targets the correct site)

```bash
python3 scripts/redeploy.py
```

This hits `/api/sites/<repo_id>/deploy` — the only method that deploys `app.py` to **`bolao.bigbase.click`**.

### WARNING: MCP `deploy_site` deploys to the WRONG site

The BigBase MCP `deploy_site` tool uses a different endpoint and deploys to
`danielvm-git-big-bolao.bigbase.click` (auto-generated static subdomain), NOT to
`bolao.bigbase.click`. **Do not use `deploy_site` for production deploys.** This has
caused `bolao.bigbase.click` to show the BigBase marketing page on multiple occasions.
Use MCP tools for inspection only (`get_deploy_status`, `get_deploy_logs`, `list_repos`).

### MCP tools (for inspection only — NOT for deploying)

Config: `.mcp.json` at project root; auth via `BIGBASE_MCP_TOKEN` env var.

| Tool                                 | Use for                                   |
| ------------------------------------ | ----------------------------------------- |
| `ping`                               | Health check                              |
| `list_repos`                         | Verify repo IDs                           |
| `get_deploy_status`                  | Check a deploy triggered by `redeploy.py` |
| `get_deploy_logs`                    | Debug a failed deploy                     |
| `list_services` / `get_service_docs` | Platform docs                             |

### GitHub Actions (CI/CD)

```yaml
name: Deploy to BigBase
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd web && npm ci && npm run build
      - run: |
          curl -X POST https://bigbase.click/api/deploy \
            -H "Authorization: Bearer ${{ secrets.BIGBASE_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{"repo_id":"04c58b9df51405ee33378c2539f9ea68","branch":"main"}'
```

Secret `BIGBASE_API_KEY` via `POST /api/orgs/{id}/api-keys` no dashboard.

### BigBase expectations

- **Python**: `app.py` na raiz, ouve `$PORT`
- **Node**: `package.json` com `start` script, ouve `$PORT`
- **Static**: `dist/` na raiz
- CSP header: `default-src 'self'` — sem inline `<style>` / `<script>` / CDN externo

### Key URLs

| Recurso    | URL                                              |
| ---------- | ------------------------------------------------ |
| Dashboard  | https://bigbase.click/admin                      |
| Deploy API | `POST https://bigbase.click/api/deploy`          |
| Status     | `GET https://bigbase.click/api/deploy/{id}`      |
| Logs       | `GET https://bigbase.click/api/deploy/{id}/logs` |
| Site       | https://bolao.bigbase.click                      |
| Landing    | https://bolao.bigbase.click/landing.html         |

## Architecture

```
big-bolao/
├── app.py              # BigBase entry: serves web/dist/ on $PORT + bot in thread
├── bolao/              # Telegram bot
│   ├── bot.py          # Application builder + periodic jobs
│   ├── handlers.py     # Command handlers (ParseMode.HTML)
│   ├── bigbase.py      # BigBase client (list_records, O(n) filter, no SQL)
│   ├── betting_flow.py # Betting state machine (Step enum + serialize/deserialize)
│   ├── config.py       # validate_config() called at startup
│   ├── fixtures.py     # apifootball.com fixture parser + normalise + fetch_from_api
│   ├── group_publisher.py  # Pure formatting for group messages (no I/O)
│   ├── historico.py    # Rodada 1 historical data transcribed from spreadsheet
│   ├── logger.py       # Structured JSON logging (JSONFormatter)
│   ├── matches.py      # Hardcoded match schedule: 72 games, 3 rounds
│   ├── ranking.py      # Ranking calculation (calcular) + formatting (formatar)
│   ├── results.py      # apifootball.com results provider
│   ├── scoring.py      # Pontos: exact=3, winner=1, miss=0
│   └── util.py         # Time helpers (agora, quiet hours, kickoff), labels, version
├── web/
│   ├── src/
│   │   ├── api.js      # Re-export barrel (backward compat)
│   │   ├── transport.js# HTTP client for BigBase API (BB singleton)
│   │   ├── queries.js  # Domain query functions (fetchJogos, savePalpite, etc.)
│   │   ├── scoring.js  # Pure scoring + flags + formatting (mirrors Python scoring)
│   │   ├── store.js    # Vue reactive state (jogos, palpites, ranking, user)
│   │   ├── App.vue     # Nav + bottom-nav + footer + <router-view>
│   │   ├── style.css   # Global styles
│   │   ├── views/
│   │   │   ├── DashboardView.vue  # Public landing, stats + leader + next games
│   │   │   ├── JogosView.vue      # Game list with filters + palpite modal
│   │   │   └── MeusPalpitesView.vue  # My bets grouped by status
│   │   └── router/index.js  # / (public), /jogos, /meus
│   ├── public/
│   │   ├── landing.html / landing.css / landing.js  # Swiss grid landing page
│   └── dist/           # Pre-built, committed to git
├── scripts/
│   ├── redeploy.py     # Trigger BigBase redeploy (/api/sites/<id>/deploy)
│   ├── sync_fixtures.py# Sync fixtures from apifootball to BigBase
│   ├── seed_bigbase.py # One-time seed: R1 data + placeholders
│   ├── check_ranking.py# Validate scoring rules + R1 ranking
│   ├── cleanup_duplicates.py  # Fix duplicate participants
│   ├── setup_server.sh # VPS provisioning (Caddy, systemd, env)
│   └── mcp_setup.sh    # MCP server configuration
├── tests/
│   ├── test_betting_flow.py    # 24 tests
│   ├── test_config.py          # 5 tests
│   ├── test_fixtures.py        # 14 tests
│   ├── test_group_publisher.py # 11 tests
│   ├── test_participantes.py   # 6 tests
│   ├── test_quiet_hours.py     # 4 tests
│   ├── test_ranking.py         # 9 tests
│   ├── test_results.py         # 7 tests
│   └── test_version.py         # 2 tests
└── .github/workflows/
    └── ci-cd.yml       # CI/CD: semantic-release → build → test → deploy → health check
```

## Bot Commands

| Comando                | Quem          | Descrição                                        |
| ---------------------- | ------------- | ------------------------------------------------ |
| `/start`, `/ajuda`     | todos         | Boas-vindas                                      |
| `/sou Nome`            | todos         | Registra participante                            |
| `/jogos`, `/palpitar`  | privado       | Palpitar jogos abertos                           |
| `/meus`                | privado       | Ver seus palpites                                |
| `/ranking`             | grupo/privado | Ranking atual                                    |
| `/version`             | qualquer      | Versão do build (diagnóstico de instância zumbi) |
| `/web`                 | qualquer      | Link do site com auth automática                 |
| `/lembrete`            | grupo         | Jogos do dia                                     |
| `/sync`                | admin         | Busca resultados da apifootball API              |
| `/resultado R2-05 2 1` | admin         | Registra resultado manual                        |
| `/chatid`              | qualquer      | Retorna chat ID                                  |

## Environment Variables (in /opt/bolao/.env on server)

```
TELEGRAM_TOKEN=...
GRUPO_CHAT_ID=-1002259214669   # official group
ADMIN_IDS=53886674
BIGBASE_URL=https://bigbase.click
BIGBASE_EMAIL=bolao-bot@bigbase.local
BIGBASE_PASSWORD=bolao-bot-secure-password-2026
APIFOOTBALL_KEY=...
APIFOOTBALL_LEAGUE_ID=28       # Copa 2026 (NOT 1)
RESULTS_PROVIDER=apifootball
```

## Tests

```bash
python -m pytest tests/ -v   # requires: pip install pytest pytest-asyncio
```

## Web Build

```bash
cd web && npx vite build      # outputs to web/dist/ (committed to git)
```

## Observability

Logging uses structured JSON via `bolao/logger.py` — all entries are single-line JSON
with `level`, `timestamp`, `logger`, and `message`. Context fields (match_id, user_id,
duration, etc.) are attached via the `extra={...}` parameter.

| What                      | Command                                                               |
| ------------------------- | --------------------------------------------------------------------- |
| View live logs            | `journalctl -u bigbase -f -n 100 \| grep bolao`                       |
| Health check              | `curl https://bolao.bigbase.click/health`                             |
| Health check (local)      | `curl http://localhost:$PORT/health`                                  |
| Check BigBase collections | `sqlite3 /opt/bigbase/data/bigbase.db "SELECT COUNT(*) FROM records"` |
| Bot log file              | `tail -f /opt/bigbase/data/logs/app.log \| grep bolao`                |

### Log format

```json
{
  "level": "INFO",
  "timestamp": "2026-06-21T13:45:23.123+00:00",
  "logger": "bolao.bigbase",
  "message": "Login successful",
  "duration_ms": 42
}
```

### Key loggers

| Logger           | Module        | Events                                                       |
| ---------------- | ------------- | ------------------------------------------------------------ |
| `bolao.app`      | `app.py`      | Server startup, HTTP requests, bot thread lifecycle          |
| `bolao.bot`      | `bot.py`      | Bot init, job registration                                   |
| `bolao.bigbase`  | `bigbase.py`  | All DB operations (login, create, patch, list) with duration |
| `bolao.handlers` | `handlers.py` | Command handlers, sync jobs, quiet hours gating              |
| `bolao.results`  | `results.py`  | External API calls (apifootball)                             |
| `bolao.fixtures` | `fixtures.py` | Fixture sync and parsing                                     |

**Never log secrets, passwords, tokens, or PII.** Telegram IDs are logged for
auditing but are not considered PII in this context.

### New Relic (optional)

The project supports New Relic for APM (Python agent) and MCP (AI agent context).

| Component      | Config                            | How to activate                                                       |
| -------------- | --------------------------------- | --------------------------------------------------------------------- |
| **APM agent**  | `NEW_RELIC_LICENSE_KEY` in `.env` | Add a License Key (NRII-...) to `.env` — auto-detected at startup     |
| **MCP server** | `.pi/mcp.json`                    | Restart Pi after editing `.pi/mcp.json` (MCP config loads at startup) |

Account ID: `8192379`

**Examples (via ssh to BigBase server):**

```bash
# Check VPS host metrics
ssh root@bigbase.click 'NEW_RELIC_API_KEY=$NEW_RELIC_API_KEY \
  NEW_RELIC_ACCOUNT_ID=8192379 newrelic entity search --name bigbase'

# Query NRQL
ssh root@bigbase.click 'NEW_RELIC_API_KEY=$NEW_RELIC_API_KEY \
  NEW_RELIC_ACCOUNT_ID=8192379 newrelic nrql query --accountId 8192379 \
  --query "SELECT * FROM SystemSample SINCE 30 MINUTES AGO"'
```

## Known Issues / Notes

- BigBase CSP blocks inline styles and external CDNs — use external files at same origin
- BigBase `root_path: ./web` is ignored by DetectAppType (BUG-190000) — `app.py` handles serving
- `/sync` uses `apiv3.apifootball.com` (not `api-football.com`) with `APIkey` query param
- Game names from API are in English; FLAGS dict has both PT and EN variants
- All Telegram messages use `ParseMode.HTML` (not Markdown — underscores in bot name break MD)
