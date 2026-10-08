import { test, expect } from "@playwright/test";
import { execSync } from "node:child_process";

const API_URL = "http://localhost:8000";

test.describe.configure({ mode: "serial" });

test.beforeAll(() => {
  execSync("uv run python scripts/seed_e2e.py", {
    cwd: "..",
    stdio: "inherit",
    env: { ...process.env, MYLIC_DATABASE_URL: process.env.MYLIC_DATABASE_URL! },
  });
});

test("caixa lista editais, status novo em destaque e badge de score", async ({ page }) => {
  await page.goto("/caixa");
  const itemNovo = page.locator("li", { hasText: "Servico de clipping e monitoramento de publicacoes" });
  await expect(itemNovo).toBeVisible();
  await expect(itemNovo.getByText("90%")).toBeVisible();
  await expect(itemNovo.locator("span.bg-primary")).toBeVisible();

  const itemLido = page.locator("li", { hasText: "Aquisicao de mobiliario de escritorio" });
  await expect(itemLido).toBeVisible();
  await expect(itemLido.locator("span.bg-primary")).toHaveCount(0);
});

test("detalhe abre com link do PDF que resolve de verdade", async ({ page, request }) => {
  await page.goto("/caixa");
  await page.getByRole("link", { name: /Servico de clipping e monitoramento de publicacoes/ }).click();
  await expect(page).toHaveURL(/\/editais\/\d+$/);

  const linkArquivo = page.getByRole("link", { name: /Edital \(arquivo #/ });
  await expect(linkArquivo).toBeVisible();
  const href = await linkArquivo.getAttribute("href");
  expect(href).toContain("/arquivo/");

  const resp = await request.get(href!);
  expect(resp.status()).toBe(200);
  expect(resp.headers()["content-type"]).toContain("application/pdf");
});

test("acao 'marcar como lido' reflete no backend, nao so na UI", async ({ page, request }) => {
  await page.goto("/caixa");
  await page.getByRole("link", { name: /Servico de clipping e monitoramento de publicacoes/ }).click();
  await expect(page).toHaveURL(/\/editais\/(\d+)$/);
  const id = (page.url().match(/\/editais\/(\d+)$/) ?? [])[1];

  await page.getByRole("button", { name: "Marcar como lido" }).click();
  await expect(page.getByTestId("status-atual")).toHaveText("lido");

  const resp = await request.get(`${API_URL}/editais/${id}`);
  const corpo = await resp.json();
  expect(corpo.status).toBe("lido");
});

test("filtros e busca restringem a lista corretamente", async ({ page }) => {
  await page.goto("/caixa");

  await page.getByPlaceholder("Buscar no objeto do edital...").fill("mobiliario");
  await page.getByRole("button", { name: "Buscar" }).click();
  await expect(page.locator("li", { hasText: "Aquisicao de mobiliario de escritorio" })).toBeVisible();
  await expect(page.locator("li", { hasText: "Servico de clipping" })).toHaveCount(0);

  await page.getByPlaceholder("Buscar no objeto do edital...").fill("");
  await page.getByPlaceholder("UF").fill("AM");
  await page.getByRole("button", { name: "Buscar" }).click();
  await expect(page.locator("li", { hasText: "Servico de clipping" })).toBeVisible();
  await expect(page.locator("li", { hasText: "Aquisicao de mobiliario" })).toHaveCount(0);

  await page.getByPlaceholder("UF").fill("");
  await page.getByRole("button", { name: "Buscar" }).click();
  await page.getByRole("combobox").nth(0).selectOption("lido");
  await expect(page.locator("li", { hasText: "Servico de clipping" })).toBeVisible();
  await expect(page.locator("li", { hasText: "Aquisicao de mobiliario" })).toHaveCount(0);
});
