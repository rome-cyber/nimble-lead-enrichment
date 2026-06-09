import { useState } from 'react'
import type { Lead } from '../lib/types'
import { favUrl, getDomain, fmtDate, toList, cleanMd, avatarColor, initials } from '../lib/utils'
import StatusBadge from './StatusBadge'
import ReactMarkdown from 'react-markdown'

export default function LeadProfile({ lead }: { lead: Lead }) {
  const [reportOpen, setReportOpen] = useState(false)

  const name     = lead.full_name    || '—'
  const company  = lead.company_raw  || '—'
  const title    = lead.lead_title   || '—'
  const website  = lead.company_website || ''
  const linkedin = lead.lead_linkedin   || ''
  const email    = lead.email           || ''
  const domain   = getDomain(website)
  const fav      = favUrl(website)
  const color    = avatarColor(name)
  const ini      = initials(name)

  const buying = toList(lead.buying_signals)
  const dms    = toList(lead.decision_makers)
  const sigs   = toList(lead.recent_signals)
  const acts   = toList(lead.recent_activity)

  const rmd = (() => {
    const r = lead.report_md || ''
    const idx = r.indexOf('---')
    return idx >= 0 ? r.slice(idx) : r
  })()

  const [copied, setCopied] = useState(false)
  const copyEmail = () => {
    navigator.clipboard.writeText(email).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    })
  }

  return (
    <div className="flex-1 p-8 overflow-auto">
      {/* Hero */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 mb-5">
        <div className="flex items-start gap-5">
          <div
            className="w-14 h-14 rounded-xl flex items-center justify-center text-xl font-bold text-white flex-shrink-0"
            style={{ background: color }}
          >
            {ini}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap mb-1.5">
              {linkedin ? (
                <a href={linkedin} target="_blank" rel="noreferrer"
                   className="text-2xl font-extrabold text-gray-900 hover:text-indigo-600 transition-colors tracking-tight">
                  {name}
                </a>
              ) : (
                <span className="text-2xl font-extrabold text-gray-900 tracking-tight">{name}</span>
              )}
              <StatusBadge status={lead.status} />
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-4 flex-wrap">
              <span>{title}</span>
              <span className="text-gray-300">·</span>
              {fav && <img src={fav} className="w-5 h-5 rounded object-contain" onError={e => (e.currentTarget.style.display='none')} />}
              {website ? (
                <a href={website} target="_blank" rel="noreferrer" className="text-gray-700 font-medium hover:text-indigo-600 transition-colors">{company}</a>
              ) : (
                <span className="text-gray-700 font-medium">{company}</span>
              )}
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {linkedin && (
                <a href={linkedin} target="_blank" rel="noreferrer"
                   className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-50 text-blue-700 border border-blue-100 text-xs font-semibold hover:bg-blue-100 transition-colors">
                  <LinkedInIcon /> LinkedIn
                </a>
              )}
              {website && (
                <a href={website} target="_blank" rel="noreferrer"
                   className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-50 text-gray-700 border border-gray-200 text-xs font-semibold hover:bg-gray-100 transition-colors">
                  ↗ {domain}
                </a>
              )}
              {email && (
                <button onClick={copyEmail}
                   className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-50 text-gray-700 border border-gray-200 text-xs font-semibold hover:bg-gray-100 transition-colors">
                  {copied ? '✓ Copied' : `✉ ${email}`}
                </button>
              )}
            </div>
          </div>
          <div className="text-right flex-shrink-0 pt-1">
            <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Enriched</p>
            <p className="text-sm font-semibold text-gray-700 mt-0.5">{fmtDate(lead.enriched_at)}</p>
            <p className="text-xs text-gray-400 mt-0.5">{fmtDate(lead.created_at)}</p>
          </div>
        </div>
      </div>

      {/* Row 1: Company + Lead Profile */}
      <div className="grid grid-cols-2 gap-5 mb-5">
        <Card title="🏢 Company">
          {lead.company_description && (
            <p className="text-sm text-gray-500 leading-relaxed mb-5 pb-5 border-b border-gray-50">{lead.company_description}</p>
          )}
          <Field label="Company"  value={company} />
          <Field label="Industry" value={lead.industry} />
          <Field label="Stage"    value={lead.company_stage} />
          <Field label="Size"     value={lead.company_size} />
          <Field label="HQ"       value={lead.company_hq} />
          {lead.company_founded && <Field label="Founded" value={lead.company_founded} />}
          <Field label="Website"  value={website ? <a href={website} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">{domain}</a> : null} />
        </Card>

        <Card title="👤 Lead Profile">
          <Field label="Full Name"     value={name} />
          <Field label="Email"         value={email} />
          <Field label="Title"         value={lead.lead_title} />
          <Field label="Tenure"        value={lead.lead_tenure} />
          <Field label="Background"    value={lead.lead_background} />
          <Field label="Verified"      value={<VerifiedBadge v={lead.lead_verified} />} />
          <Field label="LinkedIn"      value={linkedin ? <a href={linkedin} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">View profile ↗</a> : null} />
          <Field label="Contact Owner" value={lead.contact_owner} />
          <Field label="Traffic Source" value={lead.traffic_source} />
          <Field label="Signup Date"   value={fmtDate(lead.created_at)} />
        </Card>
      </div>

      {/* Buying Signals */}
      <Card title="🎯 Buying Signals" className="mb-5">
        {buying.length === 0 ? (
          <p className="text-sm text-gray-400">No buying signals identified</p>
        ) : (
          <div className="flex flex-col gap-2">
            {buying.map((item, i) => (
              <div key={i} className="flex items-start gap-3 bg-green-50 border border-green-100 rounded-xl p-4">
                <span className="text-green-600 text-sm mt-0.5 flex-shrink-0">◆</span>
                <span className="text-sm text-green-900 font-medium leading-snug">{cleanMd(item)}</span>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Row 3: Decision Makers + Recent Signals */}
      <div className="grid grid-cols-2 gap-5 mb-5">
        <Card title="👥 Decision Makers">
          <ListRows items={dms} dot="#6366f1" />
        </Card>
        <Card title="📡 Recent Company Signals">
          <ListRows items={sigs} dot="#f59e0b" />
        </Card>
      </div>

      {/* Competitive Intel */}
      <Card title="⚔️ Competitive Intel" className="mb-5">
        <div className="grid grid-cols-3 gap-6">
          <div>
            <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">Tools they use</p>
            <div className="flex flex-wrap gap-1.5">
              {lead.competitive_using && lead.competitive_using !== '—'
                ? lead.competitive_using.split(/[,;/]/).filter(Boolean).map(t => (
                    <span key={t} className="bg-slate-100 text-slate-600 border border-slate-200 rounded-md px-2 py-0.5 text-xs font-medium">{t.trim()}</span>
                  ))
                : <span className="text-sm text-gray-400">—</span>
              }
            </div>
          </div>
          <Field label="Displacement Angle" value={lead.competitive_angle} />
          <Field label="Evidence"           value={lead.competitive_evidence} />
        </div>
      </Card>

      {/* Lead Activity */}
      {acts.length > 0 && (
        <Card title="📝 Lead's Recent Activity" className="mb-5">
          <ListRows items={acts} dot="#a855f7" />
        </Card>
      )}

      {/* Full Intelligence Report */}
      {rmd && (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <button
            onClick={() => setReportOpen(o => !o)}
            className="w-full flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
          >
            <span className="text-sm font-semibold text-gray-700">View Full Intelligence Report</span>
            <span className="text-gray-400 text-sm">{reportOpen ? '▲' : '▼'}</span>
          </button>
          {reportOpen && (
            <div className="px-6 pb-6 pt-2 border-t border-gray-50">
              <div className="report-body">
                <ReactMarkdown>{rmd}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Card({ title, children, className = '' }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-white rounded-xl border border-gray-100 shadow-sm p-6 ${className}`}>
      <p className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-5">{title}</p>
      {children}
    </div>
  )
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="mb-4">
      <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-0.5">{label}</p>
      <div className="text-sm text-gray-800 font-medium leading-snug">{value || '—'}</div>
    </div>
  )
}

function ListRows({ items, dot }: { items: string[]; dot: string }) {
  if (!items.length) return <p className="text-sm text-gray-400">None found</p>
  return (
    <div>
      {items.map((item, i) => (
        <div key={i} className="flex items-start gap-2.5 py-2.5 border-b border-gray-50 last:border-0">
          <span className="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5" style={{ background: dot }} />
          <span className="text-sm text-gray-600 leading-snug"
            dangerouslySetInnerHTML={{ __html: cleanMd(item).replace(/\(https?:\/\/[^)]+\)/g, '') }} />
        </div>
      ))}
    </div>
  )
}

function VerifiedBadge({ v }: { v: string | null }) {
  if (!v) return <span className="text-gray-400">—</span>
  if (v.includes('✅') || v.includes('Confirmed'))
    return <span className="bg-green-50 text-green-700 text-xs font-semibold px-2 py-0.5 rounded-full">✅ Confirmed</span>
  if (v.includes('⚠') || v.includes('Found'))
    return <span className="bg-yellow-50 text-yellow-700 text-xs font-semibold px-2 py-0.5 rounded-full">⚠ Unverified</span>
  return <span className="bg-red-50 text-red-700 text-xs font-semibold px-2 py-0.5 rounded-full">❌ Not found</span>
}

function LinkedInIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
    </svg>
  )
}
