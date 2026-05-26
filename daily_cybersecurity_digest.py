#!/usr/bin/env python3
"""
Daily Cybersecurity Digest
Fetches cybersecurity RSS feeds concurrently, saves an HTML report to GitHub Pages.
Email notification is handled by GitHub Actions (.github/workflows/notify.yml).
"""

import difflib
import html
import os
import re
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

FEEDS = [
    ("Krebs on Security",       "https://krebsonsecurity.com/feed/"),
    ("The Hacker News",         "https://feeds.feedburner.com/TheHackersNews"),
    ("Bleeping Computer",       "https://www.bleepingcomputer.com/feed/"),
    ("SANS ISC",                "https://isc.sans.edu/rssfeed_full.xml"),
    ("SecurityWeek",            "https://feeds.feedburner.com/securityweek"),
    ("Dark Reading",            "https://www.darkreading.com/rss.xml"),
    ("CISA Alerts",             "https://www.cisa.gov/uscert/ncas/alerts.xml"),
    ("Schneier on Security",    "https://www.schneier.com/feed/atom/"),
    ("Exploit-DB",              "https://www.exploit-db.com/rss.xml"),
    ("CISA ICS Advisories",     "https://www.cisa.gov/uscert/ics/advisories/advisories.xml"),
    ("Talos Intelligence",      "https://blog.talosintelligence.com/rss/"),
    ("Google Project Zero",     "https://googleprojectzero.blogspot.com/feeds/posts/default"),
    ("ThreatPost",              "https://threatpost.com/feed/"),
    ("Wired Security",          "https://www.wired.com/feed/category/security/latest/rss"),
    ("Ars Technica Security",   "https://feeds.arstechnica.com/arstechnica/security"),
    ("Naked Security (Sophos)", "https://nakedsecurity.sophos.com/feed/"),
    ("Troy Hunt",               "https://feeds.feedburner.com/TroyHunt"),
    ("Microsoft Security Blog", "https://www.microsoft.com/en-us/security/blog/feed/"),
    ("US-CERT",                 "https://www.cisa.gov/uscert/ncas/current-activity.xml"),
]

FETCH_TIMEOUT  = 10
MAX_WORKERS    = len(FEEDS)
LOOKBACK_HOURS = 24

REPORT_FILE = "index.html"
REPORT_URL  = "https://lukan47.github.io/RSS/"

CATEGORIES = {
    "Zero-Day Exploits & Vulnerabilities": [
        "zero-day", "zero day", "0-day", "0day",
        "exploit", "exploited", "exploitation",
        "remote code execution", "rce", "arbitrary code",
        "cve-", "nvd", "patch tuesday", "out-of-band patch",
        "unpatched", "proof of concept", "poc",
        "privilege escalation", "sql injection", "buffer overflow",
        "use-after-free", "heap overflow",
    ],
    "Company & Service Acquisitions": [
        "acqui", "acquisition", "acquired", "acquires",
        "merger", "merges", "merged",
        "bought", "buys", "purchase", "deal worth",
        "hostile takeover", "corporate takeover",
        "investment", "investor", "investing",
        "funding round", "series a", "series b", "series c",
        "valuation", "ipo", "spin-off", "divest",
    ],
    "Top Cybersecurity Companies": [
        # Trend Micro / TrendAI
        "trend micro", "trendmicro", "trendai", "trend ai",
        # CrowdStrike
        "crowdstrike", "falcon sensor", "falcon platform",
        # Palo Alto Networks
        "palo alto", "palo alto networks", "cortex", "prisma",
        # Fortinet
        "fortinet", "fortigate", "fortios", "forticlient",
        # SentinelOne
        "sentinelone", "sentinel one",
        # Microsoft Security
        "microsoft security", "microsoft defender", "azure security",
        "microsoft entra", "microsoft sentinel",
        # Google / Mandiant
        "mandiant", "google threat", "google security",
        # Cisco / Talos
        "cisco talos", "cisco security", "cisco umbrella",
        # Check Point
        "checkpoint", "check point",
        # Sophos
        "sophos", "naked security",
        # Others
        "darktrace", "recorded future", "malwarebytes",
        "symantec", "broadcom security",
        "okta", "cyberark", "varonis", "vectra",
        "secureworks", "huntress",
    ],
    "Rapid7": [
        "rapid7", "insightvm", "metasploit", "nexpose",
        "insight platform", "rapid 7",
    ],
    "Tenable": [
        "tenable", "nessus", "tenable.io", "tenable.sc",
        "tenable one", "lumin",
    ],
    "Qualys": [
        "qualys", "qualysguard", "vmdr", "qualys cloud",
    ],
    "Zscaler": [
        "zscaler", "zpa", "zia", "zero trust exchange",
        "zscaler internet access", "zscaler private access",
    ],
}

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

