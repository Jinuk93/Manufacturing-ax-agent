// ============================================================
// API 클라이언트 — FastAPI 백엔드 연동 (vite.config에서 /api 프록시)
// ============================================================

const BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${path}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
}
