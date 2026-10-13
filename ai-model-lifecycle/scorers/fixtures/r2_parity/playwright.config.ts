import { defineConfig } from '@playwright/test';

// The R2 parity suite. BASE_URL is either the original GWT app
// (http://127.0.0.1:<port>/) or a model's Angular port of it (.../ng/).
export default defineConfig({
  testDir: '.',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  workers: 1,
  fullyParallel: false,
  retries: 0,
  reporter: [['json', { outputFile: process.env.PARITY_REPORT ?? 'parity-report.json' }], ['line']],
  use: {
    baseURL: process.env.BASE_URL ?? 'http://127.0.0.1:8888/',
    channel: 'chrome',
    headless: true,
  },
});
