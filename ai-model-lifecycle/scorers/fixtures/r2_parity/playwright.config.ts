import { defineConfig } from '@playwright/test';

// The R2 parity suite. BASE_URL is either the original GWT app
// (http://127.0.0.1:<port>/) or a model's Angular port of it (.../ng/).
export default defineConfig({
  testDir: '.',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  workers: 1,
  fullyParallel: false,
  // One retry: a test that fails then passes is reported "flaky" and counts
  // as a pass (scorers/r2_scorer.py records which). A real defect fails both
  // tries. A serial group (Manufacturers, Ratings) retries as a whole; its
  // tests compare row counts before and after, so a retry is safe.
  retries: 1,
  reporter: [['json', { outputFile: process.env.PARITY_REPORT ?? 'parity-report.json' }], ['line']],
  use: {
    baseURL: process.env.BASE_URL ?? 'http://127.0.0.1:8888/',
    channel: 'chrome',
    headless: true,
  },
});
