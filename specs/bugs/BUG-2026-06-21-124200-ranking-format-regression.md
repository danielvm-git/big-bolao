# BUG-2026-06-21T124200: /ranking lost aligned monospace table format

## Problem

- **Actual:** `/ranking` rendered an unaligned bold-HTML list:
  `🥇 **Ricardo** — 23 pts  🎯4  ✅11  📋30`
- **Expected:** Aligned monospace table inside a `<pre>` block (Telegram "copy" box):
  ```
  🏆 Ranking do Bolao
  ──────────────────────────────────────
  🥇  Ricardo       23pts  🎯4  ✅11  📋30
  4º  Mari Gallo    14pts  🎯2  ✅ 8  📋28
  ```
  Names padded to column width, points/stats right-aligned.

## Root Cause Analysis

A prior fix commit (`e7b8dfb fix(ranking): use simpler format without code tags for
Telegram emoji rendering`) removed the `<pre>` block to work around an emoji-rendering
concern. That commit left the ranking unaligned (bold HTML, no column padding) and was
never reverted when the concern was resolved.

The correct output uses `<pre>` (Telegram renders it as a monospace code block with a
copy button). Emojis render correctly inside `<pre>` on all Telegram clients.

**Risk level:** Low — formatting only, no data or logic change.

## TDD Fix Plan

1. **RED**: Test that `formatar()` output contains `<pre>` and `</pre>` tags.
   **GREEN**: Wrap the table in `<pre>...</pre>`.
   **verify**: `python -m pytest tests/test_ranking.py -k formatar -v`

2. **RED**: Test that names are padded to uniform width (all lines same name-column width).
   **GREEN**: `ljust(max_name_len)` on each name; right-justify numeric columns.
   **verify**: `python -m pytest tests/test_ranking.py -k formatar -v`

**REFACTOR**: Single-pass width calculation before building lines.

## Acceptance Criteria

- [x] `formatar()` wraps output in `<pre>...</pre>`
- [x] Names left-padded to max name length across the rank
- [x] Points, exatos, acertos, jogos right-aligned per column
- [x] Separator line (`─`) under header
- [x] All existing ranking tests pass
- [x] No truncation of long names

## Resolution

Fixed in commit `0c9cdc4` (released as v1.12.3). Replaced bold-HTML unaligned format
with `<pre>` monospace table. Column widths computed from actual data each call so the
table self-adjusts as participants are added.
