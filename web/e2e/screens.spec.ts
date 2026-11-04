import { test } from '@playwright/test';

const out = '../docs/screens';

test('desktop hero', async ({ browser }) => {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, colorScheme: 'dark' });
  const page = await ctx.newPage();
  await page.goto('/?store=10001');
  await page.getByTestId('hero').waitFor();
  await page.waitForTimeout(1500);
  await page.screenshot({ path: `${out}/desktop.png` });
  await page.screenshot({ path: `${out}/desktop-full.png`, fullPage: true });
  await ctx.close();
});

test('phone hero', async ({ browser }) => {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, colorScheme: 'dark' });
  const page = await ctx.newPage();
  await page.goto('/?store=10001');
  await page.getByTestId('hero').waitFor();
  await page.waitForTimeout(1500);
  await page.screenshot({ path: `${out}/phone.png` });
  await page.screenshot({ path: `${out}/phone-full.png`, fullPage: true });
  await ctx.close();
});

test('landing', async ({ browser }) => {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: 'dark' });
  const page = await ctx.newPage();
  await page.goto('/?pick=1');
  await page.waitForTimeout(2500);
  await page.screenshot({ path: `${out}/landing.png` });
  await ctx.close();
});

test('desktop light', async ({ browser }) => {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: 'light' });
  const page = await ctx.newPage();
  await page.goto('/?store=10001');
  await page.getByTestId('hero').waitFor();
  await page.waitForTimeout(2500);
  await page.screenshot({ path: `${out}/desktop-light.png` });
  await ctx.close();
});
