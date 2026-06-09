import { useState, useEffect, useCallback } from 'react'
import { supabase } from './lib/supabase'
import type { Lead, TableName, LeadStatus } from './lib/types'
import Sidebar from './components/Sidebar'
import LeadTable from './components/LeadTable'
import LeadProfile from './components/LeadProfile'

export default function App() {
  const [table, setTable]       = useState<TableName>('demo_requests')
  const [leads, setLeads]       = useState<Lead[]>([])
  const [loading, setLoading]   = useState(true)
  const [selected, setSelected] = useState<Lead | null>(null)
  const [search, setSearch]     = useState('')
  const [statuses, setStatuses] = useState<LeadStatus[]>([])
  const [owner, setOwner]       = useState('')

  const fetchLeads = useCallback(async () => {
    setLoading(true)
    const { data } = await supabase
      .from(table)
      .select('*')
      .order('created_at', { ascending: false })
    setLeads((data as Lead[]) ?? [])
    setLoading(false)
  }, [table])

  useEffect(() => { fetchLeads() }, [fetchLeads])

  // Re-fetch selected lead to get fresh data
  const handleSelect = async (lead: Lead) => {
    const { data } = await supabase.from(table).select('*').eq('id', lead.id).single()
    setSelected(data as Lead ?? lead)
  }

  const refresh = () => {
    if (selected) {
      supabase.from(table).select('*').eq('id', selected.id).single()
        .then(({ data }) => { if (data) setSelected(data as Lead) })
    }
    fetchLeads()
  }

  const filtered = leads.filter(l => {
    if (search) {
      const q = search.toLowerCase()
      if (!((l.full_name ?? '').toLowerCase().includes(q) || (l.company_raw ?? '').toLowerCase().includes(q))) return false
    }
    if (statuses.length && !statuses.includes((l.status ?? 'pending') as LeadStatus)) return false
    if (owner && !(l.contact_owner ?? '').toLowerCase().includes(owner.toLowerCase())) return false
    return true
  })

  const allLeads = leads
  const total      = allLeads.length
  const enriched   = allLeads.filter(l => l.status === 'enriched').length
  const processing = allLeads.filter(l => l.status === 'pending').length
  const failed     = allLeads.filter(l => l.status === 'failed').length

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar
        table={table}
        search={search}
        statuses={statuses}
        owner={owner}
        onTable={t => { setTable(t); setSelected(null) }}
        onSearch={setSearch}
        onStatuses={setStatuses}
        onOwner={setOwner}
        onRefresh={refresh}
        onBack={selected ? () => setSelected(null) : undefined}
      />

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-gray-400 text-sm">Loading leads…</div>
        </div>
      ) : selected ? (
        <LeadProfile lead={selected} />
      ) : (
        <LeadTable
          leads={filtered}
          onSelect={handleSelect}
          total={total}
          enriched={enriched}
          processing={processing}
          failed={failed}
        />
      )}
    </div>
  )
}
