"""Gera web/src/data/mock.js a partir dos dados reais da planilha do grupo.

Fonte da verdade (mesma usada pelo bot):
  - bolao/matches.py   -> agenda (R1..R3)
  - bolao/historico.py -> resultados + palpites da Rodada 1 (transcritos da planilha)
  - bolao/scoring.py   -> regra 3/1/0

Saida: web/src/data/mock.js, no formato consumido pelos composables do site.
Reexecute sempre que a planilha mudar:
    python -m scripts.gen_web_data
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bolao.historico import PARTICIPANTES, RODADA1, parse_placar
from bolao.matches import BY_ID, MATCHES
from bolao.scoring import pontos

# "Agora" de referencia (data do ambiente). Define o que esta aberto x em andamento.
NOW = datetime(2026, 6, 19, 12, 0, 0)

# Usuario logado no site (perspectiva da planilha).
USUARIO_NOME = "Mari Gallo"

MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
         "jul", "ago", "set", "out", "nov", "dez"]

FLAGS = {
    "México": "🇲🇽", "África do Sul": "🇿🇦", "Coreia do Sul": "🇰🇷",
    "República Tcheca": "🇨🇿", "Canadá": "🇨🇦", "Bósnia e Herzegovina": "🇧🇦",
    "Estados Unidos": "🇺🇸", "Paraguai": "🇵🇾", "Catar": "🇶🇦", "Suíça": "🇨🇭",
    "Brasil": "🇧🇷", "Marrocos": "🇲🇦", "Haiti": "🇭🇹", "Escócia": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Austrália": "🇦🇺", "Turquia": "🇹🇷", "Alemanha": "🇩🇪", "Curaçao": "🇨🇼",
    "Países Baixos": "🇳🇱", "Japão": "🇯🇵", "Costa do Marfim": "🇨🇮",
    "Equador": "🇪🇨", "Suécia": "🇸🇪", "Tunísia": "🇹🇳", "Espanha": "🇪🇸",
    "Cabo Verde": "🇨🇻", "Bélgica": "🇧🇪", "Egito": "🇪🇬",
    "Arábia Saudita": "🇸🇦", "Uruguai": "🇺🇾", "Irã": "🇮🇷",
    "Nova Zelândia": "🇳🇿", "França": "🇫🇷", "Senegal": "🇸🇳", "Iraque": "🇮🇶",
    "Noruega": "🇳🇴", "Argentina": "🇦🇷", "Argélia": "🇩🇿", "Áustria": "🇦🇹",
    "Jordânia": "🇯🇴", "Portugal": "🇵🇹",
    "República Democrática do Congo": "🇨🇩", "Inglaterra": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Croácia": "🇭🇷", "Gana": "🇬🇭", "Panamá": "🇵🇦", "Uzbequistão": "🇺🇿",
    "Colômbia": "🇨🇴",
}

# match_id -> id numerico estavel (R1-01 -> 1, R2-01 -> 101, R3-01 -> 201)
def num_id(match_id: str) -> int:
    rodada, n = match_id[1:].split("-")
    return int(rodada) * 100 + int(n)


def flag(team: str) -> str:
    return FLAGS.get(team, "🏳️")


def date_label(dt: datetime) -> str:
    d = dt.date()
    if d == NOW.date():
        return "Hoje"
    if d == (NOW + timedelta(days=1)).date():
        return "Amanhã"
    return f"{d.day} {MESES[d.month - 1].capitalize()}"


def js(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


# ---------------------------------------------------------------------------
# 1) Indexa resultados + palpites da Rodada 1 (a planilha real)
# ---------------------------------------------------------------------------
res_por_id: dict[str, tuple[int, int]] = {}
palp_por_id: dict[str, dict[str, tuple[int, int]]] = {}  # mid -> {nome: (a,b)}

for mid, res, palps in RODADA1:
    real = parse_placar(res)
    res_por_id[mid] = real
    palp_por_id[mid] = {}
    for nome, p in zip(PARTICIPANTES, palps):
        pp = parse_placar(p)
        if pp is not None:
            palp_por_id[mid][nome] = pp

# ---------------------------------------------------------------------------
# 2) Ranking (regra 3/1/0) — fonte da verdade, igual ao check_ranking
# ---------------------------------------------------------------------------
tot = {n: {"pontos": 0, "exatos": 0} for n in PARTICIPANTES}
for mid, real in res_por_id.items():
    for nome, pp in palp_por_id[mid].items():
        pts = pontos(pp[0], pp[1], real[0], real[1])
        tot[nome]["pontos"] += pts
        if pts == 3:
            tot[nome]["exatos"] += 1

ranking = sorted(
    ([n, tot[n]["pontos"], tot[n]["exatos"]] for n in PARTICIPANTES),
    key=lambda r: (-r[1], -r[2], r[0].lower()),
)
pos_id = {nome: i + 1 for i, (nome, _, _) in enumerate(ranking)}

# ---------------------------------------------------------------------------
# 3) GAMES — R1 finalizados (planilha) + R2 como proximos jogos
# ---------------------------------------------------------------------------
games = []
palpites_user = {}  # gameId -> {goalsA, goalsB}  (palpites do usuario logado)

for m in MATCHES:
    if m.rodada > 2:
        continue
    gid = num_id(m.match_id)
    dt = datetime.fromisoformat(m.kickoff)
    base = {
        "id": gid,
        "teamA": m.casa, "teamB": m.fora,
        "flagA": flag(m.casa), "flagB": flag(m.fora),
        "date": date_label(dt), "time": dt.strftime("%H:%M"),
        "grupo": f"Rodada {m.rodada}",
        "kickoff": m.kickoff,
    }

    if m.match_id in res_por_id:  # Rodada 1 — finalizado, com placar real
        ra, rb = res_por_id[m.match_id]
        cravou, vencedor = [], []
        for nome, (pa, pb) in palp_por_id[m.match_id].items():
            pts = pontos(pa, pb, ra, rb)
            if pts == 3:
                cravou.append(nome)
            elif pts == 1:
                vencedor.append(nome)
        base.update({
            "status": "finalizado",
            "resultado": {"goalsA": ra, "goalsB": rb},
            "quemCravou": cravou,
            "quemVencedor": vencedor,
        })
        if USUARIO_NOME in palp_por_id[m.match_id]:
            ua, ub = palp_por_id[m.match_id][USUARIO_NOME]
            palpites_user[gid] = {"goalsA": ua, "goalsB": ub}
    else:  # Rodada 2 — ainda nao jogado
        base["status"] = "aberto" if dt >= NOW else "bloqueado"

    games.append(base)

# ---------------------------------------------------------------------------
# 4) Emite o mock.js
# ---------------------------------------------------------------------------
u_nome = USUARIO_NOME
u_pos = pos_id[u_nome]
u_pts = tot[u_nome]["pontos"]
u_exatos = tot[u_nome]["exatos"]

out = []
out.append("// AUTO-GERADO por scripts/gen_web_data.py — não editar à mão.")
out.append("// Fonte: planilha do grupo (bolao/historico.py + matches.py), regra 3/1/0.")
out.append("// Reexecute: python -m scripts.gen_web_data")
out.append("")
out.append("export const USUARIO = {")
out.append(f"  id: {u_pos},")
out.append(f"  nome: '{js(u_nome)}',")
out.append("  telegram_id: 0,")
out.append(f"  pontos: {u_pts},")
out.append(f"  exatos: {u_exatos},")
out.append("}")
out.append("")
out.append("export const RANKING = [")
for nome, pts, exatos in ranking:
    out.append(
        f"  {{ id: {pos_id[nome]}, name: '{js(nome)}', "
        f"pontos: {pts}, exatos: {exatos} }},")
out.append("]")
out.append("")
out.append("export const GAMES = [")
for g in games:
    out.append("  {")
    out.append(f"    id: {g['id']}, teamA: '{js(g['teamA'])}', teamB: '{js(g['teamB'])}',")
    out.append(f"    flagA: '{g['flagA']}', flagB: '{g['flagB']}',")
    out.append(f"    date: '{js(g['date'])}', time: '{g['time']}', status: '{g['status']}',")
    out.append(f"    grupo: '{js(g['grupo'])}', kickoff: '{g['kickoff']}',")
    if "resultado" in g:
        r = g["resultado"]
        out.append(f"    resultado: {{ goalsA: {r['goalsA']}, goalsB: {r['goalsB']} }},")
        cravou = ", ".join(f"'{js(n)}'" for n in g["quemCravou"])
        venc = ", ".join(f"'{js(n)}'" for n in g["quemVencedor"])
        out.append(f"    quemCravou: [{cravou}],")
        out.append(f"    quemVencedor: [{venc}],")
    out.append("  },")
out.append("]")
out.append("")
out.append("// Palpites salvos do usuário logado: gameId -> { goalsA, goalsB }")
out.append("export const PALPITES_SALVOS = {")
for gid in sorted(palpites_user):
    p = palpites_user[gid]
    out.append(f"  {gid}: {{ goalsA: {p['goalsA']}, goalsB: {p['goalsB']} }},")
out.append("}")
out.append("")
out.append("export const REGRA_PONTUACAO = "
           "'3 pts placar exato · 1 pt vencedor/empate · 0 pt erro'")
out.append("")

dest = Path(__file__).resolve().parent.parent / "web" / "src" / "data" / "mock.js"
dest.write_text("\n".join(out), encoding="utf-8")
print(f"✅ {dest}")
print(f"   {len(games)} jogos ({sum(1 for g in games if g['status']=='finalizado')} finalizados), "
      f"{len(palpites_user)} palpites do usuário, {len(ranking)} no ranking")
print("   Ranking:", ", ".join(f"{n} {p}" for n, p, _ in ranking))