DATE_FORMATS = [
    "%a, %d %b %Y %H:%M:%S %z",
    "%a, %d %b %Y %H:%M:%S GMT",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%SZ",
]


def _parse_date(text: str) -> datetime | None:
    if not text:
        return None
    text = text.strip()
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(text, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def _text(element, tag: str) -> str:
    child = element.find(tag)
    return html.unescape(child.text.strip()) if child is not None and child.text else ""

# ---------------------------------------------------------------------------
# Feed fetching
# ---------------------------------------------------------------------------

def fetch_feed(name: str, url: str) -> list[dict]:
    try:
        req = Request(url, headers={"User-Agent": "DailyCybersecurityDigest/1.0"})
        with urlopen(req, timeout=FETCH_TIMEOUT) as resp:
            raw = resp.read()
    except (URLError, OSError) as exc:
        print(f"  [WARN] {name}: {exc}", file=sys.stderr)
        return []

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        print(f"  [WARN] {name}: XML parse error - {exc}", file=sys.stderr)
        return []

    articles = []
    is_atom = root.tag in ("feed", "{http://www.w3.org/2005/Atom}feed")

    if is_atom:
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title   = _text(entry, "{http://www.w3.org/2005/Atom}title")
            link_el = entry.find("{http://www.w3.org/2005/Atom}link")
            link    = link_el.get("href", "") if link_el is not None else ""
            date    = _parse_date(
                _text(entry, "{http://www.w3.org/2005/Atom}updated") or
                _text(entry, "{http://www.w3.org/2005/Atom}published")
            )
            articles.append({"source": name, "title": title, "link": link, "date": date})
    else:
        channel = root.find("channel")
        if channel is None:
            channel = root
        for item in channel.findall("item"):
            articles.append({
                "source": name,
                "title": _text(item, "title"),
                "link":  _text(item, "link"),
                "date":  _parse_date(_text(item, "pubDate")),
            })

    return articles


def fetch_all_feeds() -> list[dict]:
    all_articles: list[dict] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(fetch_feed, name, url): name for name, url in FEEDS}
        for future in as_completed(futures):
            all_articles.extend(future.result())
    return all_articles

# ---------------------------------------------------------------------------
# Filtering & categorization
# ---------------------------------------------------------------------------

def filter_recent(articles: list[dict], hours: int = LOOKBACK_HOURS) -> list[dict]:
    cutoff  = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent  = [a for a in articles if a["date"] and a["date"] >= cutoff]
    undated = [a for a in articles if not a["date"]]
    return sorted(recent, key=lambda a: a["date"], reverse=True) + undated


# Words too common to be useful for topic matching
_STOP_WORDS = {
    "a", "an", "the", "and", "or", "for", "of", "in", "on", "at", "to",
    "is", "are", "was", "were", "be", "been", "have", "has", "had", "with",
    "from", "by", "as", "its", "not", "but", "this", "that", "over", "after",
    "new", "says", "said", "via", "how", "why", "what", "when", "who",
    "into", "than", "more", "your", "about", "just", "using", "used",
}


def _keywords(title: str) -> set[str]:
    """Extract significant words (4+ chars, not stop words) from a title."""
    words = re.findall(r'[a-z0-9]+(?:-[a-z0-9]+)*', title.lower())
    return {w for w in words if len(w) >= 4 and w not in _STOP_WORDS}


