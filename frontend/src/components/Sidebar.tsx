import type { TableName, LeadStatus } from '../lib/types'

const STATUSES: LeadStatus[] = ['enriched', 'pending', 'failed']

interface Props {
  table: TableName
  search: string
  statuses: LeadStatus[]
  owner: string
  onTable: (t: TableName) => void
  onSearch: (s: string) => void
  onStatuses: (s: LeadStatus[]) => void
  onOwner: (s: string) => void
  onRefresh: () => void
  onBack?: () => void
}

export default function Sidebar({ table, search, statuses, owner, onTable, onSearch, onStatuses, onOwner, onRefresh, onBack }: Props) {
  const toggleStatus = (s: LeadStatus) =>
    onStatuses(statuses.includes(s) ? statuses.filter(x => x !== s) : [...statuses, s])

  return (
    <aside className="w-64 min-h-screen bg-sidebar flex flex-col flex-shrink-0 border-r border-sidebar-border">
      <div className="px-5 pt-6 pb-5 border-b border-sidebar-border">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-indigo-600 rounded-lg flex items-center justify-center text-sm">⚡</div>
          <span className="text-base font-bold text-slate-200 tracking-tight">Nimble Leads</span>
        </div>
        <p className="text-xs text-slate-500 mt-1 ml-9">Sales Intelligence</p>
      </div>

      <div className="flex-1 px-4 py-5 flex flex-col gap-5">
        {onBack ? (
          <button
            onClick={onBack}
            className="w-full text-left text-sm text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1.5 transition-colors"
          >
            ← Back to all leads
          </button>
        ) : (
          <>
            <Section label="Source">
              {(['demo_requests', 'signups'] as TableName[]).map(t => (
                <button
                  key={t}
                  onClick={() => onTable(t)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    table === t
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-600/40'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                  }`}
                >
                  {t === 'demo_requests' ? 'Demo Requests' : 'Self-Serve Signups'}
                </button>
              ))}
            </Section>

            <Section label="Search">
              <input
                value={search}
                onChange={e => onSearch(e.target.value)}
                placeholder="Name or company…"
                className="w-full bg-sidebar-input border border-sidebar-input-border rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500/50 transition-colors"
              />
            </Section>

            <Section label="Status">
              <div className="flex flex-col gap-1">
                {STATUSES.map(s => (
                  <label key={s} className="flex items-center gap-2.5 px-1 py-1 cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={statuses.includes(s)}
                      onChange={() => toggleStatus(s)}
                      className="w-3.5 h-3.5 rounded accent-indigo-500"
                    />
                    <span className="text-sm text-slate-400 group-hover:text-slate-200 capitalize transition-colors">
                      {s === 'pending' ? 'Processing' : s.charAt(0).toUpperCase() + s.slice(1)}
                    </span>
                  </label>
                ))}
              </div>
            </Section>

            <Section label="Owner">
              <input
                value={owner}
                onChange={e => onOwner(e.target.value)}
                placeholder="Contact owner…"
                className="w-full bg-sidebar-input border border-sidebar-input-border rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500/50 transition-colors"
              />
            </Section>
          </>
        )}
      </div>

      <div className="px-4 pb-5">
        <button
          onClick={onRefresh}
          className="w-full bg-sidebar-input border border-sidebar-input-border text-blue-400 hover:bg-white/5 rounded-lg px-3 py-2 text-sm font-medium transition-colors"
        >
          ↺ Refresh
        </button>
      </div>
    </aside>
  )
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-[11px] font-semibold text-slate-600 uppercase tracking-widest mb-2">{label}</p>
      {children}
    </div>
  )
}
