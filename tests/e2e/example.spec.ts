import { test, expect } from '@playwright/test';

test('пример: открытие главной страницы', async ({ page }) => {
	await page.goto('/');
	await expect(page).toHaveTitle(/.+/);
});


