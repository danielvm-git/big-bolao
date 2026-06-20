"""Tests for bolao/bigbase.py — participant registration & placeholder linking.

Mock strategy: patch BigBase.list_records, .patch, and .create to test
registrar_participante in isolation from real BigBase HTTP calls.
"""
import pytest
from unittest.mock import AsyncMock
from bolao.bigbase import BigBase

# ── helpers ─────────────────────────────────────────────────────────────────

def _make_bb(
    participantes: list[dict] | None = None,
    palpites: list[dict] | None = None,
) -> BigBase:
    """Cria um BigBase com list_records mockado."""
    store = {
        "participantes": participantes or [],
        "palpites": palpites or [],
        "jogos": [],
    }
    bb = BigBase(url="http://test.local")
    bb._token = "fake-token"  # skip login

    async def fake_list_records(collection: str, limit: int = 1000) -> list[dict]:
        return store.get(collection, [])

    async def fake_create(collection: str, data: dict) -> int:
        recs = store.setdefault(collection, [])
        new_id = max((r["id"] for r in recs), default=0) + 1
        store[collection].append({"id": new_id, **data})
        return new_id

    async def fake_patch(collection: str, rec_id: int, data: dict) -> None:
        for r in store.get(collection, []):
            if r["id"] == rec_id:
                r.update(data)
                return
        raise ValueError(f"record {rec_id} not found in {collection}")

    bb.list_records = AsyncMock(side_effect=fake_list_records)
    bb.create = AsyncMock(side_effect=fake_create)
    bb.patch = AsyncMock(side_effect=fake_patch)
    # Store reference so tests can inspect state
    bb._store = store
    return bb


# ── Ciclo 1: placeholder vinculado por substring ───────────────────────────

@pytest.mark.asyncio
async def test_placeholder_contains_match():
    """Placeholder 'Flávia' deve ser vinculado quando chega 'Ana Flavia Cernic Ramos'.

    Cria participante placeholder (telegram_id=-4, nome='Flávia', ativo=False)
    e chama registrar_participante(12345, 'Ana Flavia Cernic Ramos').
    Deve patch no placeholder (não criar novo registro).
    """
    bb = _make_bb(participantes=[
        {"id": 1, "telegram_id": -4, "nome": "Flávia", "ativo": False},
    ])
    bb._store["palpites"] = [
        {"id": 10, "match_id": "R1-01", "telegram_id": -4,
         "gols_casa": 2, "gols_fora": 1},
    ]

    await bb.registrar_participante(12345, "Ana Flavia Cernic Ramos")

    # Deve ter apenas 1 participante (o placeholder foi atualizado)
    parts = await bb.listar_participantes()
    assert len(parts) == 1, f"Esperado 1 participante, tem {len(parts)}"

    p = parts[0]
    assert p["telegram_id"] == 12345, "telegram_id deve ser o real"
    assert p["ativo"] is True, "deve estar ativo"
    assert p["nome"] == "Ana Flavia Cernic Ramos", "nome deve ser o completo"

    # Palpites migrados para o novo telegram_id
    palpites = bb._store["palpites"]
    for pal in palpites:
        assert pal["telegram_id"] == 12345, "palpite deve ter telegram_id real"


# ── Ciclo 1 (continuacao): placeholder vinculado com nome contendo o novo ──

@pytest.mark.asyncio
async def test_new_name_contained_in_placeholder():
    """Placeholder 'Maria Fernanda' deve vincular quando chega 'Fernanda'.

    Caso inverso: o nome novo está contido no nome do placeholder.
    """
    bb = _make_bb(participantes=[
        {"id": 1, "telegram_id": -2, "nome": "Maria Fernanda Silva", "ativo": False},
    ])

    await bb.registrar_participante(88888, "Fernanda")

    parts = await bb.listar_participantes()
    assert len(parts) == 1, "não deve criar novo registro"
    assert parts[0]["telegram_id"] == 88888
    assert parts[0]["ativo"] is True


# ── Ciclo 2: placeholder sem correspondencia não é vinculado ───────────────

