import { SummaryReporter } from '@hypothesis/frontend-testing/vitest';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    reporters: [new SummaryReporter()],

    browser: {
      provider: 'playwright',
      enabled: true,
      headless: true,
      screenshotFailures: false,
      instances: [{ browser: 'chromium' }],
      viewport: { width: 1024, height: 768 },
    },

    include: ['./build/scripts/tests.bundle.js'],

    coverage: {
      enabled: true,
      provider: 'istanbul',
      reportsDirectory: './coverage',
      reporter: ['json', 'html'],
      include: ['h/static/scripts/**/*.{ts,tsx}'],
      exclude: [
        '**/node_modules/**',
        '**/test/**/*.js',
        '**/tests/**/*.js',
        '**/test-util/**',
      ],
    },
  },
});
