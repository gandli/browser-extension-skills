---
name: chrome-for-testing-extensions
description: Load unpacked extension over CDP via Chrome for Testing.
---

# Chrome extension E2E testing over raw CDP

Proven harness (23/23 checks, e2e_test.py + update_test.py + run_all.py). Reusable CDP client installed as this skill's `scripts/cdplib.py` (~150 lines, websocket-client only) — copy it into new projects.

## Why not stable Chrome
Chrome 137+ stable **silently ignores** `--load-extension` (no error, extension never loads). Use Chrome for Testing — same stable codebase, automation build, flag works:
```bash
npx -y @puppeteer/browsers install chrome@stable
# binary: chrome/mac_arm-<ver>/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing
# CI: find chrome -name "Google Chrome for Testing" -type f | head -1  (don't hardcode version)
```

## Launch
```python
subprocess.Popen([CHROME,
    "--user-data-dir=/fresh/profile",   # shutil.rmtree before each run for true first-install
    "--remote-debugging-port=9333",
    "--load-extension=/path/to/extension",
    "--no-first-run", "--no-default-browser-check",
    "--remote-allow-origins=*",          # REQUIRED: else WS handshake 403
    "about:blank"])
```
Poll `http://127.0.0.1:9333/json/version` for `webSocketDebuggerUrl`. Cleanup between runs: `pkill -f "user-data-dir=<profile>"`.

## CDP pitfalls (each cost a debug cycle)
1. **awaitPromise + arrow function**: uncalled `(async () => ...)` is a function object → resolves to `{}`, NO error. Always IIFE: `"((async () => JSON.stringify(await chrome.storage.local.get('notes')))())"`.
2. **SW target filtering**: `Target.getTargets` lists Chrome component-extension workers (`nkeimhog.../thunk.js`). Filter by your ext ID in URL, else you evaluate in the wrong context and storage reads return `{}`.
3. **SW registers async**: after launch, retry-loop (10×0.5s) for the `service_worker` target.
4. **Console events land on the BROWSER websocket** (flatten sessions): collect `Runtime.consoleAPICalled` from shared `cdp.events`, filter by `sessionId`; event shape `{"method":..., "params":...}`.
5. **Extension ID**: derives from unpacked path; read live from chrome://extensions shadow DOM (`extensions-manager` → `extensions-item-list` → `extensions-item.id`), never hardcode.
6. **Content-script assertions**: match stable marker substrings ("content script active"), not host/version text that repeats across pages.

## Popup testing
Open `chrome-extension://<id>/popup.html` via `Target.createTarget` — identical DOM/JS context to the real toolbar popup (chrome.action.openPopup not CDP-exposed). Drive with `Runtime.evaluate` (set input `.value`, `.click()` buttons), read back list/status/storage. Persistence check = close target, reopen, assert data still rendered.

## Upgrade flow (version bump → reload → update semantics)
- Fresh-profile launch fires `onInstalled reason=install` on EVERY browser start — update semantics need IN-SESSION reload.
- Reload button: `extensions-item` shadow DOM `#dev-reload-button` (NOT `#reloadButton`). Click via evaluate, wait ~3s, re-read chrome://extensions.
- Assert: version updated, `reason=update` recorded (have background.js write `details.reason` into storage as a test hook), data survives, restart Chrome → version+data persist.

## Screenshots & reports
`Page.captureScreenshot {format:"png"}` → base64 (needs `Page.enable`). Wire into the assert helper: on FAIL, auto-save PNG to `reports/artifacts/<slug>.png`. Runner aggregates suites via subprocess, parses `[PASS]/[FAIL]` lines, writes `reports/result.json`, exit code for CI. Fixture site: stdlib `HTTPServer` + `functools.partial(handler, directory=...)`, `allow_reuse_address=True`, daemon thread.

## MV3 test hooks (fixture design)
background.js: `onInstalled` → `storage.local.set({lastInstallReason})`; `onMessage` ping → pong + `console.log` (proves SW alive via CDP event capture). popup.js: expose `window.__ping = () => chrome.runtime.sendMessage({type:'ping'})` for round-trip tests.

## Verified
Chrome for Testing 152.0.7977.82 macOS arm64, Python 3.11, websocket-client 1.9.2. 23/23: load, content script ×2 pages, popup save/persist/reopen, SW ping + console capture, SW storage read, upgrade reload, restart persistence, screenshots.
