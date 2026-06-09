import type { LeadStatus } from '../lib/types'

const cfg: Record<string, { bg: string; text: string; dot: string; label: string }> = {
  enriched: { bg: 'bg-green-50',  text: 'text-green-700',  dot: 'bg-green-500',  label: 'Enriched'   },
  pending:  { bg: 'bg-yellow-50', text: 'text-yellow-700', dot: 'bg-yellow-400', label: 'Processing' },
  failed:   { bg: 'bg-red-50',    text: 'text-red-700',    dot: 'bg-red-500',    label: 'Failed'     },
}

export default function StatusBadge({ status }: { status: LeadStatus | null }) {
  const s = cfg[status ?? 'pending'] ?? cfg.pending
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold ${s.bg} ${s.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot} ${status === 'pending' ? 'animate-pulse' : ''}`} />
      {s.label}
    </span>
  )
}
