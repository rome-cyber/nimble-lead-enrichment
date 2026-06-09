#!/usr/bin/env python3
"""
Nimble Lead Enrichment Monitor

Polls two Slack channels for new signup notifications.
For each new lead: parses the message, runs the enrichment agent,
and stores structured results in Supabase.

Required env vars (add to .env):
  SLACK_BOT_TOKEN    — existing bot token
  SUPABASE_URL       — https://xxxx.supabase.co
  SUPABASE_ANON_KEY  — your anon/service key
  LEAD_CHANNELS      — comma-separated channel IDs, e.g. C123ABC,C456DEF
"""

import os
import re
import sys
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from supabase import create_client

sys.path.insert(0, str(Path(__file__).parent))
from agent import enrich_lead

load_dotenv(Path(__file__).parent / ".env", override=True)

# ── Config ─────────────────────────────────────────────────────────────────────

SLACK_TOKEN    = os.getenv("SLACK_BOT_TOKEN")
SUPABASE_URL   = os.getenv("SUPABASE_URL")
SUPABASE_KEY   = os.getenv("SUPABASE_ANON_KEY")
CHANNEL_IDS    = [c.strip() for c in os.getenv("LEAD_CHANNELS", "").split(",") if c.strip()]
POLL_INTERVAL  = 30  # seconds between channel polls

# Channel → Supabase table routing
CHANNEL_TABLE = {
    "C0AGVM6H76U": "signups",       # Nimble self-serve signups
    "C09P15RLKL4": "demo_requests", # Demo requests
}

slack    = WebClient(token=SLACK_TOKEN)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Slack message parser ───────────────────────────────────────────────────────

def is_signup(text: str) -> bool:
    return "new sign up has been submitted" in text.lower()


def parse_signup(text: str) -> dict:
    """
    Parse a Nimble HubSpot signup notification from Slack.
    Handles the 'Company: XyzOriginal Traffic Source' run-on formatting.
    """
    def grab(pattern, default=""):
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return m.group(1).strip() if m else default

    first   = grab(r"First name:\s*(\S+)")
    last    = grab(r"Last name:\s*(\S+)")
    email   = grab(r"Email:\s*(?:<mailto:)?([\w.+\-]+@[\w.\-]+)")
    company = grab(r"Company:\s*(.+?)(?=Original Traffic Source|Contact owner|\Z)")
    owner   = grab(r"Contact owner:\s*(.+?)(?=\n|Recent Conversion|\Z)")
    source  = grab(r"Original Traffic Source:\s*(.+?)(?=\n|Original Traffic Source Drill|\Z)")

    company = company.strip()

    # Fallback: derive company from email domain if field is blank
    if not company and email and "@" in email:
        domain = email.split("@")[1]
        # Strip common free email providers
        free = {"gmail.com","yahoo.com","hotmail.com","outlook.com","icloud.com","me.com"}
        if domain not in free:
            company = domain.split(".")[0].capitalize()

    return {
        "first_name":     first,
        "last_name":      last,
        "full_name":      f"{first} {last}".strip(),
        "email":          email,
        "company_raw":    company,
        "contact_owner":  owner.strip(),
        "traffic_source": source.strip(),
    }


# ── Report parser — markdown bullets → structured fields ──────────────────────

def _section(report: str, title: str) -> str:
    """Extract body of a ## section from the report."""
    m = re.search(
        rf"## {re.escape(title)}\s*\n(.*?)(?=\n## |\Z)",
        report, re.DOTALL
    )
    return m.group(1).strip() if m else ""


def _field(body: str, label: str) -> str:
    """Extract value of a '- **Label:** value' bullet.
    Handles both **Label:** value and **Label**: value formats."""
    m = re.search(rf"\*\*{re.escape(label)}:?\*\*:?\s*(.+)", body)
    return m.group(1).strip() if m else ""


def _bullets(body: str) -> list:
    """Return list of bullet point strings (without leading '- ')."""
    return [
        line[2:].strip()
        for line in body.splitlines()
        if line.strip().startswith("- ")
    ]


