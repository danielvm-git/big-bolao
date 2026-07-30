# Big Bolão — Copa 2026 no Telegram + Web

[![Test, Build & Release](https://github.com/danielvm-git/big-bolao/actions/workflows/test-build-release.yml/badge.svg)](https://github.com/danielvm-git/big-bolao/actions/workflows/test-build-release.yml)
[![Deploy](https://github.com/danielvm-git/big-bolao/actions/workflows/deploy.yml/badge.svg)](https://github.com/danielvm-git/big-bolao/actions/workflows/deploy.yml)

Bot de Telegram + Vue SPA pra rodar o bolão da Copa do Mundo 2026. Os palpites são feitos **no privado com o bot** (ninguém vê o palpite do outro, zero flood no grupo). O grupo só recebe lembretes, resultados e o ranking. Backend de dados no [BigBase](https://bigbase.click).

Site web em **https://bolao.bigbase.click** — dashboard público com ranking, jogos e grade de palpites.

## Como funciona (UX)

- **No privado do bot:** cada pessoa palpita o **placar exato** de cada jogo por botões (escolhe gols do mandante, depois do visitante). Pode editar até o apito.
- **No grupo:** o bot posta lembrete dos jogos das próximas 24h, o placar final com quem cravou, e o ranking atualizado. Comandos de palpite no grupo são redirecionados pro privado.
- **No site:** dashboard público (sem login) com ranking, lista de jogos, grade de palpites. Login automático via `?uid=` na URL enviada pelo bot (`/web`).
- **Quiet Hours:** entre 22h e 8h BRT, o bot não publica resultados/ranking no grupo — enfileira e libera tudo às 8h.
- **Pontuação:** `3` placar exato · `1` acertar vencedor/empate · `0` erro.

## Tech Stack

| Tool                          | Purpose                                    |
| ----------------------------- | ------------------------------------------ |
| **Python 3.12+**              | Bot backend (python-telegram-bot)          |
| **Vue 3**                     | SPA com Composition API (`<script setup>`) |
| **Vite**                      | Dev server + build bundler                 |
| **BigBase**                   | Backend-as-a-Service (REST + JWT, SQLite)  |
| **API-Football**              | Live match results (optional)              |
| **pytest**                    | Python test framework (167 tests)          |
| **Vitest / Node test runner** | Web test framework (88 tests)              |

## Code Style

- **Python**: Type hints on all public functions. Structured JSON logging via `bolao/logger.py`. Flake8 linting.
- **Vue**: Composition API with `<script setup>`. Named exports only. No inline styles (BigBase CSP).
- **All**: Conventional Commits mandatory. See `CONVENTIONS.md` for full conventions.

## Comandos do Bot

| Comando                               | Onde     | O quê                                                        |
| ------------------------------------- | -------- | ------------------------------------------------------------ |
| `/start` ou `/ajuda`                  | privado  | cadastra e mostra ajuda                                      |
| `/sou <Nome>`                         | privado  | herda os palpites da Rodada 1 (jogadores antigos)            |
| `/jogos` ou `/palpitar`               | privado  | palpitar nos próximos jogos (botões)                         |
| `/meus`                               | privado  | ver meus palpites                                            |
| `/ranking`                            | qualquer | classificação geral (recalculada)                            |
| `/version`                            | qualquer | versão do build em execução (diagnóstico de instância zumbi) |
| `/web`                                | qualquer | envia link do site com autenticação automática               |
| `/chatid`                             | grupo    | mostra o chat_id (pra configurar)                            |
| `/resultado <match_id> <casa> <fora>` | admin    | lança placar manual                                          |
| `/sync`                               | admin    | puxa resultados do provider e publica                        |
| `/lembrete`                           | admin    | posta os jogos abertos no grupo                              |

## Arquitetura

```
big-bolao/
├── app.py               # BigBase entry: serves web/dist/ on $PORT + bot in thread
├── bolao/               # Telegram bot (Python)
│   ├── bot.py           # Application builder + jobs
│   ├── handlers.py      # Command handlers (ParseMode.HTML)
│   ├── bigbase.py       # BigBase client (list_records, no SQL)
│   ├── betting_flow.py  # Betting state machine (Step enum + serialize/deserialize)
│   ├── config.py        # validate_config() called at startup
│   ├── fixtures.py      # apifootball.com fixture parser + normaliser
│   ├── group_publisher.py  # Pure formatting of group messages
│   ├── historico.py     # R1 historical data from spreadsheet
│   ├── logger.py        # Structured JSON logging
│   ├── matches.py       # Hardcoded match schedule (72 games)
│   ├── ranking.py       # Ranking calculation + formatting
│   ├── results.py       # apifootball.com results provider
│   ├── scoring.py       # Scoring rules (exact=3, winner=1, miss=0)
│   └── util.py          # Time helpers, labels, version, quiet hours
├── web/                 # Vue 3 SPA (Vite)
│   ├── src/
│   │   ├── api.js       # Re-export barrel (backward compat)
│   │   ├── transport.js # HTTP client for BigBase API
│   │   ├── queries.js   # Domain query functions
│   │   ├── scoring.js   # Pure scoring + flags + formatting (mirrors Python)
│   │   ├── store.js     # Vue reactive state (jogos, palpites, ranking)
│   │   ├── App.vue      # Nav + bottom nav + footer + router-view
│   │   ├── style.css    # Global styles
│   │   ├── views/
│   │   │   ├── DashboardView.vue  # Public landing (stats, leader, next games, ranking)
│   │   │   ├── JogosView.vue      # Game list with filters + palpite modal
│   │   │   └── MeusPalpitesView.vue  # My bets grouped by status
│   │   └── router/index.js  # Public / + /jogos + /meus routes
│   ├── public/
│   │   └── landing.html / landing.css / landing.js  # Swiss grid landing page
│   └── dist/            # Pre-built, committed to git
├── scripts/
│   ├── redeploy.py      # Trigger BigBase redeploy (/api/sites/<id>/deploy)
│   ├── sync_fixtures.py # Sync fixtures from apifootball to BigBase
│   ├── seed_bigbase.py  # One-time seed of R1 data + placeholders
│   ├── check_ranking.py # Validate scoring rules + R1 ranking
│   ├── cleanup_duplicates.py  # Clean duplicate participants
│   ├── setup_server.sh  # VPS provisioning script
│   └── mcp_setup.sh     # MCP server setup
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
    ├── test-build-release.yml  # CI: lint → test → build → release
    └── deploy.yml              # Deploy to BigBase + smoke test (workflow_run)
```

### Data flow

```
Bot Python (long polling)  ──REST+JWT──►  BigBase (/api/collections)
        │                                  = SQLite database
        ▼
   Telegram (DM + grupo)  ◄── API-Football (resultados automáticos)
                                ▲
                                │
Vue SPA (browser) ──REST+JWT───┘
  (via fetch nativo, sem backend intermediário)
```

> ℹ️ O BigBase é usado como **banco** (coleções `participantes`, `jogos`, `palpites`). O bot e o site acessam as mesmas coleções via `/api/collections/*`. Não há Functions ou SQL — filtragem é feita em processo sobre `list_records()`.

## Setup

### 1. BigBase (banco)

Suba sua instância e crie uma conta de serviço pro bot:

```bash
curl -X POST $BIGBASE_URL/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"bolao-bot@bigbase.local","password":"<senha-forte>"}'
```

### 2. Telegram

1. Crie o bot no [@BotFather](https://t.me/BotFather) → copie o token.
2. Adicione o bot ao grupo; mande `/chatid` pra pegar o `GRUPO_CHAT_ID`.
3. Pegue seu próprio Telegram ID (ex: [@userinfobot](https://t.me/userinfobot)) pra `ADMIN_IDS`.

### 3. Configuração

```bash
cp .env.example .env   # preencha os valores
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Seed (uma vez)

Sobe a agenda, os resultados e os palpites da Rodada 1:

```bash
python3 -m scripts.seed_bigbase --dry   # confere
python3 -m scripts.seed_bigbase         # sobe pra valer
```

Depois, cada jogador antigo roda `/sou <Nome>` no privado do bot pra herdar seus pontos da R1.

### 5. Rodar

```bash
python3 -m bolao.bot                     # só o bot (long polling)
python3 app.py                           # bot + servidor web (pra BigBase)
```

### 6. Web (desenvolvimento)

```bash
cd web && npm install && npm run dev     # Vite dev server (porta 5173)
cd web && npx vite build                 # produz web/dist/
```

## Resultados automáticos (opcional)

Por padrão o admin lança placares com `/resultado`. Pra automatizar via [API-Football](https://www.api-football.com/) (RapidAPI), preencha no `.env`:

```
RESULTS_PROVIDER=apifootball
APIFOOTBALL_KEY=...
APIFOOTBALL_LEAGUE_ID=28   # Copa 2026
APIFOOTBALL_SEASON=2026
```

O bot passa a puxar resultados a cada 30 min e publicar no grupo.

## Deploy

O deploy é feito via **`python3 scripts/redeploy.py`** que usa o endpoint correto `/api/sites/<repo_id>/deploy` do BigBase. O CI/CD via GitHub Actions também executa automaticamente ao fazer push na `main`.

```bash
python3 scripts/redeploy.py   # deploy no bolao.bigbase.click
```

> ⚠️ O MCP `deploy_site` do BigBase deploya no subdomínio errado (`danielvm-git-big-bolao.bigbase.click`). Use apenas `redeploy.py`.

## Tests

```bash
python -m pytest tests/ -q         # 167 Python tests
cd web && node --test tests/*.test.js  # 88 web tests
```

See `specs/test-strategy/README.md` for the full test strategy, governance gates, and golden fixture invariant. Coverage gates enforce ≥90% on business-logic modules (scoring, fixtures, ranking).

## Observabilidade

Logging usa JSON estruturado via `bolao/logger.py`. Todos os eventos são single-line JSON com `level`, `timestamp`, `logger`, `message` e campos de contexto.

| O quê        | Comando                                                               |
| ------------ | --------------------------------------------------------------------- |
| Logs ao vivo | `journalctl -u bigbase -f -n 100 \| grep bolao`                       |
| Health check | `curl https://bolao.bigbase.click/health`                             |
| BigBase data | `sqlite3 /opt/bigbase/data/bigbase.db "SELECT COUNT(*) FROM records"` |

**Nunca logar secrets, tokens, senhas ou PII.** Telegram IDs são logged para auditoria.

## Contribute

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Write tests first (TDD). Run `python -m pytest tests/ -q` after every change.
4. Commit using [Conventional Commits](https://www.conventionalcommits.org/)
5. Push and open a Pull Request

All contributions must pass tests, lint, and coverage gates. See `CONTRIBUTING.md` for the full development setup.

## License

MIT — see [LICENSE](./LICENSE) for details.