def deduplicate(articles: list[dict], threshold: float = 0.80, keyword_overlap: int = 3) -> list[dict]:
    """
    Remove redundant articles using three checks (any one triggers dedup):
      1. Exact URL match        — same link from multiple feeds
      2. Title string similarity — same phrasing  (>= threshold)
      3. Keyword overlap        — same topic, different wording (>= keyword_overlap shared words)
    The first article encountered (most recent / highest priority source) is kept.
    """
    seen_urls: set[str] = set()
    unique:    list[dict] = []

    for article in articles:
        # ── Pass 1: exact URL dedup ──────────────────────────────────────
        url = article["link"].strip().rstrip("/")
        if url and url in seen_urls:
            continue

        # ── Pass 2 & 3: title similarity + keyword overlap ───────────────
        title     = article["title"].lower()
        title_kws = _keywords(article["title"])
        is_duplicate = False

        for kept in unique:
            # Check 2: string similarity
            if difflib.SequenceMatcher(None, title, kept["title"].lower()).ratio() >= threshold:
                is_duplicate = True
                break
            # Check 3: shared significant keywords
            if len(title_kws & _keywords(kept["title"])) >= keyword_overlap:
                is_duplicate = True
                break

        if is_duplicate:
            continue

        if url:
            seen_urls.add(url)
        unique.append(article)

    removed = len(articles) - len(unique)
    if removed:
        print(f"  [INFO] Deduplication removed {removed} redundant article(s).", file=sys.stderr)
    return unique


def categorize(article: dict) -> list[str]:
    haystack = article["title"].lower()
    matched  = [cat for cat, kws in CATEGORIES.items() if any(kw in haystack for kw in kws)]
    return matched or ["General Security News"]


def bucket_articles(articles: list[dict]) -> dict[str, list[dict]]:
    buckets: dict[str, list[dict]] = {cat: [] for cat in CATEGORIES}
    buckets["General Security News"] = []
    for a in articles:
        for cat in categorize(a):
            buckets[cat].append(a)
    # Preserve display order: named categories first, General Security News last
    ordered = {cat: buckets[cat] for cat in CATEGORY_COLORS if cat in buckets}
    ordered["General Security News"] = buckets["General Security News"]
    return ordered

# ---------------------------------------------------------------------------
# HTML report — column layout
# ---------------------------------------------------------------------------

CATEGORY_COLORS = {
    "Zero-Day Exploits & Vulnerabilities": "#e74c3c",  # red
    "Company & Service Acquisitions":      "#3498db",  # blue
    "Top Cybersecurity Companies":         "#2ecc71",  # green
    "Rapid7":                              "#e67e22",  # orange
    "Tenable":                             "#9b59b6",  # purple
    "Qualys":                              "#1abc9c",  # teal
    "Zscaler":                             "#f1c40f",  # yellow
    "General Security News":               "#95a5a6",  # grey
}


