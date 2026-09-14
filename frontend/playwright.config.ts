import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
  projects: [
    {
      // Sem PW_CHANNEL usa o chromium empacotado (correto no CI, apos
      // `npx playwright install chromium`); define PW_CHANNEL=chrome para
      // usar o Chrome de sistema localmente.
      name: "chromium",
      use: { ...devices["Desktop Chrome"], channel: process.env.PW_CHANNEL || undefined },
    },
  ],
});
