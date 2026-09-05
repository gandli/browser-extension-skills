---
name: crxjs-extension-dev
description: Build Chrome extensions with CRXJS Vite plugin (true HMR, content-script HMR, zero-config MV3). Use when the user mentions CRXJS, `@crxjs/vite-plugin`, `npm create crxjs`, or wants Vite-native HMR in content scripts. Route E2E to chrome-for-testing-extensions.
---

# CRXJS Extension Development

CRXJS = Vite plugin for Chrome extensions. Zero config, true HMR (including
content scripts), auto-`web_accessible_resources`, Vite 8 support.

## CLI / scaffold (verified from `@crxjs/vite-plugin` npm README, 2.7.1)

```bash
npm create crxjs@latest    # scaffold (React/Vue/Svelte/TS/vanilla)
npm run dev                 # Vite dev server + Chrome auto-launch with HMR
npm run build               # production build → dist/ (standard Vite output)
```

> **`@latest` is required** — omitting it uses a stale cached version.

## Project anatomy

Standard Vite project + `vite.config.ts`:
```ts
// vite.config.ts
import { crx } from '@crxjs/vite-plugin';
export default defineConfig({
  plugins: [crx({ manifest: './manifest.json' })],
});
```
`manifest.json` sits at project root (CRXJS injects into Vite's pipeline).

## Build output

`npm run build` → `dist/` (standard Vite output dir). Pass `dist/` as
`--load-extension` to Chrome for Testing for real-browser E2E.

## HMR in content scripts

CRXJS's **unique value**: content scripts get real Vite HMR (no full reload).
CSS/JS changes update in-place on the page. This is **not** available in
Plasmo (full reload) or Extension.js (partial).

## E2E: route to chrome-for-testing-extensions

Same integration as WXT/Plasmo:
1. `npm run build` → `dist/`
2. `--load-extension=dist` + Chrome for Testing binary
3. CDP assertions via `cdplib.py`

For dev mode: CRXJS launches Chrome automatically via Vite plugin. To use
Chrome for Testing instead, set `process.env.CHROME_PATH` in the Vite config
or pass `--browser` flag.

## Gotchas
- **`@latest` must not be omitted** from `npm create crxjs` (npm caches stale
  versions otherwise).
- CRXJS is **Chrome-first**. Firefox support is partial (MV2 via
  `rollup-plugin`). For true multi-browser, use Extension.js or WXT.
- Content script HMR works on **CSS and JS** but not all state is preserved
  across HMR (storage state survives, runtime state may not).
- `web_accessible_resources` auto-generated — don't manually duplicate in
  `manifest.json`.

## Verified (real test run 2026-09-06)

- `npm run build` → `dist/` works as `--load-extension` path; 6/6 CDP assertions pass.
- **CRXJS 2.x has NO `manifest.json` at root** — it's `manifest.config.js`
  (`defineManifest({...})`) referenced from `vite.config.ts` `crx({ manifest })`.
- Built SW path is rewritten to **`service-worker-loader.js`** (module type) —
  read `manifest.json` `background.service_worker` from the BUILD OUTPUT and
  match that exact filename when finding the SW target. Substring matching
  "background" collides with stale Chrome processes from other frameworks.
- Content script matches default to `https://*/*` — change to `<all_urls>`
  to test on http://localhost.
- `vite-plugin-zip-pack` is included: `npm run build` also emits
  `release/crx-<name>-<version>.zip` (store-ready).

## Sources
- [@crxjs/vite-plugin](https://www.npmjs.com/package/@crxjs/vite-plugin) v2.7.1
- [crxjs.dev](https://crxjs.dev) — docs (llms.txt available)
- [crxjs/chrome-extension-tools](https://github.com/crxjs/chrome-extension-tools)
