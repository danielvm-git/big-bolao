"""Provedor de resultados de jogos (pluggable).

- Modo manual (default): nenhum provider; admin usa /resultado no Telegram.
- apifootball: consulta API-Football (RapidAPI) os jogos da liga/temporada e
  devolve placares finais, casados com a agenda local pelo nome dos times.

A API-Football usa nomes em ingles; o casamento e por traducao + heuristica.
Se a cobertura da Copa 2026 nao estiver disponivel no seu plano, deixe
RESULTS_PROVIDER vazio e use o modo manual.
"""
from __future__ import annotations

import httpx

from bolao import config
from bolao.matches import MATCHES, Match

# Mapeia nome PT (agenda) -> nome EN (API-Football). Ajuste conforme necessario.
PT_TO_EN = {
    "México": "Mexico", "África do Sul": "South Africa", "Coreia do Sul": "South Korea",
    "República Tcheca": "Czech Republic", "Canadá": "Canada",
    "Bósnia e Herzegovina": "Bosnia and Herzegovina", "Estados Unidos": "USA",
    "Paraguai": "Paraguay", "Catar": "Qatar", "Suíça": "Switzerland",
    "Brasil": "Brazil", "Marrocos": "Morocco", "Haiti": "Haiti", "Escócia": "Scotland",
    "Austrália": "Australia", "Turquia": "Turkey", "Alemanha": "Germany",
    "Curaçao": "Curacao", "Países Baixos": "Netherlands", "Japão": "Japan",
    "Costa do Marfim": "Ivory Coast", "Equador": "Ecuador", "Suécia": "Sweden",
    "Tunísia": "Tunisia", "Espanha": "Spain", "Cabo Verde": "Cape Verde",
    "Bélgica": "Belgium", "Egito": "Egypt", "Arábia Saudita": "Saudi Arabia",
    "Uruguai": "Uruguay", "Irã": "Iran", "Nova Zelândia": "New Zealand",
    "França": "France", "Senegal": "Senegal", "Iraque": "Iraq", "Noruega": "Norway",
    "Argentina": "Argentina", "Argélia": "Algeria", "Áustria": "Austria",
    "Jordânia": "Jordan", "Portugal": "Portugal",
    "República Democrática do Congo": "Congo DR", "Inglaterra": "England",
    "Croácia": "Croatia", "Gana": "Ghana", "Panamá": "Panama",
    "Uzbequistão": "Uzbekistan", "Colômbia": "Colombia",
}


class Resultado:
    def __init__(self, match: Match, gols_casa: int, gols_fora: int):
        self.match = match
        self.gols_casa = gols_casa
        self.gols_fora = gols_fora


async def buscar_encerrados() -> list[Resultado]:
    """Retorna placares finais conhecidos pelo provider configurado."""
    if config.RESULTS_PROVIDER == "apifootball":
        return await _apifootball()
    return []  # modo manual


def _en(nome: str) -> str:
    return PT_TO_EN.get(nome, nome).lower()


async def _apifootball() -> list[Resultado]:
    if not config.APIFOOTBALL_KEY:
        return []
    headers = {
        "x-rapidapi-key": config.APIFOOTBALL_KEY,
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
    }
    params = {"league": config.APIFOOTBALL_LEAGUE_ID, "season": config.APIFOOTBALL_SEASON}
    async with httpx.AsyncClient(timeout=20.0) as cli:
        r = await cli.get("https://api-football-v1.p.rapidapi.com/v3/fixtures",
                          headers=headers, params=params)
        r.raise_for_status()
        fixtures = r.json().get("response", [])

    # indexa placares finais por par de times (EN, minusculo)
    placares: dict[tuple[str, str], tuple[int, int]] = {}
    for fx in fixtures:
        status = fx.get("fixture", {}).get("status", {}).get("short")
        if status not in ("FT", "AET", "PEN"):
            continue
        teams, goals = fx.get("teams", {}), fx.get("goals", {})
        home = (teams.get("home", {}).get("name") or "").lower()
        away = (teams.get("away", {}).get("name") or "").lower()
        gh, ga = goals.get("home"), goals.get("away")
        if home and away and gh is not None and ga is not None:
            placares[(home, away)] = (int(gh), int(ga))

    out: list[Resultado] = []
    for m in MATCHES:
        key = (_en(m.casa), _en(m.fora))
        if key in placares:
            gc, gf = placares[key]
            out.append(Resultado(m, gc, gf))
    return out
