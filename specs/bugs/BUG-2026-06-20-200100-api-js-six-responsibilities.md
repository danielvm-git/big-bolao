# BUG-2026-06-20T200100: api.js concentra seis responsabilidades num único arquivo raso

> Tipo: dívida arquitetural (deepening opportunity), não defeito de runtime.
> Módulo **raso** (Module Depth 1): interface tão complexa quanto a implementação.

## Problem

**Actual behavior:** `web/src/api.js` (160 linhas) é simultaneamente:

- (a) gerenciador de auth/sessão (singleton `BB`, `_auth`, token)
- (b) wrapper de transporte HTTP (`get`/`post`/`patch`)
- (c) funções de query de domínio (`fetchJogos`, `savePalpite`, `findUser`, ...)
- (d) motor de pontuação (`calcPontos`, `calcRanking`)
- (e) tabela de bandeiras de país (`FLAGS`, 40+ entradas, `_normTeam`, `flag`)
- (f) formatadores de data (`fmtDate`, `fmtTime`, `avatarColor`)

Além disso, `calcPontos`/`calcRanking` são **cópia verbatim** de `scoring.py`/`ranking.py`
do lado Python — duas fontes de verdade que podem divergir.

**Expected behavior:** Transporte, queries de domínio e lógica pura (scoring + flags +
formatação) deveriam estar em módulos separados. A lógica pura deveria ser testável sem
rede, espelhando `scoring.py`/`ranking.py`.

## Root Cause Analysis

O arquivo virou o "balde" de tudo que não era componente Vue. **Deletion test:** se
deletássemos `api.js`, a complexidade reaparece em **todos** os arquivos de view — ele
é carga real, mas mal-particionado.

**Fricção concreta:** hoje só `flags` tem teste (`web/tests/flags.test.js`), porque a
função de bandeira é a única extraível sem arrastar o singleton de transporte junto.
`calcRanking` — a lógica mais sujeita a bug — não tem teste isolado porque está no mesmo
módulo que faz `fetch`.

**Risk level:** Low — split é mecânico (mover funções puras para arquivos novos,
reexportar). Sem mudança de comportamento.

## Fix Plan (deepening)

Dividir em três módulos:

1. `transport.js` — singleton `BB`, auth, `get`/`post`/`patch` crus.
2. `queries.js` — `fetchJogos`, `fetchAllPalpites`, `savePalpite`, `findUser` (consomem `transport`).
3. `scoring.js` — `calcPontos`, `calcRanking`, `flag`, `_normTeam`, `FLAGS`, formatadores.
   Mapeia 1:1 com `scoring.py` + `ranking.py`. Puro, sem rede.

`web/tests/flags.test.js` passa a importar de `scoring.js`.

## Acceptance Criteria

- [ ] `scoring.js` testável isoladamente com `node --test` (sem stub de rede)
- [ ] `calcRanking` ganha teste de unidade espelhando `tests/test_ranking.py`
- [ ] Transporte stubável em testes de query sem tocar em scoring
- [ ] Testes web existentes continuam passando
- [ ] Build do Vite (`web/dist/`) continua válido
