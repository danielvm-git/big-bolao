### Story e03-s01: Estrutura do Dashboard — Implementation Steps

**type:** feat
**context:** frontend
**BCP:** 1
**Status:** planned

**Context:** Criar o layout base do Web Dashboard desktop-first (1440px), com sticky header e rota `/dashboard`, seguindo o protótipo `Big Bolão Web.dc.html`. Este é o esqueleto que as stories seguintes (e03-s02 a e03-s08) vão preencher.

## Steps

1. **Add `/dashboard` route** — Register DashboardView component in `web/src/router/index.js`. Dashboard não deve mostrar BottomNav (layout independente do mobile SPA). → verify: `grep -q 'dashboard' web/src/router/index.js && echo "✅ rota dashboard existe"`

2. **Create DashboardView.vue** — Componente principal com:
   - Sticky header (z-index 100, backdrop-filter blur)
   - Logo "⚽ Big Bolão" + badge "COPA 2026"
   - Indicador de progresso "X / Y jogos finalizados"
   - Botão "← Voltar" condicional (mostra em sub-páginas)
   - Slot/área para conteúdo do dashboard
   - Max-width 1440px centralizado
   → verify: `grep -q 'DashboardView' web/src/router/index.js && test -f web/src/views/DashboardView.vue && echo "✅ DashboardView existe"`

3. **Dashboard-specific CSS** — No DashboardView.vue (scoped):
   - Desktop scrollbar visível (::-webkit-scrollbar width 5px)
   - Animações fadeIn/fadeInUp
   - Layout responsivo: 1440px max-width, padding 32px nas laterais
   → verify: `grep -q '1440px' web/src/views/DashboardView.vue && echo "✅ layout desktop configurado"`

4. **Wire navigation** — Clicar no logo "Big Bolão" volta à landing do dashboard. Botão "Voltar" aparece em sub-páginas (player/country/group detail) e chama `goBack()` que retorna à landing. → verify: `grep -q 'goHome\|goBack' web/src/views/DashboardView.vue && echo "✅ navegação wireada"`

5. **Verify build** — Dashboard compila sem erros e a rota responde. → verify: `cd web && npx vite build 2>&1 | tail -5 | grep -q 'built in' && echo "✅ build ok"`

## Verification Script

1. Start dev server: `cd web && npm run dev`
2. Open `http://localhost:5173/#/dashboard`
3. Verify sticky header appears with logo "⚽ Big Bolão" + badge "COPA 2026"
4. Verify progress indicator shows "X / Y jogos finalizados"
5. Verify no BottomNav is shown (dashboard has its own header)
6. Verify scrollbar is visible on desktop
7. Run `npx vite build` — should succeed with no errors

## Out of scope

- Conteúdo do dashboard (hero, two-column, tabela) — stories e03-s02 a e03-s08
- Navegação para sub-páginas (player, country, group) — story e03-s08
- Integração com dados reais do BigBase — já existe via `useJogos`/`useRanking`

## Risks

- DashboardView pode conflitar com o layout do App.vue (que tem BottomNav fixo). Solução: DashboardView usa layout próprio, não herda `<BottomNav />`.
- Rota `/dashboard` não deve mostrar login overlay.
