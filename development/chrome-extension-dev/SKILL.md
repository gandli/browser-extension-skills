---
name: chrome-extension-dev
description: Build + real-browser-test Chrome MV3 extensions end to end.
---

# Chrome Extension Development — build & test (one skill to rule them)

Companion skills (read first for specifics):
- `chrome-extensions` — Google Modern Web Guidance: 20 mandatory MV3 rules + 25 reference files (permissions, storage, message-passing, service-worker, side-panel, webstore/CHROMEWEBSTORE.md). Load it for ANY `manifest.json` / API / publishing question.
- `chrome-for-testing-extensions` — raw CDP harness to load + drive unpacked extensions (Chrome for Testing, --load-extension, SW targeting, screenshots).
- `chrome-devtools` + siblings (a11y, cookie, lcp, memory-leak) — debug/audit a *running* page/extension.

## Pick the right tool
| Task | Use |
|------|-----|
| Write manifest.json / use chrome.* API | `chrome-extensions` |
| Audit live page (a11y, perf, cookies) | `chrome-devtools`, `a11y-debugging`, `cookie-debugging`, `debug-optimize-lcp`, `memory-leak-debugging` |
| Load unpacked + drive over CDP + assert | `chrome-for-testing-extensions` |
| Full build+test loop (this skill) | below |

## Minimal MV3 anatomy (reference fixture: this repo's published harness)
```json
// manifest.json
{ "manifest_version": 3,
  "name": "X", "version": "1.0.0",
  "permissions": ["storage"],
  "action": { "default_popup": "popup.html" },
  "background": { "service_worker": "background.js" },
  "content_scripts": [{ "matches": ["<all_urls>"], "js": ["content.js"], "run_at": "document_idle" }] }
```
- popup.js: `chrome.action` popup. Use `async/await`. DOM via addEventListener.
- background.js: service worker — NO module-level mutable state (dies ~30s idle); persist to `chrome.storage`. Use `chrome.alarms` not `setTimeout`.
- content.js: runs in page DOM; communicate with SW via `chrome.runtime.sendMessage` (return `true` in listener to keep channel open).

## MV3 gotchas
All covered by `chrome-extensions` mandatory rules 1-20 (CSP/sandbox, tabs permission, `"action":{}`, windows API, side-panel trigger, activeTab, offscreen, icon files). Read that skill before writing manifest/API code — no restatement here.

## Test loop (mandatory before declaring done)
Use `chrome-for-testing-extensions`. Real browser, real load, real assertions. Never claim an extension works without running it:
```bash
# 1. install Chrome for Testing (stable ignores --load-extension since v137 — see testing skill)
npx -y @puppeteer/browsers install chrome@stable
# 2. launch + --load-extension + --remote-allow-origins=*
# 3. drive over CDP (see cdplib.py / chrome-for-testing-extensions)
```
Assert matrix (each a real failure we hit): extension listed & enabled in chrome://extensions; MV3 SW target registered; content script injected on live pages; popup save→storage→reopen persistence; popup↔SW `sendMessage` round-trip; SW console captured via CDP; version bump + `#dev-reload-button` reload → `onInstalled reason=update` + data survives + survives browser restart.

## Publishing
Maintain `CHROMEWEBSTORE.md` (see `chrome-extensions` Part 2): every permission needs a specific plain-English justification; never "needed to work". Pre-publish: review-checklist.md, 1 screenshot 1280x800, ZIP excludes .git/node_modules/.env. Respond to rejections by updating the file.

## Verified
macOS Sequoia, Chrome for Testing 152.0.7977.82 arm64, Python 3.11, websocket-client 1.9.2. Reference harness 23/23 checks (e2e, upgrade flow, run_all).
