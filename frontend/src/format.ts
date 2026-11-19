const nf0 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 })
const nf1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
const nf2 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export const brl = (v?: number | null) => (v == null ? '—' : 'R$ ' + nf0.format(v))
export const brlc = (v?: number | null) => {
  if (v == null) return '—'
  const a = Math.abs(v), s = v < 0 ? '-' : ''
  if (a >= 1e6) return `${s}R$ ${nf2.format(a / 1e6)} mi`
  if (a >= 1e3) return `${s}R$ ${nf0.format(a / 1e3)} mil`
  return `${s}R$ ${nf0.format(a)}`
}
export const num = (v?: number | null) => (v == null ? '—' : nf0.format(v))
export const pct = (v?: number | null, signed = false) =>
  v == null ? '—' : `${signed && v > 0 ? '+' : ''}${nf1.format(v)}%`
const M = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
export const mlabel = (iso: string) => `${M[+iso.slice(5, 7) - 1]}/${iso.slice(2, 4)}`
export const mlong = (iso: string) => {
  const L = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
  return `${L[+iso.slice(5, 7) - 1]} de ${iso.slice(0, 4)}`
}

export const CLOUD_COLOR: Record<string, string> = {
  aws: '#F59E0B', azure: '#2563EB', oci: '#E11D48', gcp: '#0E9F8E', huawei: '#7C3AED',
}
export const CLOUD_NAME: Record<string, string> = {
  aws: 'AWS', azure: 'Azure', oci: 'OCI', gcp: 'Google Cloud', huawei: 'Huawei Cloud',
}
export const PALETTE = ['#4F46E5', '#0E9F8E', '#F59E0B', '#E11D48', '#2563EB', '#7C3AED', '#64748B', '#06B6D4', '#84CC16', '#EC4899']
