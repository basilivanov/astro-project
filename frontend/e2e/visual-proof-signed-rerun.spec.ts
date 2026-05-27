import { test, expect } from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import { bootstrapSignedTelegram, attachConsoleAndPageErrors, expectNoCrash } from './utils';

const outDir = '/home/astro/.ductor/workspace/output_to_user';

function stamp() {
  return new Date().toISOString().replace(/[:.]/g, '-');
}

async function ensureDir() {
  await fs.mkdir(outDir, { recursive: true });
}

async function snap(locator: any, name: string) {
  await locator.screenshot({ path: path.join(outDir, name) });
}

async function seedSignedProfile(page: import('@playwright/test').Page, initData: string) {
  const response = await page.request.put('/api/users/me', {
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Auth': initData,
    },
    data: {
      full_name: 'Today Scoped',
      birth_date: '1991-08-21',
      birth_time: '08:45',
      birth_time_known: true,
      birth_place: 'Moscow, Russia',
      birth_lat: 55.7558,
      birth_lon: 37.6176,
      birth_timezone: 'Europe/Moscow',
      current_timezone: 'Europe/Moscow',
    },
  });

  expect(response.ok()).toBeTruthy();
}

test('visual proof rerun for signed today/week surfaces', async ({ page }) => {
  await ensureDir();
  const ts = stamp();
  await page.setViewportSize({ width: 430, height: 932 });
  const hygiene = attachConsoleAndPageErrors(page);

  const runtime = await bootstrapSignedTelegram(page, {
    user: {
      id: 45454546,
      first_name: 'Today',
      last_name: 'Scoped',
      username: 'signed_today_scoped',
      language_code: 'ru',
    },
  });

  await seedSignedProfile(page, runtime.initData);

  const responses: Array<{ url: string; status: number; body: any | null }> = [];
  page.on('response', async (response) => {
    const url = response.url();
    if (!url.includes('/api/feed/today') && !url.includes('/api/reports/my') && !url.includes('/api/reports/')) return;
    try {
      responses.push({ url, status: response.status(), body: await response.json() });
    } catch {
      responses.push({ url, status: response.status(), body: null });
    }
  });

  await page.goto('/?mock=0', { waitUntil: 'networkidle' });
  await expectNoCrash(page);
  await fs.writeFile(path.join(outDir, `signed-today-body-${ts}.txt`), await page.locator('body').innerText(), 'utf8');
  await page.screenshot({ path: path.join(outDir, `signed-today-full-${ts}.png`), fullPage: true });

  const todayTargets = [
    ['today-verdict', `today-verdict-${ts}.png`],
    ['today-windows', `today-windows-${ts}.png`],
    ['today-actions', `today-actions-${ts}.png`],
    ['today-explainability', `today-explainability-${ts}.png`],
  ] as const;

  for (const [testId, file] of todayTargets) {
    const locator = page.getByTestId(testId);
    if (await locator.count()) {
      await expect(locator).toBeVisible({ timeout: 15000 });
      await snap(locator, file);
    }
  }

  const todayCards: Record<string, { text: string | null }> = {};
  for (const key of ['energy', 'money', 'love', 'focus'] as const) {
    const card = page.getByTestId(`today-score-${key}`);
    if (await card.count()) {
      todayCards[key] = { text: await card.textContent().catch(() => null) };
      await snap(card, `today-score-${key}-${ts}.png`);
      const button = card.locator('button').first();
      if (await button.count()) {
        await button.click();
        await page.waitForTimeout(250);
        await snap(card, `today-score-${key}-expanded-${ts}.png`);
      }
    }
  }

  await page.goto('/week?mock=0', { waitUntil: 'networkidle' });
  await expectNoCrash(page);
  await fs.writeFile(path.join(outDir, `signed-week-body-${ts}.txt`), await page.locator('body').innerText(), 'utf8');
  await page.screenshot({ path: path.join(outDir, `signed-week-full-${ts}.png`), fullPage: true });

  const weekTargets = [
    ['week-map-surface', `week-map-surface-${ts}.png`],
    ['week-day-strip', `week-day-strip-${ts}.png`],
    ['week-day-grid', `week-day-grid-${ts}.png`],
    ['week-domain-panel', `week-domain-panel-${ts}.png`],
    ['week-actions-panel', `week-actions-panel-${ts}.png`],
    ['week-explainability-panel', `week-explainability-panel-${ts}.png`],
    ['week-deep-sections', `week-deep-sections-${ts}.png`],
  ] as const;

  for (const [testId, file] of weekTargets) {
    const locator = page.getByTestId(testId);
    if (await locator.count()) {
      await expect(locator).toBeVisible({ timeout: 15000 });
      await snap(locator, file);
    }
  }

  const result = {
    timestamp: ts,
    runtimeInitDataLength: runtime.initData.length,
    todayCards,
    responses,
    hygiene: hygiene.logs,
    todayUrl: '/?mock=0',
    weekUrl: page.url(),
  };

  await fs.writeFile(path.join(outDir, `visual-proof-signed-${ts}.json`), JSON.stringify(result, null, 2), 'utf8');
  expect(hygiene.logs).toEqual([]);
  hygiene.dispose();
});
