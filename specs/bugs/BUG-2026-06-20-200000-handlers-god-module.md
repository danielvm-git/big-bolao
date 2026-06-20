# BUG-2026-06-20T200000: handlers.py é um god-module raso que esconde a máquina de estados do palpite

> Tipo: dívida arquitetural (deepening opportunity), não defeito de runtime.
> Módulo **raso** (Module Depth 1): interface tão complexa quanto a implementação.

## Problem

**Actual behavior:** `bolao/handlers.py` (315 linhas, 6 responsabilidades) espalha
o protocolo de palpite por 3 handlers de callback registrados separadamente em
`bot.py`, sem um único ponto de serialização de `callback_data`. A função
`_montar_ranking` acopla computação de ranking ao `ContextTypes` do Telegram,
impedindo teste unitário isolado.

**Expected behavior:**
- Máquina de estados de palpite concentrada num módulo **profundo** com enum de
  passo + ponto único de (de)serialização de `callback_data`
- Publicação no grupo encapsulada atrás de uma interface pequena
- Ranking computável de dados planos sem mock do Telegram
- `handlers.py` fino: só wiring de comandos → módulos profundos

**How to reproduce (friction):**
1. Tentar adicionar tela de confirmação ao fluxo de palpite: exige editar
   `cb_escolher_jogo`, `cb_gols_casa`, `cb_gols_fora` em handlers.py **e**
   adicionar `CallbackQueryHandler` + pattern em bot.py — 4 pontos de edição
   para uma responsabilidade.
2. `_montar_ranking(context)` não pode ser testado sem mock do Telegram porque
   usa `context.bot_data["db"]` em vez de receber dados planos.

## Root Cause Analysis

Three verified root causes:

**RCA-1: callback_data sem contrato centralizado.** A serialização acontece em
3 lugares: `f"g|{mid}"` no botão da lista, `f"h|{mid}|{n}"` no seletor de gols
casa, `f"f|{mid}|{gc}|{n}"` no seletor de gols fora. A deserialização tem 3
implementações paralelas: `split("|", 1)[1]`, `split("|")` com unpack 3, e
`split("|")` com unpack 4 — cada uma assume um número diferente de partes.
Sem validação compartilhada, qualquer mudança no formato quebra silenciosamente.

**RCA-2: `_montar_ranking` acoplado ao Telegram.** A função recebe `ContextTypes`
e extrai `db = context.bot_data["db"]`. A computação real em `ranking_mod.calcular()`
já aceita dados planos (jogos, palpites, participantes). A única razão para o
acoplamento é evitar refatorar os 2 callers (`cmd_ranking`, `_publicar_ranking`).

**RCA-3: Publicação no grupo mistura formatação e envio.** `_publicar_resultado`,
`_publicar_ranking`, `_postar_lembrete` fazem formatação de texto + chamada a
`context.bot.send_message()` no mesmo método. Testar a formatação requer mock
do bot ou de `context.bot.send_message`.

**Contributing factor:** O módulo cresceu por acreção — cada novo comando/job foi
adicionado no mesmo arquivo. Nenhuma seam foi extraída porque não havia teste
que tornasse a extração necessária.

**Risk level:** Medium — refatoração toca o caminho crítico de palpite (coração
do bot). Precisa de teste de round-trip antes de mexer.

## TDD Fix Plan

Quatro ciclos RED-GREEN-REFACTOR, cada um extraindo um módulo sem quebrar os
testes existentes. Ordem: das camadas mais internas (sem I/O) para as mais externas
(wiring). Isso garante que cada módulo novo seja testável isoladamente.

### Ciclo 1: `bolao/betting_flow.py` — máquina de estados de palpite

**RED**: Escrever teste que verifica round-trip de serialização/deserialização
de callback_data para os três passos, e que steps só transitam na ordem correta.

