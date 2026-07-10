# Story e07-s01: Extract GroupAnnouncer — deep group-channel + quiet-hours seam

**type:** refactor
**context:** infra
**Phase:** Sustain — Architecture Deepening

## Context

handlers.py contains two duplicated quiet-hours gates (`_publicar_resultado` line 316,
`_publicar_ranking` line 331) and 4 raw `send_message(GRUPO_CHAT_ID, ...)` sites
(lines 321, 336, 351, 418). Each reaches into `context.bot` + `context.bot_data` +
module-level `is_quiet_hours()` at once — making the group-publication path untestable.

This story creates `bolao/group_channel.py` with a `GroupAnnouncer` class that owns
the official-group Telegram channel as a deep I/O seam. It lands alongside the existing
code with zero callers rewired — pure net-new module with its own test suite.

**Reason for Depth (GroupAnnouncer):** Wraps three orthogonal concerns (Telegram I/O,
quiet-hours deferral, message queuing) behind a 2-method interface, making each testable
individually. An inline helper would not separate queue management from send logic.

## Steps

1. Create `bolao/group_channel.py` with `GroupAnnouncer` class (3 imports: telegram.ParseMode, config, logging)
   → verify: `python -c "from bolao.group_channel import GroupAnnouncer; print('OK')"`

2. Implement `__init__(self, bot, chat_id, queue, should_defer)` — stores 4 references, no logic
   → verify: `python -c "from bolao.group_channel import GroupAnnouncer; a = GroupAnnouncer(None, 0, [], lambda: False); print('OK')"`

3. Implement `announce(text, *, force=False)`:
   - If no chat_id (falsy): noop
   - If not force AND should_defer(): append `{"texto": text, "parse_mode": "HTML"}` to queue, log "enfileirada"
   - Else: await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
     → verify: `python -m pytest tests/test_group_channel.py -k "test_announce" -q`

4. Implement `flush()`:
   - If no chat_id or empty queue: return (clear queue)
   - Iterate queue with enumerate; for each item, await bot.send_message; if not last item, await asyncio.sleep(2)
   - Clear queue after loop
     → verify: `python -m pytest tests/test_group_channel.py -k "test_flush" -q`

5. Add `announcer_from(context)` factory function:
   - Returns `GroupAnnouncer(context.bot, config.GRUPO_CHAT_ID, context.bot_data.setdefault("pending_results", []), is_quiet_hours)`
     → verify: `python -c "from bolao.group_channel import announcer_from; print('OK')"`

6. Write `tests/test_group_channel.py` with full test suite:
   - Test announce sends when not quiet hours
   - Test announce enqueues when quiet hours (not force)
   - Test announce sends when force=True (even during quiet hours)
   - Test announce noop when no chat_id
   - Test flush sends all queued + clears
   - Test flush handles empty queue
   - Test flush has 2s gap between sends
   - Test flush noop when no chat_id
   - Test flush logs appropriately
   - Test announcer_from factory returns configured GroupAnnouncer
     → verify: `python -m pytest tests/test_group_channel.py -v`

## Verification Script

1. Run the new test suite: `python -m pytest tests/test_group_channel.py -v` → 10+ tests pass
2. Confirm no existing tests broke: `python -m pytest tests/ -q` → 166 pass
3. Confirm module imports cleanly: `python -c "from bolao.group_channel import GroupAnnouncer, announcer_from"` → no error

## Out of scope

- Rewiring existing callers in handlers.py (e07-s02)
- Extracting ResultsPublisher (e07-s03)
- Creating jobs.py (e07-s04)
- Doc updates (e07-s05)

## Risks

- **Mocking gap**: If the 2s gap is `asyncio.sleep` patched in tests, the tests could pass with wrong timing — the flush test must actually assert calls happen with sleeps between them.
- **queue mutation**: Tests that pass a list and check it's cleared must verify the original list is mutated (not a copy).
