---
name: extension-js-extension-dev
description: Build Chrome/Edge/Firefox/Safari extensions with Extension.js (zero-config CLI, multi-framework HMR). Use when the user mentions `extension` CLI, `npx extension create`, `--browser=chrome`, or wants zero-config cross-browser builds. Route E2E to chrome-for-testing-extensions.
---

# Extension.js Development

Extension.js = cross-browser CLI with zero config. One manifest.json,
auto-adapted output per browser, HMR for content scripts + background.

## CLI (verified from `extension` npm README, 4.1.12)

```bash
npx extension@latest create my-extension   # scaffold (React/Vue/Svelte/TS/vanilla)
cd my-extension
npm run dev                                 # dev mode: HMR + auto browser launch
npm run dev -- --browser=firefox           # target a different browser
extension build --zip                       # production: store-ready zip
```

`extension dev` auto-launches the browser with the extension loaded.  
Target browser: `--browser=chrome|edge|firefox|safari` (defaults to Chrome).

## Build output

`extension build --zip` produces a store-ready `.zip` in the project root.
For the CDP harness: pass `--load-extension` with the **unpacked output dir**
(runs the same `manifest.json` used by the dev server; dist location varies
by template — typically `dist/` or the scaffold's default build output).

## Multi-browser manifest compilation

Extension.js reads one `manifest.json` and emits browser-specific variants:
- Chrome/Edge: `chrome-extension://` service workers
- Firefox: `moz-extension://`, background scripts (MV3 service worker adapter)
- Safari: Xcode project scaffolding (`extension build` for macOS/iOS)

This is the **strongest differentiator** vs WXT (which is Chromium-first).
Route browser-specific questions to `chrome-extensions` (MV3 rules) or the
Extension.js docs index: https://extension.js.org/llms.txt

## E2E: route to chrome-for-testing-extensions

Same pattern as the verified skills: build output is the `--load-extension` path.

## Gotchas
- CLI launches its own browser — to use **Chrome for Testing**, set the
  `CHROME_PATH` or equivalent env var (varies by template; check
  `extension dev --help`).
- `--browser=safari` generates an Xcode project, not a direct load.
  Use Chrome/Edge/Firefox for the CDP-based E2E workflow.
- Output location is template-dependent (not always `.output/` like WXT).
  Read the build log to find the unpacked extension directory.

## Verified (real test run 2026-09-06)

- `npx extension@latest create <dir> --template javascript` scaffolds a
  side-panel app; `npm run build` → **`dist/chromium/`** (browser-suffixed).
- 6/6 CDP assertions pass on the build output.
- **Template manifest lacks `storage` permission by default** — add it to
  `src/manifest.json` `chromium:permissions` or storage asserts fail with
  `Cannot read properties of undefined (reading 'local')`.
- Manifest uses `chromium:` / `firefox:` prefixed keys (one file, both
  browsers) — `chromium:manifest_version`, `firefox:manifest_version`,
  `chromium:action`, `firefox:browser_action`, etc.
- Built SW: `background/service_worker.js` (read from built manifest).
- Content script renders into a **shadow DOM** at `[data-extension-root]` —
  query `root.shadowRoot.getElementById(...)` (same pattern as Plasmo CSUI).
- Side panel page loadable as `chrome-extension://<id>/sidebar/index.html`.

## Sources
- [extension](https://www.npmjs.com/package/extension) v4.1.12 — npm README
- [extension.js.org](https://extension.js.org) — docs + templates index
- llms.txt: https://extension.js.org/llms.txt (118 pages)
