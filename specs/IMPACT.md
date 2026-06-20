# Impact Assessment — All Identified Gaps

> Generated: 2026-06-20
> Scope: 7 gaps found in codebase audit, covering code changes, spec inconsistencies, and planning gaps.

---

## Gap 1 — Deploy fail (BUG-2026-06-19-190000)

**Target:** New `package.json` at repo root (workaround for BigBase `DetectAppType` ignoring `root_path`)

### Dependents
- BigBase deploy pipeline (external) — looks for `package.json` at clone root
- `web/package.json` — existing file, not affected (new root-level file delegates to it)

**Callers: 0** (new file, no existing dependents)

### Affected Stories
- `e01-s11` — Deploy no BigBase (currently `pending`; this fix unblocks it)

### Test Coverage
- None needed — root `package.json` with `"scripts": {"build": "cd web && npm install && npm run build"}` and Vite `outDir` adjustment is a build config change, not testable logic
- Verify: `npm install && npm run build` at root produces `dist/` or `web/dist/`

### Risk: **Low**
New file, zero existing callers. Risk is misconfiguration (wrong `outDir`) which is caught on first deploy attempt. No regression possible.

### Recommended Action: Proceed directly

---

## Gap 2 — Duplicate participants (BUG-2026-06-20-100000)

**Target:** `BigBase.registrar_participante()` in `bolao/bigbase.py`
Change scope: Add placeholder scan (`telegram_id < 0`) before creating new participant; extract `_placeholder_por_nome_parcial()` helper; rename `participante_por_nome` → `participante_por_nome_exato`.

### Dependents (count: 3)

| File | Usage |
|------|-------|
| `bolao/handlers.py:50` | `cmd_start` calls `registrar_participante(user.id, nome)` |
| `bolao/handlers.py:75` | `cmd_sou` calls `reivindicar(nome, user.id)` — indirectly affected (placeholder already linked) |
| `scripts/seed_bigbase.py:29` | Creates placeholders with `telegram_id=-1..-7` — these are the targets of the scan |

### Module Dependency Graph

```
registrar_participante()
  └─ get_participante()       ← also called by reivindicar(), cmd_jogos flow
  └─ participante_por_nome()  ← also called by reivindicar()
  └─ create()
  └─ patch()

participante_por_nome rename → participante_por_nome_exato
  └─ registrar_participante()  ← single caller after rename
  └─ reivindicar()             ← single caller after rename
```

### Affected Stories
- No story in release-plan covers participant registration hardening
- Related to all stories that use `/start` or `/sou` (e01-s01 through e01-s09, implicitly)

### Test Coverage

| Test File | Covers |
|-----------|--------|
| `tests/test_ranking.py` (9 tests) | `calcular` + `formatar` — tests inactive participant exclusion (indirectly touches this area) |
| **None** | `registrar_participante` — **zero tests** |
| **None** | `participante_por_nome` — **zero tests** |
| **None** | `reivindicar` — **zero tests** |
| **None** | Placeholder scan logic — **zero tests** |

**Gap:** The entire participant registration flow has zero test coverage. BUG-2026-06-20-100000's TDD plan specifies 3 test cycles, but they were never written.

### Risk: **Medium**

**Rationale:**
- 3 direct callers, 2 of which are production paths (`/start`, `/sou`)
- Zero test coverage on the target method — any refactor carries risk of breaking user registration
- The bug itself is low-severity (duplicate participants are fixable manually), so a mistake during the fix would not cause data loss
- However: `reivindicar` has palpite migration logic (PATCH loop) — a bug here *could* lose historical palpites

### Recommended Action
1. **Write tests first** (as outlined in existing TDD plan in BUG-2026-06-20-100000.md)
2. Then implement the fix
3. Verify `python -m pytest tests/ -v` passes before and after

---

## Gap 3 — Stories órfãs (e01-s12, e01-s13, e01-s14)

**Target:** `specs/release-plan.yaml` — add 3 stories to the e01 stories list

### Dependents

| Story | File | Status |
|-------|------|--------|
| `e01-s12` (Country Detail) | `epic.yaml` exists | Done per execution-status |
| `e01-s13` (Timeline de eventos) | `epic.yaml` exists | `planned` |
| `e01-s14` (Grade de Palpites) | `epic.yaml` exists | Done per execution-status (part of e03-s04) |

### Callers: 0 — pure spec change

### Affected Stories
None — these stories already exist in `epic.yaml` but were never added to the release plan index

### Test Coverage
N/A — spec change only

### Risk: **Low**
No code change. Updating release-plan.yaml to include these stories is documentation reconciliation. No regression.

### Recommended Action: Proceed directly

---

## Gap 4 — API Integration (e02, 0/6 stories implemented)

**Target:** Multiple files across the bot module
- `bolao/fixtures.py` — **exists** (14 tests, normalise + parse_result + fetch_from_api)
- `bolao/bigbase.py` — modify `ensure_setup()` to upsert from API fixtures instead of hardcoded `MATCHES`
- `bolao/results.py` — **exists** (uses `api_fixture_id` matching — already done)
- `bolao/handlers.py` — add `/sync_jogos` admin command + `job_sync_fixtures`
- `bolao/bot.py` — register new command + fixture-sync job
- `bolao/config.py` — add `FIXTURES_PROVIDER` env var
- `.env.example` — document new vars

### Dependents

