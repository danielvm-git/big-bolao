# Story e07-s04: Relocate job\_\* wrappers to jobs.py; handlers.py = routing only

**type:** refactor
**context:** infra
**Phase:** Sustain — Architecture Deepening

## Context

Four job wrappers currently live in handlers.py (lines 360–423): `job_sync`,
`job_sync_fixtures`, `job_lembrete`, `job_morning_flush`. They are registered
in bot.py by name: `handlers.job_sync`, `handlers.job_lembrete`, etc.

After e07-s01→s03, these functions are thin wrappers that delegate to
ResultsPublisher or GroupAnnouncer. Moving them to `bolao/jobs.py` lets
handlers.py become pure routing (command + callback handlers only).

Additionally, there's an inline `from bolao.util import kickoff_dt` inside
`kickoff_horas()` (line 356) that should be moved to module-level.

## Steps

1. Create `bolao/jobs.py`:
   - Copy job_sync, job_sync_fixtures, job_lembrete, job_morning_flush from handlers.py
   - Update imports: `from bolao import config`, `from bolao.handlers import db`, `from bolao.group_channel import announcer_from`, logging, etc.
   - `job_sync_fixtures` keeps its inline `from bolao.fixtures import fetch_from_api` (it's the only function using it)
     → verify: `python -c "from bolao.jobs import job_sync, job_sync_fixtures, job_lembrete, job_morning_flush; print('OK')"`

2. Remove the four job functions from handlers.py (delete lines between `def kickoff_horas` and end of file)
   - Keep `kickoff_horas()` — it's used by `_postar_lembrete` which stays in handlers.py
     → verify: `python -c "import bolao.handlers; print('OK')"`

3. Update `bolao/bot.py` imports: change `handlers.job_sync` → `jobs.job_sync`, etc.
   - Add `from bolao import jobs`
   - Update all 4 job references in build_app()
     → verify: `python -c "from bolao import bot; print('OK')"`

4. Move inline `from bolao.util import kickoff_dt` to module-level in handlers.py
   - Current at line 356 inside kickoff_horas(); move to the util import block at line 20
     → verify: `python -c "import ast; ast.parse(open('bolao/handlers.py').read()); print('syntax OK')"`

5. Update `tests/test_version.py` import — it does `from bolao import handlers` which still works (handlers.py still exists)
   → verify: `python -m pytest tests/test_version.py -v` (3 tests pass)

6. Full regression sweep + import verification
   → verify: `python -m pytest tests/ -q && python -c "import bolao.bot, bolao.jobs, bolao.handlers; print('all import OK')"`

## Verification Script

1. `python -c "from bolao.jobs import job_sync, job_sync_fixtures, job_lembrete, job_morning_flush"` → no ImportError
2. `python -c "from bolao import bot; print(bot.build_app())"` → builds without error
3. `python -m pytest tests/test_quiet_hours.py -v` → 14 pass (job_morning_flush now imported from jobs)
4. `python -m pytest tests/test_version.py -v` → 3 pass
5. `python -m pytest tests/ -q` → 166 pass
6. `python -c "import bolao.bot, bolao.jobs, bolao.handlers"` → all modules import cleanly

## Out of scope

- Doc updates (e07-s05)
- Any behavioral changes to the jobs themselves

## Risks

- **test_quiet_hours.py imports job_morning_flush from handlers.py**. After the move, the import must change to `from bolao.jobs import job_morning_flush`. Tests that only use `_publicar_resultado` are fine — it stays in handlers.py.
- **test_quiet_hours.py also imports `_publicar_resultado` from handlers.py** — this continues to work.
- **Circular imports**: jobs.py imports from handlers.py (`db()` function). handlers.py must NOT import from jobs.py (it doesn't). No cycle risk.
