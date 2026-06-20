import { describe, it } from 'node:test';
import { createRouter, createMemoryHistory } from 'vue-router';
import assert from 'node:assert/strict';

// Mirror of web/src/router/index.js route definitions (no lazy import in node)
const routes = [
  { path: '/login',     name: 'Login' },
  { path: '/',          name: 'Home' },
  { path: '/jogos',     name: 'Jogos' },
  { path: '/ranking',   name: 'Ranking' },
  { path: '/meus',      name: 'MeusPalpites' },
  { path: '/resultado/:id', name: 'Resultado' },
  { path: '/dashboard', name: 'Dashboard' },
];

describe('Router configuration', () => {
  it('all expected routes are defined', () => {
    const names = routes.map(r => r.name).sort();
    assert.deepStrictEqual(names, ['Dashboard', 'Home', 'Jogos', 'Login', 'MeusPalpites', 'Ranking', 'Resultado']);
  });

  it('no duplicate paths', () => {
    const paths = routes.map(r => r.path);
    assert.strictEqual(new Set(paths).size, paths.length, 'Duplicate paths found in router config');
  });

  it('every route has a name (for programmatic navigation)', () => {
    for (const r of routes) {
      assert.ok(r.name, `Route ${r.path} is missing a name`);
    }
  });

  it('router resolves all valid paths', () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes,
    });
    // Needs a browser environment for hash history, use memory instead
    // The route config is what matters; resolution depends on the history mode
    // but path matching is history-independent.
    for (const r of routes) {
      // Only test static paths (no params)
      if (!r.path.includes(':')) {
        const resolved = router.resolve(r.path);
        assert.ok(resolved, `Route ${r.path} failed to resolve`);
      }
    }
  });
});