def parse_report(report: str) -> dict:
    snap = _section(report, "Company Snapshot")
    lead = _section(report, "Lead Profile")
    sigs = _section(report, "Recent Signals")
    buys = _section(report, "Buying Signals")
    comp = _section(report, "Competitive Landscape")
    dmap = _section(report, "Decision Maker Map")
    acty = _section(report, "Lead's Recent Activity")

    return {
        "industry":              _field(snap, "Industry"),
        "company_stage":         _field(snap, "Stage"),
        "company_size":          _field(snap, "Size"),
        "company_hq":            _field(snap, "HQ"),
        "company_website":       _field(snap, "Website"),
        "company_description":   _field(snap, "What they do"),
        "lead_verified":         _field(snap, "Verified"),
        "lead_title":            _field(lead, "Title"),
        "lead_tenure":           _field(lead, "Tenure"),
        "lead_background":       _field(lead, "Background"),
        "lead_linkedin":         _field(lead, "LinkedIn"),
        "recent_signals":        _bullets(sigs),
        "buying_signals":        _bullets(buys),
        "decision_makers":       _bullets(dmap),
        "recent_activity":       _bullets(acty),
        "competitive_using":     _field(comp, "Using"),
        "competitive_angle":     _field(comp, "Angle"),
        "competitive_evidence":  _field(comp, "Evidence"),
    }


# ── Supabase helpers ───────────────────────────────────────────────────────────

def table_for(channel: str) -> str:
    return CHANNEL_TABLE.get(channel, "signups")


def already_processed(email: str, channel: str) -> bool:
    tbl = table_for(channel)
    result = supabase.table(tbl).select("id").eq("email", email).execute()
    return len(result.data) > 0


def insert_pending(signup: dict, channel: str):
    supabase.table(table_for(channel)).insert({
        "first_name":     signup["first_name"],
        "last_name":      signup["last_name"],
        "full_name":      signup["full_name"],
        "email":          signup["email"],
        "company_raw":    signup["company_raw"],
        "contact_owner":  signup["contact_owner"],
        "traffic_source": signup["traffic_source"],
        "status":         "pending",
    }).execute()


def store_enriched(signup: dict, structured: dict, report: str, channel: str):
    row = {
        "first_name":     signup["first_name"],
        "last_name":      signup["last_name"],
        "full_name":      signup["full_name"],
        "email":          signup["email"],
        "company_raw":    signup["company_raw"],
        "contact_owner":  signup["contact_owner"],
        "traffic_source": signup["traffic_source"],
        "report_md":      report,
        "enriched_at":    datetime.now(timezone.utc).isoformat(),
        "status":         "enriched",
        **structured,
    }
    supabase.table(table_for(channel)).upsert(row, on_conflict="email").execute()


# ── Core processing ────────────────────────────────────────────────────────────

def process_message(msg: dict, channel: str):
    text = msg.get("text", "") or ""
    if not is_signup(text):
        return

    signup = parse_signup(text)
    if not signup["email"]:
        log.warning("Could not parse email from message — skipping")
        return

    if already_processed(signup["email"], channel):
        log.info(f"Already enriched {signup['email']} — skipping duplicate from channel {channel}")
        return

    log.info(f"New lead: {signup['full_name']} @ {signup['company_raw']} ({signup['email']})")

    # Block duplicate processing from the second channel before the async gap
    insert_pending(signup, channel)

    try:
        report     = enrich_lead(signup["company_raw"], signup["full_name"])
        # Detect when the agent couldn't enrich due to missing/ambiguous inputs
        if "## Company Snapshot" not in report:
            log.warning(f"Insufficient data for {signup['email']} — storing report only")
            supabase.table(table_for(channel)).update({
                "report_md": report,
                "status":    "insufficient_data",
                "enriched_at": datetime.now(timezone.utc).isoformat(),
            }).eq("email", signup["email"]).execute()
            return
        structured = parse_report(report)
        store_enriched(signup, structured, report, channel)
        log.info(f"Enriched and stored: {signup['full_name']}")
    except Exception as e:
        log.error(f"Enrichment failed for {signup['email']}: {e}")
        supabase.table(table_for(channel)).update({"status": "failed"}) \
            .eq("email", signup["email"]).execute()


