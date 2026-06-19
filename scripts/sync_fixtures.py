"""Sincroniza fixtures da Copa 2026 (apifootball.com) → BigBase.

Idempotente: pode ser rodado a qualquer momento.

Logica de upsert (em ordem):
  1. Se o registro ja tem api_fixture_id igual → PATCH (so o que mudou).
  2. Se nao tem api_fixture_id mas os times batem → vincula e PATCH.
  3. Se nao encontrou nada → CREATE (novo jogo, ex. fase knockout).
  Nunca apaga registros — palpites vinculados ficam intactos.

Uso:
    python -m scripts.sync_fixtures                # sync completo
    python -m scripts.sync_fixtures --dry          # mostra o que faria, sem escrever
    python -m scripts.sync_fixtures --from 2026-07-01 --to 2026-07-31  # so knockouts

Variaveis de ambiente necessarias (.env):
    APIFOOTBALL_KEY        chave da API
    APIFOOTBALL_LEAGUE_ID  ID da liga Copa 2026 (28)
    BIGBASE_URL / BIGBASE_EMAIL / BIGBASE_PASSWORD
"""
from __future__ import annotations

import asyncio
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

import argparse
import logging

from bolao.bigbase import BigBase, JOGOS
from bolao.fixtures import fetch_from_api

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s | %(message)s",
)
log = logging.getLogger("sync_fixtures")


# ---------------------------------------------------------------------------
# Team name normalisation — maps API English names to a canonical lowercase key
# so we can match against existing BigBase records (stored in Portuguese).
# ---------------------------------------------------------------------------

# PT (BigBase) → EN (API canonical)
_PT_TO_EN: dict[str, str] = {
    "México": "mexico", "África do Sul": "south africa",
    "Coreia do Sul": "south korea", "República Tcheca": "czech republic",
    "Canadá": "canada", "Bósnia e Herzegovina": "bosnia and herzegovina",
    "Estados Unidos": "usa", "Paraguai": "paraguay",
    "Catar": "qatar", "Suíça": "switzerland",
    "Brasil": "brazil", "Marrocos": "morocco",
    "Haiti": "haiti", "Escócia": "scotland",
    "Austrália": "australia", "Turquia": "turkey",
    "Alemanha": "germany", "Curaçao": "curacao",
    "Países Baixos": "netherlands", "Japão": "japan",
    "Costa do Marfim": "ivory coast", "Equador": "ecuador",
    "Suécia": "sweden", "Tunísia": "tunisia",
    "Espanha": "spain", "Cabo Verde": "cape verde",
    "Bélgica": "belgium", "Egito": "egypt",
    "Arábia Saudita": "saudi arabia", "Uruguai": "uruguay",
    "Irã": "iran", "Nova Zelândia": "new zealand",
    "França": "france", "Senegal": "senegal",
    "Iraque": "iraq", "Noruega": "norway",
    "Argentina": "argentina", "Argélia": "algeria",
    "Áustria": "austria", "Jordânia": "jordan",
    "Portugal": "portugal",
    "República Democrática do Congo": "dr congo",
    "Inglaterra": "england", "Croácia": "croatia",
    "Gana": "ghana", "Panamá": "panama",
    "Uzbequistão": "uzbekistan", "Colômbia": "colombia",
}

# Extra aliases for API name variations
_API_ALIASES: dict[str, str] = {
    "bosnia & herzegovina": "bosnia and herzegovina",
    "d.r. congo": "dr congo",
    "congo dr": "dr congo",
    "republic of ireland": "ireland",
    "korea republic": "south korea",
    "korea dpr": "north korea",
    "united states": "usa",
}


def _norm(name: str) -> str:
    """Normalize a team name to a canonical lowercase key for matching."""
    s = name.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return _API_ALIASES.get(s, s)


def _norm_existing(name: str) -> str:
    """Normalize a name stored in BigBase (may be Portuguese or English)."""
    if name in _PT_TO_EN:
        return _PT_TO_EN[name]   # already canonical
    return _norm(name)


def _changed(existing: dict, incoming: dict) -> dict:
    """Returns only the fields that actually differ."""
    TRACKED = ("kickoff", "casa", "fora", "gols_casa", "gols_fora",
               "status", "api_fixture_id", "rodada")
    return {k: incoming[k] for k in TRACKED
            if k in incoming and incoming.get(k) != existing.get(k)}


