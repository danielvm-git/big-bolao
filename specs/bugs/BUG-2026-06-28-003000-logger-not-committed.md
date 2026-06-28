# BUG-2026-06-28-003000: bot fails to start — logger.py not committed

## Problem

All Telegram bot commands (`/jogos`, `/ranking`, `/palpitar`, etc.) stopped working
after the `feat(scoring)` deploy (v1.14.0).

- **Actual**: bot is unreachable; all commands time out or get no response
- **Expected**: bot starts normally and handles commands
- **Reproduce**: deploy any commit where `bot.py` imports `bolao.logger` but
  `bolao/logger.py` is not in the repository

## Root Cause Analysis

The `feat(scoring)` commit staged a version of `bot.py` that had been modified
(from a local stash) to replace stdlib logging with a custom `bolao.logger` module:

```
# removed from bot.py:
import logging
logging.basicConfig(...)
log = logging.getLogger("bolao")

# added in its place:
from bolao.logger import get_logger
log = get_logger("bolao.bot")
```

However, `bolao/logger.py` — the module that defines `get_logger` — was never staged
or committed. It existed only as an untracked local file.

At server startup, Python raises `ModuleNotFoundError: No module named 'bolao.logger'`
before the bot's `build_app()` is ever called. The bot thread never starts; all
Telegram commands are permanently unresponsive.

The CI tests do not catch this because they test individual modules (ranking, fixtures,
scoring, etc.) and never import `bolao.bot` directly. The health check only verifies
HTTP 200 from the web app, which stays up even when the bot thread is dead.

**Risk level: High** — all bot functionality is completely down until `logger.py` is
committed and redeployed.

## TDD Fix Plan

1. **RED**: Write a test that imports `bolao.bot` and verifies it can be imported
   without error.
   **GREEN**: Commit `bolao/logger.py` to the repository.
   **verify**: `python -c "import bolao.bot; print('OK')"`

2. **RED**: Write a test that verifies `bolao.logger.get_logger()` returns a
   `logging.Logger` instance.
   **GREEN**: Already done — `logger.py` defines this correctly.
   **verify**: `python -m pytest tests/test_logger.py -v`

**REFACTOR**: No refactor needed — the module is clean and documented.

## Acceptance Criteria

- [x] `bolao/logger.py` is committed and present in the deployed repo
- [x] `python -c "import bolao.bot"` succeeds on the server
- [x] Bot responds to `/jogos` again (verified by deploy)
- [x] Existing tests still pass (110 pass, 5 new logger tests added)

## Resolution

Committed `bolao/logger.py` (the missing module) and added `tests/test_logger.py`
(5 tests covering import, `get_logger()`, `JSONFormatter`, and `bolao.bot` importability).
Full suite: 110 passed.
