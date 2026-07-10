# Big Bolão — Conventions

## Git

- **Conventional Commits** mandatory. Format: `type(scope): description`. Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- Branch naming: `<type>/<slug>` for features, `fix/<slug>` for bugs, `docs/<slug>` for docs.
- Never push to `main` directly except via automated tooling (semantic-release, CI auto-commits).
- Never force-push to `main` or any shared branch.

## Code

- **Python**: Type hints on all public functions. `from __future__ import annotations` in every module.
- **Python**: Structured JSON logging via `bolao/logger.py`. Never `print()` in production code.
- **Python**: Config from `bolao/config.py` — never read env vars directly outside config or `app.py`.
- **Vue/JS**: Composition API with `<script setup>`. No Options API.
- **Vue/JS**: Named exports only from modules. No default exports except Vue components.
- **CSS**: No inline styles. No external CDNs (BigBase CSP blocks them).
- **All**: Never hardcode secrets, tokens, passwords, or PII anywhere in the repo. Read from `.env`.

## Testing

- **TDD**: Red → Green → Refactor. Write the test first, see it fail, then implement.
- **Coverage gates**: P0 modules (scoring, fixtures, ranking) ≥ 90%. Business logic ≥ 95%.
- **Golden fixtures**: `specs/test-strategy/scoring-golden.json` and `parse-result-golden.json` are shared truth between Python and JS suites. Changes to scoring rules must update both.
- Tests go in `tests/` (Python) or `web/tests/` (JS). One test file per source module.

## Specs & Planning

- All planning output goes in `specs/`.
- Epic capsules in `specs/epics/eNN-slug/`.
- ADRs in `specs/adr/`.
- Bug investigations in `specs/bugs/BUG-*.md`.
- State tracking in `specs/state.yaml` — update before and after every major step.

## Agent Rules

- Read `AGENTS.md` and `specs/` before writing code.
- Use bigpowers skills (`plan-work`, `develop-tdd`, `release-branch`, etc.) for structured work.
- Always Green: Preflight and CI must be green before forward work.
- Write the minimum code that solves the stated problem.
- Run tests after every change. Show evidence before declaring done.
- Never dismiss reproducible gate failures as pre-existing or out of scope.

## Never

- Never hardcode secrets, tokens, or credentials. Read from `.env` only.
- Never commit `web/dist/` build output manually (CI handles it).
- Never use `print()` for logging — use `bolao/logger.py`.
- Never dismiss reproducible gate failures.
- Never proceed on red Preflight or red CI.
