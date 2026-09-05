export default defineContentScript({
  matches: ['<all_urls>'],
  runAt: 'document_idle',
  main() {
    const banner = document.createElement('div');
    banner.id = 'wxt-demo-banner';
    banner.textContent = `wxt content script active on ${location.host}`;
    banner.style.cssText =
      'position:fixed;bottom:8px;left:8px;z-index:2147483647;background:#111;' +
      'color:#4f8cff;padding:6px 12px;border-radius:6px;font:13px monospace;';
    document.body.appendChild(banner);
  },
});
