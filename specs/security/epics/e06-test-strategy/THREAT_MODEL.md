# Threat Model — Epic e06: Test Strategy & Architecture Overhaul

## Epic Scope

Create test strategy documentation (risk register, traceability matrix), shared
golden fixtures (scoring + parse_result), CI governance gates, and reconciliation
docs. No production code is modified in this epic — all artifacts are under
`specs/test-strategy/`, `scripts/`, `.github/workflows/`, and `CLAUDE.md`.

## Scope per story

| Story   | What changes                                                       | Code or docs? |
| ------- | ------------------------------------------------------------------ | ------------- |
| e06-s01 | specs/test-strategy/ (README, risk-register.yaml, traceability.md) | Docs only     |
| e06-s02 | specs/test-strategy/scoring-golden.json + test files               | Tests + JSON  |
| e06-s03 | web/src/scoring.js + web/src/store.js                              | Bug fix       |
| e06-s04 | specs/test-strategy/parse-result-golden.json + test files          | Tests + JSON  |
| e06-s05 | scripts/\*.py + .github/workflows/ci-cd.yml                        | Governance    |
| e06-s06 | CLAUDE.md                                                          | Docs only     |

## Vulnerability Assessment

| #   | Category | Location        | Finding                                                                                                                            | Confidence | Risk | Status                               |
| --- | -------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ---------- | ---- | ------------------------------------ |
| 1   | N/A      | All e06 stories | Documentation, test fixtures, and governance scripts. No user input processing, no external API calls, no auth boundaries crossed. | 0/10       | NONE | **Not reported** — no threat surface |

## Risk Summary

**Overall risk: NONE** — this epic touches no production code paths. All changes
are in `specs/test-strategy/`, `scripts/`, and test files.

| Metric          | Value |
| --------------- | ----- |
| HIGH findings   | 0     |
| MEDIUM findings | 0     |
| LOW findings    | 0     |
| Confidence > 7  | 0     |

## Edge cases noted

- **e06-s03** (bug fix) will modify `web/src/scoring.js` and `web/src/store.js`. If
  the `scoreLabelFor()` function receives unsanitized match_id from BigBase data,
  there's a theoretical stored-data injection path. Mitigation: Vue auto-escapes
  template bindings; match_id is alphanumeric (`R3-12`, `KO-QF-01`).
- **e06-s05** governance scripts (`scripts/check_test_governance.py`) read files
  from `specs/bugs/` and parse YAML — no external input.
