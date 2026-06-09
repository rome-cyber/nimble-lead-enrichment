#!/usr/bin/env python3
"""
Nimble Lead Intelligence Dashboard
Sales-facing app to review enriched leads before calls.
"""

import os
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
    page_title="Nimble Lead Intelligence",
    page_icon="🎯",
    layout="wide",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f5f6fa; }
.lead-row:hover { background: #eef2ff; }
.card {
    background: white;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 16px;
    border: 1px solid #e8eaf0;
}
.buying-signal {
    background: #edfcf2;
    border-left: 4px solid #22c55e;
    padding: 8px 14px;
    margin: 6px 0;
    border-radius: 0 6px 6px 0;
    font-size: 14px;
}
.recent-signal {
    background: #fffbeb;
    border-left: 4px solid #f59e0b;
    padding: 8px 14px;
    margin: 6px 0;
    border-radius: 0 6px 6px 0;
    font-size: 14px;
}
.dm-item {
    background: #eff6ff;
    border-left: 4px solid #3b82f6;
    padding: 8px 14px;
    margin: 6px 0;
    border-radius: 0 6px 6px 0;
    font-size: 14px;
}
.activity-item {
    background: #faf5ff;
    border-left: 4px solid #a855f7;
    padding: 8px 14px;
    margin: 6px 0;
    border-radius: 0 6px 6px 0;
    font-size: 14px;
}
.badge-enriched { background:#22c55e; color:white; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
.badge-pending  { background:#f59e0b; color:white; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
.badge-failed   { background:#ef4444; color:white; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
.section-title  { font-size:15px; font-weight:700; color:#374151; margin-bottom:10px; }
.meta-label     { font-size:12px; color:#9ca3af; text-transform:uppercase; letter-spacing:.05em; }
.meta-value     { font-size:14px; color:#111827; font-weight:500; }
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


def badge(status: str) -> str:
    s = (status or "pending").lower()
    return f'<span class="badge-{s}">{s.upper()}</span>'


def item_list(items, css_class: str) -> str:
    if not items:
        return "<p style='color:#9ca3af;font-size:13px'>None found</p>"
    return "".join(f'<div class="{css_class}">• {i}</div>' for i in items)


def meta(label: str, value: str):
    st.markdown(
        f'<div class="meta-label">{label}</div>'
        f'<div class="meta-value">{value or "—"}</div>',
        unsafe_allow_html=True,
    )


# ── Detail view ────────────────────────────────────────────────────────────────

def show_lead(lead: dict):
    name    = lead.get("full_name") or "—"
    company = lead.get("company_raw") or "—"
    title   = lead.get("lead_title") or "—"
    website = lead.get("company_website") or ""

    # ── Header ──
    st.markdown("---")
    hcol1, hcol2 = st.columns([4, 1])
    with hcol1:
        st.markdown(f"## {name}")
        co_link = f"[{company}]({website})" if website else company
        st.markdown(f"**{title}** · {co_link}")
        if lead.get("lead_linkedin"):
            st.markdown(f"[View LinkedIn ↗]({lead['lead_linkedin']})")
    with hcol2:
        st.markdown(badge(lead.get("status")), unsafe_allow_html=True)
        st.caption(f"Enriched {fmt_date(lead.get('enriched_at'))}")

    # ── Buying signals (top of page — most important for sales) ──
    buying = lead.get("buying_signals") or []
    st.markdown('<div class="section-title">🎯 Buying Signals</div>', unsafe_allow_html=True)
    if isinstance(buying, list) and buying:
        st.markdown(item_list(buying, "buying-signal"), unsafe_allow_html=True)
    else:
        st.info("No buying signals identified for this lead.")

    st.markdown("")

    # ── Company + Lead side by side ──
    col1, col2 = st.columns(2)

    with col1:
        with st.container():
            st.markdown('<div class="section-title">🏢 Company Snapshot</div>', unsafe_allow_html=True)
            desc = lead.get("company_description")
            if desc:
                st.markdown(f"_{desc}_")
            r1c1, r1c2 = st.columns(2)
            with r1c1:
                meta("Industry",  lead.get("industry"))
                meta("Stage",     lead.get("company_stage"))
            with r1c2:
                meta("Size",      lead.get("company_size"))
                meta("HQ",        lead.get("company_hq"))

    with col2:
        with st.container():
            st.markdown('<div class="section-title">👤 Lead Profile</div>', unsafe_allow_html=True)
            meta("Title",          lead.get("lead_title"))
            meta("Tenure",         lead.get("lead_tenure"))
            meta("Background",     lead.get("lead_background"))
            meta("Traffic Source", lead.get("traffic_source"))
            meta("Contact Owner",  lead.get("contact_owner"))
            verified = lead.get("lead_verified", "")
            if verified:
                meta("Verified", verified)

    st.markdown("")

    # ── Decision makers + Recent signals ──
    col3, col4 = st.columns(2)

    with col3:
        st.markdown('<div class="section-title">👥 Decision Maker Map</div>', unsafe_allow_html=True)
        dms = lead.get("decision_makers") or []
        st.markdown(item_list(dms if isinstance(dms, list) else [], "dm-item"), unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="section-title">📡 Recent Signals</div>', unsafe_allow_html=True)
        sigs = lead.get("recent_signals") or []
        st.markdown(item_list(sigs if isinstance(sigs, list) else [], "recent-signal"), unsafe_allow_html=True)

    st.markdown("")

    # ── Competitive intel ──
    st.markdown('<div class="section-title">⚔️ Competitive Intel</div>', unsafe_allow_html=True)
    cc1, cc2, cc3 = st.columns(3)
    with cc1: meta("Tools they use",  lead.get("competitive_using"))
    with cc2: meta("Displacement angle", lead.get("competitive_angle"))
    with cc3: meta("Evidence",        lead.get("competitive_evidence"))

    # ── Lead activity ──
    activity = lead.get("recent_activity") or []
    if isinstance(activity, list) and activity:
        st.markdown("")
        st.markdown('<div class="section-title">📝 Lead\'s Recent Activity</div>', unsafe_allow_html=True)
        st.markdown(item_list(activity, "activity-item"), unsafe_allow_html=True)

    # ── Full report ──
    if lead.get("report_md"):
        st.markdown("")
        with st.expander("📄 Full Intelligence Report", expanded=False):
            st.markdown(lead["report_md"])


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if "selected_idx" not in st.session_state:
        st.session_state.selected_idx = None
    if "selected_table" not in st.session_state:
        st.session_state.selected_table = None

    # Sidebar
    with st.sidebar:
        st.image("https://nimbleway.com/wp-content/uploads/2022/01/Nimble-Logo.svg", width=140)
        st.markdown("### Lead Intelligence")
        st.caption("Review enriched leads before your calls")
        st.markdown("---")

        table_label = st.radio("Lead Type", ["Demo Requests", "Self-Serve Signups"])
        table = "demo_requests" if table_label == "Demo Requests" else "signups"

        search = st.text_input("🔍 Search", placeholder="Name or company...")

        status_filter = st.multiselect(
            "Status",
            ["enriched", "pending", "failed"],
            default=["enriched"],
        )

        owner_filter = st.text_input("Contact Owner", placeholder="Filter by owner...")

        st.markdown("---")
        if st.button("🔄 Refresh data"):
            st.cache_data.clear()
            st.session_state.selected_idx = None

    # Load + filter
    leads = load_leads(table)

    if search:
        q = search.lower()
        leads = [l for l in leads if
                 q in (l.get("full_name") or "").lower() or
                 q in (l.get("company_raw") or "").lower()]

    if status_filter:
        leads = [l for l in leads if (l.get("status") or "pending") in status_filter]

    if owner_filter:
        q = owner_filter.lower()
        leads = [l for l in leads if q in (l.get("contact_owner") or "").lower()]

    # Title + metrics
    st.title("🎯 Nimble Lead Intelligence")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total",    len(leads))
    m2.metric("Enriched", sum(1 for l in leads if l.get("status") == "enriched"))
    m3.metric("Pending",  sum(1 for l in leads if l.get("status") == "pending"))
    m4.metric("Failed",   sum(1 for l in leads if l.get("status") == "failed"))

    st.markdown("---")

    if not leads:
        st.info("No leads match your filters.")
        return

    # Table header
    h0, h1, h2, h3, h4, h5, h6 = st.columns([2.5, 2, 2, 1.2, 1, 1.2, 1])
    for col, label in zip(
        [h0, h1, h2, h3, h4, h5, h6],
        ["Lead", "Company", "Title", "Stage", "Signals", "Enriched", "Status"],
    ):
        col.markdown(f"<span style='font-size:12px;color:#6b7280;font-weight:600;text-transform:uppercase'>{label}</span>", unsafe_allow_html=True)

    st.markdown("<hr style='margin:6px 0'>", unsafe_allow_html=True)

    # Rows
    for i, lead in enumerate(leads):
        buying_count = len(lead.get("buying_signals") or [])
        c0, c1, c2, c3, c4, c5, c6 = st.columns([2.5, 2, 2, 1.2, 1, 1.2, 1])

        label = lead.get("full_name") or "—"
        if c0.button(label, key=f"lead_{table}_{i}", use_container_width=True):
            st.session_state.selected_idx   = i
            st.session_state.selected_table = table

        c1.write(lead.get("company_raw") or "—")
        c2.write(lead.get("lead_title") or "—")
        c3.write(lead.get("company_stage") or "—")
        c4.write(f"🎯 {buying_count}" if buying_count else "—")
        c5.write(fmt_date(lead.get("enriched_at")))
        c6.markdown(badge(lead.get("status")), unsafe_allow_html=True)

    # Detail panel
    if (
        st.session_state.selected_idx is not None
        and st.session_state.selected_table == table
        and st.session_state.selected_idx < len(leads)
    ):
        show_lead(leads[st.session_state.selected_idx])


if __name__ == "__main__":
    main()
