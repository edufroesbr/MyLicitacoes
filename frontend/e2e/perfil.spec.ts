import { test, expect } from "@playwright/test";

test("salvar preferencias de perfil persiste de verdade", async ({ page, request }) => {
  await page.goto("/perfil");
  await page.getByLabel(/receber digest por e-mail/i).check();
  await page.getByRole("button", { name: /guardar/i }).click();
  // esperar o estado de salvando terminar antes de recarregar
  await page.waitForLoadState("networkidle");
  await page.reload();
  await expect(page.getByLabel(/receber digest por e-mail/i)).toBeChecked();

  const resp = await request.get("http://localhost:8000/perfil");
  const corpo = await resp.json();
  expect(corpo.receber_email).toBe(true);
});
