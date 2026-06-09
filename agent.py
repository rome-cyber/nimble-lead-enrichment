#!/usr/bin/env python3
"""
Lead Enrichment Agent

When a new lead signs up for a demo, this agent automatically researches
them so the sales rep walks into every call fully informed.

Uses:
  - Nimble Search API  → discover signals: news, LinkedIn, funding, hiring
  - Nimble Extract API → pull full content from LinkedIn, Crunchbase, articles
  - Claude            → orchestrate research and synthesize the report
"""

import os
import re
import sys
import json
import requests
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from dotenv import load_dotenv
import anthropic

load_dotenv(Path(__file__).parent / ".env", override=True)

# ── Config ─────────────────────────────────────────────────────────────────────

NIMBLE_API_KEY  = os.getenv("NIMBLE_API_KEY")
ANTHROPIC_KEY   = os.getenv("ANTHROPIC_API_KEY")
NIMBLE_SEARCH   = "https://sdk.nimbleway.com/v1/search"
NIMBLE_EXTRACT  = "https://sdk.nimbleway.com/v1/extract"
TODAY           = datetime.now().strftime("%Y-%m-%d")

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# ── HTML → readable text ───────────────────────────────────────────────────────

class _TextExtractor(HTMLParser):
    SKIP  = {"script", "style", "nav", "footer", "head", "noscript", "iframe"}
    BLOCK = {"p", "div", "li", "h1", "h2", "h3", "h4", "br", "tr", "section", "article"}

    def __init__(self):
        super().__init__()
        self._chunks: list = []
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._depth += 1
        elif tag in self.BLOCK and self._chunks and self._chunks[-1] != "\n":
            self._chunks.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self._depth = max(0, self._depth - 1)

    def handle_data(self, data):
        if self._depth:
            return
        text = data.strip()
        if text:
            self._chunks.append(text)

    def get_text(self) -> str:
        joined = " ".join(self._chunks)
        text = re.sub(r"[ \t]+", " ", joined)
        text = re.sub(r"\n{3,}", "\n\n", text)
        lines = [l for l in text.splitlines() if len(l.strip()) > 2]
        return "\n".join(lines).strip()


def _html_to_text(html: str) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(html)
        return parser.get_text()
    except Exception:
        return re.sub(r"<[^>]+>", " ", html).strip()


# ── Nimble API calls ───────────────────────────────────────────────────────────

def nimble_search(query: str, focus: str = "general", max_results: int = 6) -> str:
    headers = {"Authorization": f"Bearer {NIMBLE_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "query": query,
        "num_results": max_results,
        "search_depth": "lite",
        "focus": focus,
    }
    try:
        resp = requests.post(NIMBLE_SEARCH, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            return "No results found."
        lines = []
        for r in results:
            lines.append(f"{r.get('title', '')} | {r.get('url', '')}")
            lines.append(r.get('description', '')[:150])
            lines.append("---")
        return "\n".join(lines)
    except Exception as e:
        return f"Search error: {e}"


def nimble_extract(url: str) -> str:
    headers = {"Authorization": f"Bearer {NIMBLE_API_KEY}", "Content-Type": "application/json"}
    payload = {"url": url, "render": True, "driver": "vx8"}
    try:
        resp = requests.post(NIMBLE_EXTRACT, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data  = resp.json().get("data", {})
        raw   = data.get("markdown") or data.get("text") or data.get("html", "")
        if not raw:
            return "No content extracted."
        text = _html_to_text(raw) if raw.lstrip().startswith("<") else raw
        return text[:2500]
    except Exception as e:
        return f"Extract error: {e}"


# ── Tool definitions ───────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "web_search",
        "description": (
            "Search the web for information about a company or person using Nimble Search. "
            "Use this to discover news, LinkedIn profiles, funding announcements, "
            "job postings, product launches, and any other signals. "
            "Run multiple targeted searches — one focused query per topic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Be specific and targeted.",
                },
                "focus": {
                    "type": "string",
                    "enum": ["general", "news", "social"],
                    "description": (
                        "'news' for articles and press, "
                        "'social' for LinkedIn/Twitter posts, "
                        "'general' for everything else."
                    ),
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "extract_page",
        "description": (
            "Extract the full content of a specific URL using Nimble Extract API. "
            "Nimble bypasses bot detection and anti-scraping measures, so use it freely "
            "on news articles, company websites, changelogs, Crunchbase, job boards, "
            "blogs, and press releases. "
            "AVOID extracting linkedin.com/in/* personal profile URLs — LinkedIn gates "
            "those behind login even for real browsers; use search snippet data instead. "
            "LinkedIn company pages (linkedin.com/company/*) and LinkedIn posts are fine to extract."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL to extract content from.",
                },
            },
            "required": ["url"],
        },
    },
]


# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""You are a B2B lead enrichment agent for Nimble's sales team.
Research each lead and produce a concise intelligence report. Bullets only — no prose.

