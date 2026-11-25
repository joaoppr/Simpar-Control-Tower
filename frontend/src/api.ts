import { createContext, useContext, useEffect, useState } from 'react'

const BASE_PATH = import.meta.env.BASE_URL.replace(/\/$/, '')

export async function api<T = any>(url: string, init?: RequestInit): Promise<T> {
  const apiUrl = url.startsWith('/api/') ? `${BASE_PATH}${url}` : url
  const r = await fetch(apiUrl, { headers: { 'Content-Type': 'application/json' }, ...init })
  if (!r.ok) {
    let msg = r.statusText
    try { msg = (await r.json()).detail || msg } catch { /* ignore */ }
    throw new Error(`${r.status} ${msg}`)
  }
  return r.json()
}

export function useApi<T = any>(url: string | null, deps: any[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(!!url)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    if (!url) return
    let alive = true
    setLoading(true)
    api<T>(url).then((d) => { if (alive) { setData(d); setError(null) } })
      .catch((e) => alive && setError(String(e.message || e)))
      .finally(() => alive && setLoading(false))
    return () => { alive = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, ...deps])
  return { data, loading, error }
}

export const qs = (o: Record<string, any>) => {
  const p = new URLSearchParams()
  Object.entries(o).forEach(([k, v]) => v !== undefined && v !== null && v !== '' && p.set(k, String(v)))
  const s = p.toString()
  return s ? `?${s}` : ''
}

export type Meta = {
  org: { code: string; name: string }
  reference_month: string
  months: string[]
  companies: { code: string; name: string; segment: string; color: string }[]
  clouds: { code: string; name: string; color: string; cost_source: string }[]
}
export const MetaCtx = createContext<Meta | null>(null)
export const useMeta = () => useContext(MetaCtx)!
