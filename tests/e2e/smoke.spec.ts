import { expect, test } from "@playwright/test";

test("opens the Enact workspace", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Enact" })).toBeVisible();
});