| Symbol / File | Callers | Impact |
|---------------|---------|--------|
| `fixtures.py:FINISHED_STATUSES` | `results.py` — imported and used | **Already shared** ✓ |
| `fixtures.py:parse_result()` | `results.py:80` — called in `_apifootball()` | **Already shared** ✓ |
| `fixtures.py:fetch_from_api()` | 0 callers (new — will be called by `ensure_setup`) | **Net-new** |
| `bigbase.py:ensure_setup()` | `bot.py:24`, `seed_bigbase.py:29` | **Modified** — existing callers must continue to work unchanged |
| `bigbase.py:list_records()` | 11 callers across `bigbase.py`, `handlers.py`, `ranking.py`, `group_publisher.py` | **Not changed** |
| `results.py:buscar_encerrados()` | `handlers.py:_sync_resultados()` | **Already using api_fixture_id** ✓ |
| `config.py` | `validate_config()` → `FIXTURES_PROVIDER` validation | **Add new var** — no existing contract broken |

### Affected Stories
- `e02-s01` — `fixtures.py` (DONE — exists and tested)
- `e02-s02` — `FIXTURES_PROVIDER` env var (DONE — in epic design, not yet in config)
- `e02-s03` — `BigBase.ensure_setup` upsert from API (NOT STARTED)
- `e02-s04` — `results.py` match by `api_fixture_id` (DONE — already implemented)
- `e02-s05` — `/sync_jogos` admin command + job (NOT STARTED)
- `e02-s06` — `.env.example` + docs (NOT STARTED)

### Test Coverage

| Test File | Tests | Covers |
|-----------|-------|--------|
| `tests/test_fixtures.py` | 14 tests | Phase parsing, BRT conversion, normalise, finished/pending matches ✅ |
| `tests/test_results.py` | 7 tests | api_fixture_id match, name fallback, FT score hierarchy ✅ |
| `tests/test_config.py` | 5 tests | Provider validation for apifootball ✅ |
| **None** | — | `fetch_from_api()` with mocked HTTP — **gap** |
| **None** | — | `ensure_setup()` with API upsert — **gap** (would need BigBase mock) |
| **None** | — | `/sync_jogos` handler — **gap** |

### Risk: **Medium**

**Rationale:**
- **fixtures.py** + **results.py** core logic is already written and tested (21 tests)
- What remains is integration: wiring `ensure_setup()` to call `fetch_from_api()`, registering commands, and admin handlers
- Risk points: `ensure_setup()` currently seeds from hardcoded `MATCHES` — changing it to call `fetch_from_api()` could break startup if the API is down or returns unexpected data
- `ensure_setup` is called at bot startup (`bot.py:_post_init`) — any exception here prevents the bot from starting
- **Mitigation:** Keep fallback: if API fails, fall back to `MATCHES` (current behavior)

### Recommended Action
1. Add `fetch_from_api()` integration test (mock HTTP)
2. Implement `ensure_setup` upsert with graceful fallback to `MATCHES`
3. Add `/sync_jogos` command handler + `job_sync_fixtures`
4. Update `.env.example`

---

## Gap 5 — e03 status discrepancy

**Target:** `specs/release-plan.yaml` + `specs/epics/e03-web-dashboard/epic.yaml`
- e03-s01 through e03-s08 all exist in code but are marked `planned` in release-plan.yaml
- `epic.yaml` says `status: planned`

### Dependents: 0 — spec changes only

### Affected Stories
- e03-s01 through e03-s08: all were implemented but never marked done in specs

### Test Coverage
N/A — web dashboard views exist and are functional. Vue components are tested via `web/tests/` (scoring, transport, queries, flags).

### Risk: **Low**
Spec change only. No code touched.

### Recommended Action: Proceed directly

---

## Gap 6 — e04 status discrepancy

**Target:** `specs/release-plan.yaml` + `specs/epics/e04-github-actions/epic.yaml` + `specs/execution-status.yaml`
- `.github/workflows/ci-cd.yml` exists (200+ lines, fully functional)
- `epic.yaml` says `status: planned`
- `release-plan.yaml` says epic `done` but all 8 stories `planned`
- `execution-status.yaml` doesn't mention e04 at all

### Dependents: 0 — spec changes only

### Affected Stories
- e04-s01 through e04-s08: all implemented in `.github/workflows/ci-cd.yml`

### Test Coverage
N/A — the workflow is already running on push to main. Validation is in the deploy logs.

### Risk: **Low**
Spec change only. No code touched.

### Recommended Action: Proceed directly

---

## Gap 7 — e01-s11 Deploy pending

**Target:** Unblocked by fixing Gap 1 (deploy fail bug). 
- Changing `web/vite.config.js` to output to project root `dist/` OR adding `package.json` at root delegating build
- Then: push to GitHub → BigBase auto-deploys

### Dependents
- `app.py:68` — serves `web/dist/` (if `outDir` changes to `dist/`, `app.py` path must update too)

### Affected Stories
- `e01-s11` — Deploy no BigBase (currently `pending`)

### Risk: **Low** (contingent on Gap 1 fix)

### Recommended Action: Fix Gap 1 first, then trigger deploy

---

## Summary

| # | Gap | Risk | Action |
|---|-----|------|--------|
| 1 | Deploy fail (BUG-deploy) | **Low** | Add root `package.json` with build delegate |
| 2 | Duplicate participants (BUG-duplicate) | **Medium** | Write tests first, then implement placeholder scan |
| 3 | e01-s12/s13/s14 orphans | **Low** | Add to release-plan.yaml |
| 4 | e02 API Integration (0/6 done) | **Medium** | Wire existing fixtures.py into ensure_setup + add cmds |
| 5 | e03 status discrepancy | **Low** | Update release-plan.yaml + epic.yaml |
| 6 | e04 status discrepancy | **Low** | Update release-plan.yaml + epic.yaml + execution-status.yaml |
| 7 | e01-s11 deploy pending | **Low** | Blocked on Gap 1 |

**2 code gaps** (G1, G2, G4) — require implementation
**3 spec gaps** (G3, G5, G6) — fast documentation fixes
**1 dependency** (G7) — blocked on G1