async def run(dry: bool, from_date: str, to_date: str) -> None:
    if dry:
        log.info("*** DRY RUN — nada sera escrito no BigBase ***")

    # 1. Fetch from API
    log.info("Buscando fixtures da API...")
    fixtures = await fetch_from_api(from_date=from_date, to_date=to_date)
    log.info("%d fixtures recebidos (fases reconhecidas)", len(fixtures))

    if not fixtures:
        log.warning("Nenhum fixture retornado. Verifique APIFOOTBALL_LEAGUE_ID.")
        return

    # 2. Load existing records from BigBase
    db = BigBase()
    try:
        log.info("Carregando jogos existentes do BigBase...")
        existentes = await db.list_records(JOGOS)
        log.info("%d registros existentes no BigBase", len(existentes))

        # Index 1: by api_fixture_id (already linked records)
        por_api_id: dict[str, dict] = {}
        # Index 2: by normalized (home, away) pair (unlinked records)
        por_times: dict[tuple[str, str], dict] = {}
        # Set of match_ids already in use
        match_ids_usados: set[str] = set()

        for j in existentes:
            aid = j.get("api_fixture_id")
            if aid:
                por_api_id[str(aid)] = j
            # Build team-pair index with normalised names
            key = (_norm_existing(j.get("casa", "")),
                   _norm_existing(j.get("fora", "")))
            por_times[key] = j
            mid = j.get("match_id")
            if mid:
                match_ids_usados.add(mid)

        criados = 0
        atualizados = 0
        vinculados = 0
        sem_mudanca = 0

        for fx in fixtures:
            api_id = fx["api_fixture_id"]
            team_key = (_norm(fx["casa"]), _norm(fx["fora"]))

            # --- Lookup: api_fixture_id first, then team names ---
            existing = por_api_id.get(api_id)
            linked_by_teams = False
            if existing is None:
                existing = por_times.get(team_key)
                if existing:
                    linked_by_teams = True  # first-time link

            if existing is None:
                # --- CREATE (new fixture, e.g. knockout round) ---
                mid = fx["match_id"]
                original = mid
                suffix = 0
                while mid in match_ids_usados:
                    suffix += 1
                    mid = f"{original}-{suffix}"
                fx["match_id"] = mid
                match_ids_usados.add(mid)

                log.info("  [CRIAR] %s  %s x %s  (%s)",
                         fx["match_id"], fx["casa"], fx["fora"], fx["kickoff"])
                if not dry:
                    await db.create(JOGOS, {
                        "match_id":       fx["match_id"],
                        "api_fixture_id": fx["api_fixture_id"],
                        "rodada":         fx["rodada"],
                        "kickoff":        fx["kickoff"],
                        "casa":           fx["casa"],
                        "fora":           fx["fora"],
                        "gols_casa":      fx["gols_casa"],
                        "gols_fora":      fx["gols_fora"],
                        "status":         fx["status"],
                    })
                criados += 1

            else:
                # --- PATCH: only fields that changed ---
                diff = _changed(existing, fx)

                # Always include api_fixture_id when linking for the first time
                if linked_by_teams and "api_fixture_id" not in diff:
                    diff["api_fixture_id"] = api_id

                if not diff:
                    sem_mudanca += 1
                    continue

                label = (existing.get("casa", "?") + " x " +
                         existing.get("fora", "?"))
                row_id = existing.get("id")

                if linked_by_teams:
                    log.info("  [VINCULAR+UPDATE] %s  %s  mudancas: %s",
                             existing.get("match_id"), label, list(diff.keys()))
                    vinculados += 1
                else:
                    log.info("  [UPDATE] %s  %s  mudancas: %s",
                             existing.get("match_id"), label, list(diff.keys()))
                    atualizados += 1

                if not dry and row_id:
                    await db.patch(JOGOS, row_id, diff)

        print()
        print("=" * 52)
        print(f"  Criados:                {criados}")
        print(f"  Vinculados (1a vez):    {vinculados}")
        print(f"  Atualizados:            {atualizados}")
        print(f"  Sem mudanca:            {sem_mudanca}")
        print(f"  Total da API:           {len(fixtures)}")
        if dry:
            print("  (dry run — nada foi escrito)")
        print("=" * 52)

    finally:
        await db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sincroniza fixtures Copa 2026 → BigBase"
    )
    parser.add_argument("--dry", action="store_true",
                        help="Mostra o que faria sem escrever nada")
    parser.add_argument("--from", dest="from_date", default="2026-06-01",
                        metavar="YYYY-MM-DD", help="Data inicial (padrao: 2026-06-01)")
    parser.add_argument("--to", dest="to_date", default="2026-07-31",
                        metavar="YYYY-MM-DD", help="Data final (padrao: 2026-07-31)")
    args = parser.parse_args()

    asyncio.run(run(dry=args.dry, from_date=args.from_date, to_date=args.to_date))


if __name__ == "__main__":
    main()