# ── Poll loop ──────────────────────────────────────────────────────────────────

def seed_timestamps() -> dict:
    """Record current latest message in each channel so we don't reprocess history."""
    last_ts = {}
    for channel in CHANNEL_IDS:
        try:
            resp = slack.conversations_history(channel=channel, limit=1)
            msgs = resp.get("messages", [])
            if msgs:
                last_ts[channel] = msgs[0]["ts"]
                log.info(f"Seeded channel {channel} at ts={last_ts[channel]}")
        except SlackApiError as e:
            log.error(f"Could not seed channel {channel}: {e.response['error']}")
    return last_ts


def poll(last_ts: dict) -> dict:
    for channel in CHANNEL_IDS:
        try:
            params = {"channel": channel, "limit": 50}
            if channel in last_ts:
                params["oldest"] = last_ts[channel]

            resp     = slack.conversations_history(**params)
            messages = resp.get("messages", [])

            if messages:
                last_ts[channel] = messages[0]["ts"]   # newest is first
                for msg in reversed(messages):          # process oldest → newest
                    process_message(msg, channel)

        except SlackApiError as e:
            log.error(f"Slack error on channel {channel}: {e.response['error']}")

    return last_ts


def retry_stuck(table: str, channel: str):
    """On startup, retry any rows stuck in pending/failed for more than 5 minutes."""
    try:
        cutoff = (datetime.now(timezone.utc) - __import__('datetime').timedelta(minutes=5)).isoformat()
        rows = (
            supabase.table(table)
            .select("id,full_name,email,company_raw")
            .in_("status", ["pending", "failed"])
            .lt("created_at", cutoff)
            .execute()
            .data
        )
        if rows:
            log.info(f"Retrying {len(rows)} stuck row(s) in {table}...")
        for row in rows:
            signup = {
                "first_name":     (row.get("full_name") or "").split()[0],
                "last_name":      " ".join((row.get("full_name") or "").split()[1:]),
                "full_name":      row.get("full_name", ""),
                "email":          row.get("email", ""),
                "company_raw":    row.get("company_raw", ""),
                "contact_owner":  "",
                "traffic_source": "",
            }
            log.info(f"  Retrying: {signup['full_name']} @ {signup['company_raw']}")
            try:
                report     = enrich_lead(signup["company_raw"], signup["full_name"])
                structured = parse_report(report)
                store_enriched(signup, structured, report, channel)
            except Exception as e:
                log.error(f"  Retry failed for {signup['email']}: {e}")
                supabase.table(table).update({"status": "failed"}).eq("id", row["id"]).execute()
    except Exception as e:
        log.error(f"retry_stuck error on {table}: {e}")


def main():
    if not CHANNEL_IDS:
        raise SystemExit("Set LEAD_CHANNELS=C123ABC,C456DEF in your .env and retry.")
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_ANON_KEY in your .env and retry.")

    log.info(f"Nimble Lead Enrichment Monitor starting")
    log.info(f"Watching {len(CHANNEL_IDS)} channel(s): {', '.join(CHANNEL_IDS)}")
    log.info(f"Poll interval: {POLL_INTERVAL}s")

    # Kill any duplicate monitor processes (keep only this one)
    import os as _os
    my_pid = _os.getpid()
    for line in __import__('subprocess').check_output(["pgrep", "-f", "monitor.py"]).decode().splitlines():
        pid = int(line.strip())
        if pid != my_pid:
            try:
                _os.kill(pid, 15)
                log.info(f"Killed duplicate monitor process {pid}")
            except Exception:
                pass

    # Retry any rows stuck from a previous crashed run
    for tbl, ch in [(tbl, ch) for ch, tbl in CHANNEL_TABLE.items()]:
        retry_stuck(tbl, ch)

    last_ts = seed_timestamps()

    log.info("Listening for new signups…")
    while True:
        try:
            last_ts = poll(last_ts)
        except Exception as e:
            log.error(f"Unexpected poll error: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
