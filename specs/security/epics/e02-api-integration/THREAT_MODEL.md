# Threat Model — Epic e02: Live API Integration

## Epic Scope

Replace hardcoded match schedule with live data from apifootball.com API.
Stories: fixtures.py (done), config (done), ensure_setup/upsert (pending),
results.py (done), /sync_jogos command (pending), docs (done).

## Threat Surface

```
[apifootball.com API]
    ↕ HTTPS (APIkey in query param)
[fixtures.py / results.py]
    ↕ BigBase collections (jogos, palpites, participantes)
[Telegram bot]  [Vue SPA]
```

## Vulnerability Assessment

| #   | Category          | Location                           | Finding                                                | Confidence | Risk | Status                                                                                                     |
| --- | ----------------- | ---------------------------------- | ------------------------------------------------------ | ---------- | ---- | ---------------------------------------------------------------------------------------------------------- |
| 1   | Secrets exposure  | `fixtures.py:254`, `results.py:91` | API key sent as query param `APIkey` in all requests   | 5/10       | LOW  | **Not reported** — key is over HTTPS, never logged, follows API's auth scheme                              |
| 2   | Content injection | `fixtures.py:208-213`              | API team names/status stored directly in BigBase       | 6/10       | LOW  | **Not reported** — Telegram's ParseMode.HTML and Vue auto-escape. Requires API compromise. Confidence < 8. |
| 3   | SSRF              | `fixtures.py:264`, `results.py:98` | URL hardcoded to `apiv3.apifootball.com`               | 1/10       | NONE | **Not reported** — fixed URL, no user-controlled host/path                                                 |
| 4   | Auth bypass       | _planned: handlers.py /sync_jogos_ | Will follow existing admin check pattern (`ADMIN_IDS`) | —          | —    | **Design note:** must check `ADMIN_IDS` consistent with `/sync`                                            |

## Risk Summary

**Overall risk: LOW** — no findings met the ≥ 8 confidence threshold.

| Metric          | Value          |
| --------------- | -------------- |
| HIGH findings   | 0              |
| MEDIUM findings | 0              |
| LOW findings    | 0 (suppressed) |
| Confidence > 7  | 0              |

## Security Design Decisions

1. **API key via env var** — `APIFOOTBALL_KEY` in `.env`, never hardcoded. Good.
2. **No key logging** — `fixtures.py:261` logs league_id/dates only, not the key or full URL.
3. **HTTPS only** — URL is `https://apiv3.apifootball.com/`, not HTTP.
4. **Error messages safe** — `RuntimeError` includes API error body but not the API key.
5. **Admin gate** — `/sync_jogos` (e02-s05) must implement `ADMIN_IDS` check matching the existing `/sync` pattern in `handlers.py`.

## Accepted Risks

| Risk                                                     | Rationale                                                                                                         |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| API compromise feeding malicious team names into BigBase | Third-party dependency risk, not a code vuln. CSP + Vue auto-escaping mitigate XSS. Telegram ParseMode.HTML safe. |
| API key exposure via query param in HTTPS                | Standard auth mode for apifootball.com. No alternative (header-based auth not supported).                         |

## Mitigation Recommendations

1. **Add URL-allowlist validation** in `fetch_from_api` (defense-in-depth against future changes):
   ```python
   _ALLOWED_API_HOSTS = frozenset({"apiv3.apifootball.com"})
   ```
2. **Consider replacing `APIkey` query-param auth with header-based** if apifootball adds support (prevents URL logging leaks).
3. **Verify CSP headers** on `bolao.bigbase.click` include `default-src 'self'` (already set per deployment config).
