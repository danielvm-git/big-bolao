import { test } from "node:test";
import assert from "node:assert/strict";
import {
  calcPontos,
  calcRanking,
  fmtDate,
  fmtTime,
  avatarColor,
} from "../src/scoring.js";

// ── Formatadores ────────────────────────────────────────────────

test("fmtDate: formats ISO to DD/MM", () => {
  assert.equal(fmtDate("2026-06-15T20:00:00Z"), "15/06");
  assert.equal(fmtDate("2026-07-01T12:00:00Z"), "01/07");
});

test("fmtDate: returns empty string for null/undefined", () => {
  assert.equal(fmtDate(null), "");
  assert.equal(fmtDate(undefined), "");
  assert.equal(fmtDate(""), "");
});

test("fmtTime: extracts HH:MM from ISO", () => {
  assert.equal(fmtTime("2026-06-15T20:00:00Z"), "20:00");
  assert.equal(fmtTime("2026-06-15T09:30:00Z"), "09:30");
});

test("fmtTime: returns empty string for null/undefined", () => {
  assert.equal(fmtTime(null), "");
  assert.equal(fmtTime(undefined), "");
  assert.equal(fmtTime(""), "");
});

test("avatarColor: cycles through color palette", () => {
  const c0 = avatarColor(0);
  const c1 = avatarColor(1);
  assert.notEqual(c0, c1); // First two are different
  assert.equal(avatarColor(8), c0); // Wraps around after 8
  assert.equal(avatarColor(16), c0); // Wraps again
});

// ── calcRanking ─────────────────────────────────────────────────

const SIMPLE_GAME = [
  {
    match_id: "R1-01",
    status: "encerrado",
    gols_casa: 2,
    gols_fora: 1,
  },
];

test("calcRanking: inactive participants excluded", () => {
  const palpites = [
    {
      match_id: "R1-01",
      telegram_id: 111,
      gols_casa: 2,
      gols_fora: 1,
    },
  ];
  const participantes = [
    { telegram_id: 111, nome: "Alice", ativo: true },
    { telegram_id: 222, nome: "Alice", ativo: false },
  ];
  const rank = calcRanking(SIMPLE_GAME, palpites, participantes);
  assert.equal(rank.length, 1);
  assert.equal(rank[0].telegram_id, 111);
});

test("calcRanking: active participant still appears even with 0 palpites", () => {
  const rank = calcRanking(
    SIMPLE_GAME,
    [],
    [
      { telegram_id: 111, nome: "Alice", ativo: true },
      { telegram_id: 222, nome: "Bob", ativo: true },
    ]
  );
  assert.equal(rank.length, 2);
});

test("calcRanking: missing ativo field treats participant as active", () => {
  const rank = calcRanking([], [], [{ telegram_id: 111, nome: "Alice" }]);
  assert.equal(rank.length, 1);
  assert.equal(rank[0].nome, "Alice");
});

test("calcRanking: negative telegram_id excluded", () => {
  const palpites = [
    { match_id: "R1-01", telegram_id: -4, gols_casa: 2, gols_fora: 1 },
    { match_id: "R1-01", telegram_id: 555, gols_casa: 1, gols_fora: 0 },
  ];
  const participantes = [
    { telegram_id: -4, nome: "Alice", ativo: true },
    { telegram_id: 555, nome: "Alice", ativo: true },
  ];
  const rank = calcRanking(SIMPLE_GAME, palpites, participantes);
  assert.equal(rank.length, 1);
  assert.equal(rank[0].telegram_id, 555);
});

test("calcRanking: scores 3 points for exact match, 1 for winner", () => {
  const jogos = [
    { match_id: "R1-01", status: "encerrado", gols_casa: 2, gols_fora: 1 },
    { match_id: "R1-02", status: "encerrado", gols_casa: 0, gols_fora: 2 },
  ];
  const palpites = [
    { match_id: "R1-01", telegram_id: 111, gols_casa: 2, gols_fora: 1 }, // exact → 3
    { match_id: "R1-02", telegram_id: 111, gols_casa: 0, gols_fora: 3 }, // winner (fora win) → 1
  ];
  const participantes = [{ telegram_id: 111, nome: "Alice", ativo: true }];
  const rank = calcRanking(jogos, palpites, participantes);
  assert.equal(rank[0].pontos, 4);
  assert.equal(rank[0].exatos, 1);
  assert.equal(rank[0].acertos, 2);
});

