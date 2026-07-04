#!/usr/bin/env python3
"""CI governance gate: assert FASE_PONTOS is identical in Python and JS.

Parses bolao/scoring.py (Python dict) and web/src/scoring.js (JS const Object)
and compares entry-by-entry. Exits with code 0 if identical, non-zero with diff.
"""
import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PY_FILE = REPO / "bolao" / "scoring.py"
JS_FILE = REPO / "web" / "src" / "scoring.js"


def _parse_python_fase_pontos(path: Path) -> dict:
    """Parse FASE_PONTOS dict literal from Python file using ast."""
    source = path.read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.target if isinstance(node, ast.AnnAssign) else node.targets[0]
            if isinstance(target, ast.Name) and target.id == "FASE_PONTOS":
                value = node.value if isinstance(node, ast.AnnAssign) else node.value
                if isinstance(value, ast.Dict):
                    result = {}
                    for k, v in zip(value.keys, value.values):
                        if isinstance(k, ast.Constant) and isinstance(v, ast.Tuple):
                            result[k.value] = tuple(
                                e.value for e in v.elts if isinstance(e, ast.Constant)
                            )
                    return result
    raise ValueError("FASE_PONTOS not found in Python source")


def _parse_js_fase_pontos(path: Path) -> dict:
    """Parse FASE_PONTOS const object from JS file using regex."""
    source = path.read_text()
    m = re.search(
        r"const\s+FASE_PONTOS\s*=\s*\{(.*?)\};",
        source,
        re.DOTALL,
    )
    if not m:
        raise ValueError("FASE_PONTOS not found in JS source")

    body = m.group(1)
    result = {}
    # Match "KEY: [num, num]," patterns
    for line in body.split("\n"):
        line = line.strip().rstrip(",")
        if not line or ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip().strip('"')
        val = val.strip()
        # Match [num, num]
        vm = re.match(r"\[(\d+),\s*(\d+)\]", val)
        if vm:
            result[key] = (int(vm.group(1)), int(vm.group(2)))
    return result


def main() -> int:
    py_table = _parse_python_fase_pontos(PY_FILE)
    js_table = _parse_js_fase_pontos(JS_FILE)

    all_keys = sorted(set(py_table) | set(js_table))
    diffs = []

    for key in all_keys:
        py_val = py_table.get(key)
        js_val = js_table.get(key)
        if py_val != js_val:
            diffs.append(f"  {key}: Python={py_val}  JS={js_val}")

    # Check for extra entries
    only_py = sorted(set(py_table) - set(js_table))
    only_js = sorted(set(js_table) - set(py_table))
    if only_py:
        diffs.append(f"  Only in Python: {only_py}")
    if only_js:
        diffs.append(f"  Only in JS: {only_js}")

    if diffs:
        print(f"❌ SCORING TABLES MISMATCH — {len(diffs)} difference(s):")
        for d in diffs:
            print(f"   {d}")
        return 1

    print(f"✅ SCORING TABLES MATCH — {len(py_table)} phases identical in Python and JS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
