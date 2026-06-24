import { expect, test } from "@playwright/test";

test("anonymous replay is visible and clearly non-live", async ({ page }) => {
  await page.goto("/replays");
  await expect(page.getByRole("heading", { name: "Recorded replays" })).toBeVisible();
  await expect(page.getByText("4 replay scenarios")).toBeVisible();
  await page.getByRole("link", { name: /EU Webhook Latency/i }).click();

  await expect(page.locator(".investigation-hero .panel-label")).toHaveText("Recorded replay");
  await expect(page.getByText("does not call Claude")).toBeVisible();
  await expect(page.getByText("Event 0 of")).toBeVisible();
  await expect(page.getByText("Press Play or Step forward")).toBeVisible();

  await page.getByRole("button", { name: "Skip to end" }).click();

  await expect(page.getByRole("heading", { name: "Specialist reports" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Action queue" })).toBeVisible();
  await expect(page.getByText("Replay only: approvals are disabled.")).toBeVisible();

  await page.getByRole("button", { name: "Show evidence E1" }).click();
  await expect(page.locator("#citation-E1")).toContainText("Incident review - EU delivery latency");
});

test("all canonical replay scenarios are available", async ({ page }) => {
  await page.goto("/replays");
  await expect(page.getByRole("link", { name: /EU Webhook Latency/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /Webhook 401 After Secret Rotation/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /Stripe Schema Mapping Change/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /Salesforce OAuth Expiration/i })).toBeVisible();
});

test("live case page exposes evidence search and replay-only launch state", async ({ page }) => {
  await page.goto("/cases/TKT-1007");
  await expect(page.getByRole("heading", { name: /High latency/i })).toBeVisible();
  await expect(page.getByRole("link", { name: "Find evidence" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Live Claude disabled/i })).toBeVisible();
  await expect(page.getByText("Replay-only public demo")).toBeVisible();
  await expect(page.getByRole("link", { name: "Open recorded replays" })).toBeVisible();
  await expect(page.getByText("Recent job runs")).toBeVisible();
  await expect(page.getByText("Related incidents")).toBeVisible();
});

test("investigations and evaluations navigation items are clickable", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: /Investigations/i }).click();
  await expect(page.getByRole("heading", { name: "Investigations" })).toBeVisible();

  await page.getByRole("link", { name: /Evaluations/i }).click();
  await expect(page.getByRole("heading", { name: "Evaluations" })).toBeVisible();
  await expect(page.getByText("Unauthorized Write Prevention")).toBeVisible();
});
