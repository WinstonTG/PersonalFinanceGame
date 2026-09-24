import { test, expect } from "playwright/test";

test("player can submit a named plan and read the scored year", async ({ page }) => {
  await page.goto("http://127.0.0.1:8000");
  await page.getByLabel("PLAN NAME").fill("Balanced start");
  await page.getByLabel("Monthly auto-investment").fill("150");
  await page.getByLabel("Fun spending for month 1", { exact: true }).fill("400");
  await page.getByRole("button", { name: /Run the year/ }).click();

  await expect(page.locator("#results")).toBeVisible();
  await expect(page.locator("#result-plan-name")).toHaveText("Balanced start");
  await expect(page.locator("#month-results tr")).toHaveCount(12);
  await expect(page.locator("#ending-savings")).not.toHaveText("$0");
  await expect(page.locator("#investment-balance")).not.toHaveText("$0");
  await expect(page.locator("#total-score")).not.toHaveText("0 pts");
  await expect(page.locator("#quality-bar")).toHaveAttribute("style", /width:/);
});

test("plan builder stays usable on a phone-sized viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("http://127.0.0.1:8000");

  const columns = await page.locator("#months-grid").evaluate((element) =>
    getComputedStyle(element).gridTemplateColumns.split(" ").length,
  );
  await expect(page.getByRole("button", { name: /Run the year/ })).toBeVisible();
  expect(columns).toBe(2);
});
