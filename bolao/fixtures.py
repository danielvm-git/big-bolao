"""Sincronizador de fixtures da Copa 2026 via apifootball.com.

Converte a resposta da API em registros prontos pra salvar na colecao `jogos`
do BigBase. Idempotente: usa `api_fixture_id` como chave de deduplicacao —
rodar de novo so cria o que ainda nao existe e atualiza o que mudou.

Fases suportadas (match_round da API → phase_id interno):
  "Group Stage - 1/2/3" → R1/R2/R3
  "Round of 32"         → R32
  "Round of 16"         → R16
  "Quarter-finals"      → QF
  "Semi-finals"         → SF
  "3rd Place Final"     → 3P
  "Final"               → FIN

match_id gerado: <phase_id>-<NN> ex. R1-01, R16-03, QF-02, FIN-01
"""
from __future__ import annotations

import logging
from datetime import timedelta, timezone

import httpx

from bolao import config

log = logging.getLogger("bolao.fixtures")

# Tempo retornado pela API e UTC; kickoff guardado em BRT (UTC-3)
BRT = timezone(timedelta(hours=-3))

# Constante compartilhada de status encerrado (usada tambem por results.py)
FINISHED_STATUSES = frozenset({
    "Finished", "After ET", "After Pen.",
    "FT", "AET", "PEN", "Finished AET", "Finished PEN",
})

# Copa 2026 knockout date windows (BRT) — fallback when match_round is empty.
# The API sometimes publishes fixtures before assigning match_round.
_DATE_PHASE_MAP: list[tuple[str, str, str, int]] = [
    ("2026-06-28", "2026-07-03", "R32", 4),
    ("2026-07-04", "2026-07-08", "R16", 5),
    ("2026-07-09", "2026-07-12", "QF",  6),
    ("2026-07-13", "2026-07-16", "SF",  7),
    ("2026-07-16", "2026-07-18", "3P",  8),
    ("2026-07-18", "2026-07-21", "FIN", 9),
]

# match_round → (phase_id, rodada)
# A API retorna numeros simples ("1","2","3") na fase de grupos e strings
# descritivas nos knockouts ("Round of 16", "Quarter-finals", etc.).
# Rodada numerica usada como campo `rodada` no BigBase.
_NUMERIC_PHASE_MAP: dict[str, tuple[str, int]] = {
    "1": ("R1",  1),
    "2": ("R2",  2),
    "3": ("R3",  3),
    # Knockouts tambem podem vir como numeros dependendo da API
    # Copa 2026 tem 48 selecoes → fase extra Round of 32 antes do R16
    "4": ("R32", 4),
    "5": ("R16", 5),
    "6": ("QF",  6),
    "7": ("SF",  7),
    "8": ("3P",  8),
    "9": ("FIN", 9),
}

# Fallback para quando a API usar strings descritivas (knockouts)
_STRING_PHASE_MAP: list[tuple[str, str, int]] = [
    ("group stage - 1",  "R1",  1),
    ("group stage - 2",  "R2",  2),
    ("group stage - 3",  "R3",  3),
    ("round of 32",      "R32", 4),
    ("round of 16",      "R16", 5),
    ("quarter-final",    "QF",  6),
    ("semi-final",       "SF",  7),
    ("3rd place",        "3P",  8),
    ("final",            "FIN", 9),
]


def parse_result(fixture: dict) -> tuple[int, int] | None:
    """Extrai placar de 90 minutos de um fixture bruto da API.

    Retorna (gols_casa, gols_fora) usando match_hometeam_ft_score (90min),
    com fallback para match_hometeam_score (prorrogação). Retorna None
    se o placar nao estiver disponivel ou for invalido.
    """
    gh = fixture.get("match_hometeam_ft_score") or fixture.get("match_hometeam_score")
    ga = fixture.get("match_awayteam_ft_score") or fixture.get("match_awayteam_score")
    if gh in (None, "", "-") or ga in (None, "", "-"):
        return None
    try:
        return int(gh), int(ga)
    except (TypeError, ValueError):
        return None


def _parse_phase(round_str: str, date_str: str = "") -> tuple[str, int] | None:
    """Devolve (phase_id, rodada) ou None se a rodada nao for reconhecida.

    date_str (YYYY-MM-DD) e usado como fallback quando match_round esta vazio —
    a API publica fixtures antes de definir a fase nos knockouts.
    """
    s = (round_str or "").strip()
    # Tenta mapa numerico primeiro (formato atual da API)
    if s in _NUMERIC_PHASE_MAP:
        return _NUMERIC_PHASE_MAP[s]
    # Fallback: substring match em strings descritivas
    sl = s.lower()
    for keyword, phase_id, rodada in _STRING_PHASE_MAP:
        if keyword in sl:
            return phase_id, rodada
    # Ultimo recurso: inferir pelo intervalo de datas (knockouts sem match_round)
    if date_str:
        for from_d, to_d, phase_id, rodada in _DATE_PHASE_MAP:
            if from_d <= date_str <= to_d:
                log.debug("Fase inferida por data %s → %s", date_str, phase_id)
                return phase_id, rodada
    return None


