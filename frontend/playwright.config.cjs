const { defineConfig } = require("@playwright/test");

const baseUrl = process.env.E2E_BASE_URL || "http://localhost:3001";
const outputDir = process.env.PLAYWRIGHT_OUTPUT_DIR || "/tmp/playwright-results";

module.exports = defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  navigationTimeout: 20_000,
  actionTimeout: 10_000,
  expect: {
    timeout: 15_000,
  },
  retries: 0,
  reporter: [["list"]],
  workers: 1,
  use: {
    baseURL: baseUrl,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  outputDir,
});
