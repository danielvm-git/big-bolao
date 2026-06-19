# Epic e02 — Live API Integration (Copa 2026)

## Goal

Replace the hardcoded match schedule and manual result entry with live data from
**apifootball.com**. After this epic the bot and web app will:

1. **Seed & refresh fixtures** (group stage + knockout rounds) automatically from the API.
2. **Pull final scores** every 30 min without any admin action.
3. Store the API's own fixture ID (`api_fixture_id`) on every `jogo` record so
   that result-matching is exact (no fragile PT→EN name translation).
4. Keep `/resultado` as an admin override and the hardcoded `matches.py` as an
   offline fallback.

---

## Current state vs target state

| Concern | Before | After |
|---|---|---|
| Fixture schedule | Hardcoded `matches.py` (group stage only) | API-Football → BigBase, every round incl. knockouts |
| Result entry | Admin types `/resultado R1-01 2 1` | `job_sync` pulls every 30 min automatically |
| API match ID | Not stored; team-name heuristic for matching | `api_fixture_id` stored on `jogos`, exact match |
| New rounds (knockouts) | Must redeploy with updated `matches.py` | `/sync_jogos` or 24 h job picks them up |
| Fallback | — | Hardcoded list + manual `/resultado` still work |

---

## Scope

**In:**
- `bolao/fixtures.py` — new module, fetches & normalises fixtures from apifootball.com  
- `bolao/config.py` — add `FIXTURES_PROVIDER`  
- `bolao/bigbase.py` — `ensure_setup` upserts from API; `api_fixture_id` field  
- `bolao/results.py` — match by `api_fixture_id`, keep name-fallback  
- `bolao/handlers.py` — `/sync_jogos` admin command + `job_sync_fixtures`  
- `bolao/bot.py` — register command + 24 h fixture-sync job  
- `.env.example` — document new vars  

**Out:**
- Web app changes (web reads `jogos` from BigBase — no change needed)  
- Auth / ranking logic  
- Switching away from apifootball.com  

---

## Stories

| ID | Title | BCP |
|---|---|---|
| e02-s01 | `fixtures.py` — fetch & normalise fixtures from apifootball.com | 1 |
| e02-s02 | Config: add `FIXTURES_PROVIDER` env var | 0.5 |
| e02-s03 | `BigBase.ensure_setup` — upsert from API, store `api_fixture_id` | 1 |
| e02-s04 | `results.py` — match results by `api_fixture_id` (exact, not name heuristic) | 0.5 |
| e02-s05 | `/sync_jogos` admin command + `job_sync_fixtures` (24 h) | 0.5 |
| e02-s06 | `.env.example` + README docs | 0.5 |

**Total BCP: 4**

---

## Key decisions

- **Match IDs stay as-is for group stage** (`R1-01` … `R3-72`). Existing palpites
  in BigBase keep their `match_id` foreign keys intact.
- **Knockout rounds** get new IDs in the pattern `KO-R16-01`, `KO-QF-01`, etc.,
  generated from the API's `match_round` field.
- `api_fixture_id` is stored as a separate field on every `jogo` record.
- If `FIXTURES_PROVIDER` is empty the bot falls back to the hardcoded list
  exactly as today — zero regression.
