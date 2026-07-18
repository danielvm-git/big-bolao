# BUG-2026-07-15T120400: Duplicate bot instance — zombie poller recurrence

## Problem

- **Actual:** Two bot instances are running simultaneously, competing for Telegram
  long-poll updates (409 Conflict). User observed two bots responding to commands.
- **Expected:** Only one bot instance polls the Telegram API at any time.
- **Repro:** Send any command in the group — intermittently answered by stale or current
  instance. `/ranking` format flips between old/new, `/version` may return different
  versions depending on which instance wins the poll.

## Root Cause Analysis

This is a **direct recurrence of BUG-2026-06-21-104800** (status: open in registry).

### Why the previous fix didn't prevent recurrence

The previous bug added:

1. `drop_pending_updates=True` on `run_polling` — only clears the queue on startup
2. 409 Conflict logging in `_handle_error` — detects but doesn't resolve
3. `/version` diagnostic command — helps identify but doesn't kill the zombie
4. Retry loop in `app.py:run_bot()` — handles transient deploy conflicts, not persistent ones

**None of these prevent a zombie from staying alive permanently.**

### Where the zombie lives

Two possible sources:

1. **Two BigBase sites** — AGENTS.md warns that `deploy_site` MCP deploys to
   `danielvm-git-big-bolao.bigbase.click` (auto-generated) while `redeploy.py`
   deploys to `bolao.bigbase.click`. Both run `app.py` → both start bot threads.
   If someone triggered `deploy_site` by mistake, the auto-generated site's bot
   keeps polling forever.

2. **Legacy VPS process** — `scripts/setup_server.sh` creates `/opt/bolao/` with
   `.env`. If a systemd service or manual `python -m bolao.bot` was started on the
   VPS, it persists across BigBase deploys (BigBase only manages its own processes).

### Why `app.py` retry loop doesn't help

The retry in `app.py:run_bot()` retries 12 times with backoff (5s, 10s, …, 60s).
If the other instance is ALSO persistent (not dying during deploy), the retry loop
exhausts and the **new** instance's bot thread dies — leaving the **old** zombie as
the sole poller. This is backwards: the new code should win, not the old.

## TDD Fix Plan

### Phase 1: Operational fix (no code change)

- [ ] SSH to BigBase server, check for duplicate processes
- [ ] Kill any zombie instance
- [ ] Verify `getUpdates` no longer returns 409

### Phase 2: Code hardening

1. **RED**: Write a test that `app.py:run_bot()` includes a PID/lock file mechanism —
   if a lock file exists and the PID is alive, refuse to start (log error).
   **GREEN**: Add `/tmp/bolao-bot.lock` with PID check before `run_polling`.
   **verify**: `python -m pytest tests/test_bot.py -k lock -v`

2. **RED**: Write a test that `app.py:run_bot()` treats 409 Conflict as fatal after
   N retries — the bot thread should exit cleanly (not hang), allowing the HTTP
   server to continue serving the web SPA.
   **GREEN**: After max_retries exhausted, log CRITICAL and return (don't raise).
   **verify**: `python -m pytest tests/test_bot.py -k conflict -v`

3. **RED**: Write a test that the bot startup verifies it's the intended deployment
   target by checking an env var (e.g., `BOLAO_BOT_ENABLED=true`). If not set, the
   bot thread skips `run_polling` entirely — the HTTP server still starts for
   health checks and web serving.
   **GREEN**: Gate bot thread on `BOLAO_BOT_ENABLED` env var (default `true`).
   **verify**: `python -m pytest tests/test_bot.py -k bot_enabled -v`

## Acceptance Criteria

- [ ] No 409 Conflict errors in live logs
- [ ] Only one bot instance polls Telegram at any time
- [ ] `BOLAO_BOT_ENABLED=false` allows running the web SPA without the bot
- [ ] PID lock file prevents duplicate local instances
- [ ] Bot thread exits cleanly on persistent 409 (HTTP server continues)
- [ ] All existing tests still pass (160 Python + 88 web)
- [ ] `python -m pytest tests/test_bot.py -v` passes with new tests

## Related

- **BUG-2026-06-21-104800**: Original zombie poller bug (same root cause class)
- **AGENTS.md**: Warning about `deploy_site` deploying to wrong site
- **app.py:run_bot()**: Current retry loop (12 attempts, 5s backoff)

## Resolution

<!-- filled in by validate-fix -->
