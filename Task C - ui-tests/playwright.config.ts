import { existsSync } from 'node:fs';
import { defineConfig, devices } from '@playwright/test';


if (existsSync('.env')) {
  process.loadEnvFile('.env');
}

const isCI = !!process.env.CI;

export default defineConfig({
  testDir: './tests',
  expect: {
    timeout: 10000
  },
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  workers: isCI ? 4 : undefined,
  
  reporter: 'html',
  
  use: {
    baseURL: process.env.BASE_URL,
    trace: 'on-first-retry',
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },

  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        screenshot: 'on',
        video: 'on',
        trace: 'on',
      },
    },
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        screenshot: 'on',
        video: 'on',
      trace: 'on',
      },
    },
    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        screenshot: 'on',
        video: 'on',
      trace: 'on',
      },
    },
  ],
});
