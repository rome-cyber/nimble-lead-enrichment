export type LeadStatus = 'enriched' | 'pending' | 'failed'

export interface Lead {
  id: string
  created_at: string
  enriched_at: string | null
  first_name: string | null
  last_name: string | null
  full_name: string | null
  email: string | null
  company_raw: string | null
  contact_owner: string | null
  traffic_source: string | null
  industry: string | null
  company_stage: string | null
  company_size: string | null
  company_hq: string | null
  company_founded: string | null
  company_website: string | null
  company_description: string | null
  lead_verified: string | null
  lead_title: string | null
  lead_tenure: string | null
  lead_background: string | null
  lead_linkedin: string | null
  recent_signals: string[] | null
  buying_signals: string[] | null
  decision_makers: string[] | null
  recent_activity: string[] | null
  competitive_using: string | null
  competitive_angle: string | null
  competitive_evidence: string | null
  report_md: string | null
  status: LeadStatus | null
}

export type TableName = 'demo_requests' | 'signups'
