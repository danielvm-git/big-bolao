"""Verifica estado do ranking e funde duplicatas restantes."""
from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

import httpx

BASE = "https://bigbase.click"
EMAIL = "bolao-bot@bigbase.local"
PASSWORD = "bolao-bot-secure-password-2026"
PARTICIPANTES = "participantes"
PALPITES = "palpites"


async def main():
    async with httpx.AsyncClient(base_url=BASE, timeout=20.0) as cli:
        r = await cli.post("/api/auth/login", json={
            "email": EMAIL, "password": PASSWORD})
        assert r.status_code == 200
        token = r.json()["token"]
        h = {"Authorization": f"Bearer {token}"}

        # Participants
        r = await cli.get(f"/api/collections/{PARTICIPANTES}", params={"limit": 1000}, headers=h)
        parts = r.json().get("data", [])

        # Palpites
        r = await cli.get(f"/api/collections/{PALPITES}", params={"limit": 2000}, headers=h)
        all_palpites = r.json().get("data", [])

        palp_count: dict[int, int] = {}
        for p in all_palpites:
            tid = int(p.get("telegram_id", 0))
            palp_count[tid] = palp_count.get(tid, 0) + 1

        print("📋 Todos os participantes:")
        for p in parts:
            tid = int(p.get("telegram_id", 0))
            print(f"  id={p['id']:<3} tg={tid:<12} nome='{p.get('nome','?'):<20}' "
                  f"ativo={p.get('ativo', True)} palpites={palp_count.get(tid, 0)}")

        # Check for orphaned palpites (tg not in any active participant)
        active_tgs = {int(p["telegram_id"]) for p in parts if p.get("ativo", True)}
        orphaned = {}
        for p in all_palpites:
            tid = int(p.get("telegram_id", 0))
            if tid not in active_tgs:
                orphaned.setdefault(tid, []).append(p)
        
        if orphaned:
            print(f"\n⚠️ Palpites orfaos (telegram_id sem participante ativo):")
            for tid, palp_list in orphaned.items():
                names = set(pp.get("nome", "?") for pp in palp_list)
                print(f"  tg={tid}: {len(palp_list)} palpites de {names}")

        # Merge orphaned Flávia (tg=-4) if exists
        flavia_old = next((p for p in parts if int(p.get("telegram_id", 0)) == -4), None)
        if flavia_old and flavia_old.get("ativo") == False:
            # Find active Flávia or someone with those palpites
            flavia_palpites = [pp for pp in all_palpites if int(pp.get("telegram_id", 0)) == -4]
            if flavia_palpites:
                # Find which active participant has these match_ids
                active_palpites = {}
                for pp in all_palpites:
                    tid = int(pp.get("telegram_id", 0))
                    if tid in active_tgs:
                        active_palpites.setdefault(tid, {})

                # Try to match: find if any active participant has palpites for the same games
                flavia_matches = {pp["match_id"] for pp in flavia_palpites}
                best_match = None
                for pp in all_palpites:
                    tid = int(pp.get("telegram_id", 0))
                    if tid in active_tgs and pp["match_id"] in flavia_matches:
                        if best_match is None:
                            best_match = tid
                
                if best_match:
                    print(f"\n🔀 Migrando {len(flavia_palpites)} palpites de Flávia (tg=-4) → tg={best_match}")
                    for pp in flavia_palpites:
                        await cli.patch(
                            f"/api/collections/{PALPITES}/{pp['id']}",
                            headers=h,
                            json={"telegram_id": best_match})
                    print("✅ Feito!")
                else:
                    print(f"\n⚠️ {len(flavia_palpites)} palpites de Flávia (tg=-4) sem destino claro")

        print("\n✅ Verificacao concluida.")


if __name__ == "__main__":
    asyncio.run(main())
