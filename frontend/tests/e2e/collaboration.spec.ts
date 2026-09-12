import { test, expect } from '@playwright/test';

test.describe('Collaborative Room E2E', () => {
  test('should allow user to create a room and execute code', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/');

    // Assuming we have a login mechanism, test the flow.
    // For now, let's just click 'Get Started' if it exists.
    const getStartedButton = page.getByRole('button', { name: /Get Started/i });
    if (await getStartedButton.isVisible()) {
      await getStartedButton.click();
    }

    // Login via UI
    await page.fill('input[type="email"]', 'e2e_tester@nexagrid.dev');
    await page.fill('input[type="password"]', 'Password123!');
    await page.getByRole('button', { name: /Sign In/i }).click();

    // Create a new room
    await page.getByRole('button', { name: /Create New Room/i }).click();
    await page.fill('input[placeholder="Room Name"]', 'E2E Test Room');
    await page.getByRole('button', { name: /Create/i }).click();

    // Verify we are in the room by checking for the editor
    await expect(page.locator('.monaco-editor')).toBeVisible({ timeout: 10000 });

    // Type some code into Monaco editor
    // Note: Interacting with Monaco requires clicking the view-lines and typing
    await page.locator('.view-lines').click();
    await page.keyboard.type('print("Hello FAANG")');

    // Click Run
    await page.getByRole('button', { name: /Run/i }).click();

    // Check output terminal
    await expect(page.locator('.terminal-output')).toContainText('Hello FAANG', { timeout: 15000 });
  });
});
