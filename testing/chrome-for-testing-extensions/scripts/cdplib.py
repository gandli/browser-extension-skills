"""Minimal CDP driver over websocket-client. Chrome DevTools Protocol client.

Proven on Chrome for Testing 152 (extension E2E: 23/23 checks).
Usage: see SKILL.md. Key helpers: CDPSession, attach_target, get_extension_targets, screenshot.
"""
import json
import time
import urllib.request

import websocket


def browser_ws_url(port=9333, timeout_poll=20):
    """Poll /json/version until Chrome exposes the browser websocket."""
    for _ in range(timeout_poll):
        time.sleep(0.5)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2) as r:
                return json.loads(r.read().decode())["webSocketDebuggerUrl"]
        except Exception:
            continue
    raise RuntimeError("chrome CDP endpoint never came up")


class CDPSession:
    """One websocket connection to the browser endpoint; multiplexes target sessions (flatten)."""

    def __init__(self, ws_url, timeout=15):
        self.ws = websocket.create_connection(ws_url, timeout=timeout)
        self._id = 0
        self.events = []  # shared across sessions; filter by sessionId

    def send(self, method, params=None, session_id=None):
        self._id += 1
        mid = self._id
        msg = {"id": mid, "method": method, "params": params or {}}
        if session_id:
            msg["sessionId"] = session_id
        self.ws.send(json.dumps(msg))
        deadline = time.time() + 15
        while time.time() < deadline:
            data = json.loads(self.ws.recv())
            if "id" in data:
                if data["id"] == mid:
                    if "error" in data:
                        raise RuntimeError(f"{method} error: {data['error']}")
                    return data.get("result", {})
            else:
                self.events.append(data)
        raise TimeoutError(f"{method} timed out")

    def drain_events(self, seconds=0.5):
        """Collect async events for `seconds` into self.events."""
        self.ws.settimeout(seconds)
        try:
            while True:
                data = json.loads(self.ws.recv())
                if "id" in data:
                    pass  # late response; ignore
                else:
                    self.events.append(data)
        except websocket.WebSocketTimeoutException:
            pass
        finally:
            self.ws.settimeout(15)
        return self.events

    def console_logs(self, session_id, needle):
        """True if a Runtime.consoleAPICalled event from session_id contains needle."""
        for e in self.events:
            if (e.get("method") == "Runtime.consoleAPICalled"
                    and e.get("sessionId") == session_id
                    and needle in json.dumps(e.get("params", {}))):
                return True
        return False

    def attach(self, target_id):
        res = self.send("Target.attachToTarget", {"targetId": target_id, "flatten": True})
        return res["sessionId"]


class Target:
    """Handle for one attached page/worker."""

    def __init__(self, cdp, target_id, session_id):
        self.cdp = cdp
        self.target_id = target_id
        self.session_id = session_id

    def send(self, method, params=None):
        return self.cdp.send(method, params, session_id=self.session_id)

    def evaluate(self, expression, await_promise=False):
        """PITFALL: with await_promise, expression must be an IIFE that RETURNS a
        promise — a bare arrow function resolves to the function object ({})."""
        res = self.send("Runtime.evaluate", {
            "expression": expression, "returnByValue": True, "awaitPromise": await_promise})
        if "exceptionDetails" in res:
            det = res["exceptionDetails"]
            raise RuntimeError(f"evaluate failed: {det.get('exception', {}).get('description', det)}")
        return res.get("result", {}).get("value")

    def navigate(self, url, wait_seconds=3):
        self.send("Page.navigate", {"url": url})
        time.sleep(wait_seconds)

    def enable_runtime(self):
        self.send("Runtime.enable")

    def close(self):
        self.cdp.send("Target.closeTarget", {"targetId": self.target_id})


def attach_target(cdp, target_id):
    return Target(cdp, target_id, cdp.attach(target_id))


def get_extension_targets(cdp):
    res = cdp.send("Target.getTargets")
    return [t for t in res["targetInfos"] if t["url"].startswith("chrome-extension://")]


def find_service_worker(cdp, ext_id, retries=10, delay=0.5):
    """SW registers async after install; retry. Filter by ext_id — component
    extension workers (thunk.js) also appear in getTargets."""
    for _ in range(retries):
        sw = next((t for t in get_extension_targets(cdp)
                   if t["type"] == "service_worker" and ext_id in t["url"]), None)
        if sw:
            return sw
        time.sleep(delay)
    return None


def screenshot(target, path):
    import base64
    try:
        target.send("Page.enable")
    except RuntimeError:
        pass
    res = target.send("Page.captureScreenshot", {"format": "png"})
    with open(path, "wb") as f:
        f.write(base64.b64decode(res["data"]))
    return path


def read_extensions_list(page):
    """chrome://extensions shadow-DOM scrape. page must be attached + Page.enable'd
    and navigated to chrome://extensions/ (wait ~2s). Returns [{name,version,id,enabled}]."""
    return page.evaluate("""(async () => {
      const mg = document.querySelector('extensions-manager');
      const list = mg.shadowRoot.querySelector('extensions-item-list');
      return Array.from(list.shadowRoot.querySelectorAll('extensions-item')).map(i => ({
        name: i.shadowRoot.querySelector('#name').textContent.trim(),
        version: i.shadowRoot.querySelector('#version').textContent.trim(),
        id: i.id,
        enabled: !!i.shadowRoot.querySelector('cr-toggle[checked]')
      }));
    })()""", await_promise=True)


def reload_extension(page, ext_id):
    """Click the dev reload button (shadow DOM id is #dev-reload-button, NOT #reloadButton)."""
    return page.evaluate(f"""(() => {{
      const mg = document.querySelector('extensions-manager');
      const list = mg.shadowRoot.querySelector('extensions-item-list');
      const item = Array.from(list.shadowRoot.querySelectorAll('extensions-item'))
        .find(i => i.id === '{ext_id}');
      if (!item) return 'item not found';
      const btn = item.shadowRoot.querySelector('#dev-reload-button');
      if (!btn) return 'reload button not found';
      btn.click();
      return 'clicked';
    }})()""")
