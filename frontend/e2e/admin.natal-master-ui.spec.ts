import { test, expect } from '@playwright/test';

const reportId = 'admin-natal-master-report';

const reportPayload = {
  report: {
    id: reportId,
    report_type: 'natal_master',
    status: 'in_progress',
    paid: true,
    created_at: new Date('2026-03-20T10:00:00Z').toISOString(),
    updated_at: new Date('2026-03-20T10:05:00Z').toISOString(),
    client_id: 'client-1',
    client_name: 'Елена Орлова',
    chunk_count: 15,
    error_message: null,
    error_at: null,
  },
  chart_svg: '<svg width="200" height="200"><circle cx="100" cy="100" r="80"></circle></svg>',
  runs: [
    {
      id: 'run-1',
      status: 'in_progress',
      created_at: new Date('2026-03-20T10:00:00Z').toISOString(),
      started_at: new Date('2026-03-20T10:01:00Z').toISOString(),
      finished_at: null,
      total_tokens: 3210,
      error_message: null,
    },
  ],
  chunks: [
    {
      id: 'chunk-1',
      section: 'executive_summary',
      title: 'Executive summary',
      status: 'completed',
      order_index: 0,
      created_at: new Date('2026-03-20T10:01:00Z').toISOString(),
      error_message: null,
      error_at: null,
      content: JSON.stringify([{ type: 'paragraph', text: 'Сильное открытие без воды и с ясным фокусом.' }]),
    },
    {
      id: 'chunk-2',
      section: 'core_identity',
      title: 'Core identity',
      status: 'in_progress',
      order_index: 1,
      created_at: new Date('2026-03-20T10:02:00Z').toISOString(),
      error_message: null,
      error_at: null,
      content: null,
    },
    {
      id: 'chunk-3',
      section: 'final_synthesis',
      title: 'Final synthesis',
      status: 'completed',
      order_index: 14,
      created_at: new Date('2026-03-20T10:03:00Z').toISOString(),
      error_message: 'Дополнено автоматически после fallback',
      error_at: new Date('2026-03-20T10:03:30Z').toISOString(),
      content: JSON.stringify([{ type: 'paragraph', text: 'Дополнено автоматически: финал пока держится на fallback-ветке.' }]),
    },
  ],
};

test.describe('Admin natal_master UI', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.sessionStorage.setItem('mock_telegram_user', '1');
      (window as any).Telegram = {
        WebApp: {
          initData: '123456789',
          ready: () => {},
          expand: () => {},
          close: () => {},
          initDataUnsafe: { user: { id: 123456789, first_name: 'Admin' } },
        },
      };
    });

    await page.route(`**/api/admin/reports/${reportId}*`, async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(reportPayload) });
    });

    await page.route(`**/api/admin/reports/${reportId}/sections/core_identity`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...reportPayload.chunks[1],
          status: 'completed',
          content: JSON.stringify([{ type: 'paragraph', text: 'Личностное ядро уже собрано и доступно для просмотра.' }]),
        }),
      });
    });

    await page.route(`**/api/admin/reports/${reportId}/regenerate/async`, async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ report_id: reportId, status: 'in_progress' }) });
    });

    await page.route(`**/api/admin/reports/${reportId}/sections/**/regenerate/async`, async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true }) });
    });
  });

  test('happy-path: показывает контроль генерации и выгрузку', async ({ page }) => {
    await page.goto(`/reports/${reportId}`);

    await expect(page.getByText('Елена Орлова')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Сгенерить всё' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Скачать Markdown' })).toBeVisible();
    await expect(page.getByText('Сильное открытие без воды и с ясным фокусом.')).toBeVisible();

    await page.getByRole('button', { name: 'Сгенерить всё' }).click();
    await expect(page.getByText('Запуск принят. Идём по секциям последовательно.')).toBeVisible();

    await page.getByText('Core identity').click();
    await expect(page.getByText('Секция сейчас в работе. После ответа модели блоки появятся здесь автоматически.')).toBeVisible();

    const download = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Скачать Markdown' }).click();
    await download;
  });

  test('error-path: подсвечивает fallback в summary и final', async ({ page }) => {
    await page.goto(`/reports/${reportId}`);

    await expect(page.getByText('Быстрый взгляд на opening')).toBeVisible();
    await expect(page.getByText('Быстрый взгляд на closing')).toBeVisible();
    await expect(page.getByText('Внимание: видны fallback-маркеры')).toBeVisible();
    await expect(page.getByText('Ошибка пайплайна')).toHaveCount(0);
    await expect(page.getByText('Дополнено автоматически: финал пока держится на fallback-ветке.')).toBeVisible();
  });
});
