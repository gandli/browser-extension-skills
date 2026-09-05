---
name: wxt-extension-dev
description: Build, test, and publish Chrome/Firefox extensions with the WXT framework (Vite-powered MV3). Use when the user mentions WXT, `wxt.config.ts`, `entrypoints/`, `wxt dev`, `wxt build`, `wxt zip`, or wants a modern build-tool-based extension workflow instead of hand-written manifest.json. Route E2E testing questions to chrome-for-testing-extensions.
---

# WXT Extension Development

WXT = Vite-powered framework for browser extensions. Handles manifest generation,
bundling, content-script injection, HMR, multi-browser builds, and store
publishing. Use it when the user wants a real build pipeline instead of
hand-authored `manifest.json` + loose files (see `chrome-extension-dev` for the
no-framework path).

## Project anatomy

```
wxt.config.ts            # defineConfig({ ... }) — browser, manifest, webExt
entrypoints/             # WXT discovers entrypoints by FILENAME PATTERN, not folder shape
  background.ts          # filename "background*" → service worker
  popup/index.tsx        # dir name "popup" + index → action popup
  options/index.html
  content.ts             # "*.content.ts" → content script
  youtube.content.ts     # "<site>.content.ts" → site-scoped content script
  injected.ts            # "*.injected.ts" → isolated world script
```
Rules (verified from WXT docs):
- Entrypoints are **0 or 1 level deep** inside `entrypoints/`. Don't nest (`youtube/content/index.ts` is NOT discovered — use `youtube.content.ts`).
- Related files for an entrypoint go in its **directory**, not bare in `entrypoints/` (bare files become entrypoints and error).
- `wxt/storage` (`storage.defineItem`) + `fake-browser` make storage testable without a browser.

## Commands

```bash
npm run dev          # wxt dev → web-ext auto-launches Chrome + loads extension (HMR)
                     # Chromium persists profile: set chromiumArgs: ['--user-data-dir=.wxt/chrome-data']
npm run build        # wxt build → .output/chrome-mv3/  (also -b firefox for .output/firefox-mv2)
wxt zip              # package .output/** into .zip for stores
wxt submit           # automated multi-store submission (after `wxt submit init`)
```

`web-ext` (Mozilla) is the auto-launch engine — install it as a dep and WXT uses
it. `web-ext.config.ts` (gitignored, per-dev) or `wxt.config.ts` `webExt:` (shared)
configures browser binaries + chromiumArgs.

## Testing: TWO complementary layers

### 1. Unit — Vitest + fake-browser (no browser needed)
```ts
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import { WxtVitest } from 'wxt/testing/vitest-plugin';
export default defineConfig({ plugins: [WxtVitest()] });
```
`WxtVitest()` polyfills `browser` (chrome.*) in-memory via
`@webext-core/fake-browser`, wires auto-imports, `#imports`, and `import.meta.env.*`.
Storage assertions work against the in-memory impl — no mocking required.

### 2. E2E — route to `chrome-for-testing-extensions`
WXT's own E2E guide only recommends **Playwright** and points at the build
output: `--load-extension=.output/chrome-mv3`. Our raw-CDP harness
(`chrome-for-testing-extensions`, `cdplib.py`, 23/23 assertion matrix) is a
**drop-in alternative** that needs no Playwright and tests the SAME artifact:

| WXT stage | What to drive | Reuse from chrome-for-testing-extensions |
|-----------|---------------|------------------------------------------|
| `wxt build` then test | load `.output/chrome-mv3` via `--load-extension` + Chrome for Testing | `cdplib.py` + popup/content-SW/upgrade assertions |
| `wxt dev` (live) | web-ext already loaded it — attach CDP to the dev browser, assert | same `cdplib.py`; target the running dev Chrome instead of launching |
| content script | navigate to the matched site, check injection | `D1/D2` assertions |
| SW upgrade | bump version, `wxt build`, reload → `reason=update` | `H` assertions (`#dev-reload-button`) |

Key integration facts:
- **Output path is the load path**: replace the harness's hardcoded extension
  dir with `.output/chrome-mv3` (or read `wxt.config.ts` `outDir`).
- **Dev mode**: don't `--load-extension` yourself — `wxt dev` already did.
  Connect CDP to the browser `web-ext` spawned (`--remote-debugging-port` is set
  by web-ext; read it from the dev stdout or use `browser.getBrowserContexts`).
- **`fake-browser` ≠ real CDP**: unit tests validate logic; only the E2E/CDP
  layer proves the actual extension loads, injects, and persists in Chrome.

## Publishing
`wxt zip` produces store-ready ZIPs; `wxt submit` automates Chrome/Edge/Firefox
reviews via `.env.submit` (run `wxt submit init`). First-ever publish still
requires manual store listing. For CWS permission justifications, route to
`chrome-extensions` Part 2 (CHROMEWEBSTORE.md) — WXT generates the manifest but
not the store copy.

## Gotchas (WXT-specific)
- Entrypoint discovery is filename-based — `content.ts` works, `content/index.ts`
  at depth 2 does NOT.
- `web-ext` makes a **fresh profile every dev run** by default (Chromium
  persists only with explicit `--user-data-dir`). Set it or your SW state /
  logins reset each run.
- Don't hand-edit `manifest.json` in `.output/` — it's generated; configure via
  `wxt.config.ts` `manifest:` instead.
- `import.meta.env.IS_CHROME` / `MANIFEST_VERSION` branch per-browser code.

## Verified
WXT docs (wxt.dev): entrypoints, E2E (Playwright + `.output/chrome-mv3`), unit
(Vitest + fake-browser), browser-startup (web-ext auto-launch), publishing
(zip/submit). Cross-referenced with chrome-for-testing-extensions 23/23 harness.
