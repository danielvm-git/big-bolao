# BUG-2026-06-20-100000: Participantes duplicados via `/start` quando nome do Telegram difere do nome histórico

## Problem

Quando um participante histórico (criado via `seed_bigbase.py` com `telegram_id` sintético negativo) usa o bot pela primeira vez com `/start`, o sistema cria um **novo registro** em vez de vincular ao já existente — porque o nome completo do Telegram ("Ana Flavia Cernic Ramos") difere do nome histórico curto ("Flávia").

**Comportamento atual:**
- Participante histórico "Flávia" (`telegram_id=-4`, `ativo=False`, 16 palpites)
- Novo participante "Ana Flavia Cernic Ramos" (`telegram_id=135466945`, `ativo=True`, 0 palpites)
- Duas entradas para a mesma pessoa no banco

**Comportamento esperado:**
- Ao rodar `/start` com um nome que *contém* o nome de um placeholder, o sistema deveria automaticamente vincular o placeholder ao usuário real, migrando os palpites.

**Como reproduzir:**
1. Seed cria "Flávia" com `telegram_id=-4`
2. Usuário real com nome Telegram "Ana Flavia Cernic Ramos" roda `/start`
3. Observar: dois registros em `participantes`, palpites históricos presos no placeholder

## Root Cause Analysis

### Caminho do código

O fluxo de `/start` chama `registrar_participante(telegram_id, nome)` em `bolao/bigbase.py` (método `BigBase.registrar_participante`):

1. **Passo 1** — `get_participante(telegram_id=135466945)` → `None` (não há registro com este telegram_id)
2. **Passo 2** — `participante_por_nome("Ana Flavia Cernic Ramos")` → `None` (a comparação é `nome.strip().lower() == "ana flavia cernic ramos"` vs nomes existentes; "Flávia" não é igual)
3. **Passo 3** — Cria novo participante (`id=14`)

### Por que falha

A guarda anti-duplicata em `registrar_participante` usa **comparação exata** de nome (`participante_por_nome` faz `nome.strip().lower() == alvo.strip().lower()`). Isso funciona quando o nome do Telegram coincide exatamente com o nome histórico, mas falha quando:

- O nome do Telegram é o nome completo (ex: "Ana Flavia Cernic Ramos")
- O nome histórico é um apelido ou nome curto (ex: "Flávia")

O método `reivindicar` (usado por `/sou`) existe exatamente para fazer essa vinculação, mas depende de o usuário saber usar `/sou Nome` — o que é contraintuitivo para quem acabou de entrar no bot.

### Fatores contribuintes

- `seed_bigbase.py` cria placeholders com `telegram_id` negativo e `ativo=False`, mas o `/start` não verifica placeholders antes de criar
- Nenhum teste cobre `registrar_participante` ou a lógica de detecção de placeholders
- `/start` usa `user.full_name` do Telegram, que é o nome completo do perfil, não um apelido

**Risco:** Baixo — o problema é fácil de detectar (ranking mostra duplicata) e de corrigir. O impacto é que palpites históricos ficam invisíveis até a fusão manual.

## TDD Fix Plan

### Ciclo 1: placeholder com nome contido no novo nome é vinculado

**RED**: Escrever teste em `tests/test_participantes.py` que cria um participante placeholder (`telegram_id=-4`, nome="Flávia", `ativo=False`) e depois chama `registrar_participante(12345, "Ana Flavia Cernic Ramos")`. Verificar que:
- Nenhum novo registro foi criado
- O placeholder antigo foi atualizado com `telegram_id=12345`, `nome="Ana Flavia Cernic Ramos"`, `ativo=True`
- Palpites do placeholder foram migrados para `telegram_id=12345`

**GREEN**: Em `registrar_participante`, antes de criar um novo registro, adicionar varredura por placeholders (`telegram_id < 0`) cujo nome:
  - Esteja contido no novo nome (case-insensitive), OU
  - Tenha o novo nome contido nele

  Se encontrar, fazer patch no placeholder com telegram_id real e ativo=True, igual ao que `reivindicar` faz.

**verify**: `python -m pytest tests/test_participantes.py -v -k "test_placeholder_contains_match"`

### Ciclo 2: placeholder sem correspondência não é vinculado

**RED**: Testar que chamar `registrar_participante(99999, "João Silva")` quando só existe placeholder "Flávia" não vincula o João ao placeholder da Flávia. Deve criar novo registro normalmente.

**GREEN**: A lógica já funciona — a varredura só vincula se houver match de substring entre os nomes.

**verify**: `python -m pytest tests/test_participantes.py -v -k "test_no_false_match"`

### Ciclo 3: `/sou` continua funcionando normalmente

**RED**: Testar que após a correção, `/sou Flávia` ainda migra corretamente palpites mesmo que o placeholder já tenha sido parcialmente vinculado pelo `/start`.

**GREEN**: `reivindicar` não precisa de alterações — a lógica existente de migração de palpites + fusão de registros continua funcionando.

**verify**: `python -m pytest tests/test_participantes.py -v -k "test_reivindicar_still_works"`

### REFACTOR

- Renomear `participante_por_nome` para `participante_por_nome_exato` para deixar explícito que é comparação exata
- Extrair a lógica de varredura de placeholders para método auxiliar `_placeholder_por_nome_parcial`

## Acceptance Criteria

- [ ] Ao chamar `registrar_participante(tid, nome_completo)` onde existe placeholder cujo nome está contido em `nome_completo`, o placeholder é vinculado (não cria duplicata)
- [ ] Ao chamar `registrar_participante(tid, nome_completo)` sem placeholder correspondente, cria registro novo normalmente
- [ ] `/sou Nome` continua funcionando sem regressão
- [ ] Ranking existente continua funcionando (já filtra `ativo=False`)
- [ ] Todos os testes existentes passam

## Resolution

<!-- filled in by validate-fix -->

