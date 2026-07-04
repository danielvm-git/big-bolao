#!/usr/bin/env python3
"""CI governance gate: every BUG-*.md must have a registry.yaml entry with tests_added.

Exits with code 0 if governance passes, non-zero with details on failures.
"""
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BUGS_DIR = REPO / "specs" / "bugs"
REGISTRY_FILE = BUGS_DIR / "registry.yaml"


def _load_registry(path: Path) -> dict:
    import yaml
    if not path.exists():
        return {"bugs": []}
    with open(path) as f:
        return yaml.safe_load(f) or {"bugs": []}


def _bug_files() -> list[Path]:
    if not BUGS_DIR.exists():
        return []
    return sorted(BUGS_DIR.glob("BUG-*.md"))


def _bug_id_from_filename(name: str) -> str:
    """Extract BUG-YYYY-MM-DD-NNNNNN from filename like BUG-2026-06-19-183500-foo.md."""
    m = re.match(r"(BUG-\d{4}-\d{2}-\d{2}-\d+)", name)
    return m.group(1) if m else name


def main() -> int:
    errors = []

    # Load registry
    registry = _load_registry(REGISTRY_FILE)
    registered_ids = {e["bug_id"] for e in registry.get("bugs", []) if "bug_id" in e}
    registered_with_tests = {
        e["bug_id"]
        for e in registry.get("bugs", [])
        if "bug_id" in e and "tests_added" in e
    }

    # Check every bug file has a registry entry
    files = _bug_files()
    for f in files:
        bid = _bug_id_from_filename(f.name)
        if bid not in registered_ids:
            errors.append(f"MISSING: {f.name} ({bid}) — no registry.yaml entry")
        elif bid not in registered_with_tests:
            errors.append(f"NO_TESTS: {f.name} ({bid}) — registry entry missing tests_added")

    # Check for orphaned registry entries (no corresponding file)
    file_ids = {_bug_id_from_filename(f.name) for f in files}
    for bid in sorted(registered_ids):
        if bid not in file_ids:
            errors.append(f"ORPHAN: {bid} — registry entry but no BUG-*.md file found")

    # Report
    if errors:
        print(f"❌ GOVERNANCE FAIL — {len(errors)} issue(s):")
        for e in errors:
            print(f"   {e}")
        return 1

    print(f"✅ GOVERNANCE PASS — {len(files)} bugs registered, {len(registered_with_tests)} with tests_added")
    return 0


if __name__ == "__main__":
    sys.exit(main())
