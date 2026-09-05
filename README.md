<p align="center">
  <img src="./assets/readme/hero.svg" width="100%"
       alt="Browser Extension Skills — agent skills for building, real-browser testing, and debugging Chrome MV3 extensions">
</p>

# Browser Extension Skills

15 agent skills for building, real-browser testing, and debugging Chrome MV3
extensions — in the open [Agent Skills](https://agentskills.io) format
(`SKILL.md`), installable into **78+ coding agents**. Vanilla manifest or a
framework — **WXT, Plasmo, Extension.js, CRXJS, Bedframe** all covered.

Born from verified sessions: the harness runs **23/23 real-browser E2E
checks** on a raw MV3 extension and **6/6** on every framework build
(WXT, Plasmo, CRXJS, Extension.js, Bedframe) — plus chrome://extensions
management-page checks on all six. All against live Chrome over CDP.

## Install

One command — the [skills CLI](https://github.com/vercel-labs/skills) detects
your installed agents (Claude Code, Codex, Cursor, OpenCode, Hermes, Windsurf,
and 70+ more) and wires the skills in:

```bash
npx skills add gandli/browser-extension-skills
```

Useful variants:

```bash
npx skills add gandli/browser-extension-skills --list            # preview all 10 skills
npx skills add gandli/browser-extension-skills -g                # global (~/<agent>/skills/) instead of project
npx skills add gandli/browser-extension-skills -a claude-code    # target one agent
npx skills add gandli/browser-extension-skills --skill chrome-extension-dev -y   # one skill, non-interactive
npx skills use gandli/browser-extension-skills@chrome-for-testing-extensions --agent claude-code
                                                                 # use once, no install
```

**Manual install** (any agent, no Node): copy skill dirs into the agent's
skills folder — Claude Code `~/.claude/skills/`, Hermes `~/.hermes/skills/`,
Codex `~/.codex/skills/`, or per-project `.claude/skills/` etc:

```bash
git clone https://github.com/gandli/browser-extension-skills
cp -r browser-extension-skills/development/* browser-extension-skills/testing/* \
      browser-extension-skills/debugging/* ~/.claude/skills/
```

## What's Inside

<p align="center">
  <img src="./assets/readme/architecture.svg" width="100%"
       alt="Three-layer architecture: development, testing, debugging — with skill names listed in each column">
</p>

| Layer | Skill | What it does |
|-------|-------|-------------|
| **development/** | `chrome-extensions` | Google Modern Web Guidance: 20 mandatory MV3 rules + 18 API references + Chrome Web Store publishing (CHROMEWEBSTORE.md template, review checklist) |
| | `chrome-extension-dev` | Hub skill — routes by task, ties the build+test loop together |
| | `wxt-extension-dev` | WXT framework (Vite-powered MV3): `npx wxt` auto-launch + HMR, Vitest + fake-browser unit tests, E2E routed to the CDP harness. **Verified 6/6** |
| | `plasmo-extension-dev` | Plasmo SDK (React/TS, declarative package.json manifest, CSUI shadow-root content UI). **Verified 6/6** |
| | `extension-js-extension-dev` | Extension.js (zero-config CLI, Chrome/Edge/Firefox/Safari, multi-framework HMR). **Verified 6/6** |
| | `crxjs-extension-dev` | CRXJS (`@crxjs/vite-plugin`, true content-script HMR, Chrome-first MV3). **Verified 6/6** |
| | `bedframe-extension-dev` | Bedframe (Vite CLI, per-browser manifest deltas, zip/publish workflow). **Verified 6/6** |
| **testing/** | `chrome-for-testing-extensions` | Real-browser E2E harness: load unpacked extensions via CDP, drive/assert/screenshot. Ships `scripts/cdplib.py` (174 lines, websocket-client only) |
| **debugging/** | `chrome-devtools` · `chrome-devtools-cli` | Live page/extension debugging via Chrome DevTools MCP |
| | `a11y-debugging` · `cookie-debugging` · `debug-optimize-lcp` · `memory-leak-debugging` · `troubleshooting` | Specialized audits: accessibility, auth/cookies, Core Web Vitals, heap leaks, MCP setup |

## Use

Skills load automatically when your agent sees a matching task. Examples:

```text
Build a Chrome extension that highlights search terms and saves them locally.
   → chrome-extension-dev routes to MV3 rules; agent writes manifest V3,
     service worker, popup, content script — without violating the 20 rules.

Test the extension in a real browser.
   → chrome-for-testing-extensions: installs Chrome for Testing, launches with
     --load-extension, drives CDP, asserts popup/storage/service-worker behavior.

Prepare this extension for the Chrome Web Store.
   → chrome-extensions Part 2: generates CHROMEWEBSTORE.md with a specific
     plain-English justification per permission.

Scaffold the extension with the WXT framework instead of a hand-written manifest.
   → wxt-extension-dev: entrypoints/ conventions, `wxt dev` auto-launch,
     Vitest unit tests; E2E still routes to the real-browser harness.

Build it with Plasmo, Extension.js, CRXJS, or Bedframe instead.
   → plasmo-extension-dev / extension-js-extension-dev / crxjs-extension-dev /
     bedframe-extension-dev — same real-browser E2E for every framework.

Why is my extension's storage.local returning {} in tests?
   → the pitfalls below, immediately.
```

## Hard-Won Pitfalls

Every row cost real debugging time in the 23/23 session.

| Trap | What happens | Fix |
|------|-------------|-----|
| Chrome 137+ ignores `--load-extension` | Extension silently never loads, no error | Use **Chrome for Testing**: `npx @puppeteer/browsers install chrome@stable` |
| `awaitPromise` + bare arrow function | `Runtime.evaluate` resolves to `{}` (the function object), no error | Always IIFE: `((async () => ...)())` |
| `Target.getTargets` lists component SWs | You evaluate inside a Chrome-internal extension; storage reads `{}` | Filter service workers by your extension ID |
| `onInstalled reason=update` never fires | Fresh-profile launch = `install` every time | In-session reload: click `#dev-reload-button` in chrome://extensions shadow DOM |
| Toolbar popup can't be opened via CDP | `chrome.action.openPopup` is not exposed | `Target.createTarget` → `chrome-extension://<id>/popup.html` (identical DOM/JS context) |

## Sources & License

| Skill | Origin | License |
|-------|--------|---------|
| `chrome-extensions` | Vendored from Google's [`modern-web-guidance`](https://www.npmjs.com/package/modern-web-guidance) npm package (v0.0.185) | Apache-2.0 (NOTICE preserved) |
| `debugging/*` | Vendored from [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) | Apache-2.0 (NOTICE preserved) |
| `chrome-extension-dev`, `chrome-for-testing-extensions`, `wxt-extension-dev`, `plasmo-extension-dev`, `extension-js-extension-dev`, `crxjs-extension-dev`, `bedframe-extension-dev` | Original — built from the verified E2E sessions (native 23/23, WXT/Plasmo/CRXJS/Extension.js/Bedframe all 5–6/6 real-browser CDP) | MIT |
