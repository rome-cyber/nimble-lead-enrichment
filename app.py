#!/usr/bin/env python3
"""
Nimble Lead Intelligence — v2
Pixel-perfect sales prep dashboard.
"""

import os
import re
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).parent / ".env", override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase     = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(
    page_title="Nimble · Lead Intelligence",
    page_icon="https://nimbleway.com/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design system ──────────────────────────────────────────────────────────────

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
*, *::before, *::after { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

/* ── Page background ── */
[data-testid="stAppViewContainer"]  { background: #f0f2f8; }
[data-testid="stHeader"]            { background: transparent; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #1e2530;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #f1f5f9 !important; }
[data-testid="stSidebar"] .stRadio label { color: #94a3b8 !important; font-size:13px; }
[data-testid="stSidebar"] input {
    background: #1e2530 !important;
    border: 1px solid #334155 !important;
    color: #f1f5f9 !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] hr { border-color: #1e2530 !important; }
[data-testid="stSidebar"] [data-testid="stButton"] > button {
    background: #1e2d40 !important;
    border: 1px solid #2d4a6b !important;
    color: #60a5fa !important;
    border-radius: 8px !important;
    width: 100%;
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: white;
    border-radius: 12px;
    padding: 16px 20px !important;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
    animation: fadeInUp .4s ease both;
}
[data-testid="stMetricLabel"]  { font-size: 12px !important; color: #64748b !important; text-transform: uppercase; letter-spacing: .05em; }
[data-testid="stMetricValue"]  { font-size: 28px !important; font-weight: 700 !important; color: #0f172a !important; }

/* ── Table row buttons → look like links ── */
div[data-testid="stHorizontalBlock"] [data-testid="stButton"] > button {
    background: transparent !important;
    border: none !important;
    color: #2563eb !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 4px 0 !important;
    text-align: left !important;
    box-shadow: none !important;
    text-decoration: none;
    justify-content: flex-start;
}
div[data-testid="stHorizontalBlock"] [data-testid="stButton"] > button:hover {
    color: #1d4ed8 !important;
    text-decoration: underline;
    background: transparent !important;
}

/* ── Animations ── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes slideInDown {
    from { opacity: 0; transform: translateY(-16px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: .6; }
}

/* ── Detail panel ── */
.detail-panel {
    background: white;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    padding: 32px;
    margin-top: 24px;
    box-shadow: 0 4px 24px rgba(0,0,0,.08);
    animation: slideInDown .35s ease both;
}

/* ── Lead header ── */
.lead-avatar {
    width: 56px; height: 56px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; font-weight: 700; color: white;
    flex-shrink: 0;
}
.lead-header {
    display: flex; align-items: center; gap: 16px; margin-bottom: 20px;
}
.lead-name {
    font-size: 22px; font-weight: 700; color: #0f172a; margin: 0;
    text-decoration: none;
}
.lead-name:hover { color: #2563eb; }
.lead-title-co   { font-size: 14px; color: #64748b; margin-top: 2px; }

/* ── Company logo ── */
.company-logo {
    width: 32px; height: 32px;
    border-radius: 6px;
    object-fit: contain;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    vertical-align: middle;
    margin-right: 6px;
}

/* ── Quick action buttons ── */
.qa-btn {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 13px; font-weight: 600;
    text-decoration: none;
    margin-right: 8px; margin-top: 10px;
    transition: all .15s ease;
    cursor: pointer;
}
.qa-linkedin { background:#0a66c2; color:white !important; }
.qa-linkedin:hover { background:#004182; }
.qa-website  { background:#f1f5f9; color:#334155 !important; border:1px solid #e2e8f0; }
.qa-website:hover  { background:#e2e8f0; }
.qa-email    { background:#f1f5f9; color:#334155 !important; border:1px solid #e2e8f0; }
.qa-email:hover    { background:#e2e8f0; }

/* ── Status badges ── */
.badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 4px 12px; border-radius: 20px;
    font-size: 12px; font-weight: 600; letter-spacing:.02em;
}
.badge-enriched { background:#dcfce7; color:#166534; }
.badge-pending  { background:#fef9c3; color:#854d0e; animation: pulse 2s infinite; }
.badge-failed   { background:#fee2e2; color:#991b1b; }

/* ── Section cards ── */
.section-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    height: 100%;
    animation: fadeInUp .4s ease both;
}
.section-label {
    font-size: 11px; font-weight: 700; color:#64748b;
    text-transform: uppercase; letter-spacing:.08em;
    margin-bottom: 14px; display: flex; align-items: center; gap: 6px;
}

/* ── Signal items ── */
.signal-buying {
    display:flex; align-items:flex-start; gap:10px;
    background: #f0fdf4; border: 1px solid #bbf7d0;
    border-radius: 10px; padding: 12px 14px; margin: 8px 0;
    animation: fadeInUp .3s ease both;
}
.signal-buying .dot { color: #22c55e; font-size:18px; flex-shrink:0; margin-top:-1px; }
.signal-buying .txt { font-size:14px; color:#14532d; line-height:1.5; }

.signal-recent {
    display:flex; align-items:flex-start; gap:10px;
    background: #fffbeb; border: 1px solid #fde68a;
    border-radius: 10px; padding: 10px 14px; margin: 6px 0;
}
.signal-recent .dot { color: #f59e0b; flex-shrink:0; }
.signal-recent .txt { font-size:13px; color:#78350f; line-height:1.5; }

.signal-dm {
    display:flex; align-items:flex-start; gap:10px;
    background: #eff6ff; border: 1px solid #bfdbfe;
    border-radius: 10px; padding: 10px 14px; margin: 6px 0;
}
.signal-dm .dot { color:#3b82f6; flex-shrink:0; }
.signal-dm .txt { font-size:13px; color:#1e3a5f; line-height:1.5; }

.signal-activity {
    display:flex; align-items:flex-start; gap:10px;
    background: #faf5ff; border: 1px solid #e9d5ff;
    border-radius: 10px; padding: 10px 14px; margin: 6px 0;
}
.signal-activity .dot { color:#a855f7; flex-shrink:0; }
.signal-activity .txt { font-size:13px; color:#4c1d95; line-height:1.5; }

/* ── Meta fields ── */
.meta-block { margin-bottom: 14px; }
.meta-lbl { font-size:11px; font-weight:600; color:#94a3b8; text-transform:uppercase; letter-spacing:.06em; }
.meta-val { font-size:14px; color:#1e293b; font-weight:500; margin-top:2px; }

/* ── Verified pill ── */
.verified-ok  { background:#dcfce7; color:#166534; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.verified-warn{ background:#fef9c3; color:#854d0e; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.verified-no  { background:#fee2e2; color:#991b1b; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:600; }

/* ── Divider ── */
.divider { border: none; border-top: 1px solid #e2e8f0; margin: 24px 0; }

/* ── Table header ── */
.tbl-header { font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:.06em; padding:4px 0; }

/* ── Table row ── */
.tbl-cell { font-size:14px; color:#334155; padding: 4px 0; display:flex; align-items:center; gap:6px; }

/* ── Copy feedback ── */
.copy-feedback { font-size:11px; color:#22c55e; margin-left:6px; }

/* ── Competitor pills ── */
.tech-pill {
    display:inline-block; background:#f1f5f9; color:#475569;
    border:1px solid #e2e8f0; border-radius:6px;
    padding:3px 10px; font-size:12px; font-weight:500; margin:3px 3px 3px 0;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def load_leads(table: str) -> list:
    return supabase.table(table).select("*").order("created_at", desc=True).execute().data or []


def fmt_date(ts: str) -> str:
    if not ts:
        return "—"
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%b %d, %Y")
    except Exception:
        return ts[:10]


def get_domain(url: str) -> str:
    if not url:
        return ""
    url = re.sub(r"https?://(www\.)?", "", url)
    return url.split("/")[0]


def favicon_url(website: str) -> str:
    domain = get_domain(website)
    if not domain:
        return ""
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=64"


def initials(name: str) -> str:
    parts = (name or "?").split()
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()


AVATAR_COLORS = ["#6366f1","#0ea5e9","#10b981","#f59e0b","#ef4444","#8b5cf6","#ec4899","#14b8a6"]

def avatar_color(name: str) -> str:
    return AVATAR_COLORS[sum(ord(c) for c in (name or "")) % len(AVATAR_COLORS)]


def badge_html(status: str) -> str:
    s = (status or "pending").lower()
    icons = {"enriched": "✦", "pending": "◌", "failed": "✕"}
    return f'<span class="badge badge-{s}">{icons.get(s,"·")} {s.capitalize()}</span>'


def verified_html(v: str) -> str:
    if not v:
        return ""
    if "✅" in v or "Confirmed" in v:
        return f'<span class="verified-ok">✅ Confirmed</span>'
    if "⚠️" in v or "Found" in v:
        return f'<span class="verified-warn">⚠ Unverified</span>'
    return f'<span class="verified-no">❌ Not found</span>'


def meta_html(label: str, value: str) -> str:
    return (
        f'<div class="meta-block">'
        f'<div class="meta-lbl">{label}</div>'
        f'<div class="meta-val">{value or "—"}</div>'
        f'</div>'
    )


def signal_html(items, kind: str) -> str:
    if not items:
        return "<p style='color:#94a3b8;font-size:13px;padding:8px 0'>None found</p>"
    dots = {"buying":"●","recent":"●","dm":"●","activity":"●"}
    dot = dots.get(kind, "●")
    return "".join(
        f'<div class="signal-{kind}"><span class="dot">{dot}</span>'
        f'<span class="txt">{item}</span></div>'
        for item in items
    )


def tech_pills(tools_str: str) -> str:
    if not tools_str or tools_str == "—":
        return "<span style='color:#94a3b8;font-size:13px'>—</span>"
    tools = [t.strip() for t in re.split(r"[,;]", tools_str) if t.strip()]
    return "".join(f'<span class="tech-pill">{t}</span>' for t in tools)


# ── Detail panel ───────────────────────────────────────────────────────────────

def show_lead(lead: dict):
    name      = lead.get("full_name") or "—"
    company   = lead.get("company_raw") or "—"
    title     = lead.get("lead_title") or "—"
    website   = lead.get("company_website") or ""
    linkedin  = lead.get("lead_linkedin") or ""
    email     = lead.get("email") or ""
    fav       = favicon_url(website)
    color     = avatar_color(name)
    ini       = initials(name)
    status    = lead.get("status") or "pending"

    fav_img   = f'<img src="{fav}" class="company-logo" onerror="this.style.display=\'none\'">' if fav else ""
    li_btn    = f'<a href="{linkedin}" target="_blank" class="qa-btn qa-linkedin">in LinkedIn</a>' if linkedin else ""
    web_btn   = f'<a href="{website}" target="_blank" class="qa-btn qa-website">↗ Website</a>' if website else ""

    # Copy-email JS button
    email_btn = ""
    if email:
        safe = email.replace("'", "\\'")
        email_btn = (
            f'<span class="qa-btn qa-email" style="cursor:pointer" '
            f'onclick="navigator.clipboard.writeText(\'{safe}\').then(()=>{{'
            f'this.innerHTML=\'✓ Copied\';}})">✉ {email}</span>'
        )

    st.markdown(f"""
    <div class="detail-panel">
      <div class="lead-header">
        <div class="lead-avatar" style="background:{color}">{ini}</div>
        <div style="flex:1">
          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
            {'<a href="' + linkedin + '" target="_blank" class="lead-name">' + name + ' ↗</a>' if linkedin else f'<span class="lead-name">{name}</span>'}
            {badge_html(status)}
          </div>
          <div class="lead-title-co">
            {title} &nbsp;·&nbsp; {fav_img}
            {'<a href="' + website + '" target="_blank" style="color:#64748b;text-decoration:none;font-weight:500">' + company + ' ↗</a>' if website else company}
          </div>
          <div>{li_btn}{web_btn}{email_btn}</div>
        </div>
        <div style="text-align:right;flex-shrink:0">
          <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em">Enriched</div>
          <div style="font-size:13px;font-weight:600;color:#475569">{fmt_date(lead.get('enriched_at'))}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Buying signals (full width, most important) ────────────────────────────
    buying = lead.get("buying_signals") or []
    st.markdown("""
    <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:24px;
         margin-top:16px;box-shadow:0 2px 8px rgba(0,0,0,.05);animation:fadeInUp .4s ease both">
      <div class="section-label">🎯 &nbsp;Buying Signals</div>
    """ + signal_html(buying if isinstance(buying, list) else [], "buying") + "</div>",
    unsafe_allow_html=True)

    # ── Company + Lead ─────────────────────────────────────────────────────────
    c1, c2 = st.columns(2, gap="medium")

    with c1:
        desc = lead.get("company_description") or ""
        st.markdown(f"""
        <div class="section-card" style="animation-delay:.05s">
          <div class="section-label">🏢 &nbsp;Company Snapshot</div>
          {f'<p style="font-size:13px;color:#475569;margin-bottom:16px;font-style:italic">{desc}</p>' if desc else ""}
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
            {meta_html("Industry",  lead.get("industry"))}
            {meta_html("Stage",     lead.get("company_stage"))}
            {meta_html("Size",      lead.get("company_size"))}
            {meta_html("HQ",        lead.get("company_hq"))}
          </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        verified = verified_html(lead.get("lead_verified", ""))
        st.markdown(f"""
        <div class="section-card" style="animation-delay:.1s">
          <div class="section-label">👤 &nbsp;Lead Profile</div>
          {meta_html("Title",          lead.get("lead_title"))}
          {meta_html("Tenure",         lead.get("lead_tenure"))}
          {meta_html("Background",     lead.get("lead_background"))}
          {meta_html("Traffic Source", lead.get("traffic_source"))}
          {meta_html("Contact Owner",  lead.get("contact_owner"))}
          {'<div class="meta-block"><div class="meta-lbl">Verified</div><div style="margin-top:4px">' + verified + '</div></div>' if verified else ""}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Decision makers + Recent signals ──────────────────────────────────────
    c3, c4 = st.columns(2, gap="medium")

    dms  = lead.get("decision_makers") or []
    sigs = lead.get("recent_signals")  or []

    with c3:
        st.markdown(f"""
        <div class="section-card" style="animation-delay:.15s">
          <div class="section-label">👥 &nbsp;Decision Maker Map</div>
          {signal_html(dms if isinstance(dms, list) else [], "dm")}
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="section-card" style="animation-delay:.2s">
          <div class="section-label">📡 &nbsp;Recent Signals</div>
          {signal_html(sigs if isinstance(sigs, list) else [], "recent")}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Competitive intel ──────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="section-card" style="animation-delay:.25s">
      <div class="section-label">⚔️ &nbsp;Competitive Intel</div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px">
        <div>
          <div class="meta-lbl">Tools they use</div>
          <div style="margin-top:6px">{tech_pills(lead.get("competitive_using") or "")}</div>
        </div>
        {meta_html("Displacement angle", lead.get("competitive_angle"))}
        {meta_html("Evidence",           lead.get("competitive_evidence"))}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Lead activity ──────────────────────────────────────────────────────────
    activity = lead.get("recent_activity") or []
    if isinstance(activity, list) and activity:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="section-card" style="animation-delay:.3s">
          <div class="section-label">📝 &nbsp;Lead's Recent Activity</div>
          {signal_html(activity, "activity")}
        </div>
        """, unsafe_allow_html=True)

    # ── Full report ────────────────────────────────────────────────────────────
    if lead.get("report_md"):
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        with st.expander("📄 Full Intelligence Report", expanded=False):
            st.markdown(lead["report_md"])


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if "selected_idx"   not in st.session_state: st.session_state.selected_idx   = None
    if "selected_table" not in st.session_state: st.session_state.selected_table = None

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div style="padding:8px 0 20px">
          <div style="font-size:20px;font-weight:800;color:#f1f5f9;letter-spacing:-.02em">
            Nimble <span style="color:#3b82f6">Leads</span>
          </div>
          <div style="font-size:12px;color:#475569;margin-top:4px">Sales Intelligence</div>
        </div>
        """, unsafe_allow_html=True)

        table_label = st.radio(
            "Lead Type",
            ["🔥 Demo Requests", "📋 Self-Serve Signups"],
            label_visibility="collapsed",
        )
        table = "demo_requests" if "Demo" in table_label else "signups"

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        search = st.text_input("", placeholder="🔍  Search name or company…")

        status_filter = st.multiselect(
            "Status",
            ["enriched", "pending", "failed"],
            default=["enriched"],
        )

        owner_filter = st.text_input("", placeholder="👤  Filter by contact owner…")

        st.markdown("<hr style='border-color:#1e2530;margin:20px 0'>", unsafe_allow_html=True)
        if st.button("↺  Refresh", use_container_width=True):
            st.cache_data.clear()
            st.session_state.selected_idx = None
            st.rerun()

    # ── Load + filter ──────────────────────────────────────────────────────────
    with st.spinner("Loading leads…"):
        leads = load_leads(table)

    if search:
        q = search.lower()
        leads = [l for l in leads if
                 q in (l.get("full_name")    or "").lower() or
                 q in (l.get("company_raw")  or "").lower()]

    if status_filter:
        leads = [l for l in leads if (l.get("status") or "pending") in status_filter]

    if owner_filter:
        q = owner_filter.lower()
        leads = [l for l in leads if q in (l.get("contact_owner") or "").lower()]

    # ── Page header ────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="padding:8px 0 24px">
      <h1 style="font-size:26px;font-weight:800;color:#0f172a;margin:0;letter-spacing:-.02em">
        Lead Intelligence
      </h1>
      <p style="font-size:14px;color:#64748b;margin:4px 0 0">
        Research each lead before your call — signals, background, and competitive context in one place.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Metric cards ───────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4, gap="medium")
    m1.metric("Total Leads",   len(leads))
    m2.metric("Ready ✦",       sum(1 for l in leads if l.get("status") == "enriched"))
    m3.metric("Processing ◌",  sum(1 for l in leads if l.get("status") == "pending"))
    m4.metric("Failed ✕",      sum(1 for l in leads if l.get("status") == "failed"))

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if not leads:
        st.markdown("""
        <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;
             padding:48px;text-align:center;color:#94a3b8;margin-top:16px">
          <div style="font-size:32px">🔍</div>
          <div style="font-size:15px;margin-top:8px">No leads match your filters</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Table ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;
         padding:0;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.05)">
    """, unsafe_allow_html=True)

    # Header row
    h0, h1, h2, h3, h4, h5, h6 = st.columns([2.5, 2, 2, 1.4, 0.8, 1.3, 1])
    for col, lbl in zip([h0,h1,h2,h3,h4,h5,h6],
                        ["Lead","Company","Title","Stage","Signals","Enriched","Status"]):
        col.markdown(f'<div class="tbl-header">{lbl}</div>', unsafe_allow_html=True)

    st.markdown("<hr style='margin:2px 0 4px;border-color:#f1f5f9'>", unsafe_allow_html=True)

    for i, lead in enumerate(leads):
        buying_count = len(lead.get("buying_signals") or [])
        company      = lead.get("company_raw") or "—"
        website      = lead.get("company_website") or ""
        fav          = favicon_url(website)
        status       = lead.get("status") or "pending"

        fav_tag = f'<img src="{fav}" style="width:18px;height:18px;border-radius:4px;vertical-align:middle;margin-right:5px;object-fit:contain" onerror="this.style.display=\'none\'">' if fav else ""
        co_html = f'{fav_tag}<span style="font-size:14px;color:#334155">{company}</span>'

        signals_html = (
            f'<span style="background:#dcfce7;color:#166534;border-radius:20px;'
            f'padding:2px 10px;font-size:12px;font-weight:700">🎯 {buying_count}</span>'
            if buying_count else
            '<span style="color:#94a3b8;font-size:13px">—</span>'
        )

        c0, c1, c2, c3, c4, c5, c6 = st.columns([2.5, 2, 2, 1.4, 0.8, 1.3, 1])

        if c0.button(lead.get("full_name") or "—", key=f"lead_{table}_{i}"):
            st.session_state.selected_idx   = i
            st.session_state.selected_table = table
            st.rerun()

        c1.markdown(co_html, unsafe_allow_html=True)
        c2.markdown(f'<div class="tbl-cell">{lead.get("lead_title") or "—"}</div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="tbl-cell">{lead.get("company_stage") or "—"}</div>', unsafe_allow_html=True)
        c4.markdown(signals_html, unsafe_allow_html=True)
        c5.markdown(f'<div class="tbl-cell">{fmt_date(lead.get("enriched_at"))}</div>', unsafe_allow_html=True)
        c6.markdown(badge_html(status), unsafe_allow_html=True)

        if i < len(leads) - 1:
            st.markdown("<hr style='margin:2px 0;border-color:#f8fafc'>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Detail panel ───────────────────────────────────────────────────────────
    if (
        st.session_state.selected_idx is not None
        and st.session_state.selected_table == table
        and st.session_state.selected_idx < len(leads)
    ):
        show_lead(leads[st.session_state.selected_idx])


if __name__ == "__main__":
    main()