```python
# tests/test_betting_flow.py
from bolao.betting_flow import BettingFlow, Step

class TestRoundTrip:
    def test_escolher_jogo_serialize(self):
        data = BettingFlow.serialize(Step.ESCOLHER_JOGO, match_id="R1-01")
        assert data == "g|R1-01"

    def test_escolher_jogo_deserialize(self):
        step, params = BettingFlow.deserialize("g|R1-01")
        assert step == Step.ESCOLHER_JOGO
        assert params == {"match_id": "R1-01"}

    def test_gols_casa_round_trip(self):
        data = BettingFlow.serialize(Step.GOLS_CASA, match_id="R1-01", gols=2)
        step, params = BettingFlow.deserialize(data)
        assert step == Step.GOLS_CASA
        assert params["match_id"] == "R1-01"
        assert params["gols"] == 2  # int, not str

    def test_gols_fora_round_trip(self):
        data = BettingFlow.serialize(Step.GOLS_FORA, match_id="R1-01", gc=2, gf=0)
        step, params = BettingFlow.deserialize(data)
        assert step == Step.GOLS_FORA
        assert params == {"match_id": "R1-01", "gc": 2, "gf": 0}

    def test_illegal_prefix_returns_none(self):
        assert BettingFlow.deserialize("z|R1-01") is None

    def test_illegal_transicion_raises(self):
        with pytest.raises(ValueError, match="invalid transition"):
            BettingFlow.validate_transition(Step.GOLS_CASA, Step.ESCOLHER_JOGO)

    def test_valid_transicion_passes(self):
        BettingFlow.validate_transition(Step.ESCOLHER_JOGO, Step.GOLS_CASA)
        BettingFlow.validate_transition(Step.GOLS_CASA, Step.GOLS_FORA)
```

**GREEN**: Criar `bolao/betting_flow.py` com:
- `Step` enum: `ESCOLHER_JOGO`, `GOLS_CASA`, `GOLS_FORA`
- `BettingFlow.serialize(step, **params)` → callback_data string
- `BettingFlow.deserialize(data)` → `(Step, dict)` ou `(None, None)` se prefixo inválido
- `BettingFlow.validate_transition(from_step, to_step)` → raise se inválido
- Prefixos: `g` = ESCOLHER_JOGO, `h` = GOLS_CASA, `f` = GOLS_FORA
- Mapa de transições: ESCOLHER_JOGO→GOLS_CASA→GOLS_FORA (futuramente GOLS_FORA→CONFIRMAR)
- `gols` e `gc`/`gf` convertidos para int

```bash
verify: python -m pytest tests/test_betting_flow.py -v
```

### Ciclo 2: `bolao/group_publisher.py` — publicação desacoplada

**RED**: Escrever teste que verifica que as funções de formatação produzem HTML
correto sem chamar Telegram. GroupPublisher recebe GRUPO_CHAT_ID via construtor
e bot via injeção (ou como parâmetro), tornando a formatação testável isoladamente.

```python
# tests/test_group_publisher.py
from bolao.group_publisher import format_resultado, format_ranking, format_lembrete

class TestFormatResultado:
    def test_format_resultado_with_cravadores(self):
        jogo = {"casa": "Brasil", "fora": "Argentina",
                "gols_casa": 2, "gols_fora": 1}
        palpites = [{"nome": "Ricardo", "gols_casa": 2, "gols_fora": 1}]
        html = format_resultado(jogo, palpites)
        assert "Fim de jogo" in html
        assert "Brasil" in html
        assert "Ricardo" in html  # cravou

    def test_format_resultado_no_cravadores(self):
        jogo = {"casa": "Brasil", "fora": "Argentina",
                "gols_casa": 2, "gols_fora": 1}
        palpites = [{"nome": "Ricardo", "gols_casa": 1, "gols_fora": 1}]
        html = format_resultado(jogo, palpites)
        assert "Fim de jogo" in html
        assert "Cravaram" not in html  # ninguém cravou

    def test_format_resultado_empty_palpites(self):
        jogo = {"casa": "Brasil", "fora": "Argentina",
                "gols_casa": 0, "gols_fora": 0}
        html = format_resultado(jogo, [])
        assert "Fim de jogo" in html
        assert "Cravaram" not in html


class TestFormatRanking:
    def test_delegates_to_ranking_mod(self):
        """format_ranking aceita dados planos e retorna HTML."""
        jogos = []
        palpites = []
        participantes = [{"telegram_id": 111, "nome": "Ricardo", "ativo": True}]
        html = format_ranking(jogos, palpites, participantes)
        assert html != ""


class TestFormatLembrete:
    def test_lembrete_has_jogos_list(self):
        jogo = {"casa": "Brasil", "fora": "Argentina",
                "kickoff": "2026-06-21T16:00:00"}
        html = format_lembrete([jogo], "nome_do_bot")
        assert "Brasil" in html
        assert "palpite" in html.lower()
```

