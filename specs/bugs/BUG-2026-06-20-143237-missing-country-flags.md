# BUG-2026-06-20T143237: Algumas bandeiras de países não aparecem no dashboard

## Problem

**Actual behavior:** No dashboard (e nas telas de jogos/palpites), vários países exibem
um ícone de "documento em branco" no lugar da bandeira. Confirmado para: **Iraq,
Uzbekistan, Jordan, D.R. Congo**. Por análise do código, também afetará **Bosnia and
Herzegovina, South Africa, Czech Republic, Tunisia** quando esses jogos aparecerem.

**Expected behavior:** Todo país do torneio deve exibir sua bandeira (emoji) ao lado
do nome.

**Reproduce:** Abrir https://bolao.bigbase.click/ e observar as linhas de jogos
envolvendo os países acima. O ícone renderizado é o fallback de bandeira branca
(🏳️), que aparece como "tofu"/documento em branco em alguns sistemas.

## Root Cause Analysis

A camada de apresentação resolve a bandeira a partir do **nome do time** consultando
um dicionário estático de `nome → emoji`. A entrada de cada time vem em inglês
(ex.: "D.R. Congo", "Iraq", "Uzbekistan", "Jordan").

A resolução falha por **duas causas independentes**, ambas verificadas reproduzindo
a função real de lookup:

1. **Entradas ausentes no dicionário.** O mapa de bandeiras do frontend é uma cópia
   manual e **incompleta** do mapeamento que o bot mantém. Vários países do torneio
   simplesmente não têm chave (`iraq`, `uzbekistan`, `jordan`, e outros), então caem
   no fallback de bandeira branca. (Detalhe traiçoeiro: `iran` existe, `iraq` não —
   passa batido numa leitura rápida.)

2. **Normalização não trata pontuação.** A função normaliza caixa e remove acentos,
   mas **não remove pontuação nem colapsa espaços**. Logo "D.R. Congo" vira
   `"d.r. congo"`, que não bate com a chave `"dr congo"` existente → fallback.

**Contributing factor / design flaw:** o dicionário de bandeiras do frontend é uma
fonte de verdade **duplicada e divergente** da que o bot usa. Quando o calendário
ganha países, a cópia do frontend fica para trás silenciosamente — não há nada que
garanta cobertura de todos os times do torneio.

**Risk level:** Low — correção é de dados + normalização de lookup, sem mudança de
comportamento além de mais bandeiras resolverem corretamente.

## TDD Fix Plan

O runner de testes do web é `node --test tests/*.test.js`. A função de resolução de
bandeira é exportada pela camada de API do frontend.

1. **RED**: Escrever um teste que, para uma amostra dos países hoje quebrados
   ("Iraq", "Uzbekistan", "Jordan", "D.R. Congo"), `flag(nome)` retorna um emoji que
   **não** é o fallback de bandeira branca.
   **GREEN**: Adicionar as chaves ausentes ao dicionário e fazer a normalização
   remover pontuação e colapsar espaços (para "D.R. Congo" casar com a entrada do
   Congo).
   **verify**: `cd web && node --test tests/flags.test.js`

2. **RED**: Escrever um teste de cobertura que percorre **a lista completa de times
   do torneio** (derivada do calendário oficial, em inglês) e afirma que
   **nenhum** cai no fallback de bandeira branca.
   **GREEN**: Completar o dicionário com todos os países restantes do torneio
   (Bosnia and Herzegovina, South Africa, Czech Republic, Tunisia, etc.), incluindo
   variantes PT já usadas em outras telas.
   **verify**: `cd web && node --test tests/flags.test.js`

3. **RED**: Escrever um teste de robustez de normalização — variações de capitalização,
   espaços extras e pontuação ("d.r. congo", "D.R.  Congo", "DR Congo") resolvem para
   a mesma bandeira.
   **GREEN**: Garantir que a normalização é idempotente quanto a pontuação/espaços.
   **verify**: `cd web && node --test tests/flags.test.js`

**REFACTOR**: Avaliar extrair a lista de países do torneio para uma única fonte
compartilhada (ou um teste-guardião que falhe quando o calendário introduzir um país
sem bandeira), eliminando a divergência entre a cópia do frontend e a do bot.

## Acceptance Criteria

- [ ] Iraq, Uzbekistan, Jordan e D.R. Congo exibem suas bandeiras no dashboard
- [ ] Nenhum país do calendário oficial cai no fallback de bandeira branca
- [ ] Lookup de bandeira é resiliente a pontuação, espaços e caixa
- [ ] All new tests pass
- [ ] Existing tests still pass

## Resolution

<!-- filled in by validate-fix -->