def _to_brt_iso(date_str: str, time_str: str) -> str:
    """Converte 'YYYY-MM-DD' + 'HH:MM' (ja em BRT, vindos da API com timezone=America/Sao_Paulo)
    para string ISO sem offset, consistente com os registros existentes do matches.py.
    """
    time_str = time_str[:5] if len(time_str) > 5 else time_str  # strip seconds if present
    return f"{date_str}T{time_str}:00"


def _generate_match_id(phase_id: str, counter: int) -> str:
    return f"{phase_id}-{counter:02d}"


def normalise(raw_fixtures: list[dict]) -> list[dict]:
    """Converte lista bruta da API em lista de dicts prontos pra salvar no BigBase.

    Retorna apenas fixtures de fases reconhecidas, ordenados por kickoff.
    Cada dict tem: api_fixture_id, match_id, rodada, kickoff (BRT), casa, fora,
    gols_casa, gols_fora, status.
    """
    por_fase: dict[str, list[dict]] = {}

    for fx in raw_fixtures:
        round_str = fx.get("match_round", "")
        parsed = _parse_phase(round_str, fx.get("match_date", ""))
        if parsed is None:
            log.debug("Rodada ignorada: %r", round_str)
            continue

        phase_id, rodada = parsed
        kickoff = _to_brt_iso(
            fx.get("match_date", ""),
            fx.get("match_time", "00:00"),
        )

        status_api = (fx.get("match_status") or "").strip()
        finished = status_api in FINISHED_STATUSES

        placar = parse_result(fx) if finished else None
        gols_casa = placar[0] if placar else None
        gols_fora = placar[1] if placar else None

        record = {
            "api_fixture_id": str(fx.get("match_id", "")),
            "_phase_id": phase_id,
            "_kickoff_sort": kickoff,
            "rodada": rodada,
            "kickoff": kickoff,
            "casa": fx.get("match_hometeam_name", "TBD"),
            "fora": fx.get("match_awayteam_name", "TBD"),
            "gols_casa": gols_casa,
            "gols_fora": gols_fora,
            "status": "encerrado" if finished else "agendado",
        }

        por_fase.setdefault(phase_id, []).append(record)

    # Ordena por kickoff dentro de cada fase e gera match_id
    result: list[dict] = []
    for phase_id, fixtures in por_fase.items():
        fixtures.sort(key=lambda r: r["_kickoff_sort"])
        for i, fx in enumerate(fixtures, start=1):
            fx["match_id"] = _generate_match_id(phase_id, i)
            # Remove campos auxiliares antes de salvar
            fx.pop("_phase_id", None)
            fx.pop("_kickoff_sort", None)
            result.append(fx)

    result.sort(key=lambda r: r["kickoff"])
    return result


async def fetch_from_api(
    *,
    league_id: str | None = None,
    season: str | None = None,
    from_date: str = "2026-06-01",
    to_date: str = "2026-07-31",
) -> list[dict]:
    """Busca fixtures no apifootball.com e devolve lista normalizada.

    Levanta RuntimeError se a chave nao estiver configurada ou a API retornar erro.
    """
    key = config.APIFOOTBALL_KEY
    if not key:
        raise RuntimeError(
            "APIFOOTBALL_KEY nao configurada. "
            "Defina no .env antes de rodar o sync."
        )

    params: dict[str, str] = {
        "action": "get_events",
        "from": from_date,
        "to": to_date,
        "APIkey": key,
        "timezone": "America/Sao_Paulo",  # times returned in BRT, no conversion needed
    }
    lid = league_id or config.APIFOOTBALL_LEAGUE_ID
    if lid:
        params["league_id"] = str(lid)

    log.info("apifootball.com → league_id=%s from=%s to=%s", lid, from_date, to_date)

    async with httpx.AsyncClient(timeout=30.0) as cli:
        r = await cli.get("https://apiv3.apifootball.com/", params=params)
        r.raise_for_status()
        data = r.json()

    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(
            f"apifootball.com erro {data.get('error')}: {data.get('message')}"
        )

    raw: list[dict] = data if isinstance(data, list) else []
    log.info("%d fixtures recebidos da API", len(raw))
    return normalise(raw)
