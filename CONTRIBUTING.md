# Contributing to Big Bolão

## Development setup

```bash
# Clone
git clone https://github.com/danielvm-git/big-bolao.git
cd big-bolao

# Python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Web
cd web && npm ci
```

## Workflow

1. Create a feature branch: `git checkout -b feat/my-feature`
2. Write tests first (TDD). See `specs/test-strategy/README.md`.
3. Implement. Run tests after every change.
4. Commit using [Conventional Commits](https://www.conventionalcommits.org/).
5. Push and open a Pull Request.

## Preflight

Before committing, the pre-commit hook runs:

```bash
python -m pytest tests/ -q        # 167 Python tests
python -m flake8 bolao/           # Python lint
cd web && npm test                # 88 web tests
```

All must pass. See `AGENTS.md` for the full test strategy.

## Conventions

Read `CONVENTIONS.md` before submitting any code. Key points:

- Never hardcode secrets — read from `.env`
- Type hints on all public Python functions
- Composition API with `<script setup>` for Vue
- Structured JSON logging via `bolao/logger.py`

## Agent PRs

PRs created by AI agents include a `<!-- bigpowers-provenance: agent-generated -->` marker.
Human reviewers should apply the same review standards as for human-authored PRs:
all tests passing, coverage gates met, CONVENTIONS.md compliance verified.
