import { test, expect, Locator, Page } from '@playwright/test';

// Port of GWTP carstore's Cucumber features Manufacturers.feature (5 scenarios),
// Ratings.feature (2) and Reports.feature (1), with the same selectors as the
// original Selenium page objects: GWT debug ids (id="gwt-debug-<id>"), table
// rows under the first <tbody>, header text in <thead> <th>, Edit and Delete
// buttons in the last two columns, window.confirm() before a delete.
// Never shown to models (the prompt shows the original page objects).

const dbg = (page: Page, id: string) => page.locator(`#gwt-debug-${id}`);
const rows = (table: Locator) => table.locator('xpath=./tbody[1]/tr');

async function open(page: Page) {
  page.on('dialog', (d) => d.accept());
  await page.goto('');
  // The GWT original sits behind a login screen (admin/qwerty); the Angular
  // port is out of scope for login and opens directly.
  const login = dbg(page, 'username');
  const menubar = dbg(page, 'menubar');
  await expect(login.or(menubar).first()).toBeVisible({ timeout: 30_000 });
  if (await login.isVisible()) {
    await login.fill('admin');
    await dbg(page, 'password').fill('qwerty');
    await dbg(page, 'login').click();
  }
  await expect(menubar).toBeVisible();
}

async function navigate(page: Page, token: string, tableId: string): Promise<Locator> {
  // HeaderWidgetPage.navigateTo: click the menubar link whose href contains the token
  await dbg(page, 'menubar').locator(`a[href*="${token}"]`).first().click();
  const table = dbg(page, tableId);
  await expect(table).toBeVisible();
  await expect(rows(table).first()).toBeVisible();
  return table;
}

async function cellText(table: Locator, column: string, row: number): Promise<string> {
  const headers = (await table.locator('thead th').allInnerTexts()).map((h) => h.trim());
  const index = headers.indexOf(column);
  expect(index, `column "${column}" in [${headers.join(', ')}]`).toBeGreaterThanOrEqual(0);
  return (await rows(table).nth(row).locator('td').nth(index).innerText()).trim();
}

async function expectSuccess(page: Page, text: string) {
  await expect(dbg(page, 'successMessage').filter({ hasText: text }).first()).toBeVisible();
}

test.describe.serial('Manufacturers', () => {
  let page: Page;
  let table: Locator;
  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    await open(page);
    table = await navigate(page, 'manufacturer', 'manufacturers');
  });
  test.afterEach(async () => page.close());

  test('create button shows the manufacturer editor', async () => {
    await dbg(page, 'create-manufacturer').click();
    await expect(dbg(page, 'manufacturer-editor')).toBeVisible();
  });

  test('add then close leaves the table unchanged', async () => {
    const before = await rows(table).count();
    await dbg(page, 'create-manufacturer').click();
    await expect(dbg(page, 'manufacturer-editor')).toBeVisible();
    await dbg(page, 'manufacturer-input').fill('Ford');
    await dbg(page, 'manufacturer-close').click();
    await expect(dbg(page, 'manufacturer-editor')).toBeHidden();
    await page.waitForTimeout(1000);
    expect(await rows(table).count()).toBe(before);
  });

  test('add then save appends the manufacturer', async () => {
    const before = await rows(table).count();
    await dbg(page, 'create-manufacturer').click();
    await expect(dbg(page, 'manufacturer-editor')).toBeVisible();
    await dbg(page, 'manufacturer-input').fill('Plymouth');
    await dbg(page, 'manufacturer-save').click();
    await expectSuccess(page, 'saved');
    await expect.poll(() => rows(table).count()).toBeGreaterThan(before);
    const n = await rows(table).count();
    expect(await cellText(table, 'Name', n - 1)).toBe('Plymouth');
  });

  test('editing the first manufacturer updates it', async () => {
    await rows(table).first().locator('td:nth-last-child(2) button').click();
    await expect(dbg(page, 'manufacturer-editor')).toBeVisible();
    await dbg(page, 'manufacturer-input').fill('Ford');
    await dbg(page, 'manufacturer-save').click();
    await expectSuccess(page, 'saved');
    await expect.poll(() => cellText(table, 'Name', 0)).toBe('Ford');
  });

  test('deleting the first manufacturer removes a row', async () => {
    const before = await rows(table).count();
    await rows(table).first().locator('td:last-child button').click();
    await expect.poll(() => rows(table).count()).toBe(before - 1);
  });
});

test.describe.serial('Ratings', () => {
  let page: Page;
  let table: Locator;
  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    await open(page);
    table = await navigate(page, 'rating', 'ratings');
  });
  test.afterEach(async () => page.close());

  test('adding a rating creates a row', async () => {
    const before = await rows(table).count();
    await dbg(page, 'ratingCreate').click();
    await dbg(page, 'ratingInput').fill('10');
    await dbg(page, 'ratingSave').click();
    await expect(dbg(page, 'ratingSave')).toBeHidden();
    await expectSuccess(page, '');
    await expect.poll(() => rows(table).count()).toBe(before + 1);
  });

  test('deleting the first rating removes a row', async () => {
    const before = await rows(table).count();
    await rows(table).first().locator('td:last-child button').click();
    await expect.poll(() => rows(table).count()).toBe(before - 1);
  });
});

test('Reports show the average rating of every manufacturer', async ({ page }) => {
  await open(page);
  const ratings = await navigate(page, 'rating', 'ratings');
  const sums = new Map<string, { sum: number; n: number }>();
  const n = await rows(ratings).count();
  for (let i = 0; i < n; i++) {
    const car = await cellText(ratings, 'Car', i);                 // "<manufacturer>/<model>"
    const rating = Number(await cellText(ratings, 'Rating', i));
    const manufacturer = car.substring(0, car.indexOf('/')).trim();
    const s = sums.get(manufacturer) ?? { sum: 0, n: 0 };
    sums.set(manufacturer, { sum: s.sum + rating, n: s.n + 1 });
  }
  expect(sums.size).toBeGreaterThan(0);

  const report = await navigate(page, 'report', 'reports');
  const m = await rows(report).count();
  expect(m).toBeGreaterThan(0);
  for (let i = 0; i < m; i++) {
    const manufacturer = await cellText(report, 'Manufacturer', i);
    const average = Number(await cellText(report, 'Rating', i));
    const ref = sums.get(manufacturer);
    expect(ref, `manufacturer ${manufacturer} has ratings`).toBeDefined();
    expect(Math.abs(average - ref!.sum / ref!.n)).toBeLessThan(0.001);
  }
});
