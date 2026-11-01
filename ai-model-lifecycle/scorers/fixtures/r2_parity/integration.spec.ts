import { test, expect, Locator, Page, APIRequestContext } from '@playwright/test';

// R2 integration suite: the UI and the REST API must agree. The parity suite
// (parity.spec.ts) checks what the screen shows; a port that only changed its
// tables in the browser, without saving through the API, could pass it. Here
// each UI action is followed by a check of the backend through the same
// JSON REST API the app must use (`/api`, same origin). Same selectors as the
// parity suite (GWT debug ids, table rows under the first <tbody>, Edit and
// Delete buttons in the last two columns). Never shown to models.

const dbg = (page: Page, id: string) => page.locator(`#gwt-debug-${id}`);
const rows = (table: Locator) => table.locator('xpath=./tbody[1]/tr');
const apiUrl = (path: string) =>
  new URL(`/api${path}`, process.env.BASE_URL ?? 'http://127.0.0.1:8888/').toString();

async function api<T>(request: APIRequestContext, path: string): Promise<T> {
  const res = await request.get(apiUrl(path), { headers: { Accept: 'application/json' } });
  expect(res.ok(), `GET /api${path} -> ${res.status()}`).toBeTruthy();
  return (await res.json()) as T;
}

type Manufacturer = { id: number; name: string };
type Rating = { id: number; rating: number };
type Average = { manufacturer: string; rating: number };

async function open(page: Page) {
  page.on('dialog', (d) => d.accept());
  await page.goto('');
  // the GWT original sits behind a login screen; the Angular port opens directly
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
  await dbg(page, 'menubar').locator(`a[href*="${token}"]`).first().click();
  const table = dbg(page, tableId);
  await expect(table).toBeVisible();
  await expect(rows(table).first()).toBeVisible();
  return table;
}

async function column(table: Locator, name: string): Promise<string[]> {
  const headers = (await table.locator('thead th').allInnerTexts()).map((h) => h.trim());
  const index = headers.indexOf(name);
  expect(index, `column "${name}" in [${headers.join(', ')}]`).toBeGreaterThanOrEqual(0);
  const out: string[] = [];
  const n = await rows(table).count();
  for (let i = 0; i < n; i++) {
    out.push((await rows(table).nth(i).locator('td').nth(index).innerText()).trim());
  }
  return out;
}

const sorted = (xs: string[]) => [...xs].sort();

test.describe.serial('API · manufacturers', () => {
  const name = `Integration Motors ${Date.now() % 100000}`;
  const renamed = `${name} Edited`;
  let page: Page;
  let table: Locator;
  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    await open(page);
    table = await navigate(page, 'manufacturer', 'manufacturers');
  });
  test.afterEach(async () => page.close());

  test('the table shows the manufacturers the API returns', async ({ request }) => {
    const fromApi = (await api<Manufacturer[]>(request, '/manufacturers')).map((m) => m.name);
    await expect.poll(async () => sorted(await column(table, 'Name'))).toEqual(sorted(fromApi));
  });

  test('saving a new manufacturer stores it through the API', async ({ request }) => {
    await dbg(page, 'create-manufacturer').click();
    await expect(dbg(page, 'manufacturer-editor')).toBeVisible();
    await dbg(page, 'manufacturer-input').fill(name);
    await dbg(page, 'manufacturer-save').click();
    await expect
      .poll(async () => (await api<Manufacturer[]>(request, '/manufacturers')).some((m) => m.name === name))
      .toBe(true);
  });

  test('editing a manufacturer saves the change through the API', async ({ request }) => {
    const before = (await api<Manufacturer[]>(request, '/manufacturers')).find((m) => m.name === name);
    expect(before, `${name} was saved by the previous test`).toBeDefined();
    await rows(table).filter({ hasText: name }).first().locator('td:nth-last-child(2) button').click();
    await expect(dbg(page, 'manufacturer-editor')).toBeVisible();
    await dbg(page, 'manufacturer-input').fill(renamed);
    await dbg(page, 'manufacturer-save').click();
    await expect
      .poll(async () => (await api<Manufacturer>(request, `/manufacturers/${before!.id}`)).name)
      .toBe(renamed);
  });

  test('deleting a manufacturer removes it through the API', async ({ request }) => {
    const target = (await api<Manufacturer[]>(request, '/manufacturers')).find((m) => m.name === renamed);
    expect(target, `${renamed} was saved by the previous test`).toBeDefined();
    await rows(table).filter({ hasText: renamed }).first().locator('td:last-child button').click();
    await expect
      .poll(async () => (await api<Manufacturer[]>(request, '/manufacturers')).some((m) => m.id === target!.id))
      .toBe(false);
  });
});

test.describe.serial('API · ratings', () => {
  let page: Page;
  let table: Locator;
  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    await open(page);
    table = await navigate(page, 'rating', 'ratings');
  });
  test.afterEach(async () => page.close());

  test('adding a rating stores it through the API', async ({ request }) => {
    const before = new Set((await api<Rating[]>(request, '/ratings')).map((r) => r.id));
    await dbg(page, 'ratingCreate').click();
    await dbg(page, 'ratingInput').fill('7');
    await dbg(page, 'ratingSave').click();
    await expect
      .poll(async () => (await api<Rating[]>(request, '/ratings'))
        .filter((r) => !before.has(r.id)).map((r) => r.rating))
      .toEqual([7]);
  });

  test('deleting a rating removes it through the API', async ({ request }) => {
    const before = (await api<Rating[]>(request, '/ratings')).length;
    await rows(table).first().locator('td:last-child button').click();
    await expect.poll(async () => (await api<Rating[]>(request, '/ratings')).length).toBe(before - 1);
  });
});

test('the report shows the average ratings the API computes', async ({ page, request }) => {
  await open(page);
  const report = await navigate(page, 'report', 'reports');
  const fromApi = await api<Average[]>(request, '/manufacturers/ratings');
  expect(fromApi.length).toBeGreaterThan(0);
  const names = await column(report, 'Manufacturer');
  const values = (await column(report, 'Rating')).map(Number);
  expect(sorted(names)).toEqual(sorted(fromApi.map((a) => a.manufacturer)));
  for (const a of fromApi) {
    const shown = values[names.indexOf(a.manufacturer)];
    expect(Math.abs(shown - a.rating), `${a.manufacturer}: shown ${shown}, API ${a.rating}`).toBeLessThan(0.01);
  }
});
