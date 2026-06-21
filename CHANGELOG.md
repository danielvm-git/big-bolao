# [1.11.0](https://github.com/danielvm-git/big-bolao/compare/v1.10.0...v1.11.0) (2026-06-21)


### Features

* **bot:** silence automatic group messages during quiet hours (22h–8h BRT) ([7f9708e](https://github.com/danielvm-git/big-bolao/commit/7f9708eb9297965e26578fc140d0c8d705eab2ea))


### Reverts

* **admin:** remove /fundir command — data fixed directly in DB ([f71bc0a](https://github.com/danielvm-git/big-bolao/commit/f71bc0a0fc34af3a57720688adb6baeff5903b3d))

# [1.10.0](https://github.com/danielvm-git/big-bolao/compare/v1.9.1...v1.10.0) (2026-06-21)


### Features

* **admin:** add /fundir command to merge duplicate participant records ([5358ca4](https://github.com/danielvm-git/big-bolao/commit/5358ca4de76ab703c2bef29970a72914b56e8a37))

## [1.9.1](https://github.com/danielvm-git/big-bolao/compare/v1.9.0...v1.9.1) (2026-06-21)


### Bug Fixes

* **ranking:** update tests for bold format and remove unused loop variable ([295ac42](https://github.com/danielvm-git/big-bolao/commit/295ac4293175322baceff0b4e7b37862e7e7812f))

# [1.9.0](https://github.com/danielvm-git/big-bolao/compare/v1.8.0...v1.9.0) (2026-06-20)


### Features

* **spec:** close gaps 3, 5, 6, 7 and resolve deploy blockages ([c8f0c37](https://github.com/danielvm-git/big-bolao/commit/c8f0c37f012a289b614d21817a327ae9e9123db6))

# [1.8.0](https://github.com/danielvm-git/big-bolao/compare/v1.7.1...v1.8.0) (2026-06-20)


### Features

* **web:** extract calcRanking, fmtDate, fmtTime, avatarColor into scoring.js + 13 new tests ([8b4d349](https://github.com/danielvm-git/big-bolao/commit/8b4d349e437dc4a0521841de2734248481ada08e))
* **web:** extract FLAGS + flag into scoring.js, update test import ([8512e80](https://github.com/danielvm-git/big-bolao/commit/8512e80da3118d2d556d93ce36fbcbcfac1de435))
* **web:** extract queries.js (domain functions) from api.js + 8 query tests ([c4349fd](https://github.com/danielvm-git/big-bolao/commit/c4349fd73e15a5e8582e7d4bef0bbb57608a0676))
* **web:** extract transport.js (BB singleton) from api.js + 7 transport tests ([43a856d](https://github.com/danielvm-git/big-bolao/commit/43a856d5d6106c219ca4fc693ec6cca8f02c7f46))

## [1.7.1](https://github.com/danielvm-git/big-bolao/compare/v1.7.0...v1.7.1) (2026-06-20)


### Bug Fixes

* **web:** Bosnia & Herzegovina flag not showing — add ampersand-normalized FLAGS key ([c647317](https://github.com/danielvm-git/big-bolao/commit/c6473171aa4b6e1c438a9ee12140d070dc72f5cf))

# [1.7.0](https://github.com/danielvm-git/big-bolao/compare/v1.6.0...v1.7.0) (2026-06-20)


### Features

* **web:** generate PWA icons with the football + maskable support ([ccdf316](https://github.com/danielvm-git/big-bolao/commit/ccdf31635fcbf85568c4ee4cc10f0a7205172232))

# [1.6.0](https://github.com/danielvm-git/big-bolao/compare/v1.5.0...v1.6.0) (2026-06-20)


### Features

* **web:** replace favicon with a football to match the site theme ([f70dd68](https://github.com/danielvm-git/big-bolao/commit/f70dd6845cddeb6d695134592cb8f47f3dc9b305))

# [1.5.0](https://github.com/danielvm-git/big-bolao/compare/v1.4.2...v1.5.0) (2026-06-20)


### Bug Fixes

* **web:** add missing country flags + punctuation-robust lookup ([dd803e8](https://github.com/danielvm-git/big-bolao/commit/dd803e8015836b3d7deb9da9913bef0e3ff98d4f))


### Features

* **iv:** serve static HTML to Telegram Instant View bot ([27f10b2](https://github.com/danielvm-git/big-bolao/commit/27f10b23fb75dcf454a302ec432df04904f0048c))

## [1.4.2](https://github.com/danielvm-git/big-bolao/compare/v1.4.1...v1.4.2) (2026-06-20)


### Bug Fixes

* **web:** change og:image from SVG to PNG for Telegram link preview ([2abb224](https://github.com/danielvm-git/big-bolao/commit/2abb224c543aa93a9e25ab46e1bf0da452d98459))

## [1.4.1](https://github.com/danielvm-git/big-bolao/compare/v1.4.0...v1.4.1) (2026-06-20)


### Bug Fixes

* **footer:** bake version into bundle via Vite define (CSP-safe) ([6ce6507](https://github.com/danielvm-git/big-bolao/commit/6ce6507103ac032fdbddac12bac7e65c0e012d28))

# [1.4.0](https://github.com/danielvm-git/big-bolao/compare/v1.3.4...v1.4.0) (2026-06-20)


### Features

* **deploy:** add passthrough_paths for /api/version endpoint ([98ef581](https://github.com/danielvm-git/big-bolao/commit/98ef5815bdfb1b93860f625e7acad20a0451e739))

## [1.3.4](https://github.com/danielvm-git/big-bolao/compare/v1.3.3...v1.3.4) (2026-06-20)


### Bug Fixes

* **bot:** retry with backoff on Conflict during deploy ([faf2d92](https://github.com/danielvm-git/big-bolao/commit/faf2d9215142cdd47481b5044b804513b1b61b37))

## [1.3.3](https://github.com/danielvm-git/big-bolao/compare/v1.3.2...v1.3.3) (2026-06-20)


### Bug Fixes

* **version:** inject app version into HTML to bypass BigBase SPA interception ([b5e749e](https://github.com/danielvm-git/big-bolao/commit/b5e749e220eb1fb8db4a1327c922901650c9d289))

## [1.3.2](https://github.com/danielvm-git/big-bolao/compare/v1.3.1...v1.3.2) (2026-06-20)


### Bug Fixes

* **version:** use static VERSION file instead of API endpoint ([465a3cc](https://github.com/danielvm-git/big-bolao/commit/465a3ccec33f4a376362953cf50bb15bfe491ea8))

## [1.3.1](https://github.com/danielvm-git/big-bolao/compare/v1.3.0...v1.3.1) (2026-06-20)


### Bug Fixes

* **footer:** use app-version.json endpoint ([ab19234](https://github.com/danielvm-git/big-bolao/commit/ab19234b57cc0832600b26a2107af3c1ee051456))

# [1.3.0](https://github.com/danielvm-git/big-bolao/compare/v1.2.0...v1.3.0) (2026-06-20)


### Features

* **footer:** add clickable links and BigPowers branding ([cf47d51](https://github.com/danielvm-git/big-bolao/commit/cf47d514caa7a4169a8ea98509f76f4183702ff5))

# [1.2.0](https://github.com/danielvm-git/big-bolao/compare/v1.1.1...v1.2.0) (2026-06-20)


### Features

* **footer:** add 'Built with' and Changelog link ([51d7f87](https://github.com/danielvm-git/big-bolao/commit/51d7f87df6f815c17cf2e5b170b224a268f5df63))

## [1.1.1](https://github.com/danielvm-git/big-bolao/compare/v1.1.0...v1.1.1) (2026-06-20)


### Bug Fixes

* **review:** address all review findings ([5c11e68](https://github.com/danielvm-git/big-bolao/commit/5c11e681562f67e204b6c8c999a806625e7a0ec6))

# [1.1.0](https://github.com/danielvm-git/big-bolao/compare/v1.0.5...v1.1.0) (2026-06-20)


### Features

* **web:** add version footer to main app + remove landing page ([f2ecdea](https://github.com/danielvm-git/big-bolao/commit/f2ecdea19a9b08d075e5e2a153748dadbf735060))

## [1.0.5](https://github.com/danielvm-git/big-bolao/compare/v1.0.4...v1.0.5) (2026-06-20)


### Bug Fixes

* **ranking:** named constant for min valid telegram_id + formatar tests ([e1f37e3](https://github.com/danielvm-git/big-bolao/commit/e1f37e30fda93b882f1e188849de2e6ad17bbe38))

## [1.0.4](https://github.com/danielvm-git/big-bolao/compare/v1.0.3...v1.0.4) (2026-06-20)


### Bug Fixes

* **ci:** simplify workflow — deploy trigger + health check, no status polling ([9037f67](https://github.com/danielvm-git/big-bolao/commit/9037f67d7c663d578bebb45e2b925fe5bbd6cf6a))

## [1.0.3](https://github.com/danielvm-git/big-bolao/compare/v1.0.2...v1.0.3) (2026-06-20)


### Bug Fixes

* add .npmrc to skip puppeteer Chrome download in CI/BigBase ([f37a9d2](https://github.com/danielvm-git/big-bolao/commit/f37a9d212459017a24aed59bf19617c6515361a3))

## [1.0.2](https://github.com/danielvm-git/big-bolao/compare/v1.0.1...v1.0.2) (2026-06-20)


### Bug Fixes

* **ci:** fix bash arithmetic and emoji in timeout message ([ec93251](https://github.com/danielvm-git/big-bolao/commit/ec932512426c0fe4409aa207b1a9af41012844da))

## [1.0.1](https://github.com/danielvm-git/big-bolao/compare/v1.0.0...v1.0.1) (2026-06-20)


### Bug Fixes

* **ci:** add required env vars for pytest in CI ([150b7ea](https://github.com/danielvm-git/big-bolao/commit/150b7eacd4558053dfd3190373d6c530949b6ac7))

# 1.0.0 (2026-06-20)


### Bug Fixes

* **bot:** create event loop in bg thread — bot crashed on deploy without asyncio loop ([a691689](https://github.com/danielvm-git/big-bolao/commit/a6916891a0155c503084a9c22ae265fa3f5f661a))
* **bot:** create event loop in bg thread + disable stop signals ([2b6f967](https://github.com/danielvm-git/big-bolao/commit/2b6f967e851746366bd3891060407244090efe7d))
* **ci:** add pytest to requirements.txt for CI test step ([677ecac](https://github.com/danielvm-git/big-bolao/commit/677ecac0693240589825193ede4a6b86abe45e6e))
* **ci:** remove root package.json — broke BigBase app type detection ([dab88f4](https://github.com/danielvm-git/big-bolao/commit/dab88f443cee3e378b275b1d1061385b94f55d1f))
* **ci:** use email/password login instead of API key for BigBase deploy ([c1f6dce](https://github.com/danielvm-git/big-bolao/commit/c1f6dceea21e669874c763c5522c51e34d2c4c05))
* **dashboard:** remove redundant "Últimos resultados" section and optimize layout ([9a39a44](https://github.com/danielvm-git/big-bolao/commit/9a39a447dcd452be8fe9e7c1c92bdae8b535c685))
* **deploy:** add no-op build script — BigBase requires npm run build to exist ([a6087b3](https://github.com/danielvm-git/big-bolao/commit/a6087b3b9eb4128af553452cbaeaf095000b8167))
* **deploy:** add Procfile web: node server.js + package.json main field ([0d7ba03](https://github.com/danielvm-git/big-bolao/commit/0d7ba03733e2195105ce0c922f0b122f895fbd7a))
* **deploy:** add root package.json so BigBase detects app as Node, not Python ([ab09b9b](https://github.com/danielvm-git/big-bolao/commit/ab09b9bd8ff80abd695da88ad99107aaeeacb119))
* **deploy:** app.py serves web/dist/ on $PORT + runs bot in thread ([2476100](https://github.com/danielvm-git/big-bolao/commit/2476100ca58101ca00adb5b859db2b4eaccef619))
* **deploy:** isolate bolão env to /opt/bolao/.env (separate from BigBase) ([eefa423](https://github.com/danielvm-git/big-bolao/commit/eefa4239c59e65d1061d1007e611827d5c72ce26))
* **deploy:** output Vite build to ../dist — eliminates broken cp step ([7204882](https://github.com/danielvm-git/big-bolao/commit/720488261815c442b7481e138b745f488b2b01a9))
* **deploy:** remove build script — dist/ is pre-committed, BigBase just runs npm start ([0ba3395](https://github.com/danielvm-git/big-bolao/commit/0ba3395516df645e9b0e2f5ceb2601989a74da14))
* **deploy:** rename server.js to index.js — BigBase may default to node index.js ([a9ee8b7](https://github.com/danielvm-git/big-bolao/commit/a9ee8b722914ba0ca375ba9a62d8ad7ac789c0e9))
* **deploy:** revert outDir to web/dist/ — BigBase serves root_path+/dist/ ([6da9342](https://github.com/danielvm-git/big-bolao/commit/6da934256970d414a2f46961722fb7195207fd28))
* **deploy:** revert to static serve — remove package.json/Node server ([4478807](https://github.com/danielvm-git/big-bolao/commit/4478807fd0e00347538a796f997c133f32fe0e9e))
* **deploy:** serve pre-built dist/ with Node http server — no build step needed ([cf695ed](https://github.com/danielvm-git/big-bolao/commit/cf695ed5bc5ea6e5ac9fc60588b0bdc1c366a64f))
* **deploy:** serve web/dist with Python stdlib — no external deps ([585c698](https://github.com/danielvm-git/big-bolao/commit/585c698933372cd816da86e1d36a398e12a7c571))
* **deploy:** simplify app.py to only run bot; add server setup + redeploy scripts ([07d5429](https://github.com/danielvm-git/big-bolao/commit/07d542985046728fc6bfa087fdf341d44a2a8c6f))
* **deploy:** use npx serve for static SPA — proper health checks + PORT handling ([1d206d3](https://github.com/danielvm-git/big-bolao/commit/1d206d3bac675a54ce7411d85693f7009a884147))
* mark BUG-2026-06-19-215300 as resolved — dashboard public landing page deployed ([6713375](https://github.com/danielvm-git/big-bolao/commit/6713375c5bc17814fbb00217ed539a8086208f77))
* **ranking:** add medal icons for top 3, number icons for rest ([5a9183a](https://github.com/danielvm-git/big-bolao/commit/5a9183aeff3744a6683618333a78e45c3ce6bcd0))
* **ranking:** compact mobile-friendly format with emoji stats ([6a91dbc](https://github.com/danielvm-git/big-bolao/commit/6a91dbcf6130249a2198e301e58cfa33ab67f48d))
* **ranking:** compact table with icons, remove Jog column ([6abea7e](https://github.com/danielvm-git/big-bolao/commit/6abea7eaf742d8d57c7faa4e319e4b0dd2e5fa03))
* **ranking:** duas checagens anti-duplicata — ativo + telegram_id >= 0 ([29e145f](https://github.com/danielvm-git/big-bolao/commit/29e145f11d9cb9c4dc50aacb7d6da4464615cb95))
* **ranking:** improve column alignment for better readability ([522679e](https://github.com/danielvm-git/big-bolao/commit/522679e5744c91f553e10aa2e984f5f4536c2b8b))
* **ranking:** monospace aligned table for mobile-friendly ranking output ([29e3c0d](https://github.com/danielvm-git/big-bolao/commit/29e3c0dc868f0aa8dfb6e975d2427e93321c59a7))
* **ranking:** update tiebreaker order and restore Jog column ([1a5ee9d](https://github.com/danielvm-git/big-bolao/commit/1a5ee9d51ed8b81a3a7eb88125753fcfdbc386a0))
* **ranking:** use simpler format without code tags for Telegram emoji rendering ([e7b8dfb](https://github.com/danielvm-git/big-bolao/commit/e7b8dfb2f867f17a776202b2687b21f484ef4a0d))
* **web:** auto-login with service account — loads public data without user auth ([50b353d](https://github.com/danielvm-git/big-bolao/commit/50b353d32454022e3f349de11cbc61c9cf89183a))
* **web:** extract landing CSS/JS to external files — bypass CSP default-src 'self' ([28e6ad0](https://github.com/danielvm-git/big-bolao/commit/28e6ad00c07e2ab35bcbc3703de1c19a7e40600d))
* **web:** replace dev mode login card with proper Telegram access message ([b224e71](https://github.com/danielvm-git/big-bolao/commit/b224e71a7f599e92ce44e4ca6f57414b547451c3))
* **web:** replace SQL calls with REST collections API (service account has no SQL permission) ([116e190](https://github.com/danielvm-git/big-bolao/commit/116e19040fc8061fff83ba914a765b88efd2a3c1))
* **web:** scroll, flags, ranking duplicates, real palpites ([47884d5](https://github.com/danielvm-git/big-bolao/commit/47884d53ca1cf47064d3fc140d938a41bc63d1a8))


### Features

* **api:** integrate apifootball.com live fixtures and scores — fix SQL 403 and Markdown parse errors ([7194310](https://github.com/danielvm-git/big-bolao/commit/71943104db5c096e51fec421c77e863ff0de4d47))
* **ci:** GitHub Actions CI/CD pipeline — semantic-release + build + test + deploy ([d45a4c5](https://github.com/danielvm-git/big-bolao/commit/d45a4c5ec33b244f538adb742b1725b5973fec07))
* **dashboard:** add cross-table matrix with color-coded cells ([f204469](https://github.com/danielvm-git/big-bolao/commit/f20446970f32c1f4e6b521277d0ca4035641eaaa))
* **dashboard:** add cross-table matrix with color-coded cells and legend ([09f7851](https://github.com/danielvm-git/big-bolao/commit/09f7851cf54c90db690dbb197073cdbfc6d29cbf))
* **dashboard:** add hero section with stats and leader card ([1a17ffa](https://github.com/danielvm-git/big-bolao/commit/1a17ffa702e16803005ce3e1c9c8b1b36fff4ff3))
* **dashboard:** add hero section with stats and leader card ([cbd6c17](https://github.com/danielvm-git/big-bolao/commit/cbd6c17e1e482a9691d04005c2fe91ef4a781d5f))
* **dashboard:** add player/country/group detail views with interactive navigation ([7c0d620](https://github.com/danielvm-git/big-bolao/commit/7c0d6205f8ec09327147b601feb4a08e189be51f))
* **dashboard:** add player/country/group detail views with interactive navigation ([f9809ee](https://github.com/danielvm-git/big-bolao/commit/f9809eee02988dd13915912cf85125674fa70528))
* **dashboard:** add two-column layout with games list and ranking sidebar ([edf6bee](https://github.com/danielvm-git/big-bolao/commit/edf6beebf2598a4d816991efe203dd5e0ad558b4))
* **dashboard:** add two-column layout with games list and ranking sidebar ([6932bf0](https://github.com/danielvm-git/big-bolao/commit/6932bf08f35b912380bf4b012b0938b49d62067b))
* **dashboard:** scaffold desktop dashboard layout with sticky header ([c48d22b](https://github.com/danielvm-git/big-bolao/commit/c48d22bd695281e532c262ef11ecfe936c830503))
* **dashboard:** scaffold desktop dashboard layout with sticky header ([d827409](https://github.com/danielvm-git/big-bolao/commit/d827409a98ce6a65b738544e8ef50fff23781150))
* **deploy:** add app.py web server + proxy + fix BigBase token ([045a734](https://github.com/danielvm-git/big-bolao/commit/045a734b2ec11ce164921c1cafd0a80612199b59))
* initial commit — bolão web app (FastAPI + Vue/Vite + BigBase) ([c129368](https://github.com/danielvm-git/big-bolao/commit/c129368e8a77dd20a659b726a386ae215ca27bbd))
* **landing:** add version footer to track deployments ([9a9cecc](https://github.com/danielvm-git/big-bolao/commit/9a9ceccf43fd24fa1d48612830223f2010f2f121))
* **web:** add Open Graph meta tags for Telegram/WhatsApp link previews ([5f3b18a](https://github.com/danielvm-git/big-bolao/commit/5f3b18a3dafa81ece9c4c4d485cd2b1aa4ea7208))
* **web:** add Swiss grid landing page at /landing.html ([755c854](https://github.com/danielvm-git/big-bolao/commit/755c854413d3dfb5f65f07598c1005c7b5d672ed)), closes [#111](https://github.com/danielvm-git/big-bolao/issues/111) [#e4002b](https://github.com/danielvm-git/big-bolao/issues/e4002b)
* **web:** cross-table uses real palpites — all players x all games ([00f7e2b](https://github.com/danielvm-git/big-bolao/commit/00f7e2b3e64cc622614eeecbc21c664e6392b9ef))
* **web:** make dashboard the public landing page at / ([e7fa657](https://github.com/danielvm-git/big-bolao/commit/e7fa657e72dbf1382d391256a74b03255414d1b3))
* **web:** rebuild frontend from scratch — 3 views, clean store, no mock data ([15cf799](https://github.com/danielvm-git/big-bolao/commit/15cf799b836195db1ad17f234f6f5a9aac82f527))
* **web:** remove login entirely — dashboard is fully public, no auth gate ([a729155](https://github.com/danielvm-git/big-bolao/commit/a7291556b4110a950ebd551b08967c659baa8d21))
