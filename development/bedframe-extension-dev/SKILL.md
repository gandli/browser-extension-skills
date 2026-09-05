---
name: bedframe-extension-dev
description: Build cross-browser extensions with Bedframe (Vite-based CLI with per-browser manifest deltas). Use when the user mentions Bedframe, `@bedframe/cli`, `bedframe dev`, `bedframe build`, or wants manifest-delta-based multi-browser builds. Route E2E to chrome-for-testing-extensions.
---

# Bedframe Extension Development

Bedframe = Vite-based CLI for cross-browser extensions with per-browser
manifest deltas. Scaffolds projects with framework/language/tooling choices
and handles versioning + store publishing.

## CLI (verified from `@bedframe/cli` + `nyaggah/bedframe` GitHub README)

```bash
npm install -g @bedframe/cli   # or: pnpm add -g @bedframe/cli / yarn global add @bedframe/cli / bun add -g @bedframe/cli
bedframe make                   # scaffold: interactive prompts for browser, framework, language, tooling
bedframe dev                    # dev mode (Vite HMR + browser launch)
bedframe build                  # production build
bedframe zip                    # store-ready zip
bedframe version                # bump version
bedframe publish                # submit to store
```

## Project anatomy

Bedframe generates a Vite project with:
- `manifest.json` base + per-browser delta files (e.g., `manifest.chrome.json`,
  `manifest.firefox.json`) — the **unique feature**: declarative per-browser
  overrides without maintaining separate manifests.
- `@bedframe/core` for Vite plugin helpers and shared types.
- Standard Vite output: `dist/` (Chrome) or browser-specific output dirs.

## Build output

`bedframe build` → `dist/` (or browser-specific, depending on config).  
Pass `dist/` as `--load-extension` to Chrome for Testing for real-browser E2E.

## Multi-browser manifest deltas

Bedframe's differentiator: you write one `manifest.json` base, then add
`manifest.chrome.json` / `manifest.firefox.json` with **only the deltas**
(extra permissions, different background config, etc.). Bedframe merges them
at build time.

## E2E: route to chrome-for-testing-extensions

Same integration pattern as WXT/Plasmo: `bedframe build` → `dist/` is the
`--load-extension` path; CDP assertions via `cdplib.py`.

## Gotchas
- Bedframe is **Vite-based** (not webpack) — the Vite plugin ecosystem works.
- `bedframe make` is interactive — CI needs pre-configured project files
  (use `create-bedframe` for non-interactive scaffolding).
- Manifest deltas are **merge-based** — be careful not to accidentally
  override required Chrome-specific fields.
- Smaller ecosystem than WXT/Plasmo — fewer community examples.

## Sources
- [@bedframe/cli](https://www.npmjs.com/package/@bedframe/cli)
- [@bedframe/core](https://www.npmjs.com/package/@bedframe/core)
- [nyaggah/bedframe](https://github.com/nyaggah/bedframe) — GitHub
- [bedframe.dev](https://bedframe.dev) — docs
