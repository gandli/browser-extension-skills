"""chrome://extensions management-page check for all 6 builds — real CfT, DOM read + screenshot.

Env overrides (all optional; repo-relative defaults under ~/ext-e2e-test):
  CHROME_BIN  Chrome-for-Testing binary (default ~/ext-e2e-test/chrome/.../Google Chrome for Testing)
  MGMT_PORT   CDP port (default 9333)
  MGMT_HOME   harness home (default ~/ext-e2e-test); reports go to $MGMT_HOME/reports/mgmt

Exit code 1 if any build lacks exactly one enabled card with a Service Worker link.
"""
import base64, json, os, subprocess, time, urllib.request
import websocket

HOME = os.path.expanduser(os.environ.get("MGMT_HOME", "~/ext-e2e-test"))
CHROME = os.environ.get("CHROME_BIN") or os.path.join(
    HOME, "chrome/mac_arm-152.0.7977.82/chrome-mac-arm64/"
    "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing")
PORT = int(os.environ.get("MGMT_PORT", "9333"))
REPORTS = os.path.join(HOME, "reports", "mgmt")
os.makedirs(REPORTS, exist_ok=True)

DEFAULT_BUILDS = [
    ("native", os.path.join(HOME, "extension")),
    ("wxt", "~/wxt-demo/.output/chrome-mv3"),
    ("plasmo", "~/plasmo-demo/build/chrome-mv3-prod"),
    ("crxjs", "~/crxjs-demo/dist"),
    ("extensionjs", "~/extjs-demo/dist/chromium"),
    ("bedframe", "~/bedframe-demo/dist"),
]
BUILDS = DEFAULT_BUILDS

CARDS_JS = """(() => {
  const mgr = document.querySelector('extensions-manager');
  if (!mgr || !mgr.shadowRoot) return [];
  const list = mgr.shadowRoot.querySelector('extensions-item-list');
  if (!list || !list.shadowRoot) return [];
  return [...list.shadowRoot.querySelectorAll('extensions-item')].map(it => {
    const d = it.shadowRoot;
    const tog = d.querySelector('cr-toggle');
    const swA = [...d.querySelectorAll('#inspect-views a')]
      .find(a => (a.textContent + a.getAttribute('href')).toLowerCase().includes('service worker'));
    return { id: it.id,
      name: (d.querySelector('#name')?.textContent || '').trim(),
      version: (d.querySelector('#version')?.textContent || '').trim(),
      enabled: tog ? tog.checked : null,
      hasSW: !!swA };
  });
})()"""

DEV_MODE_JS = """(() => {
  const tb = document.querySelector('extensions-manager')
    ?.shadowRoot?.querySelector('extensions-toolbar');
  const t = tb?.shadowRoot?.querySelector('#devMode');
  if (t && !t.checked) t.click();
  return !!t;
})()"""


class CDP:
    def __init__(self, ws):
        self.ws = websocket.create_connection(ws, timeout=15)
        self._id = 0

    def send(self, method, params=None, session_id=None):
        self._id += 1
        msg = {"id": self._id, "method": method, "params": params or {}}
        if session_id:
            msg["sessionId"] = session_id
        self.ws.send(json.dumps(msg))
        deadline = time.time() + 15
        while time.time() < deadline:
            data = json.loads(self.ws.recv())
            if data.get("id") == self._id:
                if "error" in data:
                    raise RuntimeError(f"{method}: {data['error']}")
                return data.get("result", {})
        raise TimeoutError(method)


def shot(cdp, sid, path):
    data = cdp.send("Page.captureScreenshot", {"format": "png"}, session_id=sid)["data"]
    with open(path, "wb") as f:
        f.write(base64.b64decode(data))


rows, failures = [], []
for name, path in BUILDS:
    path = os.path.expanduser(path)
    assert os.path.isdir(path), f"missing build: {path}"
    subprocess.run(["pkill", "-9", "-f", "Chrome for Testing"], stderr=subprocess.DEVNULL)
    subprocess.run(["rm", "-rf", "/tmp/mgmt-cft"], stderr=subprocess.DEVNULL)
    time.sleep(2)
    proc = subprocess.Popen([
        CHROME, f"--remote-debugging-port={PORT}", "--no-first-run",
        "--user-data-dir=/tmp/mgmt-cft", "--remote-allow-origins=*",
        f"--load-extension={path}",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ws = None
        for _ in range(40):
            try:
                with urllib.request.urlopen(f"http://localhost:{PORT}/json/version") as r:
                    ws = json.load(r)["webSocketDebuggerUrl"]
                break
            except Exception:
                time.sleep(0.5)
        if ws is None:
            raise TimeoutError(f"Chrome did not expose CDP on port {PORT} within 20s")
        cdp = CDP(ws)
        tab = cdp.send("Target.createTarget", {"url": "chrome://extensions/"})["targetId"]
        sid = cdp.send("Target.attachToTarget", {"targetId": tab, "flatten": True})["sessionId"]
        cdp.send("Page.enable", session_id=sid)
        time.sleep(1)
        try:
            cdp.send("Runtime.evaluate", {"expression": DEV_MODE_JS, "returnByValue": True}, session_id=sid)
        except Exception:
            pass
        items = []
        for _ in range(40):  # WebUI renders async — poll up to ~16s
            res = cdp.send("Runtime.evaluate", {"expression": CARDS_JS, "returnByValue": True}, session_id=sid)
            items = res.get("result", {}).get("value", [])
            if items:
                break
            time.sleep(0.4)
        shot(cdp, sid, f"{REPORTS}/{name}.png")
        # assert: exactly one card, fully populated, enabled, with a SW inspect link
        errs = []
        if len(items) != 1:
            errs.append(f"expected 1 card, got {len(items)}")
        for it in items:
            if not (it["id"] and it["name"] and it["version"]):
                errs.append(f"empty card field: {it}")
            if it["enabled"] is not True:
                errs.append(f"{it['name']}: enabled={it['enabled']}")
            if not it["hasSW"]:
                errs.append(f"{it['name']}: no Service Worker inspect link")
        rows.append({"build": name, "items": items, "ok": not errs})
        if errs:
            failures.append(f"{name}: " + "; ".join(errs))
        print(f"[{name}] {'OK' if not errs else 'FAIL'} — {json.dumps(items, ensure_ascii=False)}")
    finally:
        proc.terminate()
        time.sleep(1)

with open(f"{REPORTS}/result.json", "w") as f:
    json.dump(rows, f, indent=2)
if failures:
    print("\nFAILURES:\n" + "\n".join(failures))
    raise SystemExit(1)
print(f"\ndone: {len(rows)}/{len(BUILDS)} builds verified on chrome://extensions")
