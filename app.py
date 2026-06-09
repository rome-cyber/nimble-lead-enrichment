#!/usr/bin/env python3
"""
Nimble Lead Intelligence — v4
Full profile pages per lead, no signals column.
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
    page_title="Nimble · Leads",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ─────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { font-family:'Inter',sans-serif !important; box-sizing:border-box; }
a { text-decoration:none; }

[data-testid="stAppViewContainer"] { background:#f7f8fa; }
[data-testid="stHeader"]           { display:none; }
.block-container { padding-top:0 !important; padding-bottom:48px !important; max-width:none !important; }

/* sidebar */
[data-testid="stSidebar"]           { background:#0b0f19 !important; border-right:1px solid #141b2d; }
[data-testid="stSidebar"] section   { padding:24px 20px !important; }
[data-testid="stSidebar"] *         { color:#8892a4 !important; }
[data-testid="stSidebar"] h3        { color:#e2e8f0 !important; }
[data-testid="stSidebar"] label     { color:#6b7a99 !important; font-size:12px !important; font-weight:500 !important; }
[data-testid="stSidebar"] input     { background:#141b2d !important; border:1px solid #1e2a40 !important; color:#e2e8f0 !important; border-radius:8px !important; font-size:13px !important; }
[data-testid="stSidebar"] input::placeholder { color:#3d4f6b !important; }
[data-testid="stSidebar"] hr        { border-color:#141b2d !important; margin:16px 0 !important; }
[data-testid="stSidebar"] [data-testid="stButton"] > button {
    background:#141b2d !important; border:1px solid #1e2a40 !important;
    color:#60a5fa !important; border-radius:8px !important; font-size:13px !important;
    font-weight:500 !important; width:100% !important; padding:8px 14px !important;
    transition:all .15s ease !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] > button:hover { background:#1e2a40 !important; }
[data-testid="stSidebar"] [data-baseweb="radio"] > div   { gap:6px !important; }
[data-testid="stSidebar"] [data-baseweb="radio"] label   { font-size:13px !important; color:#8892a4 !important; }
[data-testid="stRadio"] > label { font-size:11px !important; font-weight:600 !important; color:#3d4f6b !important; text-transform:uppercase !important; letter-spacing:.06em !important; }
[data-testid="stSidebar"] [data-baseweb="tag"]      { background:#1e2a40 !important; border:none !important; }
[data-testid="stSidebar"] [data-baseweb="tag"] span { color:#93c5fd !important; }

/* metrics */
[data-testid="metric-container"] {
    background:white; border-radius:12px; padding:18px 22px !important;
    border:1px solid #eef0f4; box-shadow:0 1px 3px rgba(0,0,0,.04);
    animation:fadeUp .35s ease both;
}
[data-testid="stMetricLabel"] { font-size:11px !important; font-weight:600 !important; color:#9aa5b4 !important; text-transform:uppercase; letter-spacing:.07em; }
[data-testid="stMetricValue"] { font-size:28px !important; font-weight:700 !important; color:#111827 !important; letter-spacing:-.02em; }

/* table row buttons */
div[data-testid="stHorizontalBlock"] [data-testid="stButton"] > button {
    background:transparent !important; border:none !important;
    color:#111827 !important; font-weight:600 !important; font-size:14px !important;
    padding:0 !important; text-align:left !important; box-shadow:none !important;
    justify-content:flex-start; transition:color .12s ease !important;
}
div[data-testid="stHorizontalBlock"] [data-testid="stButton"] > button:hover { color:#4f46e5 !important; }

/* expander */
[data-testid="stExpander"] { background:white !important; border:1px solid #eef0f4 !important; border-radius:12px !important; }
[data-testid="stExpander"] summary { font-size:13px !important; font-weight:600 !important; color:#374151 !important; }

/* animations */
@keyframes fadeUp  { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
@keyframes fadeIn  { from{opacity:0} to{opacity:1} }
@keyframes pulse   { 0%,100%{opacity:1} 50%{opacity:.5} }

/* profile hero card */
.hero { background:white; border-radius:16px; border:1px solid #eef0f4;
        box-shadow:0 2px 12px rgba(0,0,0,.06); overflow:hidden;
        animation:fadeUp .3s ease both; margin-bottom:20px; }
.hero-body { padding:32px; }

/* avatar */
.av { width:56px; height:56px; border-radius:14px; display:flex; align-items:center;
      justify-content:center; font-size:20px; font-weight:700; color:white; flex-shrink:0; }

/* lead name link */
.ln { font-size:22px; font-weight:800; color:#0f172a; letter-spacing:-.02em; }
.ln:hover { color:#4f46e5; }

/* quick chips */
.chip { display:inline-flex; align-items:center; gap:5px; padding:5px 13px; border-radius:20px;
        font-size:12px; font-weight:600; text-decoration:none; margin:0 6px 0 0; cursor:pointer;
        transition:all .15s; border:1px solid transparent; }
.chip-li  { background:#eff6ff; color:#1d4ed8 !important; border-color:#dbeafe; }
.chip-li:hover  { background:#dbeafe; }
.chip-web { background:#f9fafb; color:#374151 !important; border-color:#e5e7eb; }
.chip-web:hover { background:#f3f4f6; }
.chip-em  { background:#f9fafb; color:#374151 !important; border-color:#e5e7eb; }
.chip-em:hover  { background:#f3f4f6; }

/* status pill */
.pill { display:inline-flex; align-items:center; gap:5px; padding:3px 11px; border-radius:20px; font-size:11px; font-weight:700; letter-spacing:.03em; }
.pill-enriched { background:#f0fdf4; color:#15803d; }
.pill-pending  { background:#fefce8; color:#a16207; animation:pulse 2.5s ease infinite; }
.pill-failed   { background:#fef2f2; color:#b91c1c; }
.pill-dot      { width:6px; height:6px; border-radius:50%; background:currentColor; display:inline-block; }

/* section cards */
.card { background:white; border-radius:14px; border:1px solid #eef0f4;
        box-shadow:0 1px 4px rgba(0,0,0,.04); padding:24px 28px;
        animation:fadeUp .35s ease both; height:100%; }

/* section label */
.sl { font-size:11px; font-weight:700; color:#9ca3af; text-transform:uppercase; letter-spacing:.08em; margin-bottom:18px; }

/* meta field */
.mf { margin-bottom:18px; }
.mf-l { font-size:11px; font-weight:600; color:#9ca3af; text-transform:uppercase; letter-spacing:.07em; margin-bottom:4px; }
.mf-v { font-size:14px; color:#111827; font-weight:500; line-height:1.45; }

/* buying signal */
.bs { display:flex; align-items:flex-start; gap:12px; background:#f0fdf4;
      border:1px solid #dcfce7; border-radius:10px; padding:14px 16px; margin:8px 0; }
.bs-dot { color:#16a34a; font-size:14px; flex-shrink:0; margin-top:1px; }
.bs-txt { font-size:14px; color:#14532d; line-height:1.55; font-weight:500; }

/* list row */
.lr { display:flex; align-items:flex-start; gap:10px; padding:11px 0; border-bottom:1px solid #f3f4f6; }
.lr:last-child { border-bottom:none; }
.lr-dot { width:7px; height:7px; border-radius:50%; flex-shrink:0; margin-top:5px; }
.lr-txt { font-size:13px; color:#374151; line-height:1.5; }

/* verified */
.vc-ok   { background:#f0fdf4; color:#15803d; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.vc-warn { background:#fefce8; color:#a16207; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.vc-no   { background:#fef2f2; color:#b91c1c; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:600; }

/* tool pill */
.tp { display:inline-block; background:#f1f5f9; color:#475569; border:1px solid #e2e8f0;
      border-radius:6px; padding:3px 9px; font-size:12px; font-weight:500; margin:2px 3px 2px 0; }

/* divider */
.div { border:none; border-top:1px solid #f3f4f6; margin:22px 0; }

/* table */
.tbl { background:white; border-radius:14px; border:1px solid #eef0f4;
       box-shadow:0 1px 4px rgba(0,0,0,.04); overflow:hidden; margin-top:8px; }
.th  { font-size:11px; font-weight:700; color:#9ca3af; text-transform:uppercase; letter-spacing:.07em; padding:14px 0 8px; }
.td  { font-size:14px; color:#374151; padding:4px 0; }
.tr-div { border:none; border-top:1px solid #f8f9fa; margin:2px 0; }

/* company favicon */
.co-fav { width:18px; height:18px; border-radius:4px; object-fit:contain; vertical-align:middle; margin-right:6px; }

/* back button override */
[data-testid="stButton"].back-btn > button {
    background:transparent !important; border:none !important; color:#6b7280 !important;
    font-size:13px !important; font-weight:500 !important; padding:0 !important;
    box-shadow:none !important;
}
[data-testid="stButton"].back-btn > button:hover { color:#111827 !important; }

/* empty state */
.empty { background:white; border:1px solid #eef0f4; border-radius:16px;
         padding:60px 32px; text-align:center; margin-top:16px; }
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
    return re.sub(r"https?://(www\.)?", "", url).split("/")[0]


def fav_url(website: str) -> str:
    d = get_domain(website)
    return f"https://www.google.com/s2/favicons?domain={d}&sz=64" if d else ""


def initials(name: str) -> str:
    parts = (name or "?").split()
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()


_COLORS = ["#6366f1","#0ea5e9","#10b981","#f59e0b","#ec4899","#8b5cf6","#14b8a6","#ef4444"]
def av_color(name: str) -> str:
    return _COLORS[sum(ord(c) for c in (name or "")) % len(_COLORS)]


def pill(status: str) -> str:
    s = (status or "pending").lower()
    labels = {"enriched":"Enriched","pending":"Processing","failed":"Failed"}
    return f'<span class="pill pill-{s}"><span class="pill-dot"></span>{labels.get(s,s)}</span>'


def verified_html(v: str) -> str:
    if not v:
        return "—"
    if "✅" in v or "Confirmed" in v:
        return '<span class="vc-ok">✅ Confirmed</span>'
    if "⚠" in v or "Found" in v:
        return '<span class="vc-warn">⚠ Unverified</span>'
    return '<span class="vc-no">❌ Not found</span>'


def mf(label: str, value: str) -> str:
    return (f'<div class="mf"><div class="mf-l">{label}</div>'
            f'<div class="mf-v">{value or "—"}</div></div>')


def mf_html(label: str, html_value: str) -> str:
    return (f'<div class="mf"><div class="mf-l">{label}</div>'
            f'<div class="mf-v" style="margin-top:4px">{html_value}</div></div>')


def tool_pills(s: str) -> str:
    if not s or s.strip() in ("—", ""):
        return "—"
    return "".join(
        f'<span class="tp">{t.strip()}</span>'
        for t in re.split(r"[,;/]", s) if t.strip()
    )


def list_rows(items: list, dot: str) -> str:
    if not items:
        return '<p style="color:#9ca3af;font-size:13px;padding:6px 0">None found</p>'
    return "".join(
        f'<div class="lr"><div class="lr-dot" style="background:{dot}"></div>'
        f'<div class="lr-txt">{item}</div></div>'
        for item in items
    )


def buying_cards(items: list) -> str:
    if not items:
        return '<p style="color:#9ca3af;font-size:13px;padding:8px 0">No buying signals identified</p>'
    return "".join(
        f'<div class="bs"><span class="bs-dot">◆</span><span class="bs-txt">{item}</span></div>'
        for item in items
    )


# ── Profile page ───────────────────────────────────────────────────────────────

def render_profile(lead: dict):
    name     = lead.get("full_name")        or "—"
    company  = lead.get("company_raw")      or "—"
    title    = lead.get("lead_title")       or "—"
    website  = lead.get("company_website")  or ""
    linkedin = lead.get("lead_linkedin")    or ""
    email    = lead.get("email")            or ""
    status   = lead.get("status")          or "pending"
    color    = av_color(name)
    ini      = initials(name)
    fav      = fav_url(website)
    domain   = get_domain(website)
    desc     = lead.get("company_description") or ""

    buying = lead.get("buying_signals")  or []
    dms    = lead.get("decision_makers") or []
    sigs   = lead.get("recent_signals")  or []
    acts   = lead.get("recent_activity") or []

    # Back button
    if st.button("← Back to leads"):
        st.session_state.page = "list"
        st.rerun()

    # Quick action chips
    li_chip = (
        f'<a href="{linkedin}" target="_blank" class="chip chip-li">'
        f'<svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor">'
        f'<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>'
        f'</svg>LinkedIn</a>'
    ) if linkedin else ""

    web_chip = (
        f'<a href="{website}" target="_blank" class="chip chip-web">↗ {domain}</a>'
    ) if website else ""

    safe_email = email.replace("'", "\\'")
    em_chip = (
        f'<span class="chip chip-em" onclick="navigator.clipboard.writeText(\'{safe_email}\')'
        f'.then(()=>{{this.innerHTML=\'✓ Copied\';}})">✉ {email}</span>'
    ) if email else ""

    fav_img = (
        f'<img src="{fav}" style="width:22px;height:22px;border-radius:5px;object-fit:contain;'
        f'vertical-align:middle;margin-right:7px;border:1px solid #f3f4f6" onerror="this.style.display=\'none\'">'
    ) if fav else ""

    co_link = (
        f'<a href="{website}" target="_blank" style="color:#374151;font-weight:600">{fav_img}{company}</a>'
    ) if website else f'{fav_img}<span style="color:#374151;font-weight:600">{company}</span>'

    name_html = (
        f'<a href="{linkedin}" target="_blank" class="ln">{name}</a>'
        if linkedin else f'<span class="ln">{name}</span>'
    )

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="hero">
      <div class="hero-body">
        <div style="display:flex;align-items:flex-start;gap:18px">
          <div class="av" style="background:{color}">{ini}</div>
          <div style="flex:1;min-width:0">
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:6px">
              {name_html}
              {pill(status)}
            </div>
            <div style="font-size:14px;color:#6b7280;margin-bottom:12px;display:flex;align-items:center;gap:6px">
              <span>{title}</span>
              <span style="color:#d1d5db">·</span>
              {co_link}
            </div>
            <div style="margin-top:2px">{li_chip}{web_chip}{em_chip}</div>
          </div>
          <div style="text-align:right;flex-shrink:0;padding-top:4px">
            <div style="font-size:11px;font-weight:600;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em">Enriched</div>
            <div style="font-size:13px;font-weight:600;color:#374151;margin-top:3px">{fmt_date(lead.get("enriched_at"))}</div>
            <div style="font-size:11px;color:#9ca3af;margin-top:2px">{fmt_date(lead.get("created_at"))}</div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Row 1: Company + Lead Profile ─────────────────────────────────────────
    c1, c2 = st.columns(2, gap="medium")

    with c1:
        st.markdown(f"""
        <div class="card">
          <div class="sl">🏢 &nbsp;Company</div>
          {f'<p style="font-size:13px;color:#4b5563;line-height:1.65;margin-bottom:20px;padding-bottom:18px;border-bottom:1px solid #f3f4f6">{desc}</p>' if desc else ""}
          {mf("Company Name", company)}
          {mf("Industry",     lead.get("industry"))}
          {mf("Stage",        lead.get("company_stage"))}
          {mf("Size",         lead.get("company_size"))}
          {mf("HQ",           lead.get("company_hq"))}
          {mf("Website",      f'<a href="{website}" target="_blank" style="color:#4f46e5">{domain}</a>' if website else "—")}
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card">
          <div class="sl">👤 &nbsp;Lead Profile</div>
          {mf("Full Name",       name)}
          {mf("Title",           lead.get("lead_title"))}
          {mf("Tenure",          lead.get("lead_tenure"))}
          {mf("Background",      lead.get("lead_background"))}
          {mf_html("Verified",   verified_html(lead.get("lead_verified","")))}
          {mf("LinkedIn",        f'<a href="{linkedin}" target="_blank" style="color:#4f46e5">View profile ↗</a>' if linkedin else "—")}
          {mf("Email",           email or "—")}
          {mf("Contact Owner",   lead.get("contact_owner"))}
          {mf("Traffic Source",  lead.get("traffic_source"))}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Row 2: Buying Signals (full width) ─────────────────────────────────────
    st.markdown(f"""
    <div class="card">
      <div class="sl">🎯 &nbsp;Buying Signals</div>
      {buying_cards(buying if isinstance(buying, list) else [])}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Row 3: Decision Makers + Recent Signals ────────────────────────────────
    c3, c4 = st.columns(2, gap="medium")

    with c3:
        st.markdown(f"""
        <div class="card">
          <div class="sl">👥 &nbsp;Decision Makers</div>
          {list_rows(dms if isinstance(dms, list) else [], "#6366f1")}
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="card">
          <div class="sl">📡 &nbsp;Recent Company Signals</div>
          {list_rows(sigs if isinstance(sigs, list) else [], "#f59e0b")}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Row 4: Competitive Intel ───────────────────────────────────────────────
    st.markdown(f"""
    <div class="card">
      <div class="sl">⚔️ &nbsp;Competitive Intel</div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0 32px">
        <div>
          <div class="mf-l">Tools they use</div>
          <div style="margin-top:6px">{tool_pills(lead.get("competitive_using",""))}</div>
        </div>
        <div>{mf("Displacement Angle", lead.get("competitive_angle"))}</div>
        <div>{mf("Evidence",           lead.get("competitive_evidence"))}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Row 5: Lead Activity ───────────────────────────────────────────────────
    if isinstance(acts, list) and acts:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card">
          <div class="sl">📝 &nbsp;Lead's Recent Activity</div>
          {list_rows(acts, "#a855f7")}
        </div>
        """, unsafe_allow_html=True)

    # ── Full report ────────────────────────────────────────────────────────────
    if lead.get("report_md"):
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        with st.expander("📄 View Full Intelligence Report", expanded=False):
            st.markdown(lead["report_md"])


# ── Lead list page ─────────────────────────────────────────────────────────────

def render_list(leads: list, table: str):
    st.markdown("""
    <div style="padding:28px 0 20px">
      <h1 style="font-size:24px;font-weight:800;color:#0f172a;letter-spacing:-.025em;margin-bottom:4px">
        Lead Intelligence
      </h1>
      <p style="font-size:13px;color:#6b7280">Enriched research on every inbound — click a lead to open their profile.</p>
    </div>
    """, unsafe_allow_html=True)

    # Metrics
    m1, m2, m3, m4 = st.columns(4, gap="small")
    m1.metric("Total",      len(leads))
    m2.metric("Enriched",   sum(1 for l in leads if l.get("status") == "enriched"))
    m3.metric("Processing", sum(1 for l in leads if l.get("status") == "pending"))
    m4.metric("Failed",     sum(1 for l in leads if l.get("status") == "failed"))

    if not leads:
        st.markdown("""
        <div class="empty">
          <div style="font-size:36px;margin-bottom:12px">🔍</div>
          <div style="font-size:15px;font-weight:600;color:#374151;margin-bottom:4px">No leads found</div>
          <div style="font-size:13px;color:#9ca3af">Try adjusting your filters</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Table
    st.markdown('<div class="tbl"><div style="padding:0 20px">', unsafe_allow_html=True)

    h0,h1,h2,h3,h4,h5 = st.columns([2.5, 2.2, 2.2, 1.5, 1.5, 1])
    for col, lbl in zip([h0,h1,h2,h3,h4,h5], ["Lead","Company","Title","Stage","Enriched","Status"]):
        col.markdown(f'<div class="th">{lbl}</div>', unsafe_allow_html=True)

    st.markdown("<hr class='tr-div' style='margin:2px 0 6px'>", unsafe_allow_html=True)

    for i, lead in enumerate(leads):
        fav  = fav_url(lead.get("company_website",""))
        co   = lead.get("company_raw") or "—"
        stat = lead.get("status") or "pending"

        fav_tag = (
            f'<img src="{fav}" class="co-fav" onerror="this.style.display=\'none\'">'
        ) if fav else ""

        c0,c1,c2,c3,c4,c5 = st.columns([2.5, 2.2, 2.2, 1.5, 1.5, 1])

        if c0.button(lead.get("full_name") or "—", key=f"r_{table}_{i}"):
            st.session_state.page         = "profile"
            st.session_state.selected_lead = lead
            st.rerun()

        c1.markdown(f'<div style="display:flex;align-items:center;font-size:14px;color:#374151;padding:4px 0">{fav_tag}{co}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="td">{lead.get("lead_title") or "—"}</div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="td">{lead.get("company_stage") or "—"}</div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="td">{fmt_date(lead.get("enriched_at"))}</div>', unsafe_allow_html=True)
        c5.markdown(pill(stat), unsafe_allow_html=True)

        if i < len(leads) - 1:
            st.markdown("<hr class='tr-div'>", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────

def render_sidebar(on_profile: bool) -> tuple:
    with st.sidebar:
        st.markdown("""
        <div style="padding:4px 0 24px">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <div style="width:28px;height:28px;background:#4f46e5;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px">⚡</div>
            <span style="font-size:16px;font-weight:700;color:#e2e8f0;letter-spacing:-.01em">Nimble Leads</span>
          </div>
          <div style="font-size:12px;color:#3d4f6b;margin-left:36px">Sales Intelligence</div>
        </div>
        """, unsafe_allow_html=True)

        if on_profile:
            if st.button("← Back to all leads", use_container_width=True):
                st.session_state.page = "list"
                st.rerun()
            return None, None, None, None

        table_label   = st.radio("TYPE", ["🔥  Demo Requests", "📋  Self-Serve"], label_visibility="visible")
        table         = "demo_requests" if "Demo" in table_label else "signups"
        search        = st.text_input("SEARCH", placeholder="Name or company…", label_visibility="visible")
        status_filter = st.multiselect("STATUS", ["enriched","pending","failed"], default=["enriched"])
        owner_filter  = st.text_input("OWNER",  placeholder="Contact owner…", label_visibility="visible")

        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("↺  Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    return table, search, status_filter, owner_filter


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    st.session_state.setdefault("page", "list")
    st.session_state.setdefault("selected_lead", None)

    on_profile = st.session_state.page == "profile"
    table, search, status_filter, owner_filter = render_sidebar(on_profile)

    if on_profile and st.session_state.selected_lead:
        render_profile(st.session_state.selected_lead)
        return

    # List page
    leads = load_leads(table or "demo_requests")

    if search:
        q = search.lower()
        leads = [l for l in leads if
                 q in (l.get("full_name")   or "").lower() or
                 q in (l.get("company_raw") or "").lower()]
    if status_filter:
        leads = [l for l in leads if (l.get("status") or "pending") in status_filter]
    if owner_filter:
        q = owner_filter.lower()
        leads = [l for l in leads if q in (l.get("contact_owner") or "").lower()]

    render_list(leads, table or "demo_requests")


if __name__ == "__main__":
    main()
