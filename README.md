# 🏆 Big Bolão — Copa 2026 no Telegram

Bot de Telegram pra rodar o bolão da Copa do Mundo 2026. Os palpites são feitos
**no privado com o bot** (ninguém vê o palpite do outro, zero flood no grupo). O
grupo só recebe lembretes, resultados e o ranking. Backend de dados no
[BigBase](https://bigbase.click).

## Como funciona (UX)

- **No privado do bot:** cada pessoa palpita o **placar exato** de cada jogo por
  botões (escolhe gols do mandante, depois do visitante). Pode editar até o apito.
- **No grupo:** o bot posta lembrete dos jogos das próximas 24h, o placar final
  com quem cravou, e o ranking atualizado. Comandos de palpite no grupo são
  redirecionados pro privado.
- **Pontuação:** `3` placar exato · `1` acertar vencedor/empate · `0` erro.

## Comandos

| Comando | Onde | O quê |
|---|---|---|
| `/start` | privado | cadastra e mostra ajuda |
| `/sou <Nome>` | privado | herda os palpites da Rodada 1 (jogadores antigos) |
| `/jogos` | privado | palpitar nos próximos jogos (botões) |
| `/meus` | privado | ver meus palpites |
| `/ranking` | qualquer | classificação geral (recalculada) |
| `/chatid` | grupo | mostra o chat_id (pra configurar) |
| `/resultado <match_id> <casa> <fora>` | admin | lança placar manual |
| `/sync` | admin | puxa resultados do provider e publica |
| `/lembrete` | admin | posta os jogos abertos no grupo |

## Arquitetura

```
Bot Python (long polling)  ──REST+JWT──►  BigBase (/api/collections, /api/sql)
        │                                  = Database + Auth
        ▼
   Telegram (DM + grupo)  ◄── API-Football (resultados, opcional)
```

> ℹ️ As *Functions* do BigBase são um sandbox JS sem rede/DB/input, então **não**
> servem pra hospedar o bot. O BigBase é usado como **banco** (coleções
> `participantes`, `jogos`, `palpites`); o bot roda como processo à parte.

## Setup

### 1. BigBase (banco)
Suba sua instância e crie uma conta de serviço pro bot:
```bash
curl -X POST $BIGBASE_URL/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"bolao-bot@bigbase.local","password":"<senha-forte>"}'
```

### 2. Telegram
1. Crie o bot no [@BotFather](https://t.me/BotFather) → copie o token.
2. Adicione o bot ao grupo; mande `/chatid` pra pegar o `GRUPO_CHAT_ID`.
3. Pegue seu próprio Telegram ID (ex: [@userinfobot](https://t.me/userinfobot))
   pra `ADMIN_IDS`.

### 3. Configuração
```bash
cp .env.example .env   # preencha os valores
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

### 4. Seed (uma vez)
Sobe a agenda, os resultados e os palpites da Rodada 1:
```bash
python -m scripts.seed_bigbase --dry   # confere
python -m scripts.seed_bigbase         # sobe pra valer
```
Depois, cada jogador antigo roda `/sou <Nome>` no privado do bot pra herdar
seus pontos da R1.

### 5. Rodar
```bash
python -m bolao.bot
```

## Resultados automáticos (opcional)

Por padrão o admin lança placares com `/resultado`. Pra automatizar via
[API-Football](https://www.api-football.com/) (RapidAPI), preencha no `.env`:
```
RESULTS_PROVIDER=apifootball
APIFOOTBALL_KEY=...
APIFOOTBALL_LEAGUE_ID=...   # id da Copa do Mundo
APIFOOTBALL_SEASON=2026
```
O bot passa a puxar resultados a cada 10 min e publicar no grupo.

## Deploy (PaaS grátis)

`Dockerfile` e `Procfile` (worker) prontos. Em Railway/Render/Fly: configure as
variáveis do `.env`, rode o seed uma vez (shell do serviço) e suba o worker.
Long polling — não precisa de porta/webhook.

## Testes
```bash
python -m scripts.check_ranking   # valida a regra de pontuação + ranking R1
```

## Ranking atual (Rodada 1, recalculado)

O ranking que estava na planilha tinha erro de soma; recalculado pela regra 3/1:

| Pos | Participante | Pontos | Exatos |
|----|----|----|----|
| 🥇 | Ricardo | 15 | 2 |
| 🥈 | Pajé | 12 | 1 |
| 🥉 | Big | 11 | 1 |
| 4º | Flávia | 11 | 1 |
| 5º | Mari Gallo | 9 | 1 |
| 6º | Mari Som | 7 | 0 |
| 7º | Lere | 0 | 0 |
