---
name: plasmo-extension-dev
description: Build Chrome/Firefox extensions with Plasmo SDK (React/TS-first, declarative manifests, CSUI). Use when the user mentions Plasmo, `src/`-based extension structure, `@plasmohq/storage`, content-script UI components, or Plasmo's declarative `package.json` manifest. Route E2E testing to chrome-for-testing-extensions.
---

# Plasmo Extension Development

Plasmo = Next.js-style SDK for browser extensions. Declarative `package.json`
manifest (no `manifest.json`), React/TS first-class, `@plasmohq/storage` +
`@plasmohq/messaging` for cross-context APIs, content-script UI (CSUI)
mounting as React components.

## Project anatomy (verified from `plasmo` npm README)

```
src/
  popup.tsx                # popup entry (React component, auto-mounted)
  options.tsx              # options page
  background.ts            # service worker
  content.ts               # content script (raw)
  some-site.content.tsx    # CSUI: mounts React component in-page
package.json
  "manifest": {            # declarative — Plasmo generates manifest.json at build
    "permissions": ["storage"],
    "host_permissions": ["https://*/*"]
  }
```

## Commands (verified from README + docs.plasmo.com/framework/quickstart)

```bash
pnpm create plasmo my-ext   # scaffold (React+TS default)
pnpm dev                     # dev mode with HMR + auto-reload
pnpm build --target=chrome-mv3   # → build/chrome-mv3-prod/
pnpm build --target=firefox-mv2  # → build/firefox-mv2-prod/
```

Build output: **`build/<browser>-mv<ver>-prod/`** — pass directly as
`--load-extension` to Chrome for Testing. The E2E path is identical to WXT.

## Testing layers

### Unit: Vitest + `@plasmohq/mock`
Plasmo mocks `chrome.*` APIs in unit tests (`@plasmohq/mock` package).  
Route to chrome-for-testing-extensions for real-browser assertions.

### E2E: `build/chrome-mv3-prod` → Chrome for Testing
Same integration pattern as WXT:
1. `pnpm build --target=chrome-mv3`
2. `--load-extension=build/chrome-mv3-prod` + Chrome for Testing binary
3. CDP assertions via `cdplib.py` (popup, storage, content script, SW)

Content-script UI (CSUI) is testable the same way: navigate to matched page,
check injected DOM node, interact.

## Gotchas (from verified docs)
- **`package.json` is the manifest** — don't create a separate `manifest.json`
  at project root (Plasmo ignores it, generates from `package.json` `manifest` key).
- CSUI mounts are **React components** — they live in DOM with a Plasmo-managed
  shadow root. Query `#plasmo-shadow-container` or the root React mount.
- `@plasmohq/storage` uses `chrome.storage.local` under the hood; in E2E,
  assert via `chrome.storage.local.get()` in SW context (same as WXT raw test).
- Content scripts in Plasmo run in a shadow DOM to avoid CSS conflicts.

## Verified (real test run 2026-09-06)

- `plasmo build` → `build/chrome-mv3-prod/` works as `--load-extension` path.
- **Broken name/icons crash Chrome silently**: `manifest.name: ""` (empty
  string, the default when no name set in package.json `manifest`) plus
  malformed icon PNGs → Chrome for Testing process starts but the CDP
  endpoint NEVER opens, no error anywhere. Fix: set a real `name` and use
  valid PNGs in `assets/`.
- **SW path**: Plasmo bundles background to `static/background/index.js` —
  match `/static/background/` when finding the SW target, NOT `/background`
  (which also matches Chrome component-extension SWs like thunk.js).
- **CSUI shadow root**: content-script UI mounts inside a `<plasmo-csui>`
  custom element with a shadow root — `document.getElementById` fails; query
  `document.querySelector('plasmo-csui').shadowRoot` instead.
- 5/5 real-browser assertions pass (SW, storage, CSUI banner, React popup).

## Sources
- [plasmo](https://www.npmjs.com/package/plasmo) v0.90.5 — npm README
- [docs.plasmo.com/framework/quickstart](https://docs.plasmo.com/framework/quickstart)
