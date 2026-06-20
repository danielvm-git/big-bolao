# BUG-2026-06-20T200300: bigbase.py expõe superfície de interface morta (sql/_hydrate)

> Tipo: dívida arquitetural (deepening opportunity), não defeito de runtime.
> Módulo **raso** (Module Depth 2): interface maior que o uso real.

## Problem

**Actual behavior:** `bolao/bigbase.py` mantém `BigBase.sql()` e `_hydrate()` como hooks
de implementação que **nunca são chamados** no caminho de código vivo. Todas as leituras
passam por `list_records()` (full-table scan, até 1000 linhas, filtragem em processo).

O uso pretendido de `sql()` — queries filtradas via `json_extract(data,'$.campo')` — está
documentado no docstring do módulo mas é **inalcançável** a partir dos callers atuais.
Histórico: o `/api/sql` retornava 403 para a service account (ver BUG-2026-06-19-180800),
e a abordagem foi trocada por `list_records` + filtro. O método ficou para trás.

**Expected behavior:** A interface da classe deveria refletir só os contratos vivos.
Superfície morta torna impossível saber, lendo o módulo, qual é o caminho de leitura real.

## Root Cause Analysis

`sql()`/`_hydrate()` sobreviveram a uma mudança de estratégia (SQL → list+filter) sem
serem removidos.

**Deletion test:** removendo `sql()` e `_hydrate()`, **nenhum** comportamento se perde
(zero callers). Eles falham o teste de deleção — não estão ganhando seu lugar.

**Fricção concreta:** o docstring do módulo ainda anuncia "leitura via /api/sql (SELECT
read-only)" como se fosse capacidade ativa, criando um footgun: um futuro contribuidor
pode tentar usar `sql()` e reencontrar o 403 já resolvido por BUG-2026-06-19-180800.

**Risk level:** Low — deleção de código morto + atualização de docstring.

## Fix Plan (deepening)

1. Remover `BigBase.sql()` e a função `_hydrate()`.
2. Atualizar o docstring do módulo: a filtragem é feita **em processo** sobre
   `list_records()`; `/api/sql` não está disponível para a service account.
3. Documentar em `list_records()` a característica O(n) (scan completo) para que a
   performance seja inequívoca.
4. Se um caller futuro precisar de filtragem SQL, introduzi-la **então**, com um
   caso de uso real guiando a forma da interface.

## Acceptance Criteria

- [x] `sql()` e `_hydrate()` removidos
- [x] Docstring reflete o caminho de leitura real (list+filter em processo)
- [x] Nenhum caller quebra (já são zero)
- [x] Testes Python continuam passando

## Resolution

**Fixed:** 2026-06-20
**Root cause confirmed:** sql()/_hydrate() survived the SQL→list+filter strategy change without being removed. Zero callers.
**Fix applied:** Removed BigBase.sql() method and module-level _hydrate() function. Updated module docstring: no mention of /api/sql, filtering is in-process O(n) over list_records(). Added O(n) note to list_records() docstring. Removed stale comment in ensure_setup() about /api/sql.
**Hardening added:** No dead interface surface. Future contributors see only the real data path.
**Evidence:** 79/79 tests pass.
