const { defineConfig } = require("@playwright/test");

const baseUrl = process.env.E2E_BASE_URL || "http://localhost:3000";

module.exports = defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: baseUrl,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  outputDir: "test-results",
});
