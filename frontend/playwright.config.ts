import { defineConfig } from "@playwright/test";

const python = process.env.ORBITLENS_PYTHON ??
  (process.platform === "win32" ? "..\\.venv\\Scripts\\python.exe" : "../.venv/bin/python");

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }], ["json", { outputFile: "test-results/results.json" }]],
  use: {
    baseURL: "http://127.0.0.1:8013",
    timezoneId: "America/Lima",
    channel: process.env.ORBITLENS_BROWSER_CHANNEL ?? "msedge",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "desktop", use: { viewport: { width: 1366, height: 900 } } },
    { name: "mobile-viewport", use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
  ],
  webServer: {
    command: `"${python}" ../scripts/start_qa_server.py`,
    url: "http://127.0.0.1:8013/api/health",
    reuseExistingServer: false,
    timeout: 60000,
  },
});
