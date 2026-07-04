## Target

`BigBase.ensure_setup()` in `bolao/bigbase.py:92` — modify from hardcoded MATCHES seed to API upsert with `api_fixture_id`.

## Dependents (3)

- `bolao/bot.py:26` — called in `_post_init` at bot startup
- `scripts/seed_bigbase.py:29` — seed script for initial data
- `tests/test_bot.py:94` — mocked in `_post_init` unit test

## Affected Stories

- **e02-s03** (this story): BigBase.ensure_setup — upsert from API
- **e02-s05** (future): `/sync_jogos` command will reuse the same API-upsert pattern

## Test Coverage

- `test_bot.py`: mocks `ensure_setup` (verifies \_post_init calls it) — no logic test
- **Gap**: No tests for ensure_setup's actual behavior (seeding, dedup, api_fixture_id storage)

## Risk: Medium

3 callers, all mock-covered but logic untested. Interface stable (async method, no return). Adding integration-style tests recommended.

## Recommended action

Proceed with plan-work. Add a test for `ensure_setup` API upsert logic in the story's task list.
