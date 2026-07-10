# Story e07-s03: Extract ResultsPublisher controller

**type:** refactor
**context:** infra
**Phase:** Sustain — Architecture Deepening

## Context

The sync-results flow in handlers.py (`_sync_resultados` at line 288) orchestrates:
fetch results from API → save to DB → publish each result → publish ranking.
This is a controller that reaches into `results_mod.buscar_encerrados`, `db.set_resultado`,
`_publicar_resultado`, and `_publicar_ranking` — all mixed in one inline function.

This story extracts `ResultsPublisher` into `bolao/results_publisher.py`, a testable
controller that takes `(db, results_provider, announcer)` as constructor dependencies.
The inline `_sync_resultados` is replaced by `ResultsPublisher.sync()`. The admin
commands `cmd_resultado`, `cmd_sync`, and `job_sync` are rewired.

**Reason for Depth (ResultsPublisher):** Encapsulates a 3-step orchestration (fetch →
save → publish) that currently spans 4 inline functions. A controller object with
injected dependencies enables unit-testing the orchestration without mocking Telegram.

## Steps

1. Create `bolao/results_publisher.py` with `ResultsPublisher` class:
   - `__init__(self, db, results_provider, announcer)` — stores 3 dependencies
   - `publish_result(jogo, *, force=False)` → get palpites via db → format_resultado → announcer.announce
   - `publish_ranking(*, force=False)` → get_jogos + get_palpites + listar_participantes via db → format_ranking → announcer.announce
   - `sync(*, force=False) -> int` → buscar_encerrados loop → for each: set_resultado + publish_result → if any: publish_ranking → return count
     → verify: `python -c "from bolao.results_publisher import ResultsPublisher; print('OK')"`

2. Rewire `_sync_resultados` in handlers.py to delegate to `ResultsPublisher(db(context), results_mod, announcer_from(context)).sync(force=manual)`
   → verify: `python -c "import bolao.handlers; print('OK')"`

3. Rewire `cmd_resultado` to use `publish_result(jogo, force=True)` via builder
   → verify: `python -c "import bolao.handlers; print('OK')"`

4. Rewire `cmd_sync` to delegate to `publish` / `sync`
   → verify: `python -c "import bolao.handlers; print('OK')"`

5. Write `tests/test_results_publisher.py` with fake db + fake announcer (no Telegram):
   - Test `publish_result` fetches palpites and announces result
   - Test `publish_ranking` fetches data and announces ranking
   - Test `sync` calls buscar_encerrados, saves each, publishes each, publishes ranking
   - Test `sync` returns correct count
   - Test `sync` with no new results (empty list) skips ranking
   - Test error in publish_result doesn't break loop (continues to next)
     → verify: `python -m pytest tests/test_results_publisher.py -v`

6. Full regression sweep
   → verify: `python -m pytest tests/ -q` (166 pass)

## Verification Script

1. `python -m pytest tests/test_results_publisher.py -v` → 6+ tests pass
2. `python -m pytest tests/test_quiet_hours.py tests/test_group_publisher.py tests/test_ranking.py -v` → 34 pass
3. `python -m pytest tests/ -q` → all 166 pass

## Out of scope

- Moving jobs (e07-s04)
- Doc updates (e07-s05)

## Risks

- **Inline import**: `job_sync_fixtures` uses `from bolao.fixtures import fetch_from_api` inside the function body (line 368). This story doesn't touch it — it stays inline until e07-s04.
- **Error handling**: The current `_sync_resultados` wraps each `_publicar_resultado` in a try/except that logs and continues. ResultsPublisher.sync must preserve this per-item error handling — a single bad result must not abort the whole sync.
