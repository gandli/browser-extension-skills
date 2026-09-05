export default defineBackground(() => {
  // WXT demo: record install/update reason, answer pings from popup/content
  browser.runtime.onInstalled.addListener((details) => {
    browser.storage.local.set({ lastInstallReason: details.reason });
  });

  browser.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg?.type === 'ping') sendResponse({ type: 'pong', from: 'wxt-background' });
  });
});
