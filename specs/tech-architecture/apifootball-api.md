# APIFootball — Reference

> **Source:** https://apifootball.com/documentation/  
> **Base URL:** `https://apiv3.apifootball.com/`  
> **Protocol:** HTTPS REST (all GET) + optional WebSocket for live scores  
> **Auth:** `APIkey=<token>` query-string parameter on every request  
> **Relevant project epic:** `specs/epics/e02-api-integration/overview.md`

---

## Quick-reference table

| Action | Endpoint | Required params | Optional params |
|--------|----------|-----------------|-----------------|
| Countries | `get_countries` | — | — |
| Competitions | `get_leagues` | — | `country_id` |
| Teams | `get_teams` | `team_id` OR `league_id` | — |
| Players | `get_players` | `player_id` OR `player_name` | — |
| Standings | `get_standings` | `league_id` | — |
| **Fixtures / Results** | **`get_events`** | `from`, `to` | `league_id`, `country_id`, `match_id`, `team_id`, `match_live=1`, `withPlayerStats=1` |
| Lineups | `get_lineups` | `match_id` | — |
| Statistics | `get_statistics` | `match_id` | — |
| Odds | `get_odds` | `from`, `to` | `match_id` |
| Live Odds + Comments | `get_live_odds_commnets` | — | `league_id`, `country_id`, `match_id` |
| H2H | `get_H2H` | `firstTeam`+`secondTeam` OR `firstTeamId`+`secondTeamId` | `timezone` |
| Predictions | `get_predictions` | `from`, `to` | `league_id`, `country_id`, `match_id` |
| Top Scorers | `get_topscorers` | `league_id` | — |
| Videos | `get_videos` | — | `match_id` |
| **Livescore (push)** | WebSocket `wss://wss.apifootball.com/livescore` | `APIkey` | `league_id`, `country_id`, `match_id`, `timezone` |

---

## `get_events` — Fixtures & Results ⭐ (primary endpoint for this project)

```
GET https://apiv3.apifootball.com/?action=get_events&from=YYYY-MM-DD&to=YYYY-MM-DD&league_id=XXX&APIkey=KEY
```

### Key response fields

```jsonc
{
  "match_id": "112282",               // ← store as api_fixture_id on jogos
  "league_id": "152",
  "league_name": "Premier League",
  "match_date": "2023-04-05",          // YYYY-MM-DD
  "match_time": "21:00",               // HH:MM (default Europe/Berlin)
  "match_status": "Finished",          // see status values below
  "match_round": "7",                  // "Group Stage", "Quarter-finals", etc.
  "match_hometeam_id": "3081",
  "match_hometeam_name": "West Ham United",
  "match_hometeam_score": "1",         // "" when not yet played
  "match_awayteam_id": "3100",
  "match_awayteam_name": "Newcastle United",
  "match_awayteam_score": "5",
  "match_hometeam_halftime_score": "1",
  "match_awayteam_halftime_score": "2",
  "match_hometeam_extra_score": "",    // extra time
  "match_awayteam_extra_score": "",
  "match_hometeam_penalty_score": "",  // penalty shootout
  "match_awayteam_penalty_score": "",
  "match_hometeam_ft_score": "1",      // full-time (90 min only)
  "match_awayteam_ft_score": "5",
  "match_live": "0",                   // "1" = live right now
  "match_stadium": "London Stadium (London)",
  "match_referee": "C. Pawson",
  "fk_stage_key": "6",
  "stage_name": "Current",
  // also: goalscorer[], cards[], substitutions{}, lineup{}, statistics[], statistics_1half[]
}
```

### `match_status` values

| Value | Meaning |
|-------|---------|
| `"Finished"` | Final result after 90 min |
| `"After ET"` | Final after extra time |
| `"After Pen."` | Final after penalty kicks |
| `"Half Time"` | Rest between halves |
| `"13'"` (any minute) | Live — minute currently in play |
| `"Postponed"` | Rescheduled |
| `"Cancelled"` | Will not be played |
| `"Awarded"` | Winner declared by official body |

> **For bolão scoring:** a match counts as `encerrado` when status is
> `"Finished"`, `"After ET"`, or `"After Pen."`.  
> The canonical score to compare against palpites is always
> `match_hometeam_ft_score` / `match_awayteam_ft_score` (90-min score only).

### `timezone` parameter

Default: `Europe/Berlin`. Pass in TZ Database format, e.g. `America/Sao_Paulo`.

---

## `get_leagues` — Finding the Copa do Mundo 2026 league ID

```
GET https://apiv3.apifootball.com/?action=get_leagues&APIkey=KEY
```

Returns leagues per subscription plan. Filter by `country_id` if needed.  
Copa do Mundo / FIFA World Cup 2026 will be listed here once available.
Store the resolved `league_id` in `.env` as `FIXTURES_LEAGUE_ID`.

---

## `get_countries` — Reference

```
GET https://apiv3.apifootball.com/?action=get_countries&APIkey=KEY
```

```jsonc
{ "country_id": "44", "country_name": "England",
  "country_logo": "https://apiv3.apifootball.com/badges/logo_country/44_england.png" }
```

---

## `get_standings` — League table

