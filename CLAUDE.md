# Big Bolão — Claude Code Context

## Project Overview

Telegram bot + Vue SPA bolão (football pool) for Copa do Mundo 2026.
- **Bot**: `bolao/` — python-telegram-bot, BigBase as backend
- **Web SPA**: `web/` — Vue 3 + Vite, served by `app.py`
- **Hosted**: `bolao.bigbase.click`

## Deploy to BigBase

### Preferred: MCP tools (fastest)
Uses `pi-mcp-adapter` extension + `.mcp.json` config to talk to BigBase MCP server.

**Setup (one-time):**
```bash
pi install npm:pi-mcp-adapter
```
Place a valid JWT in env var `BIGBASE_MCP_TOKEN` (get via `POST /api/auth/login` with service account credentials).

**Available MCP tools (mcp.bigbase.click):**
| Tool | Description |
|------|-------------|
| `ping` | Health check |
| `list_services` | Browse service catalog |
| `get_service_docs` | Get docs for a service |
| `list_frameworks` | List supported frameworks |
| `get_code_example` | Get framework-specific code snippet |
| `list_repos` | List repos |
| `deploy_site` | Deploy a site (`repo_id`, `branch`) |
| `get_deploy_status` | Check deploy status (`deployment_id`) |
| `get_deploy_logs` | Get deploy logs (`deployment_id`) |
| `deploy_guide` | Full deploy guide |

**Usage via MCP proxy:**
```
mcp({ search: "deploy" })              # discover
mcp({ tool: "deploy_site", args: '{"repo_id":"04c58b9df51405ee33378c2539f9ea68","branch":"main"}' })
mcp({ tool: "get_deploy_status", args: '{"deployment_id":"<id>"}' })
mcp({ tool: "get_deploy_logs", args: '{"deployment_id":"<id>"}' })
```

**Config:** `.mcp.json` at project root connects to `mcp.bigbase.click/mcp` with bearer auth.

### Alternative: redeploy script
```bash
python3 scripts/redeploy.py
```

### Manual: curl
```bash
curl -X POST https://bigbase.click/api/deploy \
  -H "Authorization: Bearer $BIGBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"repo_id":"04c58b9df51405ee33378c2539f9ea68","branch":"main"}'

# Status
curl https://bigbase.click/api/deploy/<id>
# Logs
curl https://bigbase.click/api/deploy/<id>/logs
```

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
| Recurso | URL |
|---------|-----|
| Dashboard | https://bigbase.click/admin |
| Deploy API | `POST https://bigbase.click/api/deploy` |
| Status | `GET https://bigbase.click/api/deploy/{id}` |
| Logs | `GET https://bigbase.click/api/deploy/{id}/logs` |
| Site | https://bolao.bigbase.click |
| Landing | https://bolao.bigbase.click/landing.html |

## Architecture

```
big-bolao/
├── app.py              # BigBase entry: serves web/dist/ on $PORT + bot in thread
├── bolao/              # Telegram bot
│   ├── bot.py          # Application builder
│   ├── handlers.py     # Command handlers (ParseMode.HTML)
│   ├── bigbase.py      # BigBase client (list_records, no SQL)
│   ├── config.py       # validate_config() called at startup
│   ├── results.py      # apifootball.com provider
│   └── scoring.py      # Pontos: exact=3, winner=1, miss=0
├── web/
│   ├── src/
│   │   ├── api.js      # BB._ensureToken() auto-login with service account
│   │   ├── views/DashboardView.vue  # Public landing, fetches on onMounted
│   │   └── router/index.js  # / → Dashboard (public), /home → HomeView (auth)
│   ├── public/
│   │   ├── landing.html / landing.css / landing.js  # Swiss grid landing page
│   └── dist/           # Pre-built, committed to git
└── scripts/
    ├── redeploy.py     # Trigger BigBase redeploy
    └── sync_fixtures.py
```

## Bot Commands

| Comando | Quem | Descrição |
|---------|------|-----------|
| `/start`, `/ajuda` | todos | Boas-vindas |
| `/sou Nome` | todos | Registra participante |
| `/jogos`, `/palpitar` | privado | Palpitar jogos abertos |
| `/meus` | privado | Ver seus palpites |
| `/ranking` | grupo/privado | Ranking atual |
| `/lembrete` | grupo | Jogos do dia |
| `/sync` | admin | Busca resultados da apifootball API |
| `/resultado R2-05 2 1` | admin | Registra resultado manual |
| `/chatid` | qualquer | Retorna chat ID |

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

## Known Issues / Notes

- BigBase CSP blocks inline styles and external CDNs — use external files at same origin
- BigBase `root_path: ./web` is ignored by DetectAppType (BUG-190000) — `app.py` handles serving
- `/sync` uses `apiv3.apifootball.com` (not `api-football.com`) with `APIkey` query param
- Game names from API are in English; FLAGS dict has both PT and EN variants
- All Telegram messages use `ParseMode.HTML` (not Markdown — underscores in bot name break MD)
