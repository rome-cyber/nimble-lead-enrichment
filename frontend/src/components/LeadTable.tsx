import type { Lead } from '../lib/types'
import { favUrl, fmtDate, getDomain } from '../lib/utils'
import StatusBadge from './StatusBadge'

interface Props {
  leads: Lead[]
  onSelect: (lead: Lead) => void
  total: number
  enriched: number
  processing: number
  failed: number
}

export default function LeadTable({ leads, onSelect, total, enriched, processing, failed }: Props) {
  return (
    <div className="flex-1 p-8 overflow-auto">
      <div className="mb-7">
        <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">Lead Intelligence</h1>
        <p className="text-sm text-gray-500 mt-1">Enriched research on every inbound — click a lead to open their profile.</p>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-7">
        {[['Total', total], ['Enriched', enriched], ['Processing', processing], ['Failed', failed]].map(([label, val]) => (
          <div key={label as string} className="bg-white rounded-xl border border-gray-100 shadow-sm px-5 py-4">
            <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1">{label}</p>
            <p className="text-3xl font-bold text-gray-900 tracking-tight">{val}</p>
          </div>
        ))}
      </div>

      {leads.length === 0 ? (
        <div className="bg-white border border-gray-100 rounded-2xl p-16 text-center">
          <div className="text-4xl mb-3">🔍</div>
          <p className="font-semibold text-gray-700">No leads found</p>
          <p className="text-sm text-gray-400 mt-1">Try adjusting your filters</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="grid grid-cols-[2.5fr_2fr_2fr_1.5fr_1.5fr_1fr] px-5 py-3 border-b border-gray-50">
            {['Lead', 'Company', 'Title', 'Stage', 'Enriched', 'Status'].map(h => (
              <span key={h} className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">{h}</span>
            ))}
          </div>
          {leads.map((lead, i) => (
            <Row key={lead.id} lead={lead} onSelect={onSelect} last={i === leads.length - 1} />
          ))}
        </div>
      )}
    </div>
  )
}

function Row({ lead, onSelect, last }: { lead: Lead; onSelect: (l: Lead) => void; last: boolean }) {
  const fav = favUrl(lead.company_website ?? '')
  const domain = getDomain(lead.company_website ?? '')

  return (
    <div className={`grid grid-cols-[2.5fr_2fr_2fr_1.5fr_1.5fr_1fr] items-center px-5 py-3 hover:bg-gray-50 transition-colors cursor-default ${!last ? 'border-b border-gray-50' : ''}`}>
      <button
        onClick={() => onSelect(lead)}
        className="text-left text-sm font-semibold text-gray-900 hover:text-indigo-600 transition-colors truncate"
      >
        {lead.full_name || '—'}
      </button>
      <div className="flex items-center gap-2 text-sm text-gray-600 truncate">
        {fav && <img src={fav} className="w-4 h-4 rounded object-contain flex-shrink-0" onError={e => (e.currentTarget.style.display = 'none')} />}
        {domain || lead.company_raw || '—'}
      </div>
      <span className="text-sm text-gray-500 truncate">{lead.lead_title || '—'}</span>
      <span className="text-sm text-gray-500 truncate">{lead.company_stage || '—'}</span>
      <span className="text-sm text-gray-500">{fmtDate(lead.enriched_at)}</span>
      <StatusBadge status={lead.status} />
    </div>
  )
}
