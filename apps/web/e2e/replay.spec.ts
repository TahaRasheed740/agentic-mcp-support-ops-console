import { expect, test } from "@playwright/test";

test("replay page is honest when no captured replays exist", async ({ page }) => {
  await page.goto("/replays");
  await expect(page.getByRole("heading", { name: "Recorded replays" })).toBeVisible();
  await expect(page.getByText("0 replay scenarios")).toBeVisible();
  await expect(page.getByText("No captured replays yet")).toBeVisible();
  await expect(page.getByText("No scripted or simulated replay")).toBeVisible();
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
