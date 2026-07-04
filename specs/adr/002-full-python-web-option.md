---
status: proposed
date: 2026-07-04
amends: ADR-001
---

# ADR 002 — Full-Python web option (server-rendered), evaluated but not yet decided

## Context

The project is polyglot: a Python Telegram bot + a Vue 3 SPA. The Telegram side
is genuinely locked to Python (python-telegram-bot). The question raised: should
the **web** side also be Python, eliminating the second language/toolchain?

The recurring-bug history motivates it — the two worst failure classes are
Python↔JS drift of shared logic (`BUG-2026-06-30-150000`, `BUG-2026-07-04-170000`)
and duplicated scoring rules (`scoring.py` ↔ `scoring.js`, `ranking.py` ↔
`calcRanking`). One language would make those bugs structurally impossible.

## Key finding — the platform already runs us as Python

Verified against BigBase's own source (opensrc cache
`github.com/danielvm-git/bigbase`, deploy slice 013). BigBase build detection:

| Type   | Detection          | Build                             | Start           |
| ------ | ------------------ | --------------------------------- | --------------- |
| Node   | `package.json`     | `npm run build`                   | `npm start`     |
| Static | `index.html`       | none                              | serve files     |
| Go     | `go.mod`           | `go build -o app`                 | `./app`         |
| Python | `requirements.txt` | `pip install -r requirements.txt` | `python app.py` |

Each deployment gets a PID-based port proxied via subdomain → that is `$PORT`.

Because big-bolao ships `requirements.txt` + `app.py`, **it is already detected
and deployed as a Python app.** The Vue SPA has no runtime of its own in
production — `app.py` (`socketserver.TCPServer` on `$PORT`, app.py:181) serves it
as static files. "Go full Python" is therefore a small delta: swap static-file
serving for template rendering **inside the same `app.py`**, and move
scoring/ranking/flags to a single Python source of truth.

## Decision

**Deferred.** Full-Python (FastAPI or Flask + Jinja2 templates + HTMX for
interactivity, all rendered inside the existing `app.py` entrypoint) is the
architecture we would choose greenfield, and it would delete the entire JS
toolchain (`vite`, `npm`, `node_modules`, committed `web/dist/`), the JS query +
scoring layers, and the Python↔JS drift bug class (making epic e06's
cross-language golden fixture largely unnecessary). But we have a working SPA and
e06 already neutralizes the drift risk cheaply, so this is a motivation-driven
rewrite, not a bug-forced one. Revisit if the Vue app becomes maintenance
friction.

## Constraints (verified — correct these if reconsidering)

- **Entrypoint is `app.py`, and `app.py` must self-launch the web server.**
  BigBase's Python start command is literally `python app.py` — it does NOT run
  `uvicorn`/`gunicorn` for you. A FastAPI rewrite must call
  `uvicorn.run(app, host="0.0.0.0", port=int(os.environ["PORT"]))` as its
  entrypoint (same shape as today's `serve_forever()`).
- **Python deploy path is less battle-tested than static/Node.** BigBase logged
  an infra bug (`BUG-2026-06-19...pip-pep668`) where `pip install` failed on
  Ubuntu 24.04 (PEP 668 "externally-managed-environment"). Fixed upstream, and we
  already exercise this path successfully — but keep `requirements.txt` lean;
  Python-deploy breakages are infra-level.
- **CSP `default-src 'self'`** blocks inline `<script>`/`<style>` and external
  CDNs. HTMX/Alpine are single same-origin JS files — compatible — but no inline
  handlers.

## Considered options

| Option                                    | Verdict                                                           |
| ----------------------------------------- | ----------------------------------------------------------------- |
| Collapse to one language (drop Python/JS) | Rejected — bot is Python-locked; web must be static-servable      |
| Server-authoritative scoring (web → API)  | Rejected — breaks offline/instant-preview UX, adds round-trips    |
| Keep polyglot, bind with shared contract  | **Current path** — e06 golden fixture makes drift executable      |
| **Full-Python server-rendered web**       | **This ADR** — cleanest greenfield; deferred as a rewrite for now |

## Consequences if adopted later

- Deletes: `web/src/*.js/.vue`, `vite`, `package.json`, `node_modules`,
  committed `web/dist/`, the web `node:test` suite, and the npm CI build stage.
- Simplifies e07 (fewer moving parts) and makes most of e06 moot.
- Loses: instant client-side score preview (→ ~50–150ms HTMX round-trip),
  PWA/offline feel, and the already-built polished mobile SPA. Low cost for a
  ~10-user pool consumed mostly via Telegram.
