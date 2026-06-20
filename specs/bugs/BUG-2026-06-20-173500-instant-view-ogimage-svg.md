# BUG-2026-06-20-173500: Telegram link preview quebrado — og:image SVG não suportado

## Problem

Ao compartilhar `https://bolao.bigbase.click/` no Telegram, o link preview não renderiza a imagem. O Instant View também não funciona porque o `<body>` é uma SPA vazia renderizada por JavaScript.

**Comportamento atual:**
- Link preview sem imagem
- Instant View: página em branco (bot não executa JS)
- `og:image` apontava para `og-image.svg` (image/svg+xml)

**Comportamento esperado:**
- Link preview com imagem do bolão
- Instant View funcional (requer template registrado + conteúdo server-rendered)

**Como reproduzir:**
1. Compartilhar `https://bolao.bigbase.click/` no Telegram
2. Observar link preview sem imagem

## Root Cause Analysis

Três fatores contribuintes, em ordem de impacto:

| # | Fator | Detalhe |
|---|-------|---------|
| 1 | `og:image` em **SVG** | Telegram só suporta JPEG/PNG/WEBP para `og:image`. SVG retorna `image/svg+xml` — ignorado. |
| 2 | SPA com `<body>` vazio | `<body>` contém apenas `<div id="app"></div>`. Conteúdo é renderizado por Vue.js no cliente. O bot de Instant View do Telegram não executa JavaScript — vê página em branco. |
| 3 | HTML inválido (BigBase) | BigBase v2.31+ injeta `<script>window.__BIGBASE_METADATA__</script>` entre `</head>` e `<body>`. Isso cria HTML estruturalmente inválido que pode confundir parsers. |

**Fator #1 é a causa primária** do link preview quebrado — confirmado via Telegram docs e testes (SVG retorna 200 com `image/svg+xml`, Telegram ignora). Fator #2 impede Instant View completo mas não afeta o link preview. Fator #3 é cosmético.

**Risco:** Low — mudança de formato de imagem, sem alteração de lógica.

## TDD Fix Plan

### Cycle 1: og:image em PNG é servido com MIME type correto

**RED**: Testar que `GET /og-image.png` retorna `image/png` com status 200 e corpo > 0 bytes.

**GREEN**: Converter `og-image.svg` → `og-image.png` (1200×630) via `rsvg-convert`. Atualizar referências em `web/index.html` e `web/dist/index.html` de `.svg` para `.png`.

**verify**: `curl -sI https://bolao.bigbase.click/og-image.png | grep 'image/png'`

### Cycle 2: Link preview carrega no Telegram

**RED**: Compartilhar `https://bolao.bigbase.click/` no Telegram e verificar que a imagem aparece no link preview.

**GREEN**: A alteração do Cycle 1 resolve — Telegram busca `og:image`, encontra PNG, renderiza.

**verify**: Compartilhar URL no Telegram e confirmar preview com imagem.

## Acceptance Criteria

- [x] `og:image` aponta para `.png` (não `.svg`)
- [x] `GET /og-image.png` retorna `image/png`, 200 OK
- [x] `og:image:width=1200`, `og:image:height=630`
- [x] Twitter card image também atualizada
- [x] Link preview funcional no Telegram

## Resolution

**Fix aplicado:** `og-image.svg` convertido para PNG via `rsvg-convert -w 1200 -h 630`. Referências atualizadas em `web/index.html` (source) e `web/dist/index.html` (built). Deploy confirmado em produção.

**Instant View** (leitura dentro do Telegram) requer template registrado em `instantview.telegram.org` + conteúdo server-rendered — fora do escopo deste fix. O link preview (imagem + título + descrição) está funcional.
