import { test, expect } from '@playwright/test';
import { bootstrapMockTelegram, expectNoCrash } from './utils';

const reportId = '22222222-2222-2222-2222-222222222222';
const reportListRoute = '**/api/admin/reports?*';
const reportDetailRoute = `**/api/admin/reports/${reportId}?include_content=1`;
const sectionRegenerateRoute = `**/api/admin/reports/${reportId}/sections/**/regenerate/async`;
const exportMarkdownRoute = `**/api/admin/reports/${reportId}/export?format=md`;
const exportPdfRoute = `**/api/admin/reports/${reportId}/export?format=pdf`;

const queueResponse = [
  {
    id: reportId,
    report_type: 'natal_master',
    status: 'done',
    paid: true,
    error_message: null,
    error_at: null,
    created_at: '2026-03-20T10:00:00Z',
    updated_at: '2026-03-20T10:05:00Z',
    client_id: 'client-ops-1',
    client_name: 'Operations E2E Client',
    chunk_count: 4,
  },
];

const detailResponse = {
  report: {
    id: reportId,
    report_type: 'natal_master',
    status: 'done',
    paid: true,
    error_message: null,
    error_at: null,
    created_at: '2026-03-20T10:00:00Z',
    updated_at: '2026-03-20T10:05:00Z',
    client_id: 'client-ops-1',
    client_name: 'Operations E2E Client',
    chunk_count: 4,
  },
  chunks: [
    {
      id: 'chunk-summary',
      section: 'executive_summary',
      title: 'Executive Summary',
      status: 'done',
      order_index: 0,
      content: 'Сильное summary без fallback.',
      content_html: null,
      created_at: '2026-03-20T10:01:00Z',
      error_message: null,
      error_at: null,
    },
    {
      id: 'chunk-core',
      section: 'core_signature',
      title: 'Core Signature',
      status: 'done',
      order_index: 1,
      content: 'Подробный разбор ядра личности и паттернов поведения.',
      content_html: null,
      created_at: '2026-03-20T10:02:00Z',
      error_message: null,
      error_at: null,
    },
    {
      id: 'chunk-life',
      section: 'life_vector',
      title: 'Life Vector',
      status: 'done',
      order_index: 2,
      content: 'Фокус на долгой траектории, решениях и направлении развития.',
      content_html: null,
      created_at: '2026-03-20T10:03:00Z',
      error_message: null,
      error_at: null,
    },
    {
      id: 'chunk-final',
      section: 'final_synthesis',
      title: 'Final Synthesis',
      status: 'done',
      order_index: 3,
      content: 'Финальная сборка без признаков fallback.',
      content_html: null,
      created_at: '2026-03-20T10:04:00Z',
      error_message: null,
      error_at: null,
    },
  ],
  runs: [
    {
      id: 'run-1',
      status: 'done',
      error_message: null,
      started_at: '2026-03-20T10:00:30Z',
      finished_at: '2026-03-20T10:04:30Z',
      prompt_tokens: 1200,
      completion_tokens: 3300,
      total_tokens: 4500,
      estimated_cost: 0.42,
      created_at: '2026-03-20T10:00:00Z',
    },
  ],
  chart_svg: '<svg width="120" height="120" xmlns="http://www.w3.org/2000/svg"><circle cx="60" cy="60" r="42" fill="none" stroke="#7c3aed" stroke-width="4" /></svg>',
};

async function mockAdminOperations(page: import('@playwright/test').Page) {
  await page.route(reportListRoute, async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(queueResponse) });
  });

  await page.route(reportDetailRoute, async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(detailResponse) });
  });

  await page.route(sectionRegenerateRoute, async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, status: 'queued' }) });
  });

  await page.route(exportMarkdownRoute, async (route) => {
    await route.fulfill({
      status: 200,
      headers: {
        'content-type': 'text/markdown; charset=utf-8',
        'content-disposition': `attachment; filename="${reportId}.md"`,
      },
      body: '# Natal Master\n\nMock markdown export.',
    });
  });

  await page.route(exportPdfRoute, async (route) => {
    await route.fulfill({
      status: 200,
      headers: {
        'content-type': 'application/pdf',
        'content-disposition': `attachment; filename="${reportId}.pdf"`,
      },
      body: 'fake-pdf-binary',
    });
  });
}

