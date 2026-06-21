"""Camada de dados sobre a API de Coleches do BigBase.

BigBase expoe coleches schema-less em /api/collections/{nome} (cada registro e um
JSON no campo `data`, com `id` autoincremento). Rotas sao protegidas por JWT (Bearer),
obtido em /api/auth/login.

Coleches usadas:
- participantes: telegram_id, nome, ativo
- jogos:         match_id, rodada, kickoff, casa, fora, gols_casa, gols_fora, status
- palpites:      match_id, telegram_id, nome, gols_casa, gols_fora, atualizado_em

Filtragem e feita em processo (O(n) sobre list_records()). /api/sql nao esta
ativo para a service account (ver BUG-2026-06-19-180800).
Escritas (POST/PATCH/DELETE) usam o id do registro retornado pela leitura.
"""
from __future__ import annotations

import unicodedata

import httpx

from bolao import config
from bolao.matches import MATCHES

PARTICIPANTES = "participantes"
JOGOS = "jogos"
PALPITES = "palpites"


class BigBaseError(RuntimeError):
    pass


class BigBase:
    def __init__(self, url: str | None = None) -> None:
        self.base = (url or config.BIGBASE_URL).rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base, timeout=20.0)
        self._token: str | None = None

    async def close(self) -> None:
        await self._client.aclose()

    # ---------- auth ----------

    async def _login(self) -> None:
        r = await self._client.post(
            "/api/auth/login",
            json={"email": config.BIGBASE_EMAIL, "password": config.BIGBASE_PASSWORD},
        )
        if r.status_code != 200:
            raise BigBaseError(f"login falhou ({r.status_code}): {r.text}")
        self._token = r.json()["token"]

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"} if self._token else {}

    async def _request(self, method: str, path: str, **kw) -> httpx.Response:
        if self._token is None:
            await self._login()
        r = await self._client.request(method, path, headers=self._headers(), **kw)
        if r.status_code in (401, 403):  # token expirou -> relogar uma vez
            await self._login()
            r = await self._client.request(method, path, headers=self._headers(), **kw)
        return r

    # ---------- primitivas de colecao ----------

    async def create(self, collection: str, data: dict) -> int:
        r = await self._request("POST", f"/api/collections/{collection}", json=data)
        if r.status_code != 201:
            raise BigBaseError(f"create {collection} ({r.status_code}): {r.text}")
        return int(r.json()["id"])

    async def patch(self, collection: str, rec_id: int, data: dict) -> None:
        r = await self._request("PATCH", f"/api/collections/{collection}/{rec_id}", json=data)
        if r.status_code != 200:
            raise BigBaseError(f"patch {collection}/{rec_id} ({r.status_code}): {r.text}")

    async def list_records(self, collection: str, limit: int = 1000) -> list[dict]:
        """Lista todos os registros via REST (auto-cria a tabela se faltar).

        Nota: scan completo O(n) — filtragem e feita em processo pelo caller.
        """
        r = await self._request(
            "GET", f"/api/collections/{collection}", params={"limit": limit})
        if r.status_code != 200:
            raise BigBaseError(f"list {collection} ({r.status_code}): {r.text}")
        return r.json().get("data", [])

    # ---------- setup / seed ----------

    async def ensure_setup(self) -> None:
        """Garante que as coleches existem e popula a agenda das rodadas."""
        # GET em cada colecao forca a criacao da tabela no servidor.
        existentes = {j.get("match_id") for j in await self.list_records(JOGOS)}
        await self.list_records(PARTICIPANTES)
        await self.list_records(PALPITES)
        for m in MATCHES:
            if m.match_id in existentes:
                continue
            await self.create(JOGOS, {
                "match_id": m.match_id, "rodada": m.rodada, "kickoff": m.kickoff,
                "casa": m.casa, "fora": m.fora,
                "gols_casa": None, "gols_fora": None, "status": "agendado",
            })

    # ---------- participantes ----------

    async def get_participante(self, telegram_id: int) -> dict | None:
        tid = int(telegram_id)
        for p in await self.list_records(PARTICIPANTES):
            if int(p.get("telegram_id", 0)) == tid:
                return p
        return None

    async def registrar_participante(self, telegram_id: int, nome: str) -> None:
        existente = await self.get_participante(telegram_id)
        if existente:
            await self.patch(PARTICIPANTES, existente["id"], {"nome": nome, "ativo": True})
            return
        # Evita duplicata de nome: se outro registro tem o mesmo nome (caso
        # de /sou ter "roubado" o registro original), reassina o telegram_id.
        mesmo_nome = await self._participante_por_nome_exato(nome)
        if mesmo_nome:
            await self.patch(PARTICIPANTES, mesmo_nome["id"], {
                "telegram_id": int(telegram_id), "nome": nome, "ativo": True})
            return
        # Varredura de placeholders: se um participante historico (telegram_id < 0)
        # tem nome contido no novo nome (ou vice-versa), vincula o placeholder
        # em vez de criar duplicata. Ex: placeholder "Flavia" + "Ana Flavia Cernic".
        placeholder = await self._placeholder_por_nome_parcial(nome)
        if placeholder:
            await self._vincular_placeholder(placeholder, telegram_id, nome)
            return
        await self.create(PARTICIPANTES, {
            "telegram_id": int(telegram_id), "nome": nome, "ativo": True})

    @staticmethod
    def _normalizar(texto: str) -> str:
        """Remove acentos e lowercases para comparacao fuzzy."""
        nfkd = unicodedata.normalize("NFKD", texto.strip())
        return nfkd.encode("ascii", "ignore").decode("ascii").lower()

    async def _placeholder_por_nome_parcial(self, nome: str) -> dict | None:
        """Busca placeholder (telegram_id < 0) cujo nome tenha substring match.

        Comparacao ignora acentos e case. Ex: "Flávia" casa com
        "Ana Flavia Cernic Ramos" porque "flavia" e substring de "ana flavia cernic".
        """
        alvo = self._normalizar(nome)
        for p in await self.listar_participantes():
            pid = int(p.get("telegram_id", 0))
            if pid >= 0:
                continue
            pnome = self._normalizar(p.get("nome", ""))
            if not pnome:
                continue
            # Match: nome do placeholder contido no novo nome OU vice-versa
            if pnome in alvo or alvo in pnome:
                return p
        return None

    async def _vincular_placeholder(
        self, placeholder: dict, telegram_id: int, nome: str,
    ) -> None:
        """Vincula um placeholder a uma conta real, migrando palpites."""
        antigo_id = int(placeholder["telegram_id"])
        novo_tid = int(telegram_id)
        # Migra palpites do id antigo -> novo
        todos = await self.list_records(PALPITES)
        for p in todos:
            if int(p.get("telegram_id", 0)) == antigo_id:
                await self.patch(PALPITES, p["id"], {"telegram_id": novo_tid})
        # Atualiza placeholder
        await self.patch(PARTICIPANTES, placeholder["id"], {
            "telegram_id": novo_tid, "nome": nome, "ativo": True})

    async def listar_participantes(self) -> list[dict]:
        return await self.list_records(PARTICIPANTES)

    async def fundir_participante(self, nome: str) -> int:
        """Funde duplicatas do mesmo participante em um registro canonical.

        Mantém o registro com mais palpites; migra palpites dos demais e
        marca-os como ativo=False. Retorna quantos registros foram fundidos.
        """
        alvo = self._normalizar(nome)
        ativos = [
            p for p in await self.listar_participantes()
            if self._normalizar(p.get("nome", "")) == alvo and p.get("ativo", True)
        ]
        if len(ativos) <= 1:
            return 0

        palpites = await self.list_records(PALPITES)

        def _n_palpites(tid: int) -> int:
            return sum(1 for p in palpites if int(p.get("telegram_id", 0)) == tid)

        ativos.sort(key=lambda p: _n_palpites(int(p.get("telegram_id", 0))), reverse=True)
        canonical_tid = int(ativos[0]["telegram_id"])

        for dup in ativos[1:]:
            dup_tid = int(dup["telegram_id"])
            for p in palpites:
                if int(p.get("telegram_id", 0)) == dup_tid:
                    await self.patch(PALPITES, p["id"], {"telegram_id": canonical_tid})
            await self.patch(PARTICIPANTES, dup["id"], {"ativo": False})

        return len(ativos) - 1

    async def _participante_por_nome_exato(self, nome: str) -> dict | None:
        """Busca participante por nome exato (case e acento insensitive)."""
        alvo = self._normalizar(nome)
        for p in await self.listar_participantes():
            if self._normalizar(p.get("nome", "")) == alvo:
                return p
        return None

    # Alias publico para compatibilidade com scripts (seed_bigbase.py e outros)
    participante_por_nome = _participante_por_nome_exato

    async def reivindicar(self, nome: str, novo_telegram_id: int) -> bool:
        """Vincula um participante historico (sem dono) a uma conta real,
        migrando os palpites antigos para o novo telegram_id. Usado por /sou."""
        alvo = await self._participante_por_nome_exato(nome)
        if not alvo:
            return False
        antigo_id = int(alvo["telegram_id"])
        novo_tid = int(novo_telegram_id)
        if antigo_id == novo_tid:
            return True
        # migra palpites do id antigo -> novo
        todos = await self.list_records(PALPITES)
        for p in todos:
            if int(p.get("telegram_id", 0)) == antigo_id:
                await self.patch(PALPITES, p["id"], {"telegram_id": novo_tid})
        # Se o novo usuario ja tem registro proprio, fundir em vez de roubar
        usuario_atual = await self.get_participante(novo_tid)
        if usuario_atual and usuario_atual["id"] != alvo["id"]:
            # Ja existe: marca o registro historico como inativo (evita
            # duplicata no ranking) e atualiza o nome do usuario real.
            await self.patch(PARTICIPANTES, usuario_atual["id"], {
                "nome": nome, "ativo": True})
            await self.patch(PARTICIPANTES, alvo["id"], {"ativo": False})
        else:
            # Nao existe: reaproveita o registro historico
            await self.patch(PARTICIPANTES, alvo["id"], {
                "telegram_id": novo_tid, "nome": nome, "ativo": True})
        return True

    # ---------- jogos ----------

    async def get_jogos(self) -> list[dict]:
        jogos = await self.list_records(JOGOS)
        return sorted(jogos, key=lambda j: j.get("kickoff", ""))

    async def get_jogo(self, match_id: str) -> dict | None:
        for j in await self.list_records(JOGOS):
            if j.get("match_id") == match_id:
                return j
        return None

    async def set_resultado(self, match_id: str, gols_casa: int, gols_fora: int) -> bool:
        jogo = await self.get_jogo(match_id)
        if not jogo:
            return False
        await self.patch(JOGOS, jogo["id"], {
            "gols_casa": int(gols_casa), "gols_fora": int(gols_fora),
            "status": "encerrado"})
        return True

    # ---------- palpites ----------

    async def get_palpite(self, match_id: str, telegram_id: int) -> dict | None:
        tid = int(telegram_id)
        for p in await self.list_records(PALPITES):
            if p.get("match_id") == match_id and int(p.get("telegram_id", 0)) == tid:
                return p
        return None

    async def salvar_palpite(self, match_id: str, telegram_id: int, nome: str,
                             gols_casa: int, gols_fora: int, agora_iso: str) -> None:
        existente = await self.get_palpite(match_id, telegram_id)
        payload = {"gols_casa": int(gols_casa), "gols_fora": int(gols_fora),
                   "atualizado_em": agora_iso}
        if existente:
            await self.patch(PALPITES, existente["id"], payload)
        else:
            await self.create(PALPITES, {
                "match_id": match_id, "telegram_id": int(telegram_id), "nome": nome,
                **payload})

    async def palpites_do_usuario(self, telegram_id: int) -> dict[str, tuple[int, int]]:
        tid = int(telegram_id)
        out: dict[str, tuple[int, int]] = {}
        for p in await self.list_records(PALPITES):
            if int(p.get("telegram_id", 0)) == tid:
                out[p["match_id"]] = (int(p["gols_casa"]), int(p["gols_fora"]))
        return out

    async def get_palpites(self) -> list[dict]:
        return await self.list_records(PALPITES)
