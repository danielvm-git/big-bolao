// Integration test: JS scoring matches the shared golden fixture.
//
// Loads specs/test-strategy/scoring-golden.json (SAME file as
// tests/test_scoring.py), iterates every case, calls calcPontos()
// from ../src/scoring.js, and asserts the result matches expected.
// This is the JS half of the Python↔JS parity invariant.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { calcPontos } from "../src/scoring.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const GOLDEN = resolve(
  __dirname,
  "../../specs/test-strategy/scoring-golden.json"
);
const cases = JSON.parse(readFileSync(GOLDEN, "utf-8"));

test("golden fixture has ≥21 cases", () => {
  assert.ok(cases.length >= 21, `Expected ≥21 cases, got ${cases.length}`);
});

for (const c of cases) {
  test(`JS golden: ${c.desc}`, () => {
    const result = calcPontos(c.pa, c.pb, c.ra, c.rb, c.match_id);
    assert.equal(
      result,
      c.expected,
      `calcPontos(${c.pa},${c.pb},${c.ra},${c.rb},"${c.match_id}") = ${result}, expected ${c.expected}`
    );
  });
}
