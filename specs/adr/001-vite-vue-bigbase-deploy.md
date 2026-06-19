# ADR 001 — Vite + Vue 3 com deploy no BigBase Sites

## Status

Accepted

## Context

Precisamos de um site para o Big Bolão. O protótipo existe em HTML/JS (dc-runtime). 
Precisamos escolher stack que:
1. Produza output que o BigBase Deploy consiga servir (detecta `package.json` → build → `dist/`)
2. Seja rápida de implementar (app pequeno, 4 telas)
3. Funcione com as APIs REST existentes do BigBase

## Decisão

- **Vue 3** com Composition API para o frontend
- **Vite 8** como bundler (produz `dist/` por padrão)
- Comunicação direta com `/api/collections/*` e `/api/sql` do BigBase
- Autenticação via BigBase Functions (JS runtime goja)
- Deploy via BigBase Sites (conecta GitHub, builda, serve)

## Consequências

- Positivas:
  - Deploy zero-config no BigBase (detecta package.json → npm run build → dist/)
  - Vue 3 template syntax é muito próxima do HTML do protótipo
  - Sem backend extra — BigBase já é o backend
  - Site e bot compartilham o mesmo banco

- Negativas:
  - Precisa de uma Function JS no BigBase para validar magic tokens
  - Precisa adicionar rota no Caddy para o subdomínio
  - Vue 3 não é a stack do admin UI do BigBase (React), mas isso é irrelevante

## Alternativas consideradas

| Alternativa | Motivo da rejeição |
|-------------|-------------------|
| React | Mais boilerplate para app pequeno, protótipo é HTML puro |
| SvelteKit (adapter-static) | Output `build/` precisa config pra `dist/`, gotcha desnecessário |
| FastAPI + templates | Perde toda a interatividade mobile do protótipo |
| HTML puro + jQuery | Manutenção de longo prazo pior, estado global complexo |
