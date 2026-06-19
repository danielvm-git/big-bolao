# Tech Stack — Big Bolão Site

## Frontend

| Camada | Tecnologia | Razão |
|--------|-----------|-------|
| Framework | Vue 3 (Composition API + `<script setup>`) | Template syntax próxima do protótipo, leve, ideal para SPA de 4 telas |
| Bundler | Vite 8 | Build → `dist/` nativamente, detectado pelo BigBase Deploy |
| Roteamento | vue-router | Navegação inferior com 4 abas |
| HTTP | fetch nativo | Só 3-4 endpoints do BigBase |
| Estilo | CSS global + variáveis (protótipo adaptado) | Sem framework CSS extra |

## Backend / Dados

| Camada | Tecnologia | Razão |
|--------|-----------|-------|
| Banco/API | BigBase (`bigbase.click`) | Já é o backend do bolão |
| Auth | Magic token via BigBase Function (JS) | Bot gera token, Function valida |
| API endpoints | `/api/collections/*`, `/api/sql` | Já existem, JWT protegidas |

## Deploy

| Camada | Tecnologia | Razão |
|--------|-----------|-------|
| Build output | `web/dist/` | Vite produz isso por padrão |
| Hospedagem | BigBase Deploy (Sites) | Conecta GitHub, builda, serve static |
| Domínio | `bolao.bigbase.click` (subdomínio) | Caddy faz o roteamento |
| Proxy | Caddy (já existente no VPS) | Só adicionar uma linha no Caddyfile |

## Pipeline de dados

```
Vue SPA (browser)
  │  GET/POST /api/collections/*  (com JWT)
  │  GET /api/auth/login          (só pra obter JWT via magic token)
  │  POST /api/functions/*/run    (pra validar magic token)
  ▼
BigBase Go (bigbase.click:8080)
  │
  ├── SQLite (bigbase.db)
  │   ├── participantes
  │   ├── jogos
  │   ├── palpites
  │   ├── magic_tokens
  │   └── users (auth do BigBase)
  │
  └── Functions (goja JS runtime)
      └── bolao-magic-login
```

## Protótipo

Em `prototype/project/Big Bolão.dc.html` — React runtime (dc-runtime). Servirá como referência visual; a implementação será em Vue 3.