test.describe('Admin operations detail view', () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapMockTelegram(page);
    await mockAdminOperations(page);
  });

  test('detail view supports section regenerate, exports, and telemetry', async ({ page }) => {
    const consoleEvents: Array<{ event: string; payload: Record<string, unknown> }> = [];
    page.on('console', async (message) => {
      if (message.type() !== 'info') return;
      const args = message.args();
      if (args.length < 2) return;
      const event = await args[0].jsonValue().catch(() => null);
      const payload = await args[1].jsonValue().catch(() => null);
      if (typeof event === 'string' && payload && typeof payload === 'object') {
        consoleEvents.push({ event, payload: payload as Record<string, unknown> });
      }
    });

    await page.goto(`/admin/reports/${reportId}`);
    await expectNoCrash(page);

    await expect(page.getByRole('heading', { name: /Запуск, контроль и выгрузка natal_master/i })).toBeVisible();
    await expect(page.getByText(`Клиент: Operations E2E Client`)).toBeVisible();
    await expect(page.getByText(`ID: ${reportId}`)).toBeVisible();
    await expect(page.getByText('Краткий итог')).toBeVisible();
    await expect(page.getByText('Финальный синтез')).toBeVisible();
    await expect(page.getByTestId('admin-section-core_signature')).toBeVisible();

    const sectionCard = page.getByTestId('admin-section-core_signature');
    await expect(sectionCard).toContainText('Подробный разбор ядра личности');

    const generateSectionButton = page.getByTestId('admin-generate-section-core_signature');
    await generateSectionButton.evaluate((element) => {
      (element as HTMLButtonElement).click();
    });
    await expect
      .poll(
        () =>
          consoleEvents.some(
            ({ event, payload }) =>
              event === 'admin.section_regenerate'
              && payload.stage === 'queued'
              && payload.reportId === reportId
              && payload.sectionId === 'core_signature',
          ),
        { timeout: 15000 },
      )
      .toBe(true);

    const markdownDownload = page.waitForEvent('download');
    await page.getByTestId('admin-download-markdown').click();
    const markdownFile = await markdownDownload;
    expect(markdownFile.suggestedFilename()).toBe(`${reportId}.md`);
    await expect(page.getByText('Markdown скачивается.')).toBeVisible();

    await page.getByTestId('admin-download-pdf').evaluate((element) => {
      (element as HTMLButtonElement).click();
    });

    await expect
      .poll(
        () =>
          consoleEvents.filter(
            ({ event, payload }) => event === 'admin.export' && payload.reportId === reportId && payload.format === 'pdf',
          ).length,
        { timeout: 15000 },
      )
      .toBeGreaterThanOrEqual(2);

    await expect.poll(() => consoleEvents.length, { timeout: 5000 }).toBeGreaterThanOrEqual(5);

    expect(consoleEvents).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          event: 'admin.entry',
          payload: expect.objectContaining({ stage: 'detail_fetch_start', reportId }),
        }),
        expect.objectContaining({
          event: 'admin.entry',
          payload: expect.objectContaining({ stage: 'detail_fetch_done', reportId }),
        }),
        expect.objectContaining({
          event: 'admin.section_regenerate',
          payload: expect.objectContaining({ stage: 'request', reportId, sectionId: 'core_signature' }),
        }),
        expect.objectContaining({
          event: 'admin.section_regenerate',
          payload: expect.objectContaining({ stage: 'queued', reportId, sectionId: 'core_signature' }),
        }),
        expect.objectContaining({
          event: 'admin.export',
          payload: expect.objectContaining({ stage: 'request', reportId, format: 'md' }),
        }),
        expect.objectContaining({
          event: 'admin.export',
          payload: expect.objectContaining({ stage: 'download_started', reportId, format: 'md' }),
        }),
        expect.objectContaining({
          event: 'admin.export',
          payload: expect.objectContaining({ stage: 'request', reportId, format: 'pdf' }),
        }),
        expect.objectContaining({
          event: 'admin.export',
          payload: expect.objectContaining({ stage: 'download_started', reportId, format: 'pdf' }),
        }),
      ]),
    );
  });
});
