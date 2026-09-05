"""WXT demo E2E: load WXT build output in Chrome for Testing via CDP, drive + assert.

Mirrors the proven ~/ext-e2e-test harness but uses WXT's `.output/chrome-mv3`
as the --load-extension path (the documented WXT→CDP integration point).
"""
import base64
import json
import os
import subprocess
import time
import urllib.request
import websocket

WXT_OUT = os.path.expanduser("~/wxt-demo/.output/chrome-mv3")
CHROME = os.path.expanduser(
    "~/ext-e2e-test/chrome/mac_arm-152.0.7977.82/chrome-mac-arm64/"
    "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
)
PORT = 9337
SITE = "http://localhost:8791/"
REPORTS = os.path.expanduser("~/wxt-demo/reports")
os.makedirs(REPORTS, exist_ok=True)


class CDP:
    def __init__(self, ws, timeout=15):
        self.ws = websocket.create_connection(ws, timeout=timeout)
        self._id = 0
        self.events = []

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

    def attach(self, target_id):
        res = self.send("Target.attachToTarget",
                        {"targetId": target_id, "flatten": True})
        return res["sessionId"]


def browser_ws(port):
    with urllib.request.urlopen(f"http://localhost:{port}/json/version") as r:
        return json.load(r)["webSocketDebuggerUrl"]


def get_targets(cdp):
    return cdp.send("Target.getTargets")["targetInfos"]


def find_ext_sw(cdp):
    """Return (eid, sw_session) via the background.js service worker target.

    Never match generic chrome-extension:// targets — Chrome component
    extensions (thunk.js) pollute Target.getTargets.
    """
    for _ in range(20):
        for t in get_targets(cdp):
            if t["type"] == "service_worker" and "/background.js" in t["url"]:
                eid = t["url"].split("/")[2]
                return eid, cdp.attach(t["targetId"])
        time.sleep(0.3)
    raise RuntimeError("our service worker (background.js) not registered")


def evaluate(sid, expr, await_promise=False):
    res = cdp.send("Runtime.evaluate",
                   {"expression": expr, "returnByValue": True,
                    "awaitPromise": await_promise}, session_id=sid)
    if "exceptionDetails" in res:
        raise RuntimeError(f"eval failed: {res['exceptionDetails']}")
    return res.get("result", {}).get("value")


def shot(cdp, sid, path):
    """Screenshot a page target. Service workers have no Page domain — skip."""
    try:
        cdp.send("Page.enable", session_id=sid)
        data = cdp.send("Page.captureScreenshot", {"format": "png"}, session_id=sid)["data"]
    except RuntimeError:
        return None  # worker target: no Page domain
    with open(path, "wb") as f:
        f.write(base64.b64decode(data))
    return path


results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


if __name__ == "__main__":
    assert os.path.isdir(WXT_OUT), f"WXT build missing: {WXT_OUT}"
    # kill stale
    subprocess.run(["pkill", "-f", "remote-debugging-port=%d" % PORT],
                   stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-f", "Chrome for Testing"], stderr=subprocess.DEVNULL)
    time.sleep(1)

    cmd = [CHROME, f"--remote-debugging-port={PORT}", "--no-first-run",
           "--user-data-dir=" + os.path.expanduser("~/wxt-demo/chrome-profile-test"),
           "--remote-allow-origins=*",
           "--load-extension=" + WXT_OUT]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            try:
                ws = browser_ws(PORT)
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("browser ws never came up")

        cdp = CDP(ws)

        # A. extension loaded + SW registered
        eid, sw = find_ext_sw(cdp)
        check("A1 extension id resolved", eid and len(eid) == 32, eid)
        check("A2 service worker registered", sw is not None)
        shot(cdp, sw, f"{REPORTS}/1-sw.png")

        # B. onInstalled reason=install written to storage
        reason = evaluate(sw,
            "((async()=>{const r=await browser.storage.local.get('lastInstallReason');return r.lastInstallReason;})())",
            await_promise=True)
        check("B1 onInstalled reason=install", reason == "install", str(reason))

        # C. content script injects banner on the demo site
        page_sid = None
        for t in get_targets(cdp):
            if t["type"] == "page" and t["url"].startswith("http"):
                page_sid = cdp.attach(t["targetId"]); break
        if not page_sid:
            # open a real page
            tab = cdp.send("Target.createTarget", {"url": SITE})["targetId"]
            page_sid = cdp.attach(tab)
            cdp.send("Page.enable", session_id=page_sid)
            cdp.send("Page.navigate", {"url": SITE}, session_id=page_sid)
            time.sleep(2)
        banner = evaluate(page_sid,
            "document.getElementById('wxt-demo-banner')?.textContent || ''")
        check("C1 content script banner present", "wxt content script active" in banner, banner)
        shot(cdp, page_sid, f"{REPORTS}/2-content-banner.png")

        # D. popup opens, save note persists in storage
        pop = cdp.send("Target.createTarget",
                       {"url": f"chrome-extension://{eid}/popup.html"})["targetId"]
        psid = cdp.attach(pop)
        cdp.send("Page.enable", session_id=psid)
        time.sleep(1.2)
        evaluate(psid, "document.querySelector('#note').value='wxt e2e note'")
        evaluate(psid, "document.querySelector('#save').click()")
        time.sleep(0.6)
        stored = evaluate(sw,
            "((async()=>{const r=await browser.storage.local.get('notes');return JSON.stringify(r.notes);})())",
            await_promise=True)
        check("D1 popup save persisted to storage", "wxt e2e note" in (stored or ""), stored)
        shot(cdp, psid, f"{REPORTS}/3-popup-saved.png")

        # E. popup→SW ping/pong messaging
        pong = evaluate(psid,
            "((async()=>{const p=await browser.runtime.sendMessage({type:'ping'});return p?.from;})())",
            await_promise=True)
        check("E1 popup→SW ping/pong", pong == "wxt-background", str(pong))

        passed = sum(1 for _, ok, _ in results if ok)
        print(f"\n==== WXT E2E: {passed}/{len(results)} passed ====")
        with open(f"{REPORTS}/result.json", "w") as f:
            json.dump({"passed": passed, "total": len(results),
                       "checks": [{"name": n, "ok": ok, "detail": d} for n, ok, d in results]}, f, indent=2)
        raise SystemExit(0 if passed == len(results) else 1)
    finally:
        proc.terminate()
