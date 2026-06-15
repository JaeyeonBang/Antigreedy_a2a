import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

// repo root is two levels up from tests/e2e
const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const PORT = process.env.E2E_PORT || '8765';
const baseURL = `http://127.0.0.1:${PORT}`;

export default defineConfig({
  testDir: '.',
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,        // one shared dashboard server; tests share editor/history state
  workers: 1,
  reporter: [['list']],
  use: { baseURL, trace: 'retain-on-failure' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  // Boot the real dashboard (mock backend) so the browser drives the true stack.
  webServer: {
    command: `.venv/bin/python -m antigreedy.dashboard --port ${PORT}`,
    cwd: repoRoot,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