**GREEN**: Criar `bolao/group_publisher.py` com funções puras de formatação:
- `format_resultado(jogo, palpites) → str`
- `format_ranking(jogos, palpites, participantes) → str`
- `format_lembrete(jogos, bot_username) → str`
- Todo o texto formatado retorna `str`, sem `await` nem I/O
- A classe `GroupPublisher` só adiciona `send_message` e `GRUPO_CHAT_ID`
- O módulo reusa `ranking_mod.calcular()` + `ranking_mod.formatar()`

```bash
verify: python -m pytest tests/test_betting_flow.py tests/test_group_publisher.py -v
```

### Ciclo 3: handlers.py — substituir implementações pelos módulos extraídos

**RED**: Verificar que handlers.py pode ser reescrito sem quebrar os testes
existentes. Os testes de integração de `_montar_ranking` param de funcionar
se removida, mas `test_ranking.py` cobre o caso puro — portanto a estratégia
é inline `_montar_ranking` nos dois callers e verificar que os comandos ainda
funcionam.

Nenhum teste novo precisa ser escrito aqui — os 35 testes existentes são o
guardião. O teste é:

```bash
python -m pytest tests/ -v  # must still pass 35/35
```

**GREEN**: Substituir em handlers.py:
1. `cmd_ranking` chama `ranking_mod.calcular()` + `ranking_mod.formatar()`
   diretamente em vez de `_montar_ranking(context)`
2. Remover `_montar_ranking` completamente
3. `cb_escolher_jogo` usa `BettingFlow.deserialize()` em vez de `split("|")`
4. `cb_gols_casa` usa `BettingFlow.deserialize()` e valida transição
5. `cb_gols_fora` usa `BettingFlow.deserialize()` e valida transição
6. `bot.py` patterns atualizados se necessário (devem ser compatíveis)
7. `_publicar_resultado` usa `group_publisher.format_resultado()` para formatação
8. `_publicar_ranking` usa `group_publisher.format_ranking()`
9. `_postar_lembrete` usa `group_publisher.format_lembrete()`
10. Criar classe `GroupPublisher` magra: guarda `GRUPO_CHAT_ID` e `bot`, só faz send

```bash
verify: python -m pytest tests/ -v
```

### Ciclo 4: bot.py — roteamento unificado

**RED**: Verificar que bot.py ainda registra os mesmos handlers e que
o menu de comandos não é afetado. Teste existente em `test_config.py`
garante que a aplicação builda.

```bash
python -m pytest tests/ -v  # must still pass 35/35
```

**GREEN**: Em bot.py:
1. Substituir 3 registros de `CallbackQueryHandler` por um único se
   `BettingFlow.serialize()` usa prefixos que o pattern único pode casar,
   ou manter 3 registros mas importar os patterns de `BettingFlow.ALL_PREFIXES`
2. Deixar os patterns explícitos como documentação, mas usando
   `BettingFlow.pattern_for(step)` em vez de string literal

```bash
verify: python -m pytest tests/ -v
```

**REFACTOR**: Garantir que `_seletor` em handlers.py (agora vazio de lógica de
callback_data) seja movido ou removido. Se sobrou só como helper de construção
de teclado, considerar mover para `betting_flow.py`.
Verificar que lint passa e que `handlers.py` caiu de 315 para ~150 linhas.

```bash
verify: python -m pytest tests/ -v && python -m compileall bolao/
```

## Acceptance Criteria

- [ ] `BettingFlow.serialize`/`deserialize` round-trip testável sem mock do Telegram
- [ ] Transições inválidas da máquina de estados são rejeitadas com erro claro
- [ ] `format_resultado`, `format_ranking`, `format_lembrete` são funções puras
      testáveis sem dependência de I/O
- [ ] `handlers.py` não importa mais `ContextTypes` para computação de ranking
- [ ] handlers.py reduzido de ~315 para ~150 linhas (só wiring)
- [ ] Todos os 35 testes existentes continuam passando
- [ ] Lint passa (`python -m compileall bolao/`)

## Resolution

<!-- filled in by validate-fix -->
