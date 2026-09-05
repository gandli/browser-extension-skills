import { defineConfig } from 'wxt';

export default defineConfig({
  manifest: {
    name: 'WXT Demo Notes',
    description: 'WXT demo extension for real-browser E2E testing',
    permissions: ['storage'],
  },
  // web-ext auto-launches this binary in dev mode. Point it at Chrome for
  // Testing — stable Chrome 137+ silently ignores --load-extension.
  webExt: {
    binaries: {
      chrome: process.env.CHROME_CFT,
    },
    chromiumArgs: ['--remote-debugging-port=9337'],
  },
});
