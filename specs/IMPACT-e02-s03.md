# Impact Assessment — e02-s03: ensure_setup upsert from API

## Target

`BigBase.ensure_setup()` in `bolao/bigbase.py` (lines 92-105)

## Type of change

Modify existing method: add API upsert path with `api_fixture_id` as dedup key,
keep hardcoded MATCHES as fallback.

## Dependents (3 callers)

- `bolao/bot.py:29` — `await db.ensure_setup()` during bot startup
- `scripts/seed_bigbase.py:14` — `await db.ensure_setup()` for manual seeding
- `tests/test_bot.py:25` — `mock_db.ensure_setup = AsyncMock()` mocked reference

## Affected Stories

- e02-s03 — this story (upsert from API)
- e02-s01 — fixtures.py (fetch_from_api, normalise) — already done, consumed here
- No other stories affected directly (fallback preserves existing behavior)

## Test Coverage

- None of the 160 Python tests directly test `ensure_setup` behavior
- `test_bot.py` mocks it entirely
- `test_participantes.py` tests BigBase methods (participant registration)
- No existing test exercises the actual upsert flow

## Risk: LOW

- Only 3 internal callers
- Additive change with fallback → zero regression for existing callers
- No public API change, no schema change
- `api_fixture_id` field already expected by `results.py` and `fixtures.py`

## Recommended action

Proceed with plan-work. After implementation, add tests for the new ensure_setup behavior
(API path + fallback path).

## Gap

No test for `ensure_setup()` at all — should add at least 2 tests:

1. API success path: verify upsert with `api_fixture_id` dedup
2. API failure path: verify fallback to MATCHES preserves existing behavior
