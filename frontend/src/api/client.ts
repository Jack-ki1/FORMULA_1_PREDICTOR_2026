const ENV_BASE = import.meta.env.VITE_API_BASE || '';
// Settings > Advanced can override the API base at runtime (e.g. pointing a
// deployed frontend at a different backend host without a rebuild). Read lazily
// so this file has no import-time dependency on the preferences store.
function currentBase(): string {
  try {
    const raw = localStorage.getItem('f1-preferences-v3')
    if (raw) {
      const override = JSON.parse(raw)?.advanced?.apiBaseOverride
      if (override) return override.replace(/\/$/, '')
    }
  } catch { /* noop */ }
  return ENV_BASE
}

function currentAdvanced(): { timeout: number; debug: boolean } {
  try {
    const raw = localStorage.getItem('f1-preferences-v3')
    if (raw) {
      const adv = JSON.parse(raw)?.advanced || {}
      return { timeout: adv.requestTimeoutMs ?? 20000, debug: !!adv.debugLogging }
    }
  } catch { /* noop */ }
  return { timeout: 20000, debug: false }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string,string> = { 'Content-Type': 'application/json', ...(init?.headers as any||{}) };
  const requestId = crypto.randomUUID?.() || Math.random().toString(36).slice(2);
  headers['X-Request-ID'] = requestId;
  const { timeout, debug } = currentAdvanced();

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  const startedAt = debug ? performance.now() : 0;
  let res: Response;
  try {
    res = await fetch(`${currentBase()}${path}`, { ...init, headers, signal: controller.signal });
  } catch (e: any) {
    clearTimeout(timer);
    if (e?.name === 'AbortError') {
      throw Object.assign(new Error(`Request timed out after ${timeout}ms (Settings > Advanced > Request timeout)`), { code: 'TIMEOUT', request_id: requestId });
    }
    throw e;
  }
  clearTimeout(timer);
  if (debug) {
    // eslint-disable-next-line no-console
    console.log(`[f1-api] ${init?.method || 'GET'} ${path} → ${res.status} in ${(performance.now() - startedAt).toFixed(0)}ms`, { requestId });
  }
  const rid = res.headers.get('X-Request-ID');
  
  if (!res.ok) {
    let body:any=null; try{ body=await res.json(); } catch{}
    const err = body?.error || { code: `HTTP_${res.status}`, message: res.statusText, request_id: rid || requestId };
    throw Object.assign(new Error(err.message), { code: err.code, request_id: err.request_id, details: err.details });
  }
  
  const ct = res.headers.get('content-type')||'';
  if (ct.includes('application/json')) return res.json() as Promise<T>;
  return res as unknown as T;
}

export const api = {
  get: <T>(path:string, options?: { headers?: Record<string,string> })=> req<T>(path, { headers: options?.headers }),
  post: <T>(path:string, body:any, options?: { params?: Record<string, string>; headers?: Record<string,string> })=> {
    // Handle query parameters for POST requests
    let url = path;
    if (options?.params) {
      const searchParams = new URLSearchParams(options.params);
      url += `?${searchParams.toString()}`;
    }
    return req<T>(url, { method:'POST', body: body ? JSON.stringify(body) : undefined, headers: options?.headers });
  },
  put: <T>(path:string, body:any, options?: { headers?: Record<string,string> })=> req<T>(path, { method:'PUT', body: JSON.stringify(body), headers: options?.headers}),
  delete: <T>(path:string, options?: { headers?: Record<string,string> })=> req<T>(path, { method:'DELETE', headers: options?.headers }),
}
