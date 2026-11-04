import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: 'e2e',
  testMatch: /flow\.spec\.ts/,
  timeout: 60_000,
  webServer: { command: 'corepack pnpm preview', port: 4173, reuseExistingServer: true },
  use: { baseURL: 'http://localhost:4173', ...devices['Desktop Chrome'], locale: 'en-CA' }
});
