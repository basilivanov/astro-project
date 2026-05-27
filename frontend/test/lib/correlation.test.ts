import { CorrelationManager, correlatedFetch, withCorrelationHeaders } from '../../lib/correlation';

describe('correlation helpers', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    jest.restoreAllMocks();
  });

  it('ensures and persists a correlation id', () => {
    const id = CorrelationManager.ensureCorrelationId();
    expect(id).toBeTruthy();
    expect(CorrelationManager.getCorrelationId()).toBe(id);
    expect(window.sessionStorage.getItem('astro.correlation_id')).toBe(id);
  });

  it('adds correlation headers and semantic block metadata', () => {
    const init = withCorrelationHeaders(
      { headers: { Existing: 'value' } },
      { flowId: 'flow.catalog', block: 'BLOCK_A', semanticBlock: 'SEM_A', correlationId: 'corr-1', traceId: 'trace-1' },
    );
    const headers = Object.fromEntries(new Headers(init.headers).entries());
    expect(headers['existing']).toBe('value');
    expect(headers['x-correlation-id']).toBe('corr-1');
    expect(headers['x-trace-id']).toBe('trace-1');
    expect(headers['x-flow-id']).toBe('flow.catalog');
    expect(headers['x-flow-block']).toBe('BLOCK_A');
    expect(headers['x-semantic-block']).toBe('SEM_A');
  });

  it('wraps fetch with generated headers', async () => {
    const fetchMock = jest.fn().mockResolvedValue(new Response('{}', { status: 200 }));
    global.fetch = fetchMock as typeof fetch;

    await correlatedFetch('/api/ping', { method: 'POST' }, { flowId: 'flow.test' });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, init] = fetchMock.mock.calls[0] as [RequestInfo | URL, RequestInit];
    const headers = Object.fromEntries(new Headers(init.headers).entries());
    expect(headers['x-flow-id']).toBe('flow.test');
    expect(headers['x-correlation-id']).toBeTruthy();
  });
});
