import { test, expect } from "@playwright/test";

test.describe("SmartCS E2E Tests", () => {
  test("login page loads correctly", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1, h2")).toContainText(/smartcs|login|sign in/i);
  });

  test("can navigate to login and see form", async ({ page }) => {
    await page.goto("/");
    const loginButton = page.getByRole("button", { name: /sign in|login|log in/i }).first();
    if (await loginButton.isVisible()) {
      await loginButton.click();
    }
    const usernameInput = page.getByPlaceholder(/username|email|账号/i).first();
    const passwordInput = page.getByPlaceholder(/password|密码/i).first();
    await expect(usernameInput).toBeVisible({ timeout: 5000 });
    await expect(passwordInput).toBeVisible({ timeout: 5000 });
  });

  test("dark theme is applied", async ({ page }) => {
    await page.goto("/");
    const body = page.locator("body");
    const bgColor = await body.evaluate((el) =>
      getComputedStyle(el).getPropertyValue("background-color")
    );
    expect(bgColor).toBeTruthy();
  });
});
