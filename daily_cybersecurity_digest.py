#!/usr/bin/env python3
"""
Daily Cybersecurity Digest
Fetches cybersecurity RSS feeds concurrently and prints articles from the last 24 hours.
"""

import html
import smtplib
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.request import urlopen, Request
from urllib.error import URLError

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

FETCH_TIMEOUT = 10       # seconds per feed request
MAX_WORKERS   = len(FEEDS)
LOOKBACK_HOURS = 24

# Optional email settings — set all three to enable email delivery
SMTP_HOST     = ""
SMTP_PORT     = 587
SMTP_USER     = ""
SMTP_PASSWORD = ""
EMAIL_FROM    = ""
EMAIL_TO      = ""


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


def _text(element, tag: str, ns: dict | None = None) -> str:
    child = element.find(tag, ns) if ns else element.find(tag)
    return html.unescape(child.text.strip()) if child is not None and child.text else ""


# ---------------------------------------------------------------------------
# Feed fetching
# ---------------------------------------------------------------------------

def fetch_feed(name: str, url: str) -> list[dict]:
    """Fetch one RSS/Atom feed and return a list of article dicts."""
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
        print(f"  [WARN] {name}: XML parse error — {exc}", file=sys.stderr)
        return []

    articles = []

    # Detect Atom vs RSS
    is_atom = root.tag in (
        "feed",
        "{http://www.w3.org/2005/Atom}feed",
    )

    if is_atom:
        entries = root.findall("{http://www.w3.org/2005/Atom}entry")
        for entry in entries:
            title   = _text(entry, "{http://www.w3.org/2005/Atom}title")
            link_el = entry.find("{http://www.w3.org/2005/Atom}link")
            link    = link_el.get("href", "") if link_el is not None else ""
            date    = _parse_date(_text(entry, "{http://www.w3.org/2005/Atom}updated") or
                                  _text(entry, "{http://www.w3.org/2005/Atom}published"))
            articles.append({"source": name, "title": title, "link": link, "date": date})
    else:
        # RSS 2.0 — items may be in <channel>
        channel = root.find("channel") or root
        for item in channel.findall("item"):
            title = _text(item, "title")
            link  = _text(item, "link")
            date  = _parse_date(_text(item, "pubDate"))
            articles.append({"source": name, "title": title, "link": link, "date": date})

    return articles


def fetch_all_feeds() -> list[dict]:
    """Fetch all feeds concurrently and return combined article list."""
    all_articles: list[dict] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(fetch_feed, name, url): name for name, url in FEEDS}
        for future in as_completed(futures):
            all_articles.extend(future.result())
    return all_articles


# ---------------------------------------------------------------------------
# Filtering & formatting
# ---------------------------------------------------------------------------

def filter_recent(articles: list[dict], hours: int = LOOKBACK_HOURS) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent = [a for a in articles if a["date"] and a["date"] >= cutoff]
    # Articles without a parseable date are included with a sentinel so they
    # appear at the bottom rather than being silently dropped.
    undated = [a for a in articles if not a["date"]]
    return sorted(recent, key=lambda a: a["date"], reverse=True) + undated


def build_digest(articles: list[dict]) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"Daily Cybersecurity Digest — {today}",
        "=" * 60,
        f"{len(articles)} article(s) in the last {LOOKBACK_HOURS} hours",
        "",
    ]

    current_source = None
    for a in articles:
        if a["source"] != current_source:
            current_source = a["source"]
            lines += ["", f"[ {current_source} ]", "-" * 40]
        date_str = a["date"].strftime("%Y-%m-%d %H:%M UTC") if a["date"] else "unknown date"
        lines += [
            f"  {a['title']}",
            f"  {date_str}",
            f"  {a['link']}",
            "",
        ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Optional email delivery
# ---------------------------------------------------------------------------

def send_email(subject: str, body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_FROM
    msg["To"]      = EMAIL_TO
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("Fetching feeds...", file=sys.stderr)
    articles = fetch_all_feeds()
    print(f"Fetched {len(articles)} total articles.", file=sys.stderr)

    recent = filter_recent(articles)
    digest = build_digest(recent)

    print(digest)

    if all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO]):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        send_email(f"Daily Cybersecurity Digest — {today}", digest)
        print("Digest emailed.", file=sys.stderr)


if __name__ == "__main__":
    main()
