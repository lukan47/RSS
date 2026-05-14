branch: main
content: #!/usr/bin/env python3
"""
Daily Cybersecurity Digest
Fetches cybersecurity RSS feeds concurrently, saves an HTML report to GitHub Pages,
and emails a link to the report.
"""

import base64
import html
import json
import os
import smtplib
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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
    ("NVD CVE Feed",            "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml"),
    ("CISA ICS Advisories",     "https://www.cisa.gov/uscert/ics/advisories/advisories.xml"),
    ("Talos Intelligence",      "https://blog.talosintelligence.com/feeds/posts/default"),
    ("Google Project Zero",     "https://googleprojectzero.blogspot.com/feeds/posts/default"),
]

FETCH_TIMEOUT  = 10
MAX_WORKERS    = len(FEEDS)
LOOKBACK_HOURS = 24

# ---------------------------------------------------------------------------
# Email settings
# ---------------------------------------------------------------------------
# Gmail (default) — set SMTP_PASSWORD env var to your Gmail App Password
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = "marcpajota@gmail.com"
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

# Outlook alternative — uncomment and comment out the Gmail block above
# SMTP_HOST     = "smtp.office365.com"
# SMTP_PORT     = 587
# SMTP_USER     = "marc_pajota@trendmicro.com"
# SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

EMAIL_FROM = "marcpajota@gmail.com"
EMAIL_TO   = "marc_pajota@trendmicro.com"

# ---------------------------------------------------------------------------
# GitHub report settings
# ---------------------------------------------------------------------------
# Set GITHUB_TOKEN env var to a Personal Access Token with repo scope.
# Enable GitHub Pages: repo Settings -> Pages -> Deploy from branch -> main -> / (root)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO  = "lukan47/RSS"
REPORT_FILE  = "index.html"
REPORT_URL   = "https://lukan47.github.io/RSS/"

# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
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
        "takeover", "invest", "funding", "valuation",
        "ipo", "spin-off", "divest",
    ],
    "Vendor News (CrowdStrike, Microsoft, Fortinet, Trend Micro & others)": [
        "crowdstrike", "microsoft", "fortinet",
        "trend micro", "trendmicro", "trendai", "trend ai",
        "palo alto", "sentinelone", "rapid7", "tenable",
        "mandiant", "recorded future", "darktrace",
        "cisco talos", "sophos", "malwarebytes",
        "checkpoint", "check point", "symantec", "broadcom",
        "google security", "project zero",
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
        channel = root.find("channel") or root
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
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent  = [a for a in articles if a["date"] and a["date"] >= cutoff]
    undated = [a for a in articles if not a["date"]]
    return sorted(recent, key=lambda a: a["date"], reverse=True) + undated


def categorize(article: dict) -> list[str]:
    haystack = article["title"].lower()
    matched = [cat for cat, kws in CATEGORIES.items() if any(kw in haystack for kw in kws)]
    return matched or ["General Security News"]


def bucket_articles(articles: list[dict]) -> dict[str, list[dict]]:
    buckets: dict[str, list[dict]] = {cat: [] for cat in CATEGORIES}
    buckets["General Security News"] = []
    for a in articles:
        for cat in categorize(a):
            buckets[cat].append(a)
    return buckets

# ---------------------------------------------------------------------------
# HTML report
# ---------------------------------------------------------------------------

CATEGORY_COLORS = {
    "Zero-Day Exploits & Vulnerabilities":                                    "#e74c3c",
    "Company & Service Acquisitions":                                         "#3498db",
    "Vendor News (CrowdStrike, Microsoft, Fortinet, Trend Micro & others)":   "#2ecc71",
    "General Security News":                                                  "#95a5a6",
}


def build_html(articles: list[dict], today: str) -> str:
    buckets = bucket_articles(articles)

    sections = []
    for cat, items in buckets.items():
        if not items:
            continue
        color = CATEGORY_COLORS.get(cat, "#95a5a6")
        cards = []
        for a in items:
            date_str = a["date"].strftime("%Y-%m-%d %H:%M UTC") if a["date"] else "unknown date"
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

        sections.append(f"""
        <section>
            <h2 style="border-left: 5px solid {color}; padding-left: 12px;">{html.escape(cat)}</h2>
            <p class="count">{len(items)} article(s)</p>
            {"".join(cards)}
        </section>""")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Cybersecurity Digest - {today}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0f1117; color: #e0e0e0; padding: 24px; }}
  header {{ max-width: 900px; margin: 0 auto 32px; }}
  header h1 {{ font-size: 1.8rem; color: #ffffff; }}
  header p {{ color: #888; margin-top: 6px; }}
  section {{ max-width: 900px; margin: 0 auto 40px; }}
  h2 {{ font-size: 1.1rem; color: #ffffff; margin-bottom: 8px; }}
  .count {{ font-size: 0.8rem; color: #666; margin-bottom: 16px; }}
  .card {{ background: #1a1d27; border-radius: 8px; padding: 16px; margin-bottom: 12px; }}
  .card-meta {{ display: flex; justify-content: space-between; font-size: 0.78rem; color: #666; margin-bottom: 8px; }}
  .source {{ color: #5b8dee; font-weight: 600; }}
  .card-title {{ color: #e0e0e0; text-decoration: none; font-size: 0.97rem; line-height: 1.5; }}
  .card-title:hover {{ color: #ffffff; text-decoration: underline; }}
  footer {{ max-width: 900px; margin: 40px auto 0; font-size: 0.78rem; color: #444; text-align: center; }}
</style>
</head>
<body>
<header>
  <h1>Daily Cybersecurity Digest</h1>
  <p>{today} &nbsp;·&nbsp; {len(articles)} article(s) in the last {LOOKBACK_HOURS} hours</p>
</header>
{"".join(sections)}
<footer>Generated automatically · lukan47/RSS</footer>
</body>
</html>"""

# ---------------------------------------------------------------------------
# GitHub Pages push
# ---------------------------------------------------------------------------

def push_report_to_github(html_content: str, today: str) -> str:
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{REPORT_FILE}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DailyCybersecurityDigest/1.0",
        "Content-Type": "application/json",
    }

    sha = None
    try:
        req = Request(api_url, headers=headers)
        with urlopen(req) as resp:
            sha = json.loads(resp.read()).get("sha")
    except HTTPError:
        pass

    payload: dict = {
        "message": f"Update digest report {today}",
        "content": base64.b64encode(html_content.encode()).decode(),
    }
    if sha:
        payload["sha"] = sha

    req = Request(api_url, data=json.dumps(payload).encode(), headers=headers, method="PUT")
    with urlopen(req):
        pass

    return REPORT_URL

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

def send_email(today: str, article_count: int, report_url: str) -> None:
    subject = f"Daily Cybersecurity Digest - {today}"

    plain = (
        f"Your Daily Cybersecurity Digest for {today} is ready.\n\n"
        f"{article_count} article(s) collected in the last {LOOKBACK_HOURS} hours.\n\n"
        f"View the full report: {report_url}\n"
    )
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;background:#0f1117;color:#e0e0e0;padding:32px;border-radius:10px;">
      <h2 style="color:#fff;">Daily Cybersecurity Digest</h2>
      <p style="color:#888;">{today}</p>
      <p style="margin:24px 0;font-size:1rem;">{article_count} article(s) collected in the last {LOOKBACK_HOURS} hours.</p>
      <a href="{report_url}" style="display:inline-block;background:#5b8dee;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold;">
        View Full Report
      </a>
      <p style="margin-top:32px;font-size:0.8rem;color:#444;">lukan47/RSS · automated digest</p>
    </div>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_FROM
    msg["To"]      = EMAIL_TO
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print("Fetching feeds...", file=sys.stderr)
    articles = fetch_all_feeds()
    print(f"Fetched {len(articles)} total articles.", file=sys.stderr)

    recent = filter_recent(articles)

    report_url = REPORT_URL
    if GITHUB_TOKEN:
        print("Pushing HTML report to GitHub...", file=sys.stderr)
        try:
            report_url = push_report_to_github(build_html(recent, today), today)
            print(f"Report published: {report_url}", file=sys.stderr)
        except Exception as exc:
            print(f"  [WARN] Could not push report: {exc}", file=sys.stderr)
    else:
        print("  [SKIP] GITHUB_TOKEN not set - skipping report upload.", file=sys.stderr)

    if SMTP_PASSWORD:
        print("Sending email...", file=sys.stderr)
        try:
            send_email(today, len(recent), report_url)
            print(f"Email sent to {EMAIL_TO}.", file=sys.stderr)
        except Exception as exc:
            print(f"  [WARN] Could not send email: {exc}", file=sys.stderr)
    else:
        print("  [SKIP] SMTP_PASSWORD not set - skipping email.", file=sys.stderr)


if __name__ == "__main__":
    main()

message: Add HTML report, GitHub Pages push, categorization, and email delivery
owner: lukan47
path: daily_cybersecurity_digest.py
repo: RSS
sha: dd9d6499d0a77c643a281b52e33c1e2db957ba92

failed to create/update file: PUT https://api.github.com/repos/lukan47/RSS/contents/daily_cybersecurity_digest.py: 403 Resource not accessible by integration []
