import { expect, test } from '@playwright/test';

test('search → store → change balance → hero updates → locked shelf', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /Pick your McDonald's/ })).toBeVisible();

  await page.getByRole('combobox').fill('Montréal');
  const first = page.getByRole('option').first();
  await expect(first).toBeVisible();
  await first.getByRole('button').click();

  await expect(page).toHaveURL(/store=\d+/);
  const hero = page.getByTestId('hero');
  await expect(hero).toBeVisible();
  const heroName = page.getByTestId('hero-name');
  await expect(heroName).not.toBeEmpty();

  // 6,000 pts default: shelves 10k and 14k locked
  await expect(page.locator('[data-testid="shelf"][data-tier="10000"]')).toHaveAttribute('data-locked', 'true');
  await expect(page.locator('[data-testid="shelf"][data-tier="2000"]')).toHaveAttribute('data-locked', 'false');

  // raise balance to 10,000: the 10k shelf unlocks and the hero can change
  const before = await heroName.textContent();
  const pts = page.locator('#pts').first();
  await pts.fill('10000');
  await expect(page.locator('[data-testid="shelf"][data-tier="10000"]')).toHaveAttribute('data-locked', 'false');
  await expect(page.locator('[data-testid="shelf"][data-tier="14000"]')).toHaveAttribute('data-locked', 'true');
  await expect(page.locator('[data-testid="shelf"][data-tier="14000"]')).toContainText(/4,000 pts to unlock/);

  // drop to 1,000: nothing unlocked, hero explains
  await pts.fill('1000');
  await expect(page.getByTestId('hero-hint')).toContainText(/1,000 more points/);
  await expect(page.locator('[data-testid="shelf"][data-tier="2000"]')).toHaveAttribute('data-locked', 'true');

  // breakfast toggle changes the hero at 2,000 when hash brown was best
  await pts.fill('2000');
  const hb = await heroName.textContent();
  await page.getByLabel(/Skip breakfast-only/).locator('visible=true').check();
  await expect(heroName).not.toHaveText(hb ?? '');
  expect(before).toBeTruthy();

  // CPP formatted like money
  await expect(page.getByTestId('hero-cpp')).toHaveText(/^\d+\.\d{2}¢$/);

  // language switch relabels and sets lang attribute
  await page.getByTestId('lang').click();
  await expect(page.locator('html')).toHaveAttribute('lang', 'fr-CA');
  await expect(page.getByText(/Le meilleur choix en ce moment/)).toBeVisible();
});

test('table view and change store', async ({ page }) => {
  await page.goto('/?store=10001');
  await page.getByRole('button', { name: 'Table' }).click();
  await expect(page.getByRole('table')).toBeVisible();
  await page.getByTestId('change-store').click();
  await expect(page.getByRole('heading', { name: /Pick your McDonald's/ })).toBeVisible();
});
