"""Tests for bolao.group_publisher — pure message formatting without Telegram I/O."""
from __future__ import annotations

import pytest
from bolao.group_publisher import format_resultado, format_ranking, format_lembrete


class TestFormatResultado:
    """format_resultado() produces correct HTML for match results."""

    def test_with_cravadores(self):
        jogo = {
            "casa": "Brasil", "fora": "Argentina",
            "gols_casa": 2, "gols_fora": 1,
        }
        palpites = [{"nome": "Ricardo", "gols_casa": 2, "gols_fora": 1}]
        html = format_resultado(jogo, palpites)
        assert "⚽" in html
        assert "Fim de jogo" in html
        assert "Brasil" in html
        assert "Argentina" in html
        assert "Ricardo" in html  # cravou
        assert "🎯" in html

    def test_multiple_cravadores(self):
        jogo = {
            "casa": "Brasil", "fora": "Argentina",
            "gols_casa": 2, "gols_fora": 1,
        }
        palpites = [
            {"nome": "Ricardo", "gols_casa": 2, "gols_fora": 1},
            {"nome": "Maria", "gols_casa": 2, "gols_fora": 1},
        ]
        html = format_resultado(jogo, palpites)
        assert "Ricardo" in html
        assert "Maria" in html

    def test_no_cravadores(self):
        jogo = {
            "casa": "Brasil", "fora": "Argentina",
            "gols_casa": 2, "gols_fora": 1,
        }
        palpites = [
            {"nome": "Ricardo", "gols_casa": 1, "gols_fora": 1},
            {"nome": "Maria", "gols_casa": 0, "gols_fora": 2},
        ]
        html = format_resultado(jogo, palpites)
        assert "Fim de jogo" in html
        assert "Cravaram" not in html

    def test_empty_palpites(self):
        jogo = {
            "casa": "Brasil", "fora": "Argentina",
            "gols_casa": 2, "gols_fora": 1,
        }
        html = format_resultado(jogo, [])
        assert "Fim de jogo" in html
        assert "Cravaram" not in html

    def test_draw_match(self):
        jogo = {
            "casa": "Brasil", "fora": "Argentina",
            "gols_casa": 1, "gols_fora": 1,
        }
        palpites = [{"nome": "Ricardo", "gols_casa": 1, "gols_fora": 1}]
        html = format_resultado(jogo, palpites)
        assert "Fim de jogo" in html
        assert "🎯" in html  # cravou empate

    def test_only_winner_acertou_not_cravou(self):
        jogo = {
            "casa": "Brasil", "fora": "Argentina",
            "gols_casa": 3, "gols_fora": 2,
        }
        palpites = [{"nome": "Joao", "gols_casa": 2, "gols_fora": 1}]
        html = format_resultado(jogo, palpites)
        assert "Fim de jogo" in html
        assert "Cravaram" not in html  # acertou vencedor mas nao placar exato


class TestFormatRanking:
    """format_ranking() produces HTML from plain data dicts."""

    def test_empty_data(self):
        html = format_ranking([], [], [])
        assert html != ""
        assert isinstance(html, str)

    def test_with_participants(self):
        jogos = [{
            "match_id": "R1-01", "status": "encerrado",
            "gols_casa": 2, "gols_fora": 1,
        }]
        palpites = [{
            "match_id": "R1-01", "telegram_id": 111,
            "gols_casa": 2, "gols_fora": 1,
        }]
        participantes = [{"telegram_id": 111, "nome": "Ricardo", "ativo": True}]
        html = format_ranking(jogos, palpites, participantes)
        assert "Ricardo" in html
        assert "pts" in html


class TestFormatLembrete:
    """format_lembrete() produces HTML reminder for upcoming matches."""

    def test_with_jogos(self):
        jogos = [
            {"casa": "Brasil", "fora": "Argentina",
             "kickoff": "2026-06-21T16:00:00"},
            {"casa": "Uruguai", "fora": "Chile",
             "kickoff": "2026-06-21T21:00:00"},
        ]
        html = format_lembrete(jogos, "meu_bot")
        assert "Brasil" in html
        assert "Uruguai" in html
        assert "palpite" in html.lower()
        assert "meu_bot" in html

    def test_empty_jogos(self):
        html = format_lembrete([], "meu_bot")
        assert html == ""

    def test_has_deeplink(self):
        jogos = [{"casa": "Brasil", "fora": "Argentina",
                  "kickoff": "2026-06-21T16:00:00"}]
        html = format_lembrete(jogos, "bolao_bot")
        assert "t.me/bolao_bot" in html
