# Tech Stack — Big Bolão Site

## Frontend

| Camada     | Tecnologia                                  | Razão                                                                 |
| ---------- | ------------------------------------------- | --------------------------------------------------------------------- |
| Framework  | Vue 3 (Composition API + `<script setup>`)  | Template syntax próxima do protótipo, leve, ideal para SPA de 4 telas |
| Bundler    | Vite 8                                      | Build → `dist/` nativamente, detectado pelo BigBase Deploy            |
| Roteamento | vue-router                                  | Navegação inferior com 4 abas                                         |
| HTTP       | fetch nativo                                | Só 3-4 endpoints do BigBase                                           |
| Estilo     | CSS global + variáveis (protótipo adaptado) | Sem framework CSS extra                                               |

## Backend / Dados

| Camada        | Tecnologia                               | Razão                                                                        |
| ------------- | ---------------------------------------- | ---------------------------------------------------------------------------- |
| Banco/API     | BigBase (`bigbase.click`)                | Já é o backend do bolão                                                      |
| Auth          | JWT via service account (email/password) | Bot e site usam mesma conta de serviço; site faz login via `/api/auth/login` |
| API endpoints | `/api/collections/*`                     | REST, JWT protegidas. Filtragem O(n) em processo — `/api/sql` não disponível |

## Deploy

| Camada       | Tecnologia                         | Razão                                |
| ------------ | ---------------------------------- | ------------------------------------ |
| Build output | `web/dist/`                        | Vite produz isso por padrão          |
| Hospedagem   | BigBase Deploy (Sites)             | Conecta GitHub, builda, serve static |
| Domínio      | `bolao.bigbase.click` (subdomínio) | Caddy faz o roteamento               |
| Proxy        | Caddy (já existente no VPS)        | Só adicionar uma linha no Caddyfile  |

## Pipeline de dados

```
Vue SPA (browser)
  │  GET/POST /api/collections/*  (com JWT Bearer)
  │  GET /api/auth/login          (login com service account)
  ▼
BigBase Go (bigbase.click:8080)
  │
  └── SQLite (bigbase.db)
      ├── participantes  (telegram_id, nome, ativo)
      ├── jogos          (match_id, rodada, kickoff, casa, fora, gols_casa, gols_fora, status)
      └── palpites       (match_id, telegram_id, nome, gols_casa, gols_fora, atualizado_em)
```

## Protótipo

Em `prototype/project/Big Bolão.dc.html` — React runtime (dc-runtime). Servirá como referência visual; a implementação será em Vue 3.