RESEARCH STEPS (run in order):

0. RESOLVE & VERIFY — search "{{company}}" and "{{lead}} {{company}}" to canonicalise
   names and confirm the lead works there. Use resolved names throughout.
   If unverifiable, continue anyway and flag in Lead Profile.

1. COMPANY — search: news {TODAY[:4]}, funding, product launches, hiring, crunchbase

2. LEAD — search: "{{lead}}" "{{company}}", "{{lead}}" site:linkedin.com

3. DECISION MAKERS — search: CEO/founder, CTO/VP Eng, VP Sales/Product at {{company}}

4. LEAD ACTIVITY — search: {{lead}} LinkedIn posts {TODAY[:4]}, Twitter/X, blog/articles

5. COMPETITIVE — search: {{company}} jobs tech stack, "built with"/"migrated from", github

6. EXTRACT up to 4 pages (skip linkedin.com/in/* — login-gated):
   company LinkedIn page, top news/funding article, crunchbase, 1 job posting

7. WRITE the report below. Bullets only, one line each, "—" if unknown.

# Lead Enrichment: {{lead}} @ {{company}}
*{TODAY}*

## Company Snapshot
- **Verified:** [✅ Confirmed at {{company}} / ⚠️ Found — no clear link to {{company}} / ❌ Not found]
- **Industry:** [one line]
- **Stage:** [e.g. Series B · $47M raised]
- **Size:** [e.g. ~120 employees]
- **HQ:** [City, Country]
- **What they do:** [one line max]
- **Website:** [URL]

## Lead Profile
- **Title:** [current title]
- **Tenure:** [e.g. 8 months]
- **Background:** [2 prior roles, one line]
- **Education:** [school if found, or —]
- **LinkedIn:** [URL or —]

## Lead's Recent Activity
- [Date] — [what they posted/wrote, max 12 words] ([URL])
- [Date] — [what they posted/wrote, max 12 words] ([URL])
- [Date] — [what they posted/wrote, max 12 words] ([URL])
[3 bullets max. If none: "— No recent public content found."]

## Decision Maker Map
- **[Name]** · [Title] · [budget owner / champion / influencer]
- **[Name]** · [Title] · [budget owner / champion / influencer]
[3-5 people. Use "Not identified" if unknown.]

## Recent Signals
- [Date] — [signal, max 12 words] ([URL])
- [Date] — [signal, max 12 words] ([URL])
- [Date] — [signal, max 12 words] ([URL])
[5 bullets max, last 90 days. If none: "— No major signals in the last 90 days."]

## Competitive Landscape
- **Using:** [specific tools comma-separated, or —]
- **Evidence:** [JD quote / GitHub / blog — one line]
- **Angle:** [displacement wedge or greenfield — one line]

## Buying Signals
- [specific trigger — one line, real finding]
- [specific trigger — one line, real finding]
- [specific trigger — one line, real finding]
[3 bullets max. Concrete facts only.]

---
*Sources: [comma-separated domains]*"""


# ── Agentic loop ───────────────────────────────────────────────────────────────

def _run_tool(name: str, tool_input: dict) -> str:
    if name == "web_search":
        return nimble_search(
            query=tool_input["query"],
            focus=tool_input.get("focus", "general"),
        )
    if name == "extract_page":
        return nimble_extract(url=tool_input["url"])
    return f"Unknown tool: {name}"


def enrich_lead(company_name: str, lead_name: str, on_tool_call=None) -> str:
    """
    Research a lead and return a markdown enrichment report.
    on_tool_call(tool_name, label) is called each time a tool is invoked —
    use it to stream progress into a UI.
    """
    user_msg = (
        f"Enrich this new demo signup and generate a full sales intelligence report.\n\n"
        f"Company:   {company_name}\n"
        f"Lead Name: {lead_name}\n"
        f"Date:      {TODAY}"
    )

    messages = [{"role": "user", "content": user_msg}]

    print(f"\nResearching {lead_name} @ {company_name}...\n")

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "No report generated."

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    label = (block.input.get("query") or block.input.get("url", "")).strip()
                    print(f"  [{block.name}] {label[:90]}")
                    if on_tool_call:
                        on_tool_call(block.name, label)
                    result = _run_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    return "Agent stopped unexpectedly."


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) == 3:
        company = sys.argv[1]
        lead    = sys.argv[2]
    else:
        company = input("Company name:  ").strip()
        lead    = input("Lead name:     ").strip()

    report = enrich_lead(company, lead)

    print("\n" + "=" * 70)
    print(report)
    print("=" * 70 + "\n")

    slug     = f"{lead.replace(' ', '_')}_{company.replace(' ', '_')}"
    out_path = Path(__file__).parent / f"enrichment_{slug}_{TODAY}.md"
    out_path.write_text(report)
    print(f"Report saved → {out_path.name}")
