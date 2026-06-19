"""Provedor de resultados de jogos (pluggable).

- Modo manual (default): admin usa /resultado no Telegram.
- apifootball: consulta apifootball.com e casa pelo api_fixture_id armazenado
  em cada registro `jogos` do BigBase. Sem traducao de nomes — match exato.

Fallback de nomes: se um registro nao tiver api_fixture_id ainda (ex: seeded
manualmente), tenta casar pelo par (home, away) em ingles como antes.
"""
from __future__ import annotations

import logging

import httpx

from bolao import config

log = logging.getLogger("bolao.results")


class Resultado:
    def __init__(self, match_id: str, gols_casa: int, gols_fora: int):
        self.match_id = match_id
        self.gols_casa = gols_casa
        self.gols_fora = gols_fora


async def buscar_encerrados(jogos: list[dict]) -> list[Resultado]:
    """Retorna placares finais para os jogos fornecidos.

    `jogos` e a lista atual do BigBase (cada dict tem match_id, api_fixture_id,
    casa, fora, status, ...). So processa jogos ainda nao encerrados.
    """
    if config.RESULTS_PROVIDER == "apifootball":
        return await _apifootball(jogos)
    return []  # modo manual


# ---------------------------------------------------------------------------
# apifootball.com provider
# ---------------------------------------------------------------------------

_FINISHED = frozenset({
    "Finished", "After ET", "After Pen.",
    "FT", "AET", "PEN", "Finished AET", "Finished PEN",
})

# Fallback name-based matching (for records without api_fixture_id)
_PT_TO_EN: dict[str, str] = {
    "México": "Mexico", "África do Sul": "South Africa",
    "Coreia do Sul": "South Korea", "República Tcheca": "Czech Republic",
    "Canadá": "Canada", "Bósnia e Herzegovina": "Bosnia and Herzegovina",
    "Estados Unidos": "USA", "Paraguai": "Paraguay",
    "Catar": "Qatar", "Suíça": "Switzerland",
    "Brasil": "Brazil", "Marrocos": "Morocco",
    "Haiti": "Haiti", "Escócia": "Scotland",
    "Austrália": "Australia", "Turquia": "Turkey",
    "Alemanha": "Germany", "Curaçao": "Curacao",
    "Países Baixos": "Netherlands", "Japão": "Japan",
    "Costa do Marfim": "Ivory Coast", "Equador": "Ecuador",
    "Suécia": "Sweden", "Tunísia": "Tunisia",
    "Espanha": "Spain", "Cabo Verde": "Cape Verde",
    "Bélgica": "Belgium", "Egito": "Egypt",
    "Arábia Saudita": "Saudi Arabia", "Uruguai": "Uruguay",
    "Irã": "Iran", "Nova Zelândia": "New Zealand",
    "França": "France", "Senegal": "Senegal",
    "Iraque": "Iraq", "Noruega": "Norway",
    "Argentina": "Argentina", "Argélia": "Algeria",
    "Áustria": "Austria", "Jordânia": "Jordan",
    "Portugal": "Portugal",
    "República Democrática do Congo": "D.R. Congo",
    "Inglaterra": "England", "Croácia": "Croatia",
    "Gana": "Ghana", "Panamá": "Panama",
    "Uzbequistão": "Uzbekistan", "Colômbia": "Colombia",
}


def _en(nome: str) -> str:
    return _PT_TO_EN.get(nome, nome).lower()


async def _apifootball(jogos: list[dict]) -> list[Resultado]:
    if not config.APIFOOTBALL_KEY:
        return []

    # Only care about games not yet finished
    pendentes = [j for j in jogos if j.get("status") != "encerrado"]
    if not pendentes:
        return []

    params = {
        "action": "get_events",
        "from": "2026-06-01",
        "to": "2026-07-31",
        "APIkey": config.APIFOOTBALL_KEY,
        "timezone": "America/Sao_Paulo",
    }
    if config.APIFOOTBALL_LEAGUE_ID:
        params["league_id"] = config.APIFOOTBALL_LEAGUE_ID

    async with httpx.AsyncClient(timeout=20.0) as cli:
        r = await cli.get("https://apiv3.apifootball.com/", params=params)
        r.raise_for_status()
        res_data = r.json()

    if isinstance(res_data, dict) and "error" in res_data:
        log.error("apifootball.com API error: %s", res_data.get("message"))
        return []

    fixtures = res_data if isinstance(res_data, list) else []

    # Build two indexes from the API response:
    # 1. api_fixture_id → (gols_casa, gols_fora)
    # 2. (home_lower, away_lower) → (gols_casa, gols_fora)  ← fallback
    por_api_id: dict[str, tuple[int, int]] = {}
    por_times: dict[tuple[str, str], tuple[int, int]] = {}

    for fx in fixtures:
        if fx.get("match_status", "") not in _FINISHED:
            continue
        # 90-min FT score only — not ET/penalties
        gh = fx.get("match_hometeam_ft_score") or fx.get("match_hometeam_score")
        ga = fx.get("match_awayteam_ft_score") or fx.get("match_awayteam_score")
        if gh in (None, "", "-") or ga in (None, "", "-"):
            continue
        try:
            gc, gf = int(gh), int(ga)
        except (TypeError, ValueError):
            continue

        api_id = str(fx.get("match_id", ""))
        if api_id:
            por_api_id[api_id] = (gc, gf)

        home = (fx.get("match_hometeam_name") or "").lower()
        away = (fx.get("match_awayteam_name") or "").lower()
        if home and away:
            por_times[(home, away)] = (gc, gf)

    out: list[Resultado] = []
    for jogo in pendentes:
        match_id = jogo.get("match_id", "")
        api_id = str(jogo.get("api_fixture_id", ""))

        # 1. Match by api_fixture_id (exact — preferred)
        placar = por_api_id.get(api_id) if api_id else None

        # 2. Fallback: match by team name pair
        if placar is None:
            key = (_en(jogo.get("casa", "")), _en(jogo.get("fora", "")))
            placar = por_times.get(key)
            if placar:
                log.debug("Resultado casado por nome (sem api_fixture_id): %s", match_id)

        if placar:
            out.append(Resultado(match_id, placar[0], placar[1]))

    return out