```
GET https://apiv3.apifootball.com/?action=get_standings&league_id=XXX&APIkey=KEY
```

Key fields: `team_id`, `team_name`, `overall_league_position`, `overall_league_PTS`,
`overall_league_W/D/L`, `overall_league_GF/GA`, `home_*`, `away_*`.

---

## `get_H2H` — Head-to-head history

```
GET https://apiv3.apifootball.com/?action=get_H2H&firstTeamId=X&secondTeamId=Y&APIkey=KEY
```

Returns three lists: `firstTeam_VS_secondTeam`, `firstTeam_lastResults`, `secondTeam_lastResults`.

---

## `get_predictions` — Match probabilities

```
GET https://apiv3.apifootball.com/?action=get_predictions&from=YYYY-MM-DD&to=YYYY-MM-DD&APIkey=KEY
```

Key probability fields (0–100%):

| Field | Meaning |
|-------|---------|
| `prob_HW` | Home win |
| `prob_D` | Draw |
| `prob_AW` | Away win |
| `prob_O` / `prob_U` | Over / Under 2.5 goals |
| `prob_bts` | Both teams to score |

---

## Livescore WebSocket

```
wss://wss.apifootball.com/livescore?APIkey=KEY&timezone=America/Sao_Paulo
```

Push notifications on any score or statistics change while matches are live.
Response structure mirrors `get_events`. Reconnect on close (with back-off).

```js
function socketsLive() {
  const socket = new WebSocket(`wss://wss.apifootball.com/livescore?APIkey=${KEY}`);
  socket.onmessage = (e) => { const data = JSON.parse(e.data); /* update UI */ };
  socket.onclose = () => setTimeout(socketsLive, 5000); // auto-reconnect
}
```

---

## Asset URL patterns

| Asset | Pattern |
|-------|---------|
| Country logo | `https://apiv3.apifootball.com/badges/logo_country/{id}_{slug}.png` |
| League logo | `https://apiv3.apifootball.com/badges/logo_leagues/{id}_{slug}.png` |
| Team badge | `https://apiv3.apifootball.com/badges/{id}_{slug}.jpg` |
| Player photo | `https://apiv3.apifootball.com/badges/players/{id}_{slug}.jpg` |

---

## Integration notes for this project

### What we use today (e02-api-integration)

| Need | Endpoint | Stored field |
|------|----------|-------------|
| Seed fixtures at season start | `get_events` (date range, league_id) | `api_fixture_id` on `jogos` |
| Sync results every 30 min | `get_events` (today ± 1 day) | `gols_casa`, `gols_fora`, `status` |
| Detect live games | `get_events?match_live=1` | `match_live` flag |
| Knockout rounds | `get_events` (ongoing) | `match_round` → generates `KO-*` match IDs |

### Environment variables

```dotenv
APIFOOTBALL_KEY=xxxxxxxxxxxxxxxx       # Account API key
FIXTURES_LEAGUE_ID=XXXX                # Copa 2026 league ID (resolve once via get_leagues)
FIXTURES_PROVIDER=apifootball          # Set to empty → falls back to hardcoded matches.py
```

### Field mapping: API → bolão `jogos`

| API field | `jogos` field | Notes |
|-----------|--------------|-------|
| `match_id` | `api_fixture_id` | Exact ID for result matching |
| `match_date` + `match_time` | `kickoff` | ISO 8601, convert timezone |
| `match_hometeam_name` | `time_casa` | Display only |
| `match_awayteam_name` | `time_fora` | Display only |
| `match_hometeam_ft_score` | `gols_casa` | Null until finished |
| `match_awayteam_ft_score` | `gols_fora` | Null until finished |
| `match_status` | `status` | Map to `agendado`/`ao_vivo`/`encerrado` |
| `match_round` | `rodada` | e.g. `"Group Stage"`, `"Quarter-finals"` |

### Scoring rules reminder (bolao/scoring.py mirror)

```python
# gols_casa / gols_fora are always the 90-min full-time score
# Extra time and penalty scores do NOT count for bolão points
def calc_pontos(palpite_casa, palpite_fora, real_casa, real_fora):
    if palpite_casa == real_casa and palpite_fora == real_fora: return 3  # exact
    if sinal(palpite_casa, palpite_fora) == sinal(real_casa, real_fora): return 1  # winner/draw
    return 0
```

---

## Useful curl examples

```bash
# All fixtures for a league in a date range
curl "https://apiv3.apifootball.com/?action=get_events&from=2026-06-01&to=2026-07-15&league_id=XXXX&APIkey=$APIFOOTBALL_KEY"

# Single match detail (with player stats)
curl "https://apiv3.apifootball.com/?action=get_events&match_id=112282&withPlayerStats=1&APIkey=$APIFOOTBALL_KEY"

# Only live matches right now
curl "https://apiv3.apifootball.com/?action=get_events&match_live=1&APIkey=$APIFOOTBALL_KEY"

# Discover Copa 2026 league_id
curl "https://apiv3.apifootball.com/?action=get_leagues&APIkey=$APIFOOTBALL_KEY" | jq '.[] | select(.league_name | test("World Cup"; "i"))'
```
