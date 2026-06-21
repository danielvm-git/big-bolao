"""Tests for bolao/ranking.py — duplicate participant handling."""
from bolao.ranking import calcular, formatar


def test_inactive_participants_excluded():
    """Participantes com ativo=False nao aparecem no ranking."""
    jogos = [{
        "match_id": "R1-01", "status": "encerrado",
        "gols_casa": 2, "gols_fora": 1,
    }]
    palpites = [{
        "match_id": "R1-01", "telegram_id": 111,
        "gols_casa": 2, "gols_fora": 1,
    }]
    participantes = [
        {"telegram_id": 111, "nome": "Ricardo", "ativo": True},
        {"telegram_id": 222, "nome": "Ricardo", "ativo": False},  # duplicata fundida
    ]
    rank = calcular(jogos, palpites, participantes)
    nomes = [e["nome"] for e in rank]
    assert nomes == ["Ricardo"]  # so 1, nao 2
    assert len(rank) == 1


def test_active_participant_still_appears():
    """Participante com ativo=True (ou sem campo ativo) aparece normal."""
    jogos = [{
        "match_id": "R1-01", "status": "encerrado",
        "gols_casa": 2, "gols_fora": 1,
    }]
    palpites = []
    participantes = [
        {"telegram_id": 111, "nome": "Ricardo", "ativo": True},
        {"telegram_id": 222, "nome": "Maria", "ativo": True},
    ]
    rank = calcular(jogos, palpites, participantes)
    assert len(rank) == 2


def test_missing_ativo_field_defaults_to_active():
    """Compatibilidade: participantes sem campo 'ativo' sao tratados como ativos."""
    jogos = []
    palpites = []
    participantes = [
        {"telegram_id": 111, "nome": "Ricardo"},  # sem ativo
    ]
    rank = calcular(jogos, palpites, participantes)
    assert len(rank) == 1
    assert rank[0]["nome"] == "Ricardo"


def test_negative_telegram_id_excluded():
    """Placeholders com telegram_id < 0 sao excluidos mesmo com ativo=True."""
    jogos = [{
        "match_id": "R1-01", "status": "encerrado",
        "gols_casa": 2, "gols_fora": 1,
    }]
    palpites = [
        {"match_id": "R1-01", "telegram_id": -4, "gols_casa": 2, "gols_fora": 1, "nome": "Flavia"},
        {"match_id": "R1-01", "telegram_id": 555, "gols_casa": 1, "gols_fora": 0, "nome": "Flavia"},
    ]
    participantes = [
        {"telegram_id": -4, "nome": "Flavia", "ativo": True},   # placeholder seed
        {"telegram_id": 555, "nome": "Flavia", "ativo": True},   # real user
    ]
    rank = calcular(jogos, palpites, participantes)
    assert len(rank) == 1
    assert rank[0]["nome"] == "Flavia"
    assert rank[0]["telegram_id"] == 555


def test_negative_telegram_id_without_ativo_field_still_excluded():
    """Placeholder sem campo ativo mas com tg < 0 e excluido."""
    jogos = []
    palpites = []
    participantes = [
        {"telegram_id": -4, "nome": "Flavia"},       # placeholder, sem ativo
        {"telegram_id": 555, "nome": "Flavia"},       # real
    ]
    rank = calcular(jogos, palpites, participantes)
    assert len(rank) == 1
    assert rank[0]["telegram_id"] == 555


# ── formatar() tests ──────────────────────────────────────────────

def test_formatar_empty_ranking():
    """Ranking vazio retorna mensagem apropriada."""
    result = formatar([])
    assert "Ainda nao" in result
    assert "<pre>" not in result


def test_formatar_uses_pre_aligned_table():
    """Ranking usa <pre> para tabela alinhada em fonte monoespaco no Telegram."""
    rank = [
        {"nome": "Ricardo", "telegram_id": 1, "pontos": 5, "exatos": 1, "acertos": 3, "jogos": 10},
    ]
    result = formatar(rank)
    assert "<pre>" in result
    assert "</pre>" in result
    assert "🏆" in result
    assert "pts" in result


def test_formatar_top3_get_medals():
    """Top 3 recebem medalhas; demais recebem numero."""
    rank = [
        {"nome": "A", "telegram_id": 1, "pontos": 9, "exatos": 2, "acertos": 5, "jogos": 10},
        {"nome": "B", "telegram_id": 2, "pontos": 6, "exatos": 1, "acertos": 3, "jogos": 10},
        {"nome": "C", "telegram_id": 3, "pontos": 3, "exatos": 0, "acertos": 2, "jogos": 10},
        {"nome": "D", "telegram_id": 4, "pontos": 1, "exatos": 0, "acertos": 1, "jogos": 10},
    ]
    result = formatar(rank)
    assert "🥇" in result
    assert "🥈" in result
    assert "🥉" in result
    assert "4º" in result


def test_formatar_shows_full_name():
    """Nome completo aparece sem truncamento."""
    rank = [
        {"nome": "Nome Muito Longo Demais", "telegram_id": 1, "pontos": 5, "exatos": 1, "acertos": 3, "jogos": 10},
    ]
    result = formatar(rank)
    assert "Nome Muito Longo Demais" in result
