# WXT Demo Notes — real-browser E2E with Chrome for Testing

Verified reproduction of the WXT→CDP integration.

```bash
npm install
npx wxt build                 # → .output/chrome-mv3
# run the CDP harness (needs Chrome for Testing + websocket-client):
python3 wxt_e2e_test.py

# dev mode (auto-launches Chrome for Testing via webExt.binaries.chrome):
CHROME_CFT=/path/to/Chrome\ for\ Testing.app/.../Google\ Chrome\ for\ Testing npx wxt
```
