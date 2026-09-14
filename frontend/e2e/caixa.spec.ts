import { test, expect } from "@playwright/test";
import { execSync } from "node:child_process";

test.beforeAll(() => {
  execSync("uv run python scripts/seed_e2e.py", {
    cwd: "..",
    stdio: "inherit",
    env: { ...process.env, MYLIC_DATABASE_URL: process.env.MYLIC_DATABASE_URL! },
  });
});

test("caixa lista, abre detalhe e muda status", async ({ page }) => {
  await page.goto("/caixa");
  await expect(page.getByText(/clipping/i).first()).toBeVisible();
  await page.getByText(/clipping/i).first().click();
  await expect(page).toHaveURL(/\/editais\/\d+/);
  await page.getByRole("button", { name: /oportunidade/i }).click();
  await expect(page.getByTestId("status-atual")).toHaveText(/oportunidade/i);
});
