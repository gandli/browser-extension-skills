# Browser Extension Skills

Agent skills for building and testing Chrome browser extensions — curated for
Hermes-style coding agents (SKILL.md format, works with any agent that reads
markdown skills).

## Layout

```
development/
  chrome-extensions/            Google Modern Web Guidance: 20 mandatory MV3
                                rules + 18 API references + CWS publishing
                                (CHROMEWEBSTORE.md template, review checklist)
  chrome-extension-dev/         Hub skill: full build+test loop, routes to the
                                others by task
testing/
  chrome-for-testing-extensions/  Real-browser E2E harness: load unpacked
                                extensions via CDP (Chrome for Testing),
                                drive/assert/screenshot; includes scripts/cdplib.py
                                (~150-line websocket-client CDP client)
debugging/                     chrome-devtools-mcp skill family (a11y, cookies,
                               LCP, memory leaks, MCP troubleshooting)
```

## Quick start

See `testing/chrome-for-testing-extensions/SKILL.md` for Chrome for Testing
install, launch flags, and CDP pitfalls (Chrome 137+ ignores `--load-extension`;
`awaitPromise` + bare arrow = `{}`; `Target.getTargets` includes component
extension SWs — filter by ext_id; `onInstalled reason=update` only on
in-session `#dev-reload-button` reload).

See `development/chrome-extension-dev/SKILL.md` for the build+test loop.

## Sources

- `chrome-extensions` — vendored from Google's `modern-web-guidance` npm package
  (v0.0.185, Apache-2.0, Copyright Google LLC)
- `chrome-*` debugging skills — vendored from
  [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp)
  (Apache-2.0)
- `chrome-extension-dev`, `chrome-for-testing-extensions` — original, built from
  a verified end-to-end test session

## License

Original skills: MIT. Vendored third-party skills remain under their Apache-2.0
license (NOTICE preserved in their directories).
