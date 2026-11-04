import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'e2e',
  testMatch: /screens\.spec\.ts/,
  timeout: 90_000,
  webServer: { command: 'corepack pnpm preview', port: 4173, reuseExistingServer: true },
  use: {
    baseURL: 'http://localhost:4173',
    locale: 'en-CA',
    colorScheme: 'dark',
    launchOptions: { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] }
  }
});