test("calcRanking: sorts by pontos desc, then exatos desc, then nome asc", () => {
  const jogos = [
    { match_id: "R1-01", status: "encerrado", gols_casa: 2, gols_fora: 1 },
    { match_id: "R1-02", status: "encerrado", gols_casa: 1, gols_fora: 1 },
  ];
  const palpites = [
    { match_id: "R1-01", telegram_id: 11, gols_casa: 2, gols_fora: 1 }, // 3pts
    { match_id: "R1-02", telegram_id: 11, gols_casa: 1, gols_fora: 1 }, // 3pts
    { match_id: "R1-01", telegram_id: 22, gols_casa: 2, gols_fora: 1 }, // 3pts
    { match_id: "R1-02", telegram_id: 22, gols_casa: 2, gols_fora: 0 }, // 1pt (casa win)
  ];
  const participantes = [
    { telegram_id: 11, nome: "Bob", ativo: true }, // 6pts, 2 exatos
    { telegram_id: 22, nome: "Alice", ativo: true }, // 4pts, 1 exato
  ];
  const rank = calcRanking(jogos, palpites, participantes);
  assert.equal(rank[0].telegram_id, 11); // Bob first (6 pts)
  assert.equal(rank[1].telegram_id, 22); // Alice second (4 pts)
});

test("calcRanking: ignores non-encerrado matches", () => {
  const jogos = [
    { match_id: "R1-01", status: "agendado", gols_casa: null, gols_fora: null },
  ];
  const palpites = [
    { match_id: "R1-01", telegram_id: 111, gols_casa: 2, gols_fora: 1 },
  ];
  const participantes = [{ telegram_id: 111, nome: "Alice", ativo: true }];
  const rank = calcRanking(jogos, palpites, participantes);
  assert.equal(rank[0].pontos, 0);
  assert.equal(rank[0].exatos, 0);
});

// ── Phase-aware scoring (knockout multipliers) ──────────────────

test("calcPontos: R32 exact returns 5, winner returns 2", () => {
  assert.equal(calcPontos(2, 1, 2, 1, "R32-03"), 5);
  assert.equal(calcPontos(2, 0, 3, 0, "R32-03"), 2);
  assert.equal(calcPontos(2, 0, 0, 1, "R32-03"), 0);
});

test("calcPontos: R16 exact returns 10, winner returns 5", () => {
  assert.equal(calcPontos(1, 0, 1, 0, "R16-01"), 10);
  assert.equal(calcPontos(2, 0, 3, 0, "R16-01"), 5);
});

test("calcPontos: QF exact returns 15, winner returns 10", () => {
  assert.equal(calcPontos(1, 0, 1, 0, "QF-01"), 15);
  assert.equal(calcPontos(2, 0, 3, 0, "QF-01"), 10);
});

test("calcPontos: SF and 3P exact returns 25, winner returns 15", () => {
  assert.equal(calcPontos(1, 0, 1, 0, "SF-01"), 25);
  assert.equal(calcPontos(2, 0, 3, 0, "SF-01"), 15);
  assert.equal(calcPontos(1, 0, 1, 0, "3P-01"), 25);
  assert.equal(calcPontos(2, 0, 3, 0, "3P-01"), 15);
});

test("calcPontos: FIN exact returns 50, winner returns 25", () => {
  assert.equal(calcPontos(1, 0, 1, 0, "FIN-01"), 50);
  assert.equal(calcPontos(2, 0, 3, 0, "FIN-01"), 25);
});

test("calcRanking: R32 exact gives 5 pts and increments exatos", () => {
  const jogos = [
    { match_id: "R32-01", status: "encerrado", gols_casa: 1, gols_fora: 0 },
  ];
  const palpites = [
    { match_id: "R32-01", telegram_id: 1, gols_casa: 1, gols_fora: 0 },
  ];
  const parts = [{ telegram_id: 1, nome: "Ana", ativo: true }];
  const r = calcRanking(jogos, palpites, parts);
  assert.equal(r[0].pontos, 5);
  assert.equal(r[0].exatos, 1);
});

test("calcRanking: R32 winner gives 2 pts and does not increment exatos", () => {
  const jogos = [
    { match_id: "R32-01", status: "encerrado", gols_casa: 2, gols_fora: 0 },
  ];
  const palpites = [
    { match_id: "R32-01", telegram_id: 1, gols_casa: 3, gols_fora: 0 },
  ];
  const parts = [{ telegram_id: 1, nome: "Ana", ativo: true }];
  const r = calcRanking(jogos, palpites, parts);
  assert.equal(r[0].pontos, 2);
  assert.equal(r[0].exatos, 0);
  assert.equal(r[0].acertos, 1);
});
