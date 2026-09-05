"""chrome://extensions management page check for all 6 builds — real CfT, DOM read + screenshot."""
import base64, glob, json, os, subprocess, time, urllib.request
import websocket

CHROME = os.path.expanduser(
    "~/ext-e2e-test/chrome/mac_arm-152.0.7977.82/chrome-mac-arm64/"
    "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
)
PORT = 9333
REPORTS = os.path.expanduser("~/ext-e2e-test/reports/mgmt")
os.makedirs(REPORTS, exist_ok=True)

BUILDS = [
    ("native", "~/ext-e2e-test/extension"),
    ("wxt", "/Users/user/wxt-demo/.output/chrome-mv3"),
    ("plasmo", "/Users/user/plasmo-demo/build/chrome-mv3-prod"),
    ("crxjs", "/Users/user/crxjs-demo/dist"),
    ("extensionjs", "/Users/user/extjs-demo/dist/chromium"),
    ("bedframe", "/Users/user/bedframe-demo/dist"),
]

ITEMS_JS = """(() => {
  const mgr = document.querySelector('extensions-manager');
  if (!mgr || !mgr.shadowRoot) return [];
  const list = mgr.shadowRoot.querySelector('extensions-item-list');
  if (!list || !list.shadowRoot) return [];
  return [...list.shadowRoot.querySelectorAll('extensions-item')].map(it => {
    const d = it.shadowRoot;
    const tog = d.querySelector('#enableToggle') || d.querySelector('cr-toggle');
    return {
      id: it.id,
      name: (d.querySelector('#name')?.textContent || '').trim(),
      version: (d.querySelector('#version')?.textContent || '').trim(),
      enabled: tog ? tog.checked : null,
      swLink: !!d.querySelector('#inspect-views'),
    };
  };
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


rows = []
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
        for _ in range(40):
            res = cdp.send("Runtime.evaluate", {"expression":
                "(() => { const mgr = document.querySelector('extensions-manager');"
                " if (!mgr || !mgr.shadowRoot) return [];"
                " const list = mgr.shadowRoot.querySelector('extensions-item-list');"
                " if (!list || !list.shadowRoot) return [];"
                " return [...list.shadowRoot.querySelectorAll('extensions-item')].map(it => {"
                "   const d = it.shadowRoot; const tog = d.querySelector('cr-toggle');"
                "   return { id: it.id,"
                "     name: (d.querySelector('#name')?.textContent || '').trim(),"
                "     version: (d.querySelector('#version')?.textContent || '').trim(),"
                "     enabled: tog ? tog.checked : null,"
                "     swLink: !!d.querySelector('#inspect-views') };"
                " }); })()", "returnByValue": True}, session_id=sid)
            items = res.get("result", {}).get("value", [])
            if items:
                break
            time.sleep(0.4)
        shot(cdp, sid, f"{REPORTS}/{name}.png")
        for it in items:
            rows.append({"build": name, **it})
        print(f"[{name}] items={json.dumps(items, ensure_ascii=False)}")
    finally:
        proc.terminate()
        time.sleep(1)

with open(f"{REPORTS}/result.json", "w") as f:
    json.dump(rows, f, indent=2)
print(f"\ndone: {len(rows)} extension cards, screenshots in {REPORTS}")
