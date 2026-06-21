# BUG-2026-06-21T104800: /ranking renders pre-June-20 format — stale zombie long-poller

## Problem

- **Actual:** At 10:46 today, `/ranking` in the group replied with the _original_ ranking
  format — `Nome — N pts (X exatos · Y/Z)` with `🥇🥈🥉`/`Nº` prefixes.
- **Expected:** The current format restored and re-confirmed this morning — bold name with
  `🎯{exatos} ✅{pts_simples} 📋{jogos}` stat icons, full (untruncated) names.
- **Repro:** Intermittent. Send `/ranking` repeatedly; some replies use the new format,
  some revert to the old one (depends on which poller wins the long-poll connection).

## Root Cause Analysis

This is **not a code regression** — it is an **operational regression from a duplicate
(zombie) bot instance** running stale code.

Evidence gathered during investigation:

- The source code is correct end-to-end. The `/ranking` command handler delegates to the
  group-publisher's `format_ranking`, which delegates to the ranking module's `formatar`,
  and that function produces the new bold + stat-icon format. There is exactly one
  formatter; no second code path emits the old string.
- The old string `({exatos} exatos · {acertos}/{jogos})` only ever existed in the
  **original** code and was retired on 2026-06-20. This morning's fix (10:14) shipped in
  releases 1.9.1 → 1.10.0 → 1.11.0; the last released at 10:43, three minutes before the
  failing screenshot.
- Crucially, the bot replied with code **older than June 20** — older than even this
  morning's _pre-fix_ state. A merely "deploy hasn't finished" explanation would surface
  this-morning's code, not week-old code. So the responder is a long-lived process that
  has not been restarted since before June 20.
- The bot runs via **Telegram long polling** (`getUpdates`). Telegram delivers each update
  to only one poller and returns **409 Conflict** when two instances share a token. With
  two instances alive, updates are answered by whichever currently holds the long-poll
  connection → the intermittent old/new flip-flop the user observed ("showed up again").

**Contributing factors:**

- A legacy manual deployment is implied by project docs referencing `/opt/bolao/.env on
server` (a VPS install via systemd/screen) in addition to the BigBase `app.py` thread.
- Nothing in the running system surfaces _which build_ answered a command, so a stale
  instance is invisible until output visibly diverges.

**Verification of root cause (run against the live token):**

- `getUpdates` returns `409 Conflict: terminated by other getUpdates request` → confirms a
  second poller exists.
- `getWebhookInfo` returns no webhook → confirms long polling (not a webhook race).
- Process/service inventory on the legacy host locates the stale instance.

**Risk level:** Medium. No data corruption, but user-facing inconsistency and any
write-capable command (`/sync`, `/resultado`) handled by the stale instance could apply
outdated logic.

## TDD Fix Plan

The _primary fix is operational_ (kill the duplicate poller); it has no unit test. The TDD
cycles below add **hardening so a stale instance is detectable and self-announcing**, which
is the part that survives radical codebase change.

1. **RED**: Write a test asserting the application exposes its running version/build
   identifier through a stable accessor (e.g. a `version()`/`build_info()` contract that
   reads the package version), independent of how it is wired into handlers.
   **GREEN**: Add the version accessor sourced from the release version (single source of
   truth already bumped by semantic-release).
   **verify**: `python -m pytest tests/ -k version -v`

2. **RED**: Write a test that an admin diagnostic command (`/version` or extending
   `/chatid`) returns text containing the running version identifier, so an operator can
   tell _which_ instance answered a command in the live group.
   **GREEN**: Register the diagnostic command handler that emits `version()`.
   **verify**: `python -m pytest tests/ -k "version or chatid" -v`

3. **RED**: Write a test that the bot startup path requests `drop_pending_updates=True`
   (or equivalent) and that a 409-conflict from polling is logged at error level with a
   clear "another instance is polling this token" message rather than silently retried.
   **GREEN**: Pass `drop_pending_updates=True` to `run_polling` and add explicit 409
   handling/logging in the polling error path.
   **verify**: `python -m pytest tests/ -k "polling or conflict" -v`

**REFACTOR**: None expected; keep the version accessor as the single source consumed by
both the diagnostic command and the startup log line.

## Acceptance Criteria

- [ ] `getUpdates` against the live token no longer returns 409 (only one poller).
- [ ] The legacy `/opt/bolao` (or other) duplicate instance is stopped and disabled, or
      confirmed absent.
- [ ] `/ranking` consistently returns the new bold + `🎯 ✅ 📋` format across repeated calls.
- [ ] A diagnostic command reports the running version so future stale instances are
      immediately identifiable.
- [ ] Startup logs a clear error if a 409 polling conflict occurs.
- [ ] All new tests pass.
- [ ] Existing tests still pass.

## Resolution

<!-- filled in by validate-fix -->
