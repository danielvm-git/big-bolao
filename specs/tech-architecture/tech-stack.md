# Tech Stack — Big Bolão (as-built, 2026-06-20)

> Derived from live code scan. Supersedes `TECH_STACK_LATEST.md` (planning-era draft).

---

## Stack

### Backend — Python 3.13
| Layer | Choice | Notes |
|-------|--------|-------|
| Runtime | Python 3.13 (`.venv`) | |
| Telegram bot | `python-telegram-bot` 21.6 + job-queue | Long-polling, not webhooks |
| HTTP client | `httpx` 0.27.2 (async) | Used exclusively for BigBase + apifootball calls |
| Env config | `python-dotenv` 1.0.1 | Loads `/opt/bolao/.env` → `.env` → env |
| Linter | `ruff` (via `.ruff_cache`) | |
| Testing | `pytest` + `pytest-asyncio` | |

### Frontend — Vue 3 SPA
| Layer | Choice | Notes |
|-------|--------|-------|
| Framework | Vue 3.5 (Composition API, `<script setup>`) | |
| Router | vue-router 4.6 | Hash-history (`#/`), defined in `main.js` (no router/ dir) |
| State | Plain Vue `ref`/`computed` in `store.js` | No Pinia or Vuex |
| HTTP | Native `fetch` wrapped in singleton `BB` object | See `api.js` |
| Bundler | Vite 8 | Builds to `web/dist/` (committed to git) |
| Node version | 22 (CI) | |

### Data Platform — BigBase
- Schema-less JSON collections over REST + optional read-only `/api/sql`
- Auth: JWT obtained by `POST /api/auth/login` (email/password), Bearer header
- Collections: `participantes`, `jogos`, `palpites`
- Hosted at `bigbase.click`; site served at `bolao.bigbase.click`

---

## Architecture

### Entry Point (`app.py`)
```
app.py (main thread = HTTP server)
├── Thread 1: Telegram bot (long-polling, daemon)
│   └── bolao/bot.py → build_app() → ApplicationBuilder + handlers
└── Thread 2 (main): http.server.TCPServer on $PORT
    └── SPAHandler: serves web/dist/ as SPA
        └── Special case: Telegram Instant View bot → static HTML response
```

### Bot Layer
```
handlers.py (command/callback handlers)
    ↓ db(context) → BigBase instance stored in bot_data["db"]
bolao/bigbase.py (data layer)
    ↓ httpx.AsyncClient
BigBase REST API (bigbase.click)
    ↓ SQLite (schema-less JSON in `data` column)
```

Betting flow is a 3-step callback query chain: `g|<match_id>` → `h|<match_id>|<gc>` → `f|<match_id>|<gc>|<gf>`

Jobs registered in `bot.py`:
- `job_sync`: every 30 min (pulls results from apifootball.com)
- `job_lembrete`: daily at 12:00 BRT

### Web Layer (Vue SPA)
```
App.vue
├── onMounted: picks up ?uid= from URL → initUser() → store.user
├── loadAll() → parallel fetch: jogos + palpites + participantes
│       ↓
│   store.js (reactive refs + computed)
│       jogosRich, rankingRich, palpitesIdx (derived)
│       ↓
└── router-view
    ├── DashboardView  → ranking table, upcoming games, cross-table of all guesses
    ├── JogosView      → open games list + bet entry UI
    └── MeusPalpitesView → personal guesses with score status
```

Auth model: **service account** credentials are hardcoded in `api.js`; all users
read the same BigBase data. Individual user identity is provided by `?uid=<telegram_id>`
in the URL (link sent by the bot via `/web`). No session tokens, no login screen.

### Data Flow — Results Pipeline
```
apifootball.com API (apiv3.apifootball.com)
    ↓ every 30 min (job_sync) or on-demand (/sync)
results.py: buscar_encerrados()
    ↓ matches by api_fixture_id, fallback to (home_en, away_en) pair
bigbase.py: set_resultado()
    ↓ PATCH jogos record → status="encerrado"
handlers: _publicar_resultado() + _publicar_ranking()
    ↓ send_message to GRUPO_CHAT_ID
```

---

## Conventions (Observed)

### Python
- `from __future__ import annotations` in every module
- `async/await` throughout bot + BigBase layers; `httpx.AsyncClient` (not requests)
- All Telegram messages use `ParseMode.HTML` — no Markdown (underscores in bot name break it)
- `BigBaseError(RuntimeError)` for explicit HTTP errors; no silent failures in the data layer
- `logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s | %(message)s")` — structured-ish, goes to stdout
- Tests are pure unit tests (no I/O mocking, no BigBase calls) — data is constructed inline

### JavaScript
- No TypeScript — plain JS throughout
- Scoring logic (`calcPontos`) is duplicated in both `api.js` and `scoring.py` — intentional for offline capability
- `flag()` normalizes team names: lowercase → strip accents (NFD) → drop punctuation → collapse spaces; PT and EN variants are both keyed in `FLAGS`
- Version baked into bundle at build time via `__APP_VERSION__` (Vite `define`) — read from root `VERSION` file; CSP-safe

### Deployment
- `web/dist/` is committed to git — BigBase deploys by pulling the repo, not building
- Semantic-release writes `VERSION` and `CHANGELOG.md`, then CI builds `web/dist/` and auto-commits it before triggering BigBase deploy
- BigBase's CSP `default-src 'self'` blocks inline `<style>`/`<script>` and external CDNs — all styles must be in `.css` files at same origin

---

## Signals / Active Considerations

### Full-table scans on every request
`list_records()` always fetches up to 1000 records. Every bet save, ranking load, or participant lookup fetches the full table. Works today at ~10 participants / ~72 games, but is an O(n) scan with no client-side caching between requests within a session.

### Service account credentials visible in JS bundle
`api.js` hardcodes email/password for the BigBase service account. The account is read-oriented (write to `palpites` only), but credentials are public. This is a known trade-off, not a hidden risk.

### Scoring logic duplicated
`calcPontos` / `pontos` exist in both `api.js` and `scoring.py`. Drift is possible if rules change.

### Error handling gap in `store.js`
`loadAll()` catches all errors with `console.error` and then sets `loaded.value = true` regardless. The UI will render with empty data on a failed load, with no user-visible error message.

### Static match schedule in `matches.py`
72 games are hard-coded as PT-language team names. The apifootball results provider uses EN names and has a `_PT_TO_EN` mapping. If new games are added (e.g. knockouts), both `MATCHES` and the mapping need updating.

### Bot conflict on deploy
`run_bot()` has a 12-attempt retry loop (5s–60s backoff) for `telegram.error.Conflict` — the old instance doesn't release the long-poll immediately during rolling deploys.

### Hash-history router
vue-router is configured with `createWebHashHistory()` — all routes are `/#/`. This means the server always serves `index.html` regardless of path, which is correct for the current SPA setup.

### Telegram Instant View
`_serve_telegram_iv()` in `app.py` returns hardcoded static HTML (no live data). The IV page is purely for link-preview metadata.
