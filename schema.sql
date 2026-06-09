-- Nimble Lead Enrichment — Supabase schema
-- Run once in your Supabase project SQL editor

-- Shared column definition as a reusable template (comment only — repeated below)
-- C0AGVM6H76U → signups (self-serve)
-- C09P15RLKL4 → demo_requests (higher intent)

CREATE TABLE IF NOT EXISTS signups (
    id               UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at       TIMESTAMPTZ DEFAULT NOW(),

    first_name       TEXT,
    last_name        TEXT,
    full_name        TEXT,
    email            TEXT        UNIQUE NOT NULL,
    company_raw      TEXT,
    contact_owner    TEXT,
    traffic_source   TEXT,

    industry         TEXT,
    company_stage    TEXT,
    company_size     TEXT,
    company_hq       TEXT,
    company_founded  TEXT,
    company_website  TEXT,
    company_description TEXT,

    lead_verified    TEXT,
    lead_title       TEXT,
    lead_tenure      TEXT,
    lead_background  TEXT,
    lead_linkedin    TEXT,

    recent_signals   JSONB       DEFAULT '[]',
    buying_signals   JSONB       DEFAULT '[]',
    decision_makers  JSONB       DEFAULT '[]',
    recent_activity  JSONB       DEFAULT '[]',

    competitive_using     TEXT,
    competitive_angle     TEXT,
    competitive_evidence  TEXT,

    report_md        TEXT,
    enriched_at      TIMESTAMPTZ,
    status           TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'enriched', 'failed'))
);

CREATE TABLE IF NOT EXISTS demo_requests (
    id               UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at       TIMESTAMPTZ DEFAULT NOW(),

    first_name       TEXT,
    last_name        TEXT,
    full_name        TEXT,
    email            TEXT        UNIQUE NOT NULL,
    company_raw      TEXT,
    contact_owner    TEXT,
    traffic_source   TEXT,

    industry         TEXT,
    company_stage    TEXT,
    company_size     TEXT,
    company_hq       TEXT,
    company_founded  TEXT,
    company_website  TEXT,
    company_description TEXT,

    lead_verified    TEXT,
    lead_title       TEXT,
    lead_tenure      TEXT,
    lead_background  TEXT,
    lead_linkedin    TEXT,

    recent_signals   JSONB       DEFAULT '[]',
    buying_signals   JSONB       DEFAULT '[]',
    decision_makers  JSONB       DEFAULT '[]',
    recent_activity  JSONB       DEFAULT '[]',

    competitive_using     TEXT,
    competitive_angle     TEXT,
    competitive_evidence  TEXT,

    report_md        TEXT,
    enriched_at      TIMESTAMPTZ,
    status           TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'enriched', 'failed'))
);

-- Indexes for signups
CREATE INDEX IF NOT EXISTS idx_signups_email      ON signups (email);
CREATE INDEX IF NOT EXISTS idx_signups_status     ON signups (status);
CREATE INDEX IF NOT EXISTS idx_signups_created_at ON signups (created_at DESC);

-- Indexes for demo_requests
CREATE INDEX IF NOT EXISTS idx_demo_email      ON demo_requests (email);
CREATE INDEX IF NOT EXISTS idx_demo_status     ON demo_requests (status);
CREATE INDEX IF NOT EXISTS idx_demo_created_at ON demo_requests (created_at DESC);
