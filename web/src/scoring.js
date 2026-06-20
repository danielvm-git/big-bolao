// Pure scoring and formatting logic — no I/O, no side effects.

export function calcPontos(pa, pb, ra, rb) {
  if (pa === ra && pb === rb) return 3
  const s = (x, y) => x > y ? 1 : x < y ? -1 : 0
  return s(pa, pb) === s(ra, rb) ? 1 : 0
}
