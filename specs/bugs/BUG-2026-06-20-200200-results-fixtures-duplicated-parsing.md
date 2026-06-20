# BUG-2026-06-20T200200: results.py duplica a lógica de parsing de fixtures.py

> Tipo: dívida arquitetural (deepening opportunity), não defeito de runtime.
> Módulo **raso** (Module Depth 2): conhecimento da API replicado em dois lugares.

## Problem

**Actual behavior:** `bolao/results.py` e `bolao/fixtures.py` ambos conhecem os detalhes
internos da resposta do apifootball.com:

- o conjunto `_FINISHED` de strings de status ("Finished", "After ET", "FT", "AET", ...)
  está definido **duas vezes** (frozenset em `results.py`, tupla inline em `fixtures.py`)
- a hierarquia de campos `match_hometeam_ft_score` → `match_hometeam_score` (placar de
  90 min, não prorrogação) é reimplementada em ambos
- o `_safe_int`/parsing de gols aparece nos dois

`fixtures.py` já tem `normalise()` — uma função pura que converte registros brutos da
API em dicts limpos — mas `results.py` reimplementa a mesma extração de campos inline
em `_apifootball()`.

**Expected behavior:** O parsing de um fixture bruto da API (status finished? placar de
90min?) deveria viver num único lugar, consumido tanto por `fixtures.py` (sync de
calendário) quanto por `results.py` (sync de resultados).

## Root Cause Analysis

`results.py` foi escrito antes (ou em paralelo a) `fixtures.py`, e a lógica de parsing
foi copiada em vez de compartilhada.

**Deletion test sobre `fixtures.normalise()`:** ambos os callers (`scripts/sync_fixtures.py`
e `results.py`) precisam desse conhecimento de parsing, mas só um o obtém da fonte
canônica. O outro tem sua própria cópia divergente.

**Fricção concreta:** quando a API introduzir um novo status de "encerrado" (já houve
caso: "After PEN" / "Finished PEN"), é preciso lembrar de atualizar **dois** lugares.
Esquecer um significa resultados que não sincronizam silenciosamente.

**Risk level:** Medium — `results.py` está no caminho de `/sync` e do job periódico;
mexer exige cobrir com os testes existentes (`tests/test_results.py`, `tests/test_fixtures.py`).

## Fix Plan (deepening)

1. Extrair em `fixtures.py` um helper `parse_result(fixture: dict) -> tuple[int, int] | None`
   (e expor `_FINISHED` como única constante).
2. `results.py` passa a chamar esse helper em vez de reimplementar o acesso aos campos.
3. `results.py` vira consumidor fino de `fixtures.py`, não um segundo parser.

## Acceptance Criteria

- [x] `_FINISHED` definido em um único lugar
- [x] Hierarquia ft_score → score implementada uma vez
- [x] Adicionar um status novo é mudança em um único arquivo
- [x] `tests/test_results.py` e `tests/test_fixtures.py` continuam passando

## Resolution

**Fixed:** 2026-06-20
**Root cause confirmed:** results.py reimplemented inline the field extraction that fixtures.normalise() already did — _FINISHED defined twice, ft_score→score hierarchy in 2 places.
**Fix applied:** Extracted `_FINISHED` (frozenset) and `parse_result(fixture) → tuple[int,int] | None` into fixtures.py. Both normalise() and _apifootball() now import and use the shared functions. results.py no longer has its own _FINISHED or inline score parsing.
**Hardening added:** Adding a new "finished" status is now a change in one file. parse_result() is independently testable.
**Intentional behavior change (noted in review):** o `normalise()` antigo calculava `gols_casa`/`gols_fora` de forma independente — um fixture encerrado com placar de casa `"2"` mas visitante ausente/`"-"` produzia `gols_casa=2, gols_fora=None`. `parse_result()` retorna `None` para o **par inteiro** se qualquer lado faltar. É uma melhoria (meio-placar não tem sentido) e os guards de ranking (`gols_casa != null`) tornam seguro nos dois casos. O caminho de `/sync` (`_apifootball`) já exigia ambos os lados, então lá é no-op.
**Evidence:** 79/79 tests pass.
