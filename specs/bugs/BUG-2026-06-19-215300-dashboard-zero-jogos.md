# BUG-2026-06-19-215300: Dashboard shows "0 0 jogos finalizados" — data never loads for unauthenticated users

## Problem

**Actual behavior:** Visiting `/dashboard` shows "● 0 0 jogos finalizados" in the sticky header. Ranking and game list are empty.

**Expected behavior:** The Dashboard is a public page (no login required). It should display live data: 30 encerrados / 72 total jogos, and the real ranking.

**Side effect:** DashboardView's sticky header has `z-index: 100`, which is higher than the LoginView overlay (`z-index: 50`), so the "0/0" header peeks through the login modal on top of the real content.

## Root Cause Analysis

`useJogos` and `useRanking` both gate all data fetching behind a `watch(isLoggedIn, ...)`. They only fetch from BigBase when `isLoggedIn` transitions to `true`. The Dashboard is mounted and rendered for unauthenticated users, but `jogos.value` stays `[]` and `rankingData.value` stays `[]` because the auth trigger never fires.

The DB has **72 jogos** and **30 encerrados** — the data exists; the composables never request it.

Risk level: **Low** — read-only public data, no auth or security impact.

## TDD Fix Plan

1. **RED**: Write a test that mounts `DashboardView` without an authenticated user and asserts the `finalizadoCount` is non-zero (fetched from API).
   **GREEN**: In `DashboardView`, call `fetchJogos()` and `fetchParticipantes()` / `calcRanking()` directly on `onMounted` — bypass the `isLoggedIn` watch entirely. The Dashboard owns its own data fetch.
   **verify**: `npm run test -- dashboard` (or Vitest equivalent)

2. **RED**: Write a test asserting the sticky header text is NOT "0/72" when mock API returns games.
   **GREEN**: Ensure `finalizadoCount` and `totalGames` are computed from the locally fetched `jogos` ref, not from `useJogos()`.
   **verify**: Same test run.

3. **RED**: Write a test that mounts `LoginView` as an overlay and asserts it covers the `DashboardView` sticky header (z-index check or stacking check).
   **GREEN**: Raise `LoginView` overlay z-index from 50 to 110 (above `dash-header` z-index 100).
   **verify**: Visual regression or CSS unit test.

**REFACTOR**: Extract a `useDashboardData()` composable (or an `onMounted` block in `DashboardView`) that fetches jogos + ranking unconditionally, with no auth dependency. Keep `useJogos`/`useRanking` for authenticated views (HomeView, JogosView, etc.).

## Acceptance Criteria

- [ ] `/dashboard` shows correct `finalizadoCount / totalGames` without being logged in
- [ ] Ranking list in the Dashboard is populated without auth
- [ ] LoginView overlay fully covers the Dashboard content (z-index fix)
- [ ] No regression in authenticated views (HomeView, JogosView)
- [ ] All existing tests pass
