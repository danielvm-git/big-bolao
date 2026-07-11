# BUG-2026-07-10-170000: CI "Commit rebuilt web/dist" fails — .gitignore `dist/` matches `web/dist/`

## Summary

CI step "Commit rebuilt web/dist" fails with:

```
The following paths are ignored by one of your .gitignore files:
web/dist
hint: Use -f if you really want to add them.
```

Cascading failure: all subsequent steps (Python tests, governance gates, web tests, deploy) are skipped.

## Root Cause

Commit `decdc00` ("feat(ci): add CodeQL security scanning, enhance .gitignore") added `dist/` to `.gitignore` under the `# Python` section, intended for Python setuptools build artifacts (`dist/` at repo root). However, the pattern `dist/` (no leading `/`) matches **any** directory named `dist` at **any level** in the tree — including `web/dist/`.

When CI builds the web SPA, new files in `web/dist/` are generated, but `git add web/dist/` fails because the path is gitignored.

## Severity

- **Severity:** high
- **Priority:** critical
- **Scope:** ci
- **Type:** regression (introduced by `decdc00`)

## Fix

Changed `dist/` → `/dist/` in `.gitignore` (line 13). The leading `/` scopes the pattern to repo root only — Python `dist/` artifacts remain ignored, while `web/dist/` (Vite output, intentionally tracked by CI) is no longer ignored.

## Verification

- Root `dist/` → still ignored (verified with `git check-ignore dist/test.txt`)
- `web/dist/` → NOT ignored (verified with `git check-ignore web/dist/test.txt` returns nothing)
- `git add --dry-run web/dist/` → exit 0 (no error)
- All 167 Python tests pass
- All web tests pass

## Files Changed

- `.gitignore` (1 line: `dist/` → `/dist/`)

## Prevention

Always scope directory patterns in `.gitignore` with a leading `/` when they are meant to match only at root level:

- `/dist/` — matches only `./dist/` (Python build)
- `dist/` — matches `./dist/`, `./web/dist/`, `./foo/bar/dist/`, etc.

Review similar patterns in project: `build/`, `.venv/`, `venv/` are well-scoped (unique names unlikely to appear elsewhere).

## Commit Message

```
fix(ci): scope dist/ gitignore to root level — /dist/ avoids catching web/dist/
```
