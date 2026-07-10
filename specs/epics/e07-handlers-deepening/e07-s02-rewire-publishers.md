# Story e07-s02: Rewire publishers through GroupAnnouncer (behavior-preserving)

**type:** refactor
**context:** infra
**Phase:** Sustain — Architecture Deepening

## Context

The four sites in handlers.py that call `context.bot.send_message(config.GRUPO_CHAT_ID, ...)`
(lines 321, 336, 351, 418) and the two duplicated quiet-hours gates (lines 316, 331) operate independently but follow identical logic. With GroupAnnouncer landed
(e07-s01), this story replaces all inline publication logic with
`announcer_from(context).announce(...)` calls.

**Hard-gate invariant** (must survive byte-for-byte):

- A publication defers to the morning-flush queue **iff** `is_quiet_hours()` **and not** manually triggered
- Manual (`/sync`, `/resultado`) and lembrete always send immediately
- Flush drains FIFO with 2s gap between messages

## Steps

1. Replace `_publicar_resultado` body: call `announcer_from(context).announce(texto, force=manual)` instead of inline quiet-hours check + send_message
   - Remove: early return on `not config.GRUPO_CHAT_ID`, `is_quiet_hours()` check, queue append, manual send_message
   - Keep: fetch d/palpites, format_resultado call, logging
     → verify: `python -m pytest tests/test_quiet_hours.py -v` (14 tests must pass unchanged)

2. Replace `_publicar_ranking` body: call `announcer_from(context).announce(texto, force=manual)` instead of inline quiet-hours check + send_message
   - Same removals as step 1
   - Keep: fetch d/jogos/palpites/participantes, format_ranking call
     → verify: `python -m pytest tests/test_quiet_hours.py -v` (still 14 pass)

3. Replace `job_morning_flush` body: call `announcer_from(context).flush()` instead of inline queue drain
   - Remove: import asyncio, inline loop with send_message + sleep + clear
   - Keep: logging
     → verify: `python -m pytest tests/test_quiet_hours.py -v` (still 14 pass)

4. Replace `_postar_lembrete` body: call `announcer_from(context).announce(texto, force=True)` instead of inline send_message
   - Remove: early return on `not config.GRUPO_CHAT_ID`, manual send_message
   - Lembrete always sends immediately (force=True) — never defers
     → verify: `python -m pytest tests/test_group_publisher.py -v` (11 tests) + `python -m pytest tests/test_ranking.py -v` (9 tests)

5. Remove now-unused imports from handlers.py: `is_quiet_hours` import is no longer needed at module level
   → verify: `python -c "import ast; ast.parse(open('bolao/handlers.py').read()); print('syntax OK')"`

6. Full regression sweep
   → verify: `python -m pytest tests/ -q` (166 pass)

## Verification Script

1. `python -m pytest tests/test_quiet_hours.py -v` → 14/14 pass (this is the hard gate)
2. `python -m pytest tests/test_group_publisher.py tests/test_ranking.py -v` → 20/20 pass
3. `python -m pytest tests/ -q` → all 166 pass
4. Inspect handlers.py for remaining `send_message(GRUPO_CHAT_ID, ...)` calls: `grep -n "send_message.*GRUPO_CHAT_ID" bolao/handlers.py` → should be 0

## Out of scope

- Extracting ResultsPublisher controller (e07-s03)
- Relocating jobs to jobs.py (e07-s04)
- Doc updates (e07-s05)

## Risks

- **Import path change**: `test_quiet_hours.py` currently imports `from bolao.handlers import _publicar_resultado, job_morning_flush`. After rewiring, `_publicar_resultado` still exists in handlers.py (just shorter) — the import path doesn't change. The function signature doesn't change either. Tests should pass unchanged.
- **Logging**: The existing quiet-hours tests check for log messages with `"enfileirada"`. After rewiring, `GroupAnnouncer.announce` logs this — the test patching `bolao.handlers.is_quiet_hours` still works because `GroupAnnouncer.should_defer()` is `is_quiet_hours` (same import path via `announcer_from`). But the log source changes from `bolao.handlers` to `bolao.group_channel`. The test `test_auto_logs_enqueue` checks `caplog.messages` (any logger) — so it still passes.
