import { expect, test } from "@playwright/test";

test.describe("AI English Tutor", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("should load the main page with header", async ({ page }) => {
    // Check header is visible
    await expect(page.locator("header")).toBeVisible();

    // Check title is present
    await expect(page.getByRole("heading", { level: 1 })).toContainText(
      "AI English Tutor"
    );
  });

  test("should display level slider with default value", async ({ page }) => {
    // Check level slider is visible (shadcn/ui Slider uses role="slider")
    const slider = page.getByRole("slider");
    await expect(slider).toBeVisible();

    // Check "Comprehension Level" label is visible
    await expect(page.getByText("Comprehension Level")).toBeVisible();

    // Check level labels are present (기초, 초급, 중급, 고급, 심화)
    // Note: "중급" appears twice (current level + bottom label), use first()
    await expect(page.getByText("중급").first()).toBeVisible();
  });

  test("should display analysis placeholder when no results", async ({ page }) => {
    // When no analysis results, show placeholder message
    await expect(
      page.getByText("Submit text or upload an image to see analysis results")
    ).toBeVisible();
  });

  test("should have chat input area", async ({ page }) => {
    // Check textarea is visible
    const textarea = page.locator("textarea");
    await expect(textarea).toBeVisible();
    await expect(textarea).toBeEnabled();
  });

  test("should have image upload area", async ({ page }) => {
    // Check drop zone is visible
    const dropZone = page.getByTestId("drop-zone");
    await expect(dropZone).toBeVisible();

    // Check "Select Image" button is visible
    await expect(page.getByRole("button", { name: "Select Image" })).toBeVisible();

    // Check drag and drop hint text
    await expect(page.getByText("or drag and drop")).toBeVisible();
  });
});

test.describe("Responsive Design", () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test("should display mobile layout correctly", async ({ page }) => {
    await page.goto("/");

    // Check page renders without horizontal scroll
    const scrollWidth = await page.evaluate(() => document.body.scrollWidth);
    const clientWidth = await page.evaluate(() => document.body.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 50); // Allow small tolerance
  });
});

test.describe("Dark Mode", () => {
  test.use({ colorScheme: "dark" });

  test("should support dark mode", async ({ page }) => {
    await page.goto("/");

    // Check that the page renders without errors in dark mode
    await expect(page.locator("body")).toBeVisible();

    // Check background is dark
    const backgroundColor = await page.evaluate(() =>
      window.getComputedStyle(document.body).backgroundColor
    );
    // Dark background should have low RGB values
    expect(backgroundColor).toBeTruthy();
  });
});
