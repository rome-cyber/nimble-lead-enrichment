const COLORS = ['#6366f1','#0ea5e9','#10b981','#f59e0b','#ec4899','#8b5cf6','#14b8a6','#ef4444']

export function avatarColor(name: string) {
  return COLORS[Array.from(name || '').reduce((s, c) => s + c.charCodeAt(0), 0) % COLORS.length]
}

export function initials(name: string) {
  const parts = (name || '?').split(' ')
  return (parts[0][0] + (parts.length > 1 ? parts[parts.length - 1][0] : '')).toUpperCase()
}

export function ensureHttps(url: string): string {
  if (!url) return ''
  return /^https?:\/\//i.test(url) ? url : `https://${url}`
}

export function getDomain(url: string) {
  return url ? url.replace(/https?:\/\/(www\.)?/i, '').split('/')[0] : ''
}

export function favUrl(website: string) {
  const d = getDomain(website)
  return d ? `https://www.google.com/s2/favicons?domain=${d}&sz=64` : ''
}

export function fmtDate(ts: string | null) {
  if (!ts) return '—'
  try { return new Date(ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) }
  catch { return ts.slice(0, 10) }
}

export function cleanMd(text: string): string {
  if (!text) return text
  return text
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '$1')
    .replace(/^\[([^\]]+)\]\s*/,'$1  ')
    .trim()
}

export function toList(val: unknown): string[] {
  if (Array.isArray(val)) return val.filter(Boolean).map(String)
  if (typeof val === 'string') {
    try {
      const p = JSON.parse(val)
      return Array.isArray(p) ? p.filter(Boolean).map(String) : []
    } catch { return [] }
  }
  return []
}
