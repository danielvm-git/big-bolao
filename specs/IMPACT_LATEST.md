# Impact Assessment — handlers.py Deepening (e07)

## Target

`bolao/handlers.py` — command/callback routing + group publication I/O + job wrappers.
423 lines, depth 2/5, 8–9 interleaved concerns.

## Dependents (3)

| File                        | Usage                                                                                 |
| --------------------------- | ------------------------------------------------------------------------------------- |
| `bolao/bot.py`              | Registers all CommandHandlers, CallbackQueryHandlers, and 4 jobs pointing at handlers |
| `tests/test_quiet_hours.py` | Imports `_publicar_resultado`, `job_morning_flush` directly (14 tests)                |
| `tests/test_version.py`     | Imports `handlers` module, tests `cmd_version` (3 tests)                              |

Additional internal callers (within handlers.py itself):

- `cmd_resultado` → `_publicar_resultado` (line 266)
- `cmd_sync` → `_sync_resultados` → `_publicar_resultado` + `_publicar_ranking` (lines 273, 296, 303)
- `job_sync` → `_sync_resultados` (line 363)
- `job_lembrete` → `_postar_lembrete` (line 403)

## Affected Stories

- **e07-s01**: Extract GroupAnnouncer (net-new module, no rewiring)
- **e07-s02**: Rewire publishers through GroupAnnouncer (behavior-preserving)
- **e07-s03**: Extract ResultsPublisher controller
- **e07-s04**: Relocate jobs to jobs.py
- **e07-s05**: Doc updates

## Test Coverage

| Test file                 | Tests | Scope                      | Affected by refactor?                                |
| ------------------------- | ----- | -------------------------- | ---------------------------------------------------- |
| `test_quiet_hours.py`     | 14    | Quiet-hours gating + flush | YES — imports directly from handlers.py              |
| `test_version.py`         | 3     | cmd_version handler        | NO — imports handlers module but tests command reply |
| `test_group_publisher.py` | 11    | Pure formatting            | NO — no handlers.py dependency                       |

**Gap**: 9 of 24 functions in handlers.py have zero test coverage (all command handlers
except cmd_version, plus 3 callback handlers). These are NOT part of the extraction's
scope — the epic only extracts the group-publication I/O path and jobs, which ARE tested.

## Risk: **Medium**

**Rationale:**

- Fan-in is small (3 files), but the module is at the center of the bot's call graph
- The 14 quiet-hours tests provide good regression guardrails for the most critical path
- 9 untested handlers are unaffected by extraction (they route to the same functions)
- Bot.py's job registration references need updating (e07-s04)
- Key invariant must be preserved: manual ≠ quiet-hours deferral ≠ lembrete immediate

## Recommended action

**Proceed.** The extraction preserves behavior and has adequate regression coverage
for the affected paths. The e07-s02 verify commands explicitly check that the 14
quiet-hours tests pass unchanged — this is the hard gate.
