// tests/e2e/login.spec.ts
declare const process: any;
import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';

test('login smoke (demo on BASE_URL)', async ({ page }) => {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'load' });

  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Пароль').fill('Passw0rd!');
  await page.getByRole('button', { name: 'Войти' }).click();

  // Наше демо редиректит на dashboard.html и показывает текст
  await expect(page).toHaveURL(/dashboard\.html$/);
  await expect(page.getByText('Добро пожаловать')).toBeVisible();
});

test('login negative: empty email shows validation error', async ({ page }) => {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'load' });

  await page.getByLabel('Email').fill('');
  await page.getByLabel('Пароль').fill('Passw0rd!');
  await page.getByRole('button', { name: 'Войти' }).click();

  await expect(page.getByRole('alert')).toHaveText('Email обязателен');
  await expect(page).toHaveURL(/login(\.html)?$/);
});

test('login negative: empty password shows validation error', async ({ page }) => {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'load' });

  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Пароль').fill('');
  await page.getByRole('button', { name: 'Войти' }).click();

  await expect(page.getByRole('alert')).toHaveText('Пароль обязателен');
  await expect(page).toHaveURL(/login(\.html)?$/);
});

test('login negative: both fields empty prioritizes email error', async ({ page }) => {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'load' });

  await page.getByLabel('Email').fill('');
  await page.getByLabel('Пароль').fill('');
  await page.getByRole('button', { name: 'Войти' }).click();

  await expect(page.getByRole('alert')).toHaveText('Email обязателен');
  await expect(page).toHaveURL(/login(\.html)?$/);
});

test('login negative: invalid email format shows specific error', async ({ page }) => {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'load' });

  await page.getByLabel('Email').fill('not-an-email');
  await page.getByLabel('Пароль').fill('Passw0rd!');
  await page.getByRole('button', { name: 'Войти' }).click();

  await expect(page.getByRole('alert')).toHaveText('Неверный формат email');
  await expect(page).toHaveURL(/login(\.html)?$/);
});

test('login negative: wrong credentials show auth error', async ({ page }) => {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'load' });

  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Пароль').fill('WrongPass123');
  await page.getByRole('button', { name: 'Войти' }).click();

  await expect(page.getByRole('alert')).toHaveText('Неверные учетные данные');
  await expect(page).toHaveURL(/login(\.html)?$/);
});
