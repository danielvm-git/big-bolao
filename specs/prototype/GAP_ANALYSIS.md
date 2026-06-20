# Gap Analysis: Prototype vs Current Website

> Generated: 2026-06-19
> Source: `specs/prototype/` (2 HTML prototypes)
> Target: `web/` (Vue 3 SPA em bolao.bigbase.click)

---

## 1. Mobile App Prototype (`Big Bolão.dc.html`)

**Status: ~90% implemented** — the current SPA already covers most views.

### ✅ Already Implemented

| View | Status | Notes |
|---|---|---|
| Login screen | ✅ Done | Logs via `?uid=` param from Telegram, mock fallback |
| Home — stats card | ✅ Done | Posição, pontos, exatos |
| Home — próximo jogo | ✅ Done | Card verde com CTA palpitar |
| Home — mini ranking | ✅ Done | Top 3 com avatar, medalha, pontos |
| Home — share card | ✅ Done | Convidar amigos |
| Jogos — filters | ✅ Done | 4 filtros: Abertos, Meus, Finalizados, Todos |
| Jogos — GameCard | ✅ Done | Status badge, times, placar, botão palpitar |
| Ranking — podium | ✅ Done | 3 degraus com cores |
| Ranking — full table | ✅ Done | Lista completa com destaque "Você" |
| Ranking — regra de pontuação | ✅ Done | Card informativo |
| Meus Palpites — 3 seções | ✅ Done | Abertos, Bloqueados, Finalizados |
| PalpiteModal | ✅ Done | Score picker +/-, quick scores, save |
| Resultado view | ✅ Done | Placar, meu palpite, quem cravou |

### 🔍 Gaps (Minor)

| # | Gap | Prototype Detail | Current Behavior | Effort |
|---|---|---|---|---|
| G01 | **Login flow** | Prototype shows a user card with avatar, name, stats ("Mari Gallo · 9 pts · #5"), and a "Continuar como" button. Also has "Abrir pelo link do Telegram" fallback. | Current shows a generic card saying "Acesse pelo Telegram". The rich user card with stats only appears in the mock login, not in the real flow. | Low |
| G02 | **Resultado as overlay** | Prototype renders Resultado as a **full-screen overlay** (`showResultado` state) on top of the app, keeping scroll position. | Current uses a **separate route** (`/resultado/:id`), navigating away from the user's context. | Medium |
| G03 | **"Ver quem cravou" — overlay** | In MeusPalpites, "Ver quem cravou" opens the Resultado overlay in place. | Current navigates to `/resultado/:id`, losing the MeusPalpites scroll position. | Medium |
| G04 | **Drag handle on modal** | Prototype has a `<div class="drag-handle">` on the PalpiteModal sheet. | Current has the same via `::after` pseudo-element. ✅ Already matches. | None |
| G05 | **Quick score highlight** | Prototype highlights the selected quick score in green (`bg: #00DC82`). | Current matches this with `.qs-btn.active`. ✅ Done. | None |

---

## 2. Web Dashboard Prototype (`Big Bolão Web.dc.html`)

**Status: ~0% implemented** — this is a completely different desktop-first layout.

### Key Differences from Current SPA

| Aspect | Current SPA | Prototype Web Dashboard |
|---|---|---|
| **Layout** | Mobile-first, 430px max-width | Desktop-first, 1440px max-width |
| **Header** | No header (only per-view titles) | Sticky header with logo, badge, progress (finalized/total), back button |
| **Navigation** | Bottom nav (4 tabs) | Header nav + breadcrumb-style back button |
| **Hero** | None | Stats bar: total players, finalized count, open games count + leader card |
| **Layout structure** | Single column, vertical scroll | Two-column grid: games list + ranking sidebar |
| **Cross-table** | Not implemented | Full matrix: rows=jogos × cols=participantes, color-coded cells |
| **Player detail** | Not implemented | Click any player → stats card (pts, exatos, vencedores, erros) + full list of their palpites |
| **Country detail** | Not implemented (e01-s12 planned) | Click team name/flag → W/D/L stats + list of their games |
| **Group detail** | Not implemented | Click group badge → standings table + games |
| **Color legend** | Not implemented | Color coding: green=exato, blue=vencedor, red=errou, orange=em andamento |

### 🔴 Critical Gaps (Not Implemented)

| # | Feature | Description | Relation to Existing Stories |
|---|---|---|---|
| G10 | **Cross-table matrix** | Full grid of jogos × participantes with color-coded cells showing every palpite. Sticky header with player names/avatars. Horizontal scroll. | `e01-s14` (planned) covers this |
| G11 | **Player detail page** | Click any player avatar/name in ranking or table → detail view showing: stats card (pts 🥇, exatos 🎯, vencedores ✓, erros ✗) + full list of all their palpites with per-game results. | **New** — not in existing epics |
| G12 | **Country/Team detail page** | Click team flag or name (from game card, table row, or sidebar) → detail view showing: flag, name, group link, W/D/L record, list of their games. | Partially covered by `e01-s12` (planned), but `e01-s12` focuses on "apostas dos participantes", not W/D/L standings |
| G13 | **Group detail page** | Click group badge → standings table (pos, team, pts, W/D/L, GF:GA) with color-coded positions. | **New** — not in existing epics |
| G14 | **Desktop layout & sticky header** | 1440px max-width, sticky header with progress bar ("3/8 jogos finalizados"), Big Bolão branding, Copa 2026 badge. | **New** — not in existing epics |
| G15 | **Hero section** | Stats overview: "X participantes · Y jogos finalizados · Z abertos para palpitar" + leader card (clickable). | **New** — not in existing epics |
| G16 | **Interactive drill-downs** | Clickable leader, players, teams, groups → navigate between views. Back button in breadcrumb. | **New** — not in existing epics |

---

## 3. Summary of Work Required

### Phase 1: Mobile App Polish (Low Effort)
1. Make Resultado an overlay instead of a separate route (G02, G03)
2. Polish LoginView with user card (G01)

### Phase 2: Web Dashboard (High Effort — New Epic)
1. Create desktop layout with sticky header (G14)
2. Hero section with stats + leader card (G15)
3. Two-column layout for landing page (G14)
4. Cross-table/matrix view (G10 — partially covered by e01-s14)
5. Player detail with stats + palpite history (G11)
6. Country detail with W/D/L stats (G12 — extends e01-s12)
7. Group detail with standings table (G13)
8. Interactive drill-downs and navigation (G16)

---

## 4. Recommendation

Create a **new epic (e03)** for the Web Dashboard implementation, which includes:
- Desktop-first layout (separate from the mobile SPA, served at a different route or subdomain)
- Cross-table matrix (consolidates e01-s14)
- Player detail view
- Country detail view (extends e01-s12)
- Group detail with standings
- Interactive navigation between views

The existing mobile SPA (`e01`) should be polished with the overlay changes (G02, G03) as a quick follow-up.
