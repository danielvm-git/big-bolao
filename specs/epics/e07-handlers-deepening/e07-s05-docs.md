# Story e07-s05: Docs — tech-stack.md as-built + traceability update

**type:** docs
**context:** infra
**Phase:** Sustain — Architecture Deepening

## Context

After landing e07-s01 through e07-s04, three new modules exist:
`bolao/group_channel.py`, `bolao/results_publisher.py`, `bolao/jobs.py`. The
tech-stack.md has a "Planned deepening seam" note (in Signals section) that
must be promoted to as-built. The test-strategy traceability matrix needs the
new test files mapped to the quiet-hours invariant.

## Steps

1. Update `specs/tech-architecture/tech-stack.md`:
   - Promote the "Planned deepening seam" section in Signals to as-built status
   - Under "Bot Layer" architecture diagram, add the three new modules:
     ```
     handlers.py (routing only)
         ↓ db(context)
     bolao/group_channel.py (GroupAnnouncer — I/O seam)
     bolao/results_publisher.py (controller — orchestration)
     bolao/jobs.py (job wrappers)
     bolao/bigbase.py (data layer)
     ```
   - Update the Jobs list to show all 4 jobs correctly (currently only shows 2)
     → verify: `grep -q 'GroupAnnouncer' specs/tech-architecture/tech-stack.md`

2. Update `specs/test-strategy/traceability.md`:
   - Add `tests/test_group_channel.py` → mapping to quiet-hours invariant
   - Add `tests/test_results_publisher.py` → mapping to sync flow invariant
   - Update any references to handlers.py test coverage now that jobs are split out
     → verify: `grep -q 'test_group_channel' specs/test-strategy/traceability.md`

3. Verify no stale references to old module structure:
   - grep for `handlers.job_` in bot.py → should be 0
   - grep for `send_message.*GRUPO_CHAT_ID` in handlers.py → should be 0
   - grep for `is_quiet_hours` in handlers.py → should be 0
     → verify: all three greps return zero

## Verification Script

1. `grep -q 'GroupAnnouncer' specs/tech-architecture/tech-stack.md` → pass
2. `grep -q 'test_group_channel' specs/test-strategy/traceability.md` → pass
3. `grep -c 'handlers.job_' bolao/bot.py` → 0
4. `grep -c 'send_message.*GRUPO_CHAT_ID' bolao/handlers.py` → 0
5. `grep -c 'is_quiet_hours' bolao/handlers.py` → 0

## Out of scope

- Updating CLAUDE.md (only if new commands or env vars were added — none were)
- Changelog entry (automatic via semantic-release)

## Risks

- None — pure documentation. If any grep check fails, it means a code step was missed.
