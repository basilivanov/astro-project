import { test } from '@playwright/test';
import { bootstrapSignedTelegram } from './utils';

test('dump signed today payload and summaries', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const runtime = await bootstrapSignedTelegram(page, {
    user: {
      id: 45454546,
      first_name: 'Today',
      last_name: 'Scoped',
      username: 'signed_today_scoped',
      language_code: 'ru',
    },
  });

  await page.request.put('/api/users/me', {
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Auth': runtime.initData,
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

  let feedJson: any = null;
  page.on('response', async (response) => {
    if (response.url().includes('/api/feed/today')) {
      try {
        feedJson = await response.json();
      } catch {}
    }
  });

  await page.goto('/?mock=0');
  await page.waitForLoadState('networkidle');

  const output: Record<string, unknown> = { feedJson, cards: {} };
  for (const key of ['energy', 'money', 'love', 'focus'] as const) {
    const card = page.getByTestId(`today-score-${key}`);
    await card.locator('button').first().click();
    const disclosure = card.getByTestId(`today-score-details-${key}`);
    const summary = await disclosure.locator('summary').textContent();
    const text = await disclosure.textContent();
    (output.cards as Record<string, unknown>)[key] = { summary, text };
  }

  console.log(JSON.stringify(output, null, 2));
});
