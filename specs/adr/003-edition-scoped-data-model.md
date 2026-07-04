---
status: accepted
date: 2026-07-04
---

# ADR 003 — Edition-scoped, single-active multi-tournament data model

## Context

The app is dual-use: men's World Cup 2026 (current), then women's World Cup 2027
on the same codebase. Today there is no notion of "which tournament" — `matches.py`
hardcodes 72 Copa-2026 games and `jogos`/`palpites`/`participantes` live in flat
collections. Next year's data must not collide with this year's.

## Decision

Introduce an **Edition** (tournament season, e.g. `wc-men-2026`, `wc-women-2027`)
as the season boundary for all data.

1. **Every `jogo`, `palpite`, and `participante` carries an `edition` field** and
   all queries filter by a single `ACTIVE_EDITION` config value. (Chosen over
   wipe-and-reseed, which loses history, and over separate collections/BigBase
   projects, which fragment the one backend.)
2. **Participants are edition-scoped.** Identity is `(edition, telegram_id)`. The
   same human playing both cups is two independent records, scored separately;
   nobody carries over. Everyone `/start`s fresh for a new edition at zero.
3. **`ACTIVE_EDITION` is a single value, never a set.** Editions are strictly
   sequential — the men's cup is fully finished and archived before the women's
   cup is seeded. No concurrent-edition support.
4. **Scoring rules are NOT edition-scoped.** `FASE_PONTOS` and group-stage
   defaults stay global code constants. An Edition does not carry a point table.
5. **Placeholder / fuzzy name auto-link is a `wc-men-2026`-only bootstrap** (it
   exists solely to migrate the historical spreadsheet). It must be gated off for
   editions that start from zero. See the fuzzy-match defect noted in tech-stack.md.

## Consequences

- Touches every read path in `bigbase.py`, `queries.js`, and ranking (add an
  `edition` filter). This is the main cost and the reason it's recorded here.
- 2026 data stays queryable after 2027 seeds — history preserved for stats.
- New edition = a config flip (`ACTIVE_EDITION`) + fixture re-seed, no code change.
- e06 can freeze the scoring contract with no edition dimension (point 4).
- Sequencing: implement before the women's-cup seed; not required for the rest of
  the 2026 season (single implicit edition works until a second one exists).