def build_html(articles: list[dict], today: str) -> str:
    buckets = bucket_articles(articles)
    columns = []

    for cat, items in buckets.items():
        if not items:
            continue  # hide empty columns
        color = CATEGORY_COLORS.get(cat, "#95a5a6")
        cards = []
        for a in items:
            date_str    = a["date"].strftime("%Y-%m-%d %H:%M UTC") if a["date"] else "unknown date"
            safe_title  = html.escape(a["title"])
            safe_source = html.escape(a["source"])
            safe_link   = html.escape(a["link"])
            cards.append(f"""
            <div class="card">
              <div class="card-meta">
                <span class="source">{safe_source}</span>
                <span class="date">{date_str}</span>
              </div>
              <a class="card-title" href="{safe_link}" target="_blank">{safe_title}</a>
            </div>""")

        columns.append(f"""
      <div class="col">
        <div class="col-header" style="border-top:4px solid {color};">
          <h2>{html.escape(cat)}</h2>
          <span class="count">{len(items)} article(s)</span>
        </div>
        <div class="col-body">
          {"".join(cards)}
        </div>
      </div>""")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Cybersecurity Digest - {today}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #0f1117;
    color: #e0e0e0;
    padding: 24px;
  }}

  /* ── Header ── */
  header {{
    margin-bottom: 28px;
  }}
  header h1 {{ font-size: 1.8rem; color: #fff; }}
  header p  {{ color: #888; margin-top: 6px; font-size: 0.9rem; }}

  /* ── Column grid ── */
  .grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    align-items: start;
  }}
  @media (max-width: 1200px) {{
    .grid {{ grid-template-columns: repeat(2, 1fr); }}
  }}
  @media (max-width: 640px) {{
    .grid {{ grid-template-columns: 1fr; }}
  }}

  /* ── Column card ── */
  .col {{
    background: #13161f;
    border-radius: 10px;
    overflow: hidden;
  }}
  .col-header {{
    padding: 14px 16px 10px;
    background: #1a1d27;
  }}
  .col-header h2 {{
    font-size: 0.88rem;
    color: #fff;
    font-weight: 700;
    line-height: 1.4;
  }}
  .count {{
    font-size: 0.74rem;
    color: #555;
    margin-top: 4px;
    display: block;
  }}
  .col-body {{ padding: 12px; }}

  /* ── Article card ── */
  .card {{
    background: #1a1d27;
    border-radius: 7px;
    padding: 12px 14px;
    margin-bottom: 10px;
  }}
  .card:last-child {{ margin-bottom: 0; }}
  .card-meta {{
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 4px;
    font-size: 0.72rem;
    color: #555;
    margin-bottom: 6px;
  }}
  .source {{ color: #5b8dee; font-weight: 600; }}
  .card-title {{
    color: #d8d8d8;
    text-decoration: none;
    font-size: 0.88rem;
    line-height: 1.5;
    display: block;
  }}
  .card-title:hover {{ color: #fff; text-decoration: underline; }}

  .empty {{ font-size: 0.82rem; color: #444; padding: 8px 0; }}

  footer {{
    margin-top: 40px;
    font-size: 0.75rem;
    color: #333;
    text-align: center;
  }}
</style>
</head>
<body>
<header>
  <h1>Daily Cybersecurity Digest</h1>
  <p>{today} &nbsp;·&nbsp; {len(articles)} article(s) in the last {LOOKBACK_HOURS} hours</p>
</header>

<div class="grid">
  {"".join(columns)}
</div>

<footer>Generated automatically · lukan47/RSS</footer>
</body>
</html>"""

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print("Fetching feeds...", file=sys.stderr)
    articles = fetch_all_feeds()
    print(f"Fetched {len(articles)} total articles.", file=sys.stderr)

    recent = filter_recent(articles)
    if not recent:
        print("  [INFO] No articles in last 24h, showing all fetched articles.", file=sys.stderr)
        recent = articles

    recent = deduplicate(recent)
    print(f"  {len(recent)} unique article(s) after deduplication.", file=sys.stderr)

    # Export latest acquisition to GitHub Actions env (used by Teams notification)
    buckets    = bucket_articles(recent)
    acq_list   = buckets.get("Company & Service Acquisitions", [])
    github_env = os.environ.get("GITHUB_ENV", "")
    if github_env:
        if acq_list:
            acq_title = acq_list[0]["title"].replace("\n", " ")
            acq_link  = acq_list[0]["link"]
            acq_found = "true"
        else:
            acq_title = ""
            acq_link  = ""
            acq_found = "false"
        with open(github_env, "a", encoding="utf-8") as f:
            f.write(f"LATEST_ACQ_TITLE={acq_title}\n")
            f.write(f"LATEST_ACQ_LINK={acq_link}\n")
            f.write(f"LATEST_ACQ_FOUND={acq_found}\n")

    print(f"Writing {REPORT_FILE}...", file=sys.stderr)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(build_html(recent, today))
    print(f"Done. Open {REPORT_URL} after pushing.", file=sys.stderr)


if __name__ == "__main__":
    main()
