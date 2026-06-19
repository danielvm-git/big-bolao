# Handoff — Dados da planilha → site (BigBase)

**Para:** Claude Code · **Epic:** e01 · **Story:** e01-s08 (Conectar dados reais do BigBase)
**Data:** 2026-06-19 · **Status:** mock real entregue; falta wiring de produção

---

## Objetivo

O site (`web/`) hoje lê de `web/src/data/mock.js`. Trocar esses dados mockados
por dados reais do BigBase, mantendo o mesmo *shape* que os composables já
consomem. A planilha do grupo (`Bolao_Jararacas_Copa_2026.xlsx`) é a fonte dos
dados da **Rodada 1** (24 jogos, resultados e palpites de 7 participantes).

## O que já foi feito (não refazer)

- **Planilha já transcrita no código** — `bolao/historico.py` (resultados +
  palpites R1) e `bolao/matches.py` (agenda R1–R3). Conferido célula a célula
  contra a planilha: bate 100%.
- **`web/src/data/mock.js` agora é gerado a partir desses dados reais**, não mais
  inventado. Gerador: `scripts/gen_web_data.py`. Reexecute se a planilha mudar:
  ```bash
  python -m scripts.gen_web_data
  ```
  Saída: 48 jogos (24 R1 finalizados com `quemCravou`/`quemVencedor` reais + 24
  R2 abertos), ranking R1 recalculado, palpites da usuária logada (Mari Gallo).
- **Ranking é a fonte da verdade** (regra 3/1/0, `bolao/scoring.py`), validado por
  `python -m scripts.check_ranking`. A planilha tinha erro de soma; **não** copie
  a coluna "Ranking" da planilha — recalcule:
  `Ricardo 15 · Pajé 12 · Big 11 · Flávia 11 · Mari Gallo 9 · Mari Som 7 · Lere 0`.
- **Seed do BigBase pronto** — `scripts/seed_bigbase.py` já sobe agenda +
  resultados R1 + palpites históricos (ids sintéticos −1..−7).

## Modelo de dados (coleções BigBase — já usadas pelo bot)

Schema-less em `/api/collections/{nome}`; leitura via `/api/sql` (SELECT
read-only, `json_extract(data,'$.campo')`); JWT Bearer de `/api/auth/login`.

| Coleção | Campos |
|---|---|
| `participantes` | `telegram_id`, `nome`, `ativo` |
| `jogos` | `match_id`, `rodada`, `kickoff`, `casa`, `fora`, `gols_casa`, `gols_fora`, `status` |
| `palpites` | `match_id`, `telegram_id`, `nome`, `gols_casa`, `gols_fora`, `atualizado_em` |

`match_id` = `R<rodada>-<NN>` (ex. `R1-06`). `status` do jogo ∈
`aberto|bloqueado|encerrado`. Mapeie para o site: `encerrado → finalizado`.

## Tarefas

1. **Seed (uma vez, após o BigBase estar de pé).**
   `python -m scripts.seed_bigbase --dry` (conferir) → `python -m scripts.seed_bigbase`.

2. **`web/src/api.js`** — wrapper `fetch` com header JWT.
   - `login(token)` → `POST /api/auth/login` (ou Function de magic-token, ver e01-s09).
   - `getJogos()`, `getParticipantes()`, `getPalpites(telegramId)`.
   - `getRanking()` via `POST /api/sql` (uma query que junta palpites×jogos
     encerrados e aplica 3/1/0) **ou** computar no cliente reusando a mesma regra
     de `bolao/scoring.py` (porta JS — ver `useJogos.js`, que já faz 3/1/0).

3. **Adaptar dados da API → shape do site.** Os composables esperam exatamente:
   - `GAMES[]`: `{ id, teamA, teamB, flagA, flagB, date, time, status, grupo,
     kickoff, resultado?{goalsA,goalsB}, quemCravou?[], quemVencedor?[] }`
   - `RANKING[]`: `{ id, name, pontos, exatos }` (ordenado)
   - `USUARIO`: `{ id, nome, telegram_id, pontos, exatos }`
   - `PALPITES_SALVOS`: `{ [gameId]: {goalsA, goalsB} }`
   - `id` numérico do jogo: usar a convenção do gerador `rodada*100 + n`
     (`R1-06 → 106`) ou outra estável — só precisa ser consistente com as rotas
     `/resultado/:id`.
   - `flagA/flagB`: emoji por país. Mapa completo em `scripts/gen_web_data.py`
     (dict `FLAGS`) — reusar.
   - `quemCravou` (placar exato) e `quemVencedor` (acertou vencedor/empate, não
     exato): derivar de `palpites` × resultado com a regra 3/1/0.

4. **Trocar os imports dos composables** (`useAuth`, `useJogos`, `usePalpites`,
   `useRanking`) de `../data/mock.js` para `api.js`, com loading/erro. Manter
   `mock.js` como fallback offline/dev (flag `import.meta.env`).

5. **Auth (e01-s09).** `LoginView.vue` pega `?token=` da URL → Function
   `bolao-magic-login` valida → JWT → home. O bot grava o token.

## Critérios de aceite

- [ ] `python -m scripts.check_ranking` passa (regra + ranking R1).
- [ ] `python -m scripts.gen_web_data` regenera `mock.js` sem erro.
- [ ] `cd web && npm run build` compila.
- [ ] `node web/test-e2e.cjs` passa (navegação das 4 abas + rota resultado).
- [ ] Com BigBase real: ranking do site == saída de `check_ranking`; jogo R1
      finalizado mostra placar oficial, palpite da usuária e os pontos certos.
- [ ] Sem rede, o site cai no `mock.js` e ainda renderiza.

## Riscos / notas

- **Não** confiar na coluna "Ranking" da planilha (erro de soma conhecido).
- `/api/sql` é single-statement read-only; ranking complexo pode ser mais
  simples de computar no cliente (a lógica 3/1/0 já existe em `useJogos.js`).
- Funções do BigBase são sandbox JS sem rede/DB — servem só pra validar
  magic-token, não pra hospedar lógica pesada.
- Datas/horários em BRT (`-03:00`). `kickoff` ISO sem timezone no `matches.py`.
