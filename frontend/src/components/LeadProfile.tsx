import { useState } from 'react'
import type { Lead } from '../lib/types'
import { favUrl, getDomain, fmtDate, toList, cleanMd, avatarColor, initials, ensureHttps } from '../lib/utils'
import StatusBadge from './StatusBadge'
import { Globe, Mail, Copy, Check, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react'

// LinkedIn brand icon — not in lucide-react (no brand icons in v1)
function LinkedInIcon({ size = 14 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
    </svg>
  )
}

// ── Urgency inference ──────────────────────────────────────────────────────

type Urgency = 'high' | 'medium' | 'info'

function inferUrgency(text: string): Urgency {
  const t = text.toLowerCase()
  if (/fundrais|raised \$|series [abcde]|seed round|key hire|strategic hire|head of (sales|marketing|revenue|product|engineering)|chief (revenue|marketing|product|technology)|new (cto|ceo|cmo|cro|cpo)|(cto|ceo|cmo|cro) (join|hire|appoint)|displac|beat out|won (the )?(deal|contract)|signed up|demo request|direct intent|inbound/.test(t)) return 'high'
  if (/partnership|acqui|expand|new market|new office|launched|product launch|integrat|growth round/.test(t)) return 'medium'
  return 'info'
}

// ── Source URL extraction from signal prose ────────────────────────────────

interface Source { url: string; label: string }

function parseSignalText(raw: string): { text: string; sources: Source[] } {
  const sources: Source[] = []
  const text = raw
    .replace(
      /\s*\((?:https?:\/\/)?([a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.(?:[a-zA-Z]{2,}\.?)+[^\s)]*)\)/g,
      (_, inner) => {
        const url = ensureHttps(inner)
        const label = inner.replace(/^https?:\/\//i, '').replace(/^www\./i, '').split('/')[0]
        if (label.includes('.')) sources.push({ url, label })
        return ''
      }
    )
    .trim()
    .replace(/\s{2,}/g, ' ')
  return { text, sources }
}

// ── Decision maker parsing ─────────────────────────────────────────────────

type Influence = 'budget' | 'champion' | 'advisor' | 'unknown'

interface DM {
  name: string
  role: string
  description: string
  influence: Influence
  linkedin?: string
}

function parseDM(raw: string): DM {
  const nameMatch = raw.match(/^\*\*([^*]+)\*\*/)
  const name = nameMatch ? nameMatch[1] : raw.split(/\s*·\s*/)[0].trim()
  const rest = raw.replace(/^\*\*[^*]+\*\*\s*·?\s*/, '').replace(/^\s*·\s*/, '')
  const parts = rest.split(/\s*·\s*/)
  const role = parts[0]?.trim() || ''
  const description = parts.slice(1).join(' · ').trim()
  const all = (role + ' ' + description).toLowerCase()

  let influence: Influence = 'unknown'
  if (/budget|final authority|purchasing|procurement|approves|signs off/.test(all)) influence = 'budget'
  else if (/champion|internal advocate|power user|sponsor/.test(all)) influence = 'champion'
  else if (/advisor|consultant|board/.test(all)) influence = 'advisor'

  const linkedinMatch = raw.match(/(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[\w-]+/)
  const linkedin = linkedinMatch ? ensureHttps(linkedinMatch[0]) : undefined

  return { name, role, description, influence, linkedin }
}

// ── Timeline item parsing ──────────────────────────────────────────────────

interface TimelineItem { date: string; text: string; sources: Source[] }

function parseTimeline(raw: string): TimelineItem {
  const cleaned = raw.replace(/^\[([^\]]+)\]\s*/, '$1 — ').trim()
  const idx = cleaned.indexOf(' — ')
  const combined = idx > 0 ? cleaned.slice(idx + 3) : cleaned
  const date = idx > 0 ? cleaned.slice(0, idx) : ''
  const { text, sources } = parseSignalText(combined)
  return { date, text, sources }
}

// ── ICP fit calculation ────────────────────────────────────────────────────

type ICPTier = 'strong' | 'partial' | 'weak'
interface ICPResult { tier: ICPTier; label: string; factors: string[] }

function calcICP(lead: Lead, highUrgencyCount: number): ICPResult {
  let score = 0
  const factors: string[] = []

  // Stage (0–25)
  const stage = (lead.company_stage || '').toLowerCase()
  if (/series [abcde]|growth|funded|venture|backed/.test(stage)) { score += 25; factors.push('Funded company') }
  else if (/pre-seed|seed|angel/.test(stage))                     { score += 15; factors.push('Seed-stage company') }
  else if (/bootstrap|private/.test(stage))                       { score += 10; factors.push('Bootstrapped') }

  // Size (0–20)
  const n = parseInt((lead.company_size || '').match(/\d+/)?.[0] || '0')
  if (n >= 20 && n <= 500)  { score += 20; factors.push('Ideal company size') }
  else if (n > 500)          { score += 10; factors.push('Enterprise size') }
  else if (n > 0)            { score += 8 }

  // Industry (0–25)
  const ind = (lead.industry || '').toLowerCase()
  if (/saas|software|tech|ai|ml|data|cloud/.test(ind))            { score += 25; factors.push('Core tech buyer') }
  else if (/health|medical|clinical|dental|vet|pharma/.test(ind)) { score += 20; factors.push('Healthcare vertical') }
  else if (/finance|fintech|legal|professional/.test(ind))        { score += 18; factors.push('Professional services') }
  else if (/recruit|staffing|hr|talent/.test(ind))                { score += 15; factors.push('HR / Recruiting') }
  else                                                             { score += 8 }

  // Signals (0–25)
  if (highUrgencyCount >= 2)                        { score += 25; factors.push('Multiple high-urgency signals') }
  else if (highUrgencyCount === 1)                   { score += 15; factors.push('High-urgency signal present') }
  else if (toList(lead.buying_signals).length > 0)  { score += 8;  factors.push('Buying signals present') }

  // Verified (0–5)
  if (lead.lead_verified && /confirmed|✅/i.test(lead.lead_verified)) { score += 5; factors.push('Identity confirmed') }

  const tier: ICPTier = score >= 65 ? 'strong' : score >= 40 ? 'partial' : 'weak'
  const label = tier === 'strong' ? 'Strong ICP Fit' : tier === 'partial' ? 'Partial Fit' : 'Weak Fit'
  return { tier, label, factors: factors.slice(0, 4) }
}

// ── Suggested outreach angle ───────────────────────────────────────────────

function buildOutreachAngle(lead: Lead, buying: string[]): string {
  const topSignal = buying[0] ? cleanMd(buying[0]) : ''
  const angle = (lead.competitive_angle || '').replace(/^—\s*/, '').trim()
  if (!topSignal && !angle) return ''
  const parts: string[] = []
  if (topSignal) parts.push(topSignal.replace(/\.?\s*$/, '.'))
  if (angle)     parts.push(angle.replace(/\.?\s*$/, '.'))
  return parts.join(' ')
}

// ── Tool chip extraction ───────────────────────────────────────────────────

function extractTools(raw: string): string[] {
  if (!raw) return []
  const trimmed = raw.trim()
  if (/^—|^no confirmed|^not found|^unknown|^couldn't|^no (tools|software|crm|ats)/i.test(trimmed)) return []
  return trimmed
    .split(/[,;|·]/)
    .map(t => t.trim())
    .filter(t => t && t.length > 1 && t.length < 60 && !t.startsWith('—') && !/^\(/.test(t))
}

// ── Stale signal detection ─────────────────────────────────────────────────

function daysSinceNewest(allSignals: string[]): number | null {
  const now = Date.now()
  let newest: number | null = null
  for (const s of allSignals) {
    const month = s.match(/\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(20\d\d)\b/i)
    const year  = s.match(/\b(20\d\d)\b/)
    let d: number | null = null
    if (month) d = new Date(`${month[1]} 1, ${month[2]}`).getTime()
    else if (year) d = new Date(`Jan 1, ${year[1]}`).getTime()
    if (d && (newest === null || d > newest)) newest = d
  }
  return newest ? Math.floor((now - newest) / 86400000) : null
}

// ─────────────────────────────────────────────────────────────────────────────

export default function LeadProfile({ lead }: { lead: Lead }) {
  const name     = lead.full_name    || '—'
  const company  = lead.company_raw  || '—'
  const title    = lead.lead_title   || ''
  const website  = ensureHttps(lead.company_website ?? '')
  const linkedin = ensureHttps(lead.lead_linkedin ?? '')
  const email    = lead.email || ''
  const domain   = getDomain(website)
  const fav      = favUrl(website)

  const buying = toList(lead.buying_signals)
  const dms    = toList(lead.decision_makers).map(parseDM)
  const sigs   = toList(lead.recent_signals).map(parseTimeline)
  const acts   = toList(lead.recent_activity).map(parseTimeline)
  const tools  = extractTools(lead.competitive_using || '')

  const highUrgencyCount = buying.filter(s => inferUrgency(s) === 'high').length
  const icp              = calcICP(lead, highUrgencyCount)
  const outreachAngle    = buildOutreachAngle(lead, buying)
  const stale            = daysSinceNewest([...toList(lead.buying_signals), ...toList(lead.recent_signals)])

  const [emailCopied, setEmailCopied] = useState(false)
  const [briefCopied, setBriefCopied] = useState(false)
  const [evidenceOpen, setEvidenceOpen] = useState(false)

  const copyEmail = () =>
    navigator.clipboard.writeText(email).then(() => {
      setEmailCopied(true); setTimeout(() => setEmailCopied(false), 1800)
    })

  const copyBrief = () => {
    const topSignal = buying[0] ? cleanMd(buying[0]) : ''
    const angle = (lead.competitive_angle || '').replace(/^—\s*/, '').trim()
    const lines = [
      `${name} · ${[title, company !== '—' ? `at ${company}` : ''].filter(Boolean).join(' ')}`,
      topSignal ? `Strongest signal: ${topSignal}` : '',
      angle      ? `Angle: ${angle}`                : '',
      email      ? `Contact: ${email}`              : '',
    ].filter(Boolean)
    navigator.clipboard.writeText(lines.join('\n')).then(() => {
      setBriefCopied(true); setTimeout(() => setBriefCopied(false), 2000)
    })
  }

  let si = 0
  const delay = () => ({ style: { animationDelay: `${si++ * 50}ms` } })

  return (
    <div className="flex-1 overflow-auto bg-[#f7f8fa]">
      <div className="max-w-4xl mx-auto px-8 py-8 space-y-5">

        {/* ── HEADER ─────────────────────────────────────────────────── */}
        <div className="lp-section bg-white rounded-2xl border border-[#eef0f4] shadow-sm p-8" {...delay()}>
          <div className="flex items-start gap-6">
            <div className="w-14 h-14 rounded-xl flex items-center justify-center font-bold text-white text-xl flex-shrink-0"
                 style={{ background: avatarColor(name) }}>
              {initials(name)}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 flex-wrap mb-1.5">
                {linkedin
                  ? <a href={linkedin} target="_blank" rel="noreferrer" className="lp-name hover:text-[#4f46e5] transition-colors">{name}</a>
                  : <span className="lp-name">{name}</span>
                }
                <StatusBadge status={lead.status} />
                <ICPBadge icp={icp} />
              </div>

              {(title || company !== '—') && (
                <p className="text-[15px] text-[#6b7280] mb-5 flex items-center gap-1.5 flex-wrap">
                  {title}
                  {title && company !== '—' && <span className="text-[#d1d5db]">·</span>}
                  {fav && <img src={fav} className="w-4 h-4 rounded object-contain" onError={e => (e.currentTarget.style.display = 'none')} />}
                  {website
                    ? <a href={website} target="_blank" rel="noreferrer" className="text-[#374151] font-medium hover:text-[#4f46e5] transition-colors">{company}</a>
                    : <span className="text-[#374151] font-medium">{company}</span>
                  }
                </p>
              )}

              <div className="flex items-center gap-2 flex-wrap">
                {linkedin && (
                  <a href={linkedin} target="_blank" rel="noreferrer" className="lp-chip bg-[#eff6ff] text-[#1d4ed8] border-[#dbeafe] hover:bg-[#dbeafe]">
                    <LinkedInIcon size={11} />LinkedIn
                  </a>
                )}
                {website && domain && (
                  <a href={website} target="_blank" rel="noreferrer" className="lp-chip bg-[#f9fafb] text-[#374151] border-[#e5e7eb] hover:bg-[#f3f4f6]">
                    <Globe size={11} />{domain}
                  </a>
                )}
                {email && (
                  <button onClick={copyEmail} className="lp-chip bg-[#f9fafb] text-[#374151] border-[#e5e7eb] hover:bg-[#f3f4f6]">
                    {emailCopied ? <Check size={11} /> : <Mail size={11} />}
                    {emailCopied ? 'Copied' : email}
                  </button>
                )}
              </div>
            </div>

            <button onClick={copyBrief}
              className="flex-shrink-0 px-4 py-2 rounded-lg bg-[#4f46e5] text-white text-sm font-semibold hover:bg-[#4338ca] transition-colors whitespace-nowrap">
              {briefCopied ? 'Copied' : 'Copy Outreach Brief'}
            </button>
          </div>
        </div>

        {/* ── BUYING SIGNALS ───────────────────────────────────────────── */}
        {buying.length > 0 && (
          <section className="lp-section" {...delay()}>
            <SectionLabel>Buying Signals</SectionLabel>
            {stale !== null && stale > 90 && (
              <p className="text-[13px] text-[#9ca3af] mb-4">Most recent signal: {stale} days ago</p>
            )}
            <div className="space-y-3">
              {buying.map((signal, i) => {
                const u = inferUrgency(signal)
                const { text, sources } = parseSignalText(cleanMd(signal))
                const base = (si - 1) * 50 + i * 40
                const cardStyle = u === 'high'
                  ? { border: '1px solid #fecaca', borderLeft: '3px solid #DC2626', backgroundColor: '#FEF2F2', borderRadius: '12px', padding: '20px 24px', animationDelay: `${base}ms` }
                  : u === 'medium'
                  ? { border: '1px solid #fde68a', borderLeft: '3px solid #D97706', backgroundColor: '#FFFBEB', borderRadius: '12px', padding: '20px 24px', animationDelay: `${base}ms` }
                  : { border: '1px solid #eef0f4', backgroundColor: '#ffffff', borderRadius: '12px', padding: '20px 24px', animationDelay: `${base}ms` }
                return (
                  <div key={i} className="lp-signal" style={cardStyle}>
                    <p className="text-[15px] text-[#374151] leading-relaxed">{text}</p>
                    {sources.length > 0 && (
                      <div className="mt-2 flex gap-3 flex-wrap">
                        {sources.map((s, j) => (
                          <a key={j} href={s.url} target="_blank" rel="noreferrer"
                             className="text-[11px] text-[#9ca3af] hover:text-[#4f46e5] transition-colors inline-flex items-center gap-1">
                            <ExternalLink size={9} />{s.label}
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </section>
        )}

        {/* ── OUTREACH ANGLE ───────────────────────────────────────────── */}
        {outreachAngle && (
          <div className="lp-section" {...delay()}>
            <div style={{ borderLeft: '3px solid #d1d5db', paddingLeft: '16px' }}>
              <p className="text-[10px] font-semibold text-[#9ca3af] uppercase tracking-[0.1em] mb-2">AI-Suggested Outreach Angle</p>
              <p className="text-[14px] text-[#6b7280] leading-relaxed">{outreachAngle}</p>
            </div>
          </div>
        )}

        {/* ── DECISION MAKERS ──────────────────────────────────────────── */}
        {dms.length > 0 && (
          <section className="lp-section bg-white rounded-2xl border border-[#eef0f4] shadow-sm p-6" {...delay()}>
            <SectionLabel>Decision Makers</SectionLabel>
            <div>
              {dms.map((dm, i) => <DMRow key={i} dm={dm} />)}
            </div>
          </section>
        )}

        {/* ── COMPANY + LEAD PROFILE ───────────────────────────────────── */}
        <div className="lp-section grid grid-cols-2 gap-5" {...delay()}>
          <div className="bg-white rounded-2xl border border-[#eef0f4] shadow-sm p-6">
            <SectionLabel>Company</SectionLabel>
            {lead.company_description && (
              <p className="text-[14px] text-[#6b7280] leading-relaxed mb-5 pb-5 border-b border-[#f3f4f6]">
                {lead.company_description}
              </p>
            )}
            <FieldList fields={[
              { label: 'Industry', value: lead.industry },
              { label: 'Stage',    value: lead.company_stage },
              { label: 'Size',     value: lead.company_size },
              { label: 'HQ',       value: lead.company_hq },
              { label: 'Founded',  value: lead.company_founded },
              { label: 'Website',  value: domain
                  ? <a href={website} target="_blank" rel="noreferrer" className="text-[#4f46e5] hover:underline inline-flex items-center gap-1">{domain} <ExternalLink size={11} /></a>
                  : null },
            ]} />
          </div>

          <div className="bg-white rounded-2xl border border-[#eef0f4] shadow-sm p-6">
            <SectionLabel>Lead Profile</SectionLabel>
            <FieldList fields={[
              { label: 'Email', value: email
                  ? <span className="flex items-center gap-2 group/email">
                      <span>{email}</span>
                      <button onClick={copyEmail} className="text-[#d1d5db] hover:text-[#374151] transition-colors opacity-0 group-hover/email:opacity-100">
                        {emailCopied ? <Check size={13} /> : <Copy size={13} />}
                      </button>
                    </span>
                  : null },
              { label: 'Title',          value: lead.lead_title },
              { label: 'Tenure',         value: lead.lead_tenure },
              { label: 'Background',     value: lead.lead_background },
              { label: 'Verified',       value: lead.lead_verified ? <VerifiedBadge v={lead.lead_verified} /> : null },
              { label: 'LinkedIn',       value: linkedin
                  ? <a href={linkedin} target="_blank" rel="noreferrer" className="text-[#4f46e5] hover:underline inline-flex items-center gap-1">View profile <ExternalLink size={11} /></a>
                  : null },
              { label: 'Enriched',       value: fmtDate(lead.enriched_at) },
              { label: 'Signup Date',    value: fmtDate(lead.created_at) },
              { label: 'Contact Owner',  value: lead.contact_owner  || null },
              { label: 'Traffic Source', value: lead.traffic_source || null },
            ]} />
          </div>
        </div>

        {/* ── RECENT COMPANY SIGNALS ───────────────────────────────────── */}
        {sigs.length > 0 && (
          <section className="lp-section bg-white rounded-2xl border border-[#eef0f4] shadow-sm p-6" {...delay()}>
            <SectionLabel>Recent Company Signals</SectionLabel>
            <Timeline items={sigs} baseDelay={(si - 1) * 50} />
          </section>
        )}

        {/* ── LEAD'S RECENT ACTIVITY ───────────────────────────────────── */}
        {acts.length > 0 && (
          <section className="lp-section bg-white rounded-2xl border border-[#eef0f4] shadow-sm p-6" {...delay()}>
            <SectionLabel>Lead's Recent Activity</SectionLabel>
            <Timeline items={acts} baseDelay={(si - 1) * 50} />
          </section>
        )}

        {/* ── COMPETITIVE INTEL ────────────────────────────────────────── */}
        {(tools.length > 0 || (lead.competitive_angle && !lead.competitive_angle.startsWith('—')) || (lead.competitive_evidence && !lead.competitive_evidence.startsWith('—'))) && (
          <section className="lp-section bg-white rounded-2xl border border-[#eef0f4] shadow-sm p-6" {...delay()}>
            <SectionLabel>Competitive Intel</SectionLabel>

            {tools.length > 0 && (
              <div className="mb-6">
                <FieldLabel>Tools They Use</FieldLabel>
                <div className="flex flex-wrap gap-2 mt-2">
                  {tools.map(t => (
                    <span key={t} className="px-2.5 py-1 text-xs text-[#475569] border border-[#e2e8f0] rounded-md bg-[#f8fafc] font-medium">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {lead.competitive_angle && !lead.competitive_angle.startsWith('—') && (
              <div className="mb-6 pl-5 py-4 pr-5 rounded-r-xl" style={{ borderLeft: '4px solid #4f46e5', backgroundColor: '#f5f3ff' }}>
                <FieldLabel>Displacement Angle</FieldLabel>
                <p className="text-[15px] text-[#374151] leading-relaxed mt-1">{lead.competitive_angle}</p>
              </div>
            )}

            {lead.competitive_evidence && !lead.competitive_evidence.startsWith('—') && (
              <div>
                <button onClick={() => setEvidenceOpen(o => !o)}
                  className="flex items-center gap-1.5 text-[13px] text-[#6b7280] hover:text-[#374151] transition-colors">
                  {evidenceOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  {evidenceOpen ? 'Hide evidence' : 'Show evidence'}
                </button>
                <div className={`lp-evidence ${evidenceOpen ? 'lp-evidence-open' : ''}`}>
                  <div>
                    <p className="text-[14px] text-[#6b7280] leading-relaxed pl-4 pt-4">
                      {lead.competitive_evidence}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </section>
        )}

      </div>
    </div>
  )
}

// ── Sub-components ─────────────────────────────────────────────────────────

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <p className="text-[11px] font-semibold text-[#9ca3af] uppercase tracking-[0.08em] mb-5">{children}</p>
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <p className="text-[11px] font-semibold text-[#9ca3af] uppercase tracking-[0.08em] mb-1">{children}</p>
}

function FieldList({ fields }: { fields: { label: string; value: React.ReactNode }[] }) {
  const visible = fields.filter(f => {
    if (f.value === null || f.value === undefined) return false
    if (typeof f.value === 'string' && (!f.value.trim() || f.value === '—')) return false
    return true
  })
  return (
    <div className="space-y-5">
      {visible.map(({ label, value }) => (
        <div key={label}>
          <FieldLabel>{label}</FieldLabel>
          <div className="text-[15px] text-[#374151] font-medium leading-snug">{value}</div>
        </div>
      ))}
    </div>
  )
}

function ICPBadge({ icp }: { icp: ICPResult }) {
  const [hover, setHover] = useState(false)
  const cfg: Record<ICPTier, string> = {
    strong: 'bg-[#f0fdf4] text-[#15803d] border-[#dcfce7]',
    partial: 'bg-[#fffbeb] text-[#a16207] border-[#fef08a]',
    weak:   'bg-[#fef2f2] text-[#b91c1c] border-[#fecaca]',
  }
  return (
    <div className="relative inline-flex"
         onMouseEnter={() => setHover(true)}
         onMouseLeave={() => setHover(false)}>
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border cursor-default select-none ${cfg[icp.tier]}`}>
        {icp.label}
      </span>
      {hover && icp.factors.length > 0 && (
        <div className="absolute bottom-full left-0 mb-2 z-50 w-52 bg-[#0f172a] rounded-xl p-3 shadow-xl pointer-events-none">
          <p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#64748b] mb-2">Score factors</p>
          {icp.factors.map((f, i) => (
            <p key={i} className="text-[12px] text-[#e2e8f0] leading-snug mb-1 last:mb-0">· {f}</p>
          ))}
        </div>
      )}
    </div>
  )
}

const INFLUENCE_BADGE: Record<Influence, { label: string; cls: string } | null> = {
  budget:   { label: 'Budget Owner', cls: 'bg-[#eff6ff] text-[#1d4ed8] border-[#dbeafe]' },
  champion: { label: 'Champion',     cls: 'bg-[#f0fdf4] text-[#15803d] border-[#dcfce7]' },
  advisor:  { label: 'Advisor',      cls: 'bg-[#faf5ff] text-[#7c3aed] border-[#ede9fe]' },
  unknown:  null,
}

function DMRow({ dm }: { dm: DM }) {
  const badge = INFLUENCE_BADGE[dm.influence]
  return (
    <div className={`py-3.5 border-b border-[#f3f4f6] last:border-0 ${dm.influence === 'unknown' ? 'opacity-40' : ''}`}>
      <div className="flex items-center gap-3">
        <div className="flex-1 min-w-0">
          <span className="text-[15px] font-semibold text-[#0f172a]">{dm.name || '—'}</span>
          {dm.role && <span className="text-[14px] text-[#6b7280] ml-2">{dm.role}</span>}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {badge && (
            <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${badge.cls}`}>
              {badge.label}
            </span>
          )}
          {dm.linkedin && (
            <a href={dm.linkedin} target="_blank" rel="noreferrer"
               className="text-[#9ca3af] hover:text-[#1d4ed8] transition-colors">
              <LinkedInIcon size={14} />
            </a>
          )}
        </div>
      </div>
      {dm.description && (
        <p className="text-[13px] text-[#6b7280] leading-relaxed mt-1.5">{dm.description}</p>
      )}
    </div>
  )
}

function Timeline({ items, baseDelay }: { items: TimelineItem[]; baseDelay: number }) {
  return (
    <div className="relative pl-[88px]">
      <div className="absolute left-[72px] top-2 bottom-2 w-px bg-[#f3f4f6]" />
      <div className="space-y-5">
        {items.map((item, i) => (
          <div key={i} className="lp-timeline-entry relative" style={{ animationDelay: `${baseDelay + i * 30}ms` }}>
            <span className="absolute -left-[88px] w-[72px] text-right text-[11px] font-mono text-[#9ca3af] leading-6 whitespace-nowrap">
              {item.date}
            </span>
            <div className="absolute -left-[6px] top-[9px] w-1.5 h-1.5 rounded-full bg-[#e5e7eb]" />
            <div className="pl-4">
              <p className="text-[15px] text-[#374151] leading-relaxed">{item.text}</p>
              {item.sources.length > 0 && (
                <div className="mt-1.5 flex gap-3 flex-wrap">
                  {item.sources.map((s, j) => (
                    <a key={j} href={s.url} target="_blank" rel="noreferrer"
                       className="text-[11px] text-[#9ca3af] hover:text-[#4f46e5] transition-colors inline-flex items-center gap-1">
                      <ExternalLink size={9} />{s.label}
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function VerifiedBadge({ v }: { v: string }) {
  const [expanded, setExpanded] = useState(false)
  const isConfirmed = /confirmed|✅/i.test(v)
  const isUncertain = /found|⚠|unverified|uncertain|best match|appears to be/i.test(v)
  const badgeCls = isConfirmed
    ? 'bg-[#f0fdf4] text-[#15803d] border-[#dcfce7]'
    : isUncertain
    ? 'bg-[#fffbeb] text-[#a16207] border-[#fef08a]'
    : 'bg-[#fef2f2] text-[#b91c1c] border-[#fecaca]'
  const label = isConfirmed ? 'Confirmed' : isUncertain ? 'Uncertain' : 'Not found'
  const detail = v.replace(/[✅⚠❌]\s*/g, '').replace(/^(Confirmed|Found|Not found|Unverified)\s*[—-]?\s*/i, '').trim()
  return (
    <div>
      <button
        onClick={() => detail && setExpanded(o => !o)}
        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border transition-opacity hover:opacity-80 ${badgeCls} ${detail ? 'cursor-pointer' : 'cursor-default'}`}>
        {label}
        {detail && (expanded ? <ChevronUp size={10} /> : <ChevronDown size={10} />)}
      </button>
      {expanded && detail && (
        <p className="text-[13px] text-[#6b7280] leading-relaxed mt-2">{detail}</p>
      )}
    </div>
  )
}