@pytest.mark.asyncio
async def test_no_false_match():
    """Placeholder 'Flávia' não deve vincular 'João Silva'.

    Chamar registrar_participante(99999, 'João Silva') quando só existe
    placeholder 'Flávia' deve criar novo registro normalmente.
    """
    bb = _make_bb(participantes=[
        {"id": 1, "telegram_id": -4, "nome": "Flávia", "ativo": False},
    ])

    await bb.registrar_participante(99999, "João Silva")

    parts = await bb.listar_participantes()
    assert len(parts) == 2, "deve criar novo registro (placeholder + novo)"
    # O placeholder continua intocado
    placeholder = next(p for p in parts if p["telegram_id"] == -4)
    assert placeholder["nome"] == "Flávia"
    assert placeholder["ativo"] is False
    # Novo registro existe
    novo = next(p for p in parts if p["telegram_id"] == 99999)
    assert novo["nome"] == "João Silva"
    assert novo["ativo"] is True


# ── Ciclo 2: sem placeholder nenhum, cria novo ────────────────────────────

@pytest.mark.asyncio
async def test_no_placeholder_at_all():
    """Sem placeholders, criar registro novo é o comportamento esperado."""
    bb = _make_bb(participantes=[])

    await bb.registrar_participante(11111, "Novo Jogador")

    parts = await bb.listar_participantes()
    assert len(parts) == 1
    assert parts[0]["telegram_id"] == 11111
    assert parts[0]["nome"] == "Novo Jogador"


# ── Ciclo 3: /sou ainda funciona ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_reivindicar_still_works():
    """Após fix, /sou Flávia ainda migra palpites corretamente.

    Cenário: placeholder 'Flávia' (-4) com palpites, chamar
    reivindicar('Flávia', 12345). Deve migrar palpites e vincular.
    """
    bb = _make_bb(participantes=[
        {"id": 1, "telegram_id": -4, "nome": "Flávia", "ativo": False},
    ])
    bb._store["palpites"] = [
        {"id": 10, "match_id": "R1-01", "telegram_id": -4,
         "gols_casa": 2, "gols_fora": 1},
        {"id": 11, "match_id": "R1-02", "telegram_id": -4,
         "gols_casa": 0, "gols_fora": 0},
    ]

    ok = await bb.reivindicar("Flávia", 12345)
    assert ok is True, "reivindicar deve retornar True"

    parts = await bb.listar_participantes()
    assert len(parts) == 1
    assert parts[0]["telegram_id"] == 12345
    assert parts[0]["ativo"] is True

    palpites = bb._store["palpites"]
    for pal in palpites:
        assert pal["telegram_id"] == 12345, "palpites migrados"


# ── Ciclo 3: /sou com nome exato apos /start vinculado ─────────────────────

@pytest.mark.asyncio
async def test_reivindicar_after_auto_link():
    """Se /start já vinculou, /sou deve reconhecer e não duplicar.

    Cenário: /start vinculou 'Flávia' → 'Ana Flavia Cernic Ramos'.
    Depois /sou Flávia deve reconhecer que já é o mesmo user.
    """
    bb = _make_bb(participantes=[
        {"id": 1, "telegram_id": -4, "nome": "Flávia", "ativo": False},
    ])

    # /start vincula
    await bb.registrar_participante(12345, "Ana Flavia Cernic Ramos")

    parts = await bb.listar_participantes()
    assert len(parts) == 1
    pid = parts[0]["id"]

    # /sou Flávia — reivindicar busca por nome exato "Flávia"
    # Mas o nome foi atualizado para "Ana Flavia Cernic Ramos"
    # Então _participante_por_nome_exato("Flávia") deve retornar None
    ok = await bb.reivindicar("Flávia", 12345)
    assert ok is False, "não acha 'Flávia' porque o nome foi atualizado"

    # O participante continua sendo o mesmo
    parts = await bb.listar_participantes()
    assert len(parts) == 1
    assert parts[0]["id"] == pid
    assert parts[0]["telegram_id"] == 12345
    assert parts[0]["nome"] == "Ana Flavia Cernic Ramos"
