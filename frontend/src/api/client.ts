const BASE = import.meta.env.VITE_API_BASE || '';

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string,string> = { 'Content-Type': 'application/json', ...(init?.headers as any||{}) };
  const requestId = crypto.randomUUID?.() || Math.random().toString(36).slice(2);
  headers['X-Request-ID'] = requestId;
  const token = localStorage.getItem('f1-jwt');
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
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
  get: <T>(path:string)=> req<T>(path),
  post: <T>(path:string, body:any)=> req<T>(path, { method:'POST', body: JSON.stringify(body)}),
}
