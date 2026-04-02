import { test, expect, type Page, type Route } from '@playwright/test';
import {
  attachConsoleAndPageErrors,
  bootstrapMockTelegram,
  expectNoCrash,
  expectNoRouteHygieneIssues,
} from './utils';

type AdminUserDetail = {
  id: string;
  telegram_id: number;
  full_name: string;
  username: string;
  balance: number;
  subscription_active_until: string | null;
  created_at: string;
  is_partner: boolean;
  referral_code: string;
  reports_count: number;
  referrals_count: number;
  recent_reports: { id: string; type: string; status: string; created_at: string }[];
  recent_transactions: { id: string; amount: number; type: string; status: string; created_at: string }[];
};

type AdminAuditLog = {
  id: string;
  action: string;
  reason: string;
  details: string;
  created_at: string;
  admin_name: string;
  target_user_name: string;
};

type AdminClientDetailPayload = {
  client: {
    id: string;
    full_name: string;
    notes: string | null;
    birth_datetime: string;
    birth_location: string | null;
    birth_time_known: boolean;
    birth_lat: number | null;
    birth_lon: number | null;
    birth_timezone: string | null;
    birth_place_id: string | null;
  };
  reports: {
    id: string;
    report_type: string;
    status: string;
    created_at: string;
    error_message?: string | null;
  }[];
};

const userDetail: AdminUserDetail = {
  id: 'user-42',
  telegram_id: 424242,
  full_name: 'Мария Админова',
  username: 'maria_admin',
  balance: 1500,
  subscription_active_until: '2026-05-01T00:00:00Z',
  created_at: '2026-01-15T08:30:00Z',
  is_partner: true,
  referral_code: 'MARIA42',
  reports_count: 3,
  referrals_count: 1,
  recent_reports: [
    {
      id: 'report-1',
      type: 'natal_master',
      status: 'completed',
      created_at: '2026-03-30T10:00:00Z',
    },
  ],
  recent_transactions: [
    {
      id: 'txn-1',
      amount: 500,
      type: 'credit',
      status: 'completed',
      created_at: '2026-03-30T11:00:00Z',
    },
  ],
};

const auditLogs: AdminAuditLog[] = [
  {
    id: 'audit-1',
    action: 'grant_credits',
    reason: 'Lane 3 route guard',
    details: '{"credits": 3}',
    created_at: '2026-03-30T12:00:00Z',
    admin_name: 'Мария Админова',
    target_user_name: 'Иван Клиент',
  },
];

async function fulfillJson(route: Route, body: unknown) {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(body),
  });
}

async function setupAdminDirectRouteHarness(page: Page) {
  await bootstrapMockTelegram(page);

  await page.route('**/api/analytics/**', async (route) => {
    await fulfillJson(route, { ok: true });
  });

  await page.route('**/api/admin/audit', async (route) => {
    await fulfillJson(route, auditLogs);
  });

  await page.route('**/api/admin/users/user-42', async (route) => {
    await fulfillJson(route, userDetail);
  });
}

test.describe('Admin direct-route guards', () => {
  test.beforeEach(async ({ page }) => {
    await setupAdminDirectRouteHarness(page);
  });

  test('guards /admin/audit deep-link load, key marker, affordance, and hygiene', async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);

    try {
      await page.goto('/admin/audit');
      await expectNoCrash(page);
      await expect(page.getByRole('heading', { name: 'Аудит действий' })).toBeVisible();
      await expect(page.getByText('grant_credits')).toBeVisible();
      await expect(page.getByText('Мария Админова')).toBeVisible();
      await expect(page.getByText('Иван Клиент')).toBeVisible();
      await expectNoRouteHygieneIssues('/admin/audit', hygiene);
    } finally {
      hygiene.dispose();
    }
  });

  test('guards /admin/users/[id] deep-link detail load and admin action affordances', async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);

    try {
      await page.goto('/admin/users/user-42');
      await expectNoCrash(page);
      await expect(page.getByRole('heading', { name: 'Мария Админова' })).toBeVisible();
      await expect(page.getByText('@maria_admin')).toBeVisible();
      await expect(page.getByRole('button', { name: '+14д' })).toBeVisible();
      await expect(page.getByRole('button', { name: '+Пополнить' })).toBeVisible();
      await expectNoRouteHygieneIssues('/admin/users/user-42', hygiene);
    } finally {
      hygiene.dispose();
    }
  });

  test('guards /admin/clients/[id] deep-link detail load and primary affordances', async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);

    try {
      await page.goto('/admin/clients');
      const uniqueName = `Lane3 Client ${Date.now()}`;

      await page.fill('input[name="client_name"]', uniqueName);
      await page.fill('input[name="birth_date_only"]', '1992-02-03');
      await page.fill('input[name="birth_time"]', '08:45');
      await page.fill('input[placeholder="Начните вводить город"]', 'Moscow');
      await page.waitForSelector('.suggestions .suggestion', { timeout: 15000 });
      await page.click('.suggestions .suggestion:not(.muted):first-child');
      await page.click('button:has-text("Создать клиента")');

      await page.waitForURL(/\/create\?client_id=.+/);
      const clientId = new URL(page.url()).searchParams.get('client_id');
      expect(clientId).toBeTruthy();

      await page.goto(`/admin/clients/${clientId}`, { waitUntil: 'networkidle' });
      await expectNoCrash(page);
      await expect(page.getByRole('heading', { name: uniqueName })).toBeVisible();
      await expect(page.getByText('Клиент', { exact: true })).toBeVisible();
      await expect(page.getByText('Редактировать профиль')).toBeVisible();
      await expect(page.getByRole('link', { name: 'Назад к списку' })).toBeVisible();
      await expect(page.getByRole('button', { name: 'Сгенерировать отчет' })).toBeVisible();
      await expectNoRouteHygieneIssues(`/admin/clients/${clientId}`, hygiene);
    } finally {
      hygiene.dispose();
    }
  });
});
