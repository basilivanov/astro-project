import { waitForTelegramWebAppRuntime } from '../../lib/telegram-runtime';

describe('waitForTelegramWebAppRuntime', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
    window.history.replaceState({}, '', '/?foo=bar#tg');
    delete (window as Window & typeof globalThis & { Telegram?: unknown }).Telegram;
    delete (window as Window & typeof globalThis & { __TEST_TELEGRAM_RUNTIME__?: unknown }).__TEST_TELEGRAM_RUNTIME__;
  });

  it('waits for late initData from Telegram runtime', async () => {
    window.setTimeout(() => {
      (window as Window & typeof globalThis & { Telegram?: unknown }).Telegram = {
        WebApp: {
          initData: 'signed-late',
          initDataUnsafe: { user: { id: 42, first_name: 'Late' } },
          ready: jest.fn(),
          expand: jest.fn(),
        },
      };
    }, 50);

    const result = await waitForTelegramWebAppRuntime({ timeoutMs: 500, intervalMs: 20 });
    expect(result.mode).toBe('telegram');
    expect(result.outcome.kind).toBe('late_ready');
    expect(result.initData).toBe('signed-late');
    expect(result.user?.id).toBe(42);
  });

  it('returns initdata_missing when runtime appears without initData', async () => {
    (window as Window & typeof globalThis & { Telegram?: unknown }).Telegram = {
      WebApp: {
        initData: '',
        initDataUnsafe: { user: { id: 7, first_name: 'Empty' } },
      },
    };

    const result = await waitForTelegramWebAppRuntime({ timeoutMs: 120, intervalMs: 20 });
    expect(result.mode).toBe('none');
    expect(result.outcome.kind).toBe('initdata_missing');
    expect(result.diagnostics.webAppPresent).toBe(true);
  });

  it('returns runtime_missing when Telegram never appears', async () => {
    const result = await waitForTelegramWebAppRuntime({ timeoutMs: 120, intervalMs: 20 });
    expect(result.mode).toBe('none');
    expect(result.outcome.kind).toBe('runtime_missing');
    expect(result.diagnostics.webAppPresent).toBe(false);
  });
});
