#!/usr/bin/env python3
"""
Cyber Competitive Daily Feed
Fetches cybersecurity RSS feeds concurrently, saves an HTML report to GitHub Pages.
Email notification is handled by GitHub Actions (.github/workflows/notify.yml).
"""

import difflib
import email.utils
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import subprocess
import json as json_lib
from html.parser import HTMLParser
from textwrap import shorten

FEEDS = [
    # ── General security news ────────────────────────────────────────────
    ("Krebs on Security",       "https://krebsonsecurity.com/feed/"),
    ("The Hacker News",         "https://feeds.feedburner.com/TheHackersNews"),
    ("Bleeping Computer",       "https://www.bleepingcomputer.com/feed/"),
    ("SANS ISC",                "https://isc.sans.edu/rssfeed_full.xml"),
    ("SecurityWeek",            "https://feeds.feedburner.com/securityweek"),
    ("Dark Reading",            "https://www.darkreading.com/rss.xml"),
    ("Schneier on Security",    "https://www.schneier.com/feed/atom/"),
    ("ThreatPost",              "https://threatpost.com/feed/"),
    ("Wired Security",          "https://www.wired.com/feed/category/security/latest/rss"),
    ("Ars Technica Security", "https://arstechnica.com/tag/security/feed/"),
    ("Troy Hunt",               "https://feeds.feedburner.com/TroyHunt"),
    ("Infosecurity Magazine",   "https://www.infosecurity-magazine.com/rss/news/"),
    ("Help Net Security",       "https://www.helpnetsecurity.com/feed/"),
    ("SC Magazine",             "https://www.scmagazine.com/feed"),
    ("Graham Cluley",           "https://grahamcluley.com/feed/"),
    ("The CyberWire",           "https://thecyberwire.com/feeds/rss.xml"),
    # ── Government / advisories ──────────────────────────────────────────
    ("CISA Advisories", "https://www.cisa.gov/cybersecurity-advisories/all.xml"),
    ("NCSC UK",                 "https://www.ncsc.gov.uk/api/1/services/v1/report-rss-feed.xml"),
    ("CIRCL KEV (exploited CVEs)", "https://vulnerability.circl.lu/known-exploited-vulnerabilities.rss"),
    ("Australian ACSC",         "https://www.cyber.gov.au/rss.xml"),
    # ── Threat intelligence ──────────────────────────────────────────────
    ("Talos Intelligence",      "https://blog.talosintelligence.com/rss/"),
    ("Google Project Zero",     "https://googleprojectzero.blogspot.com/feeds/posts/default"),
    ("Exploit-DB",              "https://www.exploit-db.com/rss.xml"),
    ("Google Threat Intel (Mandiant)", "https://cloudblog.withgoogle.com/topics/threat-intelligence/rss/"),
    ("Recorded Future",         "https://www.recordedfuture.com/feed"),
    ("Check Point Research",    "https://research.checkpoint.com/feed/"),
    ("Cyble",                   "https://cyble.com/blog/feed/"),
    ("VirusTotal Blog",         "https://blog.virustotal.com/feeds/posts/default"),
    # ── Vendor blogs ─────────────────────────────────────────────────────
    ("Trend Micro Research", "https://feeds.feedburner.com/TrendMicroResearch"),
    ("CrowdStrike Blog",        "https://www.crowdstrike.com/blog/feed/"),
    ("Palo Alto Unit 42",       "https://unit42.paloaltonetworks.com/feed/"),
    ("Fortinet Threat Research","https://feeds.fortinet.com/fortinet/blog/threat-research"),
    ("Microsoft Security Blog", "https://www.microsoft.com/en-us/security/blog/feed/"),
    ("SentinelOne Blog",        "https://www.sentinelone.com/blog/feed/"),
    ("Rapid7 Blog",             "https://blog.rapid7.com/rss/"),
    ("Tenable Blog",            "https://www.tenable.com/blog/feed"),
    ("Qualys Blog",             "https://blog.qualys.com/feed"),
    ("Zscaler ThreatLabz", "https://www.zscaler.com/blogs/feeds/security-research"),
    ("Kaspersky Blog",          "https://www.kaspersky.com/blog/feed/"),
    ("Securelist (Kaspersky)",  "https://securelist.com/feed/"),
    ("Sophos News - Threat Research", "https://news.sophos.com/en-us/category/threat-research/feed/"),
    ("Sophos News - SecOps",    "https://news.sophos.com/en-us/category/security-operations/feed/"),
    ("ESET WeLiveSecurity",     "https://feeds.feedburner.com/eset/blog"),
    ("SentinelLabs",            "https://www.sentinelone.com/labs/feed/"),
    ("Check Point Blog",        "https://blog.checkpoint.com/feed/"),
    ("Bitdefender Business Insights", "https://businessinsights.bitdefender.com/rss.xml"),
    ("Trend Micro SimplySecurity", "https://feeds.feedburner.com/TrendMicroSimplySecurity"),
    ("CrowdStrike IR News",     "https://ir.crowdstrike.com/rss/news-releases.xml"),
    ("Fortinet IR News",        "https://investor.fortinet.com/rss/news-releases.xml"),
    ("Palo Alto IR News",       "https://investors.paloaltonetworks.com/rss/news-releases.xml"),
    ("Qualys IR News",          "https://investor.qualys.com/rss/news-releases.xml"),
    ("Cybereason Blog",         "https://www.cybereason.com/blog/rss.xml"),
    ("Falco / Sysdig Blog", "https://sysdig.com/feed/"),
    ("Wiz Blog",                "https://www.wiz.io/feed/rss.xml"),
    ("Orca Security Blog",      "https://orca.security/resources/blog/feed/"),
    ("Darktrace Blog", "https://www.darktrace.com/blog/rss.xml"),
    ("Vectra AI Blog", "https://www.vectra.ai/blog/rss.xml"),
    ("Proofpoint Blog",         "https://www.proofpoint.com/us/rss.xml"),
    ("Broadcom/Symantec Blog",  "https://symantec-enterprise-blogs.security.com/blogs/rss/v1/blogs/rss.xml/221"),
    ("The Register Security",   "https://www.theregister.com/security/headlines.atom"),
    ("Databreaches.net",        "https://www.databreaches.net/feed/"),
    ("This Week in 4n6",        "https://thisweekin4n6.com/feed/atom/"),
    ("Okta Blog", "https://sec.okta.com/rss.xml"),
    ("CyberArk Blog", "https://www.cyberark.com/feed/"),
    ("Elastic Security Labs",   "https://www.elastic.co/security-labs/rss/feed.xml"),
    ("Rubrik Blog",             "https://www.rubrik.com/blog/feed/"),
    ("Arctic Wolf Blog",        "https://arcticwolf.com/resources/category/blog/feed/"),
    ("Huntress Blog",           "https://www.huntress.com/blog/rss.xml"),
    ("Aqua Security Blog", "https://www.aquasec.com/feed/"),
    ("Snyk Blog",               "https://snyk.io/blog/feed/"),
    ("BeyondTrust Blog",        "https://www.beyondtrust.com/blog/rss.xml"),
    ("Delinea Blog",            "https://delinea.com/blog/rss.xml"),
    ("Netskope Blog",           "https://www.netskope.com/blog/feed"),
    ("Claroty Blog",            "https://claroty.com/team82/blog/feed"),
]

FETCH_TIMEOUT  = 10
MAX_WORKERS    = len(FEEDS)
LOOKBACK_HOURS = 720   # front-page window (30 days); older history is preserved in the archives

REPORT_FILE  = "index.html"
REPORT_URL   = "https://lukan47.github.io/RSS/"
ARCHIVE_DIR  = "archive"
EXPORT_DIR   = os.path.join(ARCHIVE_DIR, "exports")
DATA_DIR           = os.path.join(ARCHIVE_DIR, "data")
ARTICLES_FILE      = os.path.join(DATA_DIR, "articles.json")
FULLTEXT_DIR       = os.path.join(DATA_DIR, "fulltext")
EXPLORER_FILE      = os.path.join(DATA_DIR, "explorer.html")
EXPLORER_TEMPLATE  = "explorer_template.html"
EXPLORER_URL       = REPORT_URL + "archive/data/explorer.html"
LEGACY_FULLTEXT_CACHE = os.path.join(ARCHIVE_DIR, "_cache", "fulltext_cache.json")
FULLTEXT_BUDGET_S  = int(os.environ.get("FULLTEXT_BUDGET_S", "420"))  # stop starting new downloads after this many seconds
FULLTEXT_WORKERS   = 12
FULLTEXT_MAX_ATTEMPTS = 3
FULLTEXT_MAX_CHARS = 60000
FEED_FULLTEXT_MIN  = 1500     # a feed body this long is treated as the whole article
MIN_FULLTEXT_CHARS = 200
CSV_CELL_LIMIT     = 32000    # Excel cannot hold more than 32,767 characters per cell
HISTORY_FILE = "history.json"
MAX_HISTORY  = 30
PHT          = timezone(timedelta(hours=8))

# Priority order: first match wins — Zero-Day > Acquisitions > Companies > General
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
        "merger", "merges with", "has merged",
        "bought", "buys", "purchase of", "to purchase", "asset purchase", "deal worth",
        "hostile takeover", "corporate takeover",
        "investment round", "investor", "investing in",
        "funding round", "series a", "series b", "series c",
        "valuation", "ipo", "spin-off", "divest",
    ],
    "Trend Micro": [
        "trend micro", "trendmicro", "trendai", "trend ai",
    ],
    "CrowdStrike": [
        "crowdstrike", "falcon sensor", "falcon platform", "falcon next-gen",
    ],
    "Palo Alto Networks": [
        "palo alto", "palo alto networks", "unit 42", "cortex xdr",
        "cortex xsiam", "prisma cloud", "prisma access",
    ],
    "Fortinet": [
        "fortinet", "fortigate", "fortios", "forticlient",
        "fortisiem", "fortiedr", "fortisoar",
    ],
    "SentinelOne": [
        "sentinelone", "sentinel one", "singularity platform", "sentinellabs", "sentinel labs",
    ],
    "Microsoft Security": [
        "microsoft security", "microsoft defender", "azure security",
        "microsoft entra", "microsoft sentinel", "defender for endpoint",
        "defender for cloud",
    ],
    "Mandiant": [
        "mandiant",
    ],
    "Sophos": [
        "sophos", "naked security",
    ],
    "ESET": [
        "eset", "welivesecurity", "we live security", "nod32",
    ],
    "Bitdefender": [
        "bitdefender", "gravityzone",
    ],
    "Check Point": [
        "check point", "checkpoint", "harmony endpoint",
    ],
    "Recorded Future": [
        "recorded future",
    ],
    "Cisco Security": [
        "cisco talos", "cisco security", "cisco umbrella",
        "cisco secure", "cisco xdr",
    ],
    "Wiz": [
        "wiz.io", "wiz security", "wiz cloud",
    ],
    "Orca Security": [
        "orca security", "orca.security",
    ],
    "Trellix": [
        "trellix", "fireeye", "mcafee enterprise",
    ],
    "Darktrace": [
        "darktrace", "autonomous response",
    ],
    "ExtraHop": [
        "extrahop", "extra hop", "reveal(x)",
    ],
    "Vectra AI": [
        "vectra ai", "vectra.ai", "vectra attack",
    ],
    "Proofpoint": [
        "proofpoint", "proofpoint threat",
    ],
    "Broadcom / Symantec": [
        "broadcom security", "symantec enterprise", "symantec endpoint",
        "carbon black",
    ],
    "Kaspersky": [
        "kaspersky", "securelist", "kaspersky lab",
    ],
    "Cybereason": [
        "cybereason", "malicious life",
    ],
    "Barracuda": [
        "barracuda", "barracuda networks",
    ],
    "Falco / Sysdig": [
        "falco", "sysdig", "falcosecurity",
    ],
    "Okta": [
        "okta", "okta identity", "okta workforce",
    ],
    "CyberArk": [
        "cyberark", "privileged access", "conjur",
    ],
    "IBM Security": [
        "ibm security", "qradar", "ibm x-force", "security intelligence",
    ],
    "Elastic Security": [
        "elastic security", "elastic siem", "elastic endpoint",
    ],
    "Rubrik": [
        "rubrik", "rubrik security cloud",
    ],
    "Arctic Wolf": [
        "arctic wolf", "arcticwolf",
    ],
    "Abnormal Security": [
        "abnormal security", "abnormalsecurity",
    ],
    "Huntress": [
        "huntress",
    ],
    "Lacework": [
        "lacework",
    ],
    "Aqua Security": [
        "aqua security", "aquasec", "trivy",
    ],
    "Snyk": [
        "snyk",
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
    "WithSecure": [
        "withsecure", "with secure", "f-secure", "fsecure",
    ],
    "Secureworks": [
        "secureworks", "secureworks taegis", "counter threat unit", "ctu threat",
    ],
    "Blackberry / Cylance": [
        "blackberry cylance", "cylanceprotect", "cylance", "blackberry security",
        "blackberry threat",
    ],
    "BeyondTrust": [
        "beyondtrust", "beyond trust", "privileged remote access",
    ],
    "Delinea": [
        "delinea", "thycotic", "centrify",
    ],
    "Netskope": [
        "netskope", "netskope threat",
    ],
    "Cato Networks": [
        "cato networks", "cato sase", "cato cloud",
    ],
    "Dragos": [
        "dragos", "dragos ics", "dragos ot",
    ],
    "Claroty": [
        "claroty", "team82", "claroty research",
    ],
}

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

# Explicit fallback formats (steps 1–2 in _parse_date cover most feeds; this
# list is a safety net for odd variants — no-seconds, fractional seconds, bare).
DATE_FORMATS = [
    "%a, %d %b %Y %H:%M:%S %z",
    "%a, %d %b %Y %H:%M:%S GMT",
    "%a, %d %b %Y %H:%M %z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
]


def _parse_date(text: str) -> datetime | None:
    """Parse a feed date string, returning a tz-aware datetime (UTC default).

    Real-world feeds vary widely, so try robust stdlib parsers first:
      1. email.utils — RFC 2822 RSS <pubDate>, incl. zone names (GMT/UTC/EST…)
      2. datetime.fromisoformat — ISO 8601 / Atom, incl. fractional seconds,
         numeric offsets, and trailing 'Z' (Python 3.11+)
      3. the explicit DATE_FORMATS list as a final fallback
    """
    if not text:
        return None
    text = text.strip()

    # 1) RFC 2822 (RSS pubDate) — handles numeric offsets and zone names.
    try:
        dt = email.utils.parsedate_to_datetime(text)
        if dt is not None:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        pass

    # 2) ISO 8601 / Atom — fractional seconds, offsets, trailing 'Z'.
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00") if text.endswith("Z") else text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        pass

    # 3) Explicit fallback formats.
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(text, fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _text(element, tag: str) -> str:
    child = element.find(tag)
    return html.unescape(child.text.strip()) if child is not None and child.text else ""


def _raw_text(element, tags) -> str:
    """First non-empty raw (still HTML-escaped-free) text among the given child tags."""
    for tag in tags:
        child = element.find(tag)
        if child is not None and child.text and child.text.strip():
            return child.text
    return ""

# ---------------------------------------------------------------------------
# Feed fetching
# ---------------------------------------------------------------------------

def fetch_feed(name: str, url: str) -> list[dict]:
    try:
        req = Request(url, headers={"User-Agent": "CyberCompetitiveDailyFeed/1.0"})
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
            article = {
                "source": name,
                "title": title,
                "link": link,
                "date": date,
                "context": "",
                "feed_text": _fragment_to_text(_raw_text(entry, (
                    "{http://www.w3.org/2005/Atom}content",
                    "{http://www.w3.org/2005/Atom}summary"))),
            }
            articles.append(article)
    else:
        channel = root.find("channel")
        if channel is None:
            channel = root
        for item in channel.findall("item"):
            article = {
                "source": name,
                "title": _text(item, "title"),
                "link":  _text(item, "link"),
                "date":  _parse_date(
                    _text(item, "pubDate") or
                    _text(item, "{http://purl.org/dc/elements/1.1/}date")
                ),
                "context": "",
                "feed_text": _fragment_to_text(_raw_text(item, (
                    "{http://purl.org/rss/1.0/modules/content/}encoded",
                    "description"))),
            }
            articles.append(article)

    return articles


def fetch_all_feeds() -> list[dict]:
    all_articles: list[dict] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(fetch_feed, name, url): name for name, url in FEEDS}
        for future in as_completed(futures):
            all_articles.extend(future.result())
    return all_articles


_SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "header", "footer",
              "aside", "form", "iframe", "button", "figcaption", "template"}
_FLUSH_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre",
               "td", "th", "tr", "div", "section", "article", "main", "ul", "ol", "table"}
_CONTAINER_TAGS = {"div", "section", "article", "main", "td", "body"}
_VOID_TAGS = {"br", "img", "hr", "input", "meta", "link", "source", "wbr", "area", "base", "col", "embed", "param", "track"}
EXTRACT_VERSION = 2


class _ArticleExtractor(HTMLParser):
    """Collect text blocks tagged with their enclosing container, then keep the densest one.

    Pages rarely mark up the article cleanly, and sidebars, promos and related-story
    lists sit beside it. The container holding the most paragraph text is the article.
    """
    def __init__(self, skip_tags=_SKIP_TAGS):
        super().__init__()
        self.skip_tags = skip_tags
        self.skip_depth = 0
        self.zone_depth = {"article": 0, "main": 0}
        self.buf = []
        self.blocks = []        # (zone, container_id, text); zone 2 = article, 1 = main, 0 = other
        self.cstack = [0]       # open container ids, innermost last
        self.parent = {0: None}
        self.next_id = 1

    def _flush(self):
        text = " ".join("".join(self.buf).split())
        self.buf = []
        if text:
            zone = 2 if self.zone_depth["article"] else 1 if self.zone_depth["main"] else 0
            if not self.blocks or self.blocks[-1][2] != text:
                self.blocks.append((zone, self.cstack[-1], text))

    def handle_starttag(self, tag, attrs):
        if tag in _FLUSH_TAGS:
            self._flush()
        if tag in _VOID_TAGS:
            return
        if tag in self.skip_tags:
            self.skip_depth += 1
        elif tag in self.zone_depth:
            self.zone_depth[tag] += 1
        if tag in _CONTAINER_TAGS:
            cid = self.next_id
            self.next_id += 1
            self.parent[cid] = self.cstack[-1]
            self.cstack.append(cid)

    def handle_endtag(self, tag):
        if tag in _FLUSH_TAGS:
            self._flush()
        if tag in self.skip_tags:
            self.skip_depth = max(0, self.skip_depth - 1)
        elif tag in self.zone_depth:
            self.zone_depth[tag] = max(0, self.zone_depth[tag] - 1)
        if tag in _CONTAINER_TAGS and len(self.cstack) > 1:
            self.cstack.pop()

    def handle_data(self, data):
        if not self.skip_depth:
            self.buf.append(data)

    def _densest(self, blocks):
        """Blocks inside the container (and its descendants) with the most direct text."""
        direct = {}
        for _, cid, text in blocks:
            direct[cid] = direct.get(cid, 0) + len(text)
        best = max(direct, key=direct.get)

        def inside(cid):
            while cid is not None:
                if cid == best:
                    return True
                cid = self.parent.get(cid)
            return False
        return [t for _, cid, t in blocks if inside(cid)]

    def get_text(self) -> str:
        self._flush()
        for min_zone in (2, 1, 0):
            pool = [b for b in self.blocks if b[0] >= min_zone]
            if not pool:
                continue
            chosen = self._densest(pool)
            if sum(len(t) for t in chosen) >= 300:
                return "\n\n".join(chosen)
        return "\n\n".join(t for _, _, t in self.blocks if len(t) >= 30)

    def get_all_text(self) -> str:
        self._flush()
        return "\n\n".join(t for _, _, t in self.blocks)


def _html_to_text(html_content: str) -> str:
    parser = _ArticleExtractor()
    parser.feed(html_content)
    text = parser.get_text()
    if len(text) < MIN_FULLTEXT_CHARS:
        # Unbalanced markup can leave a skip tag open; retry skipping only scripts/styles.
        parser = _ArticleExtractor(skip_tags={"script", "style", "noscript", "svg", "template"})
        parser.feed(html_content)
        text = parser.get_text()
    return text


def _fragment_to_text(html_fragment: str) -> str:
    """Plain text of an HTML fragment (e.g. a feed item's content:encoded)."""
    parser = _ArticleExtractor(skip_tags={"script", "style"})
    parser.feed(html_fragment)
    return parser.get_all_text()


_TRAILER_RX = re.compile(
    r"^(related( stories| articles| posts| reading)?\s*:|read more\s*:|found this article interesting|follow us on|"
    r"share this|subscribe|join our newsletter|sign up for|you may also like|more from)", re.I)


def _trim_trailer(text: str) -> str:
    """Drop trailing share-button labels, 'Related:' links and follow/subscribe prompts."""
    blocks = text.split("\n\n")
    while len(blocks) > 1:
        last = blocks[-1].strip()
        short = len(last) < 30 and not last.endswith((".", "!", "?", "\u201d", '"'))
        if short or _TRAILER_RX.match(last):
            blocks.pop()
        else:
            break
    return "\n\n".join(blocks)


def fetch_full_text(url: str, timeout: int = 15) -> str:
    """Download an article page and return its body text, or '' on failure."""
    from urllib.parse import quote
    try:
        url = quote(url, safe=":/?&=%#+@,;~!*()'[]$")
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        with urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            raw = resp.read(3_000_000)
        text = _html_to_text(raw.decode(charset, errors="replace"))
        return text[:FULLTEXT_MAX_CHARS] if len(text) >= MIN_FULLTEXT_CHARS else ""
    except Exception as e:
        print(f"  [DEBUG] Failed to fetch {url}: {e}", file=sys.stderr)
        return ""


def _month_key(date_iso) -> str:
    return date_iso[:7] if date_iso else "undated"


def load_fulltext_cache() -> dict:
    """Merge every monthly shard (plus the legacy single-file cache) into {link: entry}."""
    cache: dict = {}
    paths = []
    if os.path.isdir(FULLTEXT_DIR):
        paths += [os.path.join(FULLTEXT_DIR, f) for f in sorted(os.listdir(FULLTEXT_DIR)) if f.endswith(".json")]
    if os.path.exists(LEGACY_FULLTEXT_CACHE):
        paths.append(LEGACY_FULLTEXT_CACHE)
    for path in paths:
        try:
            with open(path, encoding="utf-8") as f:
                cache.update(json.load(f))
        except (OSError, ValueError):
            continue
    return cache


def save_fulltext_cache(cache: dict, months: dict) -> None:
    """Write {link: entry} back as one file per month; months maps link -> 'YYYY-MM'."""
    shards: dict = {}
    for link, entry in cache.items():
        if link in months:
            shards.setdefault(months[link], {})[link] = entry
    os.makedirs(FULLTEXT_DIR, exist_ok=True)
    for month, entries in shards.items():
        with open(os.path.join(FULLTEXT_DIR, month + ".json"), "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False)
    if os.path.exists(LEGACY_FULLTEXT_CACHE):
        os.remove(LEGACY_FULLTEXT_CACHE)


def _is_stale(entry: dict) -> bool:
    return entry.get("source") == "page" and entry.get("v", 1) < EXTRACT_VERSION


def attach_full_text(articles: list[dict]) -> int:
    """Set article['full_text'], reusing the on-disk cache and fetching what is missing.

    Order of preference: a long body already in the feed item, then the article page,
    then a short feed body as a last resort. Newest articles go first within a time
    budget; failures are retried on later runs up to FULLTEXT_MAX_ATTEMPTS.
    Returns the number of texts obtained this run.
    """
    import time
    cache = load_fulltext_cache()
    pending = [
        a for a in articles
        if a.get("link")
        and cache.get(a["link"], {}).get("attempts", 0) < FULLTEXT_MAX_ATTEMPTS
        and (not cache.get(a["link"], {}).get("text") or _is_stale(cache[a["link"]]))
    ]
    deadline = time.monotonic() + FULLTEXT_BUDGET_S

    def work(article):
        feed_text = article.get("feed_text", "")
        if len(feed_text) >= FEED_FULLTEXT_MIN:
            return article["link"], feed_text[:FULLTEXT_MAX_CHARS], "feed"
        if time.monotonic() > deadline:
            return article["link"], None, ""
        page_text = fetch_full_text(article["link"])
        if page_text:
            return article["link"], page_text, "page"
        if len(feed_text) >= MIN_FULLTEXT_CHARS:
            return article["link"], feed_text[:FULLTEXT_MAX_CHARS], "feed-excerpt"
        return article["link"], "", ""

    obtained = 0
    if pending:
        print(f"  Collecting full text for {len(pending)} article(s)...", file=sys.stderr)
        with ThreadPoolExecutor(max_workers=FULLTEXT_WORKERS) as pool:
            for link, text, source in pool.map(work, pending):
                if text is None:
                    continue
                entry = cache.setdefault(link, {"text": "", "attempts": 0})
                entry["attempts"] = entry.get("attempts", 0) + 1
                if text:
                    entry["text"] = text
                    entry["v"] = EXTRACT_VERSION
                    entry["source"] = source
                    entry["fetched"] = datetime.now(timezone.utc).isoformat()
                    obtained += 1

    months = {a["link"]: _month_key(a.get("date")) for a in articles if a.get("link")}
    save_fulltext_cache(cache, months)

    for a in articles:
        a["full_text"] = _trim_trailer(cache.get(a.get("link", ""), {}).get("text", ""))
        a.pop("feed_text", None)
    return obtained


def _extract_key_sentence(text: str, title: str = "") -> str:
    """Extract a key sentence from article text containing important context.

    Looks for sentences with keywords related to security findings, partnerships,
    or significant announcements. Returns a truncated sentence (up to 180 chars).
    """
    if not text:
        return ""

    # Keywords that indicate important context
    keywords = {
        "announced", "partnership", "acquired", "released", "vulnerability",
        "discovered", "found", "exploit", "threat", "malware", "attack",
        "detection", "capability", "feature", "certification", "award",
        "collaboration", "integration", "supported", "available", "launch",
        "first", "only", "breakthrough", "critical", "severe", "zero-day"
    }

    # Split into sentences
    sentences = re.split(r'[.!?]+', text)

    # Score sentences by keyword presence and length
    scored = []
    for sent in sentences:
        sent_clean = sent.strip()
        if len(sent_clean) < 20 or len(sent_clean) > 300:
            continue

        # Count keyword matches
        score = sum(1 for kw in keywords if kw.lower() in sent_clean.lower())
        if score > 0:
            scored.append((score, sent_clean))

    if scored:
        # Return highest-scoring sentence, truncated
        best = max(scored, key=lambda x: x[0])[1]
        return shorten(best, width=180, placeholder="...")

    # Fallback: return first meaningful sentence
    for sent in sentences:
        sent_clean = sent.strip()
        if len(sent_clean) > 30:
            return shorten(sent_clean, width=180, placeholder="...")

    return ""


def extract_context(article: dict) -> str:
    """Short dashboard snippet: the most informative sentence of the article's full text."""
    text = " ".join(article.get("full_text", "").split())[:20000]
    if len(text) < 100:
        return ""
    return _extract_key_sentence(text, article.get("title", "")) or ""

# ---------------------------------------------------------------------------
# Module classification (rule based, no AI). An article can belong to several modules.
# ---------------------------------------------------------------------------

MODULE_OTHER = "Other/General"
MODULE_NA = "N/A"
MODULE_TYPES = [
    "AI Security", "Attack Path Prediction", "Attack Surface Discovery", "Cloud IPS",
    "Cloud Risk Management", "Cloud Security Posture Management", "Code Security",
    "Compliance Management", "Container Security", "Cyber Risk Quantification",
    "Data Security Posture Management", "Email and Collaboration Security", "Endpoint Security",
    "File Security", "Identity Security Posture Management", "Mobile Security", "Network Security",
    "Phishing Simulations", "Server & Workload Protection", "Threat Intelligence",
    "Threat and Exposure Management", "Vulnerability Management", "Zero Trust Secure Access",
    MODULE_OTHER, MODULE_NA,
]
MODULE_MIN_SCORE = 3      # a strong term in the title qualifies alone; body hits must add up
MODULE_MAX_PER_ARTICLE = 4
MODULE_BODY_CHARS = 4000  # only the start of the article body is scored

# strong = specific to the module; weak = common words that only corroborate.
_MODULE_RULES = {
    "AI Security": (
        r"\bai (agents?|security|models?|assistants?|supply chain|chatbots?|governance|systems?)\b|prompt injection|\bllms?\b|large language model|"
        r"generative ai|\bgenai\b|copilot|chatgpt|openai|anthropic|\bclaude\b|\bgemini\b|\bmcp\b|agentic|jailbreak|shadow ai|"
        r"model (poisoning|theft|extraction)|ai-(powered|driven|generated|assisted) (attack|malware|phishing|exploit)",
        r"\bai\b|machine learning|neural|deepfake"),
    "Attack Path Prediction": (
        r"attack[- ]paths?|blast radius|crown jewels|choke ?points?|toxic combination",
        r"lateral movement|privilege escalation path"),
    "Attack Surface Discovery": (
        r"attack surface|\basm\b|external exposure|shadow it|exposed (assets|services|instances|servers|devices|endpoints)|"
        r"internet[- ](facing|exposed)|\bshodan\b|\bcensys\b|asset discovery|asset inventory",
        r"publicly (accessible|exposed)|exposed to the internet"),
    "Cloud IPS": (
        r"intrusion prevention|\bips\b|virtual patching|cloud ips|network ips",
        r"\bids\b|signature"),
    "Cloud Risk Management": (
        r"\bcnapp\b|cloud risk|cloud-native application protection|cloud security|cloud (breach|exposure|attack|compromise)|cloud-native",
        r"\b(aws|azure|gcp|google cloud|cloud)\b"),
    "Cloud Security Posture Management": (
        r"\bcspm\b|cloud (security )?posture|cloud misconfigur|misconfigured (cloud|s3|bucket|blob|storage)|public (s3|bucket|blob)|"
        r"overly permissive (iam|role|polic)|\bs3 buckets?\b|\bciem\b",
        r"misconfigur|\biam\b"),
    "Code Security": (
        r"supply[- ]chain (attack|compromise|risk|security)|software supply|malicious (npm|pypi|package|extension|library|gem|crate)|"
        r"\bnpm\b|\bpypi\b|rubygems|\bmaven\b|github actions?|\bsast\b|\bdast\b|\bsca\b|open[- ]source (package|library|component|dependenc)|"
        r"ci/cd|vs ?code extension|code signing|secrets? (leak|in code|scanning)|source code|devsecops|\bsbom\b|dependency confusion|typosquat",
        r"github|gitlab|developers?|repository|\bpackages?\b"),
    "Compliance Management": (
        r"compliance|\bgdpr\b|\bhipaa\b|pci[- ]dss|\bnis2\b|\bdora\b|\bsox\b|iso ?27001|soc ?2\b|\bcmmc\b|regulator|regulation|"
        r"\bfined?\b|privacy law|data protection (law|act|authority)|security audit|\bnist\b",
        r"audit|policy|legislation"),
    "Container Security": (
        r"kubernetes|\bk8s\b|\bdocker\b|helm chart|container (image|registry|escape|runtime|security|vulnerab)|\brunc\b|containerd|"
        r"\b(eks|aks|gke)\b|pod security|\bcontainers\b|aqua ?sec|\bfalco\b|\bsysdig\b",
        r"\bpods?\b|orchestrat|cluster"),
    "Cyber Risk Quantification": (
        r"risk quantification|cyber[- ]risk (score|rating|quantification|management)|cyber insurance|risk (score|rating)s?|value at risk|"
        r"financial (impact|loss|exposure) of (a )?(cyber|breach|attack)|\bcrq\b",
        r"insurers?|underwrit|risk assessment"),
    "Data Security Posture Management": (
        r"\bdspm\b|data security posture|sensitive data|data (loss|leak|leakage|exposure|breach|theft|exfiltration)|\bdlp\b|data classification|"
        r"exposed (database|records|data)|records (exposed|leaked|stolen|compromised)|personal (data|information)|\bpii\b|health records|"
        r"(customers?|patients?|users?|employees?) (data|records|information)|exfiltrat",
        r"\bdata\b|breach|\bleak"),
    "Email and Collaboration Security": (
        r"email security|\bphishing\b|business email compromise|\bbec\b|spear-?phish|quishing|smishing|vishing|mailbox|microsoft teams|"
        r"\bslack\b|\bspam\b|exchange online|microsoft 365|\bm365\b|office 365|collaboration (app|platform|tool)|\bzoom\b|email (attachment|gateway|campaign)",
        r"\bemails?\b|\binbox\b|\bsms\b"),
    "Endpoint Security": (
        r"endpoint|\bedr\b|\bxdr\b|antivirus|anti-virus|ransomware|malware|infostealer|info-stealer|stealer|trojan|backdoor|\bwiper\b|"
        r"rootkit|\bloader\b|\brat\b|keylogger|cryptominer|crypto-?mining|windows (defender|update)|macos|linux malware|botnet",
        r"\bwindows\b|\blinux\b|\bmalicious\b|laptop|workstation"),
    "File Security": (
        r"malicious (file|document|attachment|archive|pdf|doc)|file (upload|scanning|security|sharing)|sandbox|office (document|macro)|"
        r"\.lnk\b|disk image|weaponi[sz]ed (pdf|document|file)|\bwebshell|web shell|zip (file|archive)|macro-enabled",
        r"\bfiles?\b|attachment|document"),
    "Identity Security Posture Management": (
        r"identity|\bispm\b|active directory|\bentra\b|\bokta\b|\bsso\b|\bmfa\b|multi-?factor|passkeys?|credential (theft|stuffing|harvest|dump)|"
        r"stolen credentials|\bpasswords?\b|\boauth\b|token theft|session (hijack|token|cookie)|privileged access|service accounts?|\bpam\b|"
        r"account takeover|\bato\b|authentication bypass|single sign-on|\bsaml\b|\bkerberos\b",
        r"\bcredentials?\b|\blogin\b|\baccounts?\b|authenticat"),
    "Mobile Security": (
        r"\bandroid\b|(?<!cisco )\bios\b(?! ?x[er])|\biphone\b|\bipad\b|mobile (app|apps|device|devices|malware|security|phone|banking)|\bapk\b|"
        r"app store|google play|\bmdm\b|sim[- ]swap|\bspyware\b|pegasus|telegram",
        r"\bmobile\b|smartphone|\bapps?\b"),
    "Network Security": (
        r"firewall|\bvpn\b|sd-wan|\brouters?\b|network (security|detection|traffic|device|appliance|perimeter)|\bndr\b|\bddos\b|fortigate|"
        r"fortios|pan-os|globalprotect|ivanti connect|edge devices?|snmp|wi-?fi|\bswitch(es)?\b|load balancer|netscaler|\bwaf\b|cisco (asa|ftd|ios)|"
        r"packet|\bbgp\b",
        r"\bnetwork\b|\bdns\b|\btraffic\b|gateway|perimeter"),
    "Phishing Simulations": (
        r"phishing simulation|simulated phishing|security awareness (training|program)|awareness training|knowbe4|phish(ing)? (test|testing|drill)|"
        r"human risk|cyber ?security awareness",
        r"awareness|training|employees"),
    "Server & Workload Protection": (
        r"\bworkloads?\b|vmware|\besxi\b|hypervisor|vcenter|\brdp\b|\bssh\b|exchange server|\bcitrix\b|mainframe|virtual machines?|"
        r"(linux|windows|web|application|database|mail|file) servers?|server (compromise|breach|vulnerab)|\bnginx\b|\bapache\b|\bsap\b|\bwebsphere\b",
        r"\bservers?\b|\bhosts?\b|\bvms?\b|datacenter|data center"),
    "Threat Intelligence": (
        r"threat actors?|threat intelligence|threat (group|report|research|landscape|hunting)|\bapt ?\d*\b|nation[- ]state|state[- ]sponsored|"
        r"lazarus|fancy bear|\bttps?\b|indicators of compromise|\biocs?\b|mandiant|unit ?42|\btalos\b|threat campaign|hacking (group|campaign)|"
        r"ransomware (gang|group)|cybercrim(e|inal) (group|gang)|dark ?web|initial access broker",
        r"campaigns?|attributed|actors?|\bgroup\b"),
    "Threat and Exposure Management": (
        r"exposure management|\bctem\b|threat exposure|continuous threat exposure|risk-based (vulnerability|prioriti)|exposure (validation|assessment)|"
        r"prioriti[sz](e|ing|ation) (risk|vulnerab|remediation)|security posture|exposure score",
        r"\bexposures?\b|prioriti[sz]|remediation"),
    "Vulnerability Management": (
        r"cve-\d{4}-\d+|vulnerabilit|zero-?day|\b0-day\b|\bpatch(es|ed|ing)?\b|\bcvss\b|remote code execution|\brce\b|privilege escalation|"
        r"security (flaw|bug|update|advisory|fix)|actively exploited|\bkev\b|proof[- ]of[- ]concept|out-of-band|patch tuesday|unpatched|"
        r"exploited in the wild|arbitrary code|sql injection|buffer overflow|authentication bypass|critical (flaw|bug)",
        r"\bexploits?\b|exploitation|\bflaws?\b|\bbugs?\b|advisory"),
    "Zero Trust Secure Access": (
        r"zero[- ]trust|\bztna\b|\bsase\b|\bsse\b|secure access|least privilege|micro-?segmentation|secure web gateway|\bcasb\b|"
        r"conditional access|remote access (security|solution)",
        r"remote access|\bvpn\b|access control"),
}
_MODULE_RX = {n: (re.compile(sr, re.I), re.compile(wk, re.I)) for n, (sr, wk) in _MODULE_RULES.items()}


def classify_modules(article: dict) -> list[str]:
    """Return the modules an article relates to, strongest first.

    Title hits on strong terms qualify on their own; body-only evidence needs several
    mentions. Articles with no match are 'Other/General' when we had text to judge,
    or 'N/A' when there was nothing beyond the title.
    """
    title = article.get("title", "")
    context = article.get("context", "")
    body = " ".join((context + " " + article.get("full_text", "")[:MODULE_BODY_CHARS]).split())
    scored = []
    for order, (name, (strong, weak)) in enumerate(_MODULE_RX.items()):
        score = (3 if strong.search(title) else 0) + min(len(strong.findall(body)), 3)
        score += (1 if weak.search(title) else 0) + 0.5 * min(len(weak.findall(body)), 4)
        if score >= MODULE_MIN_SCORE:
            scored.append((-score, order, name))
    if scored:
        scored.sort()
        floor = max(MODULE_MIN_SCORE, 0.4 * -scored[0][0])
        return [name for neg, _, name in scored if -neg >= floor][:MODULE_MAX_PER_ARTICLE]
    return [MODULE_OTHER] if body else [MODULE_NA]


# ---------------------------------------------------------------------------
# Master article store (every article ever seen) + backfill from archive snapshots
# ---------------------------------------------------------------------------

_ARCHIVE_TOKEN = re.compile(
    r'<h2>(?P<cat>.*?)</h2>|<div class="card">(?P<card>.*?)(?=<div class="card">|<div class="col">|</body>)',
    re.S,
)


def _first(pattern: str, text: str) -> str:
    m = re.search(pattern, text, re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""


def parse_archive_html(path: str) -> list[dict]:
    """Recover the articles shown on one archived dashboard snapshot."""
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    out, category = [], ""
    for m in _ARCHIVE_TOKEN.finditer(text):
        if m.group("cat") is not None:
            category = html.unescape(m.group("cat")).strip()
            continue
        card = m.group("card")
        link = re.search(r'class="card-title"\s+href="(.*?)"', card, re.S)
        if not link:
            continue
        raw_date = _first(r'class="date">(.*?)</span>', card)
        try:
            date_iso = datetime.strptime(raw_date, "%Y-%m-%d %H:%M UTC").replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            date_iso = None
        out.append({
            "source": _first(r'class="source">(.*?)</span>', card),
            "category": category,
            "title": _first(r'class="card-title"[^>]*>(.*?)</a>', card),
            "link": html.unescape(link.group(1)).strip(),
            "date": date_iso,
            "context": _first(r'class="card-context">(.*?)</p>', card),
        })
    return out


def load_master() -> dict:
    """{link: article} from articles.json; backfilled from archive/*.html when missing."""
    master: dict = {}
    try:
        with open(ARTICLES_FILE, encoding="utf-8") as f:
            for a in json.load(f)["articles"]:
                master[a["link"]] = a
        return master
    except (OSError, ValueError, KeyError):
        pass
    snapshots = sorted(f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".html")) if os.path.isdir(ARCHIVE_DIR) else []
    print(f"  Backfilling article store from {len(snapshots)} archive snapshot(s)...", file=sys.stderr)
    for name in snapshots:  # oldest first, so later snapshots refine earlier entries
        for a in parse_archive_html(os.path.join(ARCHIVE_DIR, name)):
            old = master.get(a["link"])
            if old is None:
                master[a["link"]] = a
            elif not old.get("context") and a.get("context"):
                old["context"] = a["context"]
    return master


def merge_into_master(master: dict, live: list[dict]) -> None:
    """Add/refresh today's articles. Category is recomputed for live items only."""
    for a in live:
        link = a.get("link")
        if not link:
            continue
        entry = master.setdefault(link, {"source": a["source"], "title": a["title"], "link": link,
                                         "date": a["date"].isoformat() if a["date"] else None, "context": ""})
        entry["category"] = categorize(a)
        if a.get("context") and not entry.get("context"):
            entry["context"] = a["context"]
        if a.get("feed_text"):
            entry["feed_text"] = a["feed_text"]


def save_master(master: dict, label: str) -> None:
    items = sorted(master.values(), key=lambda a: a.get("date") or "", reverse=True)
    dated = [a for a in items if a.get("date")]
    items = dated + [a for a in items if not a.get("date")]
    slim = [{"source": a["source"], "category": a.get("category", ""), "title": a["title"],
             "link": a["link"], "date": a.get("date"), "context": a.get("context", ""),
             "modules": a.get("modules", [])} for a in items]
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump({"generated": label, "count": len(slim), "articles": slim}, f, ensure_ascii=False, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Filtering & categorization
# ---------------------------------------------------------------------------

def filter_recent(articles: list[dict], hours: int = LOOKBACK_HOURS) -> list[dict]:
    cutoff  = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent  = [a for a in articles if a["date"] and a["date"] >= cutoff]
    undated = [a for a in articles if not a["date"]]
    return sorted(recent, key=lambda a: a["date"], reverse=True) + undated


_STOP_WORDS = {
    "a", "an", "the", "and", "or", "for", "of", "in", "on", "at", "to",
    "is", "are", "was", "were", "be", "been", "have", "has", "had", "with",
    "from", "by", "as", "its", "not", "but", "this", "that", "over", "after",
    "new", "says", "said", "via", "how", "why", "what", "when", "who",
    "into", "than", "more", "your", "about", "just", "using", "used",
}


def _keywords(title: str) -> set[str]:
    words = re.findall(r'[a-z0-9]+(?:-[a-z0-9]+)*', title.lower())
    return {w for w in words if len(w) >= 4 and w not in _STOP_WORDS}


def deduplicate(articles: list[dict], threshold: float = 0.80, keyword_overlap: int = 3) -> list[dict]:
    seen_urls: set[str] = set()
    unique:    list[dict] = []

    for article in articles:
        url = article["link"].strip().rstrip("/")
        if url and url in seen_urls:
            continue

        title     = article["title"].lower()
        title_kws = _keywords(article["title"])
        is_duplicate = False

        for kept in unique:
            if difflib.SequenceMatcher(None, title, kept["title"].lower()).ratio() >= threshold:
                is_duplicate = True
                break
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


_ACQ_EXCLUSIONS = {
    "scam", "fraud", "phishing", "ransomware", "malware", "attack",
    "tactic", "threat", "hack", "hacked", "breach", "breached", "exploit", "vulnerability",
    "stolen", "theft", "criminal", "gang", "arrest", "indicted",
    "leak", "leaked", "compromised", "extortion", "ransom", "victim", "cyberattack",
}

def categorize(article: dict) -> str:
    """Return the first matching category (priority order = CATEGORIES insertion order)."""
    haystack = article["title"].lower()
    # Tokenize the same way as _keywords so trailing punctuation (e.g. "breach;")
    # doesn't defeat the whole-word exclusion check below.
    words = set(re.findall(r'[a-z0-9]+(?:-[a-z0-9]+)*', haystack))
    for cat, kws in CATEGORIES.items():
        if not any(kw in haystack for kw in kws):
            continue
        if cat == "Company & Service Acquisitions" and words & _ACQ_EXCLUSIONS:
            continue
        return cat
    return "General Security News"


def bucket_articles(articles: list[dict]) -> dict[str, list[dict]]:
    buckets: dict[str, list[dict]] = {cat: [] for cat in CATEGORY_COLORS}
    for a in articles:
        cat = categorize(a)
        buckets.setdefault(cat, []).append(a)
    return buckets

# ---------------------------------------------------------------------------
# History management
# ---------------------------------------------------------------------------

def load_history() -> list[dict]:
    """Build history from archive files on disk — avoids git merge conflicts."""
    if not os.path.exists(ARCHIVE_DIR):
        return []
    files = sorted(
        [f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".html")],
        reverse=True,
    )
    history = []
    for fname in files[:MAX_HISTORY]:
        try:
            dt = datetime.strptime(fname[:-5], "%Y-%m-%d-%H%M")
            label = dt.strftime("%Y-%m-%d %H:%M PHT")
        except ValueError:
            label = fname[:-5]
        history.append({"label": label, "url": f"{REPORT_URL}archive/{fname}"})
    return history


def save_history(history: list[dict]) -> None:
    """Write history.json so pages can fetch it dynamically."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def _csv_text(text: str) -> str:
    if len(text) <= CSV_CELL_LIMIT:
        return text
    return text[:CSV_CELL_LIMIT] + " [truncated for CSV - full text is in the JSON export]"


def export_digest_json(articles: list[dict], label: str) -> str:
    """Export digest as JSON with all article metadata including context.

    Returns JSON string suitable for external tools/dashboards.
    """
    buckets = bucket_articles(articles)
    export = {
        "generated": label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_articles": len(articles),
        "categories": {}
    }

    for cat, items in buckets.items():
        export["categories"][cat] = [
            {
                "source": a["source"],
                "title": a["title"],
                "link": a["link"],
                "date": a["date"].isoformat() if a["date"] else None,
                "context": a.get("context", ""),
                "modules": a.get("modules", []),
                "full_text": a.get("full_text", "")
            }
            for a in items
        ]

    return json.dumps(export, indent=2)


def export_digest_csv(articles: list[dict], label: str) -> str:
    """Export digest as CSV with all article metadata.

    Returns CSV string suitable for Excel/spreadsheet applications.
    """
    import io
    import csv as csv_module

    output = io.StringIO()
    writer = csv_module.writer(output)

    # Write header
    writer.writerow(["Date", "Category", "Modules", "Source", "Title", "Link", "Context", "Full Text"])

    # Write articles
    buckets = bucket_articles(articles)
    for cat, items in buckets.items():
        for article in items:
            date_str = article["date"].strftime("%Y-%m-%d %H:%M UTC") if article["date"] else ""
            writer.writerow([
                date_str,
                cat,
                "; ".join(article.get("modules", [])),
                article["source"],
                article["title"],
                article["link"],
                article.get("context", ""),
                _csv_text(article.get("full_text", ""))
            ])

    return output.getvalue()


def export_by_category(articles: list[dict], label: str) -> dict[str, tuple[str, str]]:
    """Export digest split by category as separate CSV and JSON files.

    Returns dict mapping category names to (csv_content, json_content) tuples.
    """
    import io
    import csv as csv_module

    buckets = bucket_articles(articles)
    exports = {}

    for cat, items in buckets.items():
        if not items:
            continue

        # CSV export for this category
        csv_output = io.StringIO()
        csv_writer = csv_module.writer(csv_output)
        csv_writer.writerow(["Date", "Source", "Modules", "Title", "Link", "Context", "Full Text"])
        for article in items:
            date_str = article["date"].strftime("%Y-%m-%d %H:%M UTC") if article["date"] else ""
            csv_writer.writerow([
                date_str,
                article["source"],
                "; ".join(article.get("modules", [])),
                article["title"],
                article["link"],
                article.get("context", ""),
                _csv_text(article.get("full_text", ""))
            ])
        csv_content = csv_output.getvalue()

        # JSON export for this category
        json_content = json.dumps({
            "category": cat,
            "generated": label,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "article_count": len(items),
            "articles": [
                {
                    "date": a["date"].isoformat() if a["date"] else None,
                    "source": a["source"],
                    "title": a["title"],
                    "link": a["link"],
                    "context": a.get("context", ""),
                    "modules": a.get("modules", []),
                    "full_text": a.get("full_text", "")
                }
                for a in items
            ]
        }, indent=2)

        exports[cat] = (csv_content, json_content)

    return exports

# ---------------------------------------------------------------------------
# HTML report — Trend Micro branding + column layout + history dropdown
# ---------------------------------------------------------------------------

CATEGORY_COLORS = {
    "Zero-Day Exploits & Vulnerabilities": "#DA291C",  # red
    "Company & Service Acquisitions":      "#3498db",  # blue
    "Trend Micro":                         "#DA291C",  # Trend red
    "CrowdStrike":                         "#e67e22",  # orange
    "Palo Alto Networks":                  "#00b4d8",  # cyan
    "Fortinet":                            "#c0392b",  # dark red
    "SentinelOne":                         "#8e44ad",  # purple
    "Microsoft Security":                  "#0078d4",  # Microsoft blue
    "Mandiant":                            "#e74c3c",  # red-orange
    "Sophos":                              "#2980b9",  # steel blue
    "ESET":                                "#00a9e0",  # ESET cyan-blue
    "Bitdefender":                         "#ed1c24",  # Bitdefender red
    "Check Point":                         "#27ae60",  # green
    "Recorded Future":                     "#16a085",  # teal
    "Cisco Security":                      "#1ba0d7",  # Cisco blue
    "Wiz":                                 "#4fc3f7",  # Wiz light blue
    "Orca Security":                       "#0288d1",  # Orca blue
    "Trellix":                             "#7cb342",  # Trellix green
    "Darktrace":                           "#37474f",  # dark grey
    "ExtraHop":                            "#f4511e",  # ExtraHop orange-red
    "Vectra AI":                           "#6a1b9a",  # deep purple
    "Proofpoint":                          "#0277bd",  # Proofpoint blue
    "Broadcom / Symantec":                 "#fdd835",  # yellow
    "Kaspersky":                           "#006d5b",  # Kaspersky green
    "Cybereason":                          "#e91e63",  # pink-red
    "Barracuda":                           "#e65100",  # deep orange
    "Falco / Sysdig":                      "#00acc1",  # cyan
    "Okta":                                "#00297a",  # Okta dark blue
    "CyberArk":                            "#cb2d3e",  # CyberArk red
    "BeyondTrust":                         "#f57c00",  # BeyondTrust orange
    "Delinea":                             "#e91e8c",  # Delinea magenta
    "IBM Security":                        "#1f70c1",  # IBM blue
    "Elastic Security":                    "#f04e98",  # Elastic pink
    "Rubrik":                              "#ffb900",  # Rubrik gold
    "Arctic Wolf":                         "#1a73e8",  # Arctic Wolf blue
    "Abnormal Security":                   "#00c2a8",  # Abnormal teal
    "Huntress":                            "#e84545",  # Huntress red
    "Lacework":                            "#5c2d91",  # Lacework purple
    "Aqua Security":                       "#00adef",  # Aqua cyan
    "Snyk":                                "#4c4a73",  # Snyk dark purple
    "Rapid7":                              "#e67e22",  # orange
    "Tenable":                             "#9b59b6",  # purple
    "Qualys":                              "#1abc9c",  # teal
    "Zscaler":                             "#f1c40f",  # yellow
    "Netskope":                            "#0aa5a8",  # Netskope teal
    "Cato Networks":                       "#5b6ef5",  # Cato indigo
    "Dragos":                              "#ff6f00",  # Dragos amber (OT/ICS)
    "Claroty":                             "#009688",  # Claroty teal (OT/ICS)
    "WithSecure":                          "#ff4a3d",  # WithSecure coral
    "Secureworks":                         "#b71c1c",  # Secureworks deep red
    "Blackberry / Cylance":                "#00a94f",  # Cylance green
    "General Security News":               "#95a5a6",  # grey
}


def _build_dropdown() -> str:
    """Dropdown shell — options are populated at page-load via JS fetch of history.json."""
    return """
  <div class="dropdown-bar">
    <div class="dropdown-group">
      <label for="category-select">Category:</label>
      <select id="category-select" onchange="filterByCategory(this.value);">
        <option value="">-- All categories --</option>
      </select>
    </div>
    <div class="dropdown-group">
      <label for="module-select">Module:</label>
      <select id="module-select" onchange="filterByModule(this.value);">
        <option value="">-- All modules --</option>
      </select>
    </div>
    <div class="dropdown-group">
      <label for="history-select">History:</label>
      <select id="history-select" onchange="if(this.value) window.location.href=this.value;">
        <option value="">-- Select a date --</option>
      </select>
    </div>
  </div>
  <script>
    // Populate category filter
    function populateCategories() {
      const cols = document.querySelectorAll('.col');
      const categories = new Set();
      cols.forEach(col => {
        const h2 = col.querySelector('h2');
        if (h2) categories.add(h2.textContent.trim());
      });

      const sel = document.getElementById('category-select');
      const sorted = Array.from(categories).sort();
      sorted.forEach(cat => {
        const opt = document.createElement('option');
        opt.value = cat;
        opt.textContent = cat;
        sel.appendChild(opt);
      });
    }

    // Module filter: cards carry their modules in data-modules, separated by |
    function populateModules() {
      const counts = {};
      document.querySelectorAll('.card').forEach(card => {
        (card.dataset.modules || '').split('|').forEach(m => {
          if (m) counts[m] = (counts[m] || 0) + 1;
        });
      });
      const sel = document.getElementById('module-select');
      if (!sel) return;
      Object.keys(counts).sort().forEach(m => {
        const opt = document.createElement('option');
        opt.value = m;
        opt.textContent = m + ' (' + counts[m] + ')';
        sel.appendChild(opt);
      });
    }

    function updateRows() {
      document.querySelectorAll('.col').forEach(col => {
        const any = col.querySelector('.card:not(.hide-search):not(.hide-module)') !== null;
        col.classList.toggle('search-hidden', !any);
      });
    }

    function filterByModule(mod) {
      document.querySelectorAll('.card').forEach(card => {
        const mods = (card.dataset.modules || '').split('|');
        card.classList.toggle('hide-module', mod !== '' && mods.indexOf(mod) === -1);
      });
      updateRows();
    }

    // Filter columns by category
    function filterByCategory(category) {
      const cols = document.querySelectorAll('.col');
      cols.forEach(col => {
        const h2 = col.querySelector('h2');
        if (!h2) return;
        const colCategory = h2.textContent.trim();
        col.style.display = category === '' || colCategory === category ? 'block' : 'none';
      });

      // Save preference to localStorage
      if (category) {
        localStorage.setItem('selectedCategory', category);
      } else {
        localStorage.removeItem('selectedCategory');
      }
    }

    // Restore saved category filter
    function restoreFilterPreference() {
      const saved = localStorage.getItem('selectedCategory');
      if (saved) {
        const sel = document.getElementById('category-select');
        if (sel) {
          sel.value = saved;
          filterByCategory(saved);
        }
      }
    }

    // Populate history dropdown
    fetch('https://lukan47.github.io/RSS/history.json')
      .then(r => r.json())
      .then(history => {
        const sel = document.getElementById('history-select');
        const cur = window.location.href.split('?')[0].replace(/\\/+$/, '');
        history.forEach(h => {
          const opt = document.createElement('option');
          opt.value = h.url;
          opt.textContent = h.label;
          if (cur === h.url.replace(/\\/+$/, '')) opt.selected = true;
          sel.appendChild(opt);
        });
      })
      .catch(() => {});

    // Search functionality
    function initializeSearch() {
      const searchInput = document.getElementById('search-input');
      const searchClear = document.getElementById('search-clear');
      const cards = document.querySelectorAll('.card');

      if (!searchInput) return;

      function performSearch(query) {
        const lowerQuery = query.toLowerCase().trim();
        let visibleCount = 0;

        cards.forEach(card => {
          const title = card.querySelector('.card-title')?.textContent || '';
          const source = card.querySelector('.source')?.textContent || '';
          const context = card.textContent || '';
          const fullText = (title + ' ' + source + ' ' + context).toLowerCase();

          const match = lowerQuery === '' || fullText.includes(lowerQuery);
          card.classList.toggle('hide-search', !match);
          if (match) visibleCount++;
        });

        updateRows();

        // Show/hide clear button
        searchClear.style.display = lowerQuery ? 'block' : 'none';

        // Update count
        const totalVisible = document.querySelectorAll('.card:not(.hide-search):not(.hide-module)').length;
        return totalVisible;
      }

      searchInput.addEventListener('input', (e) => {
        performSearch(e.target.value);
      });

      searchClear.addEventListener('click', () => {
        searchInput.value = '';
        performSearch('');
        searchInput.focus();
      });

      // Allow Enter key to focus search
      document.addEventListener('keydown', (e) => {
        if (e.key === '/' && e.target !== searchInput) {
          e.preventDefault();
          searchInput.focus();
        }
      });
    }

    // Row expand/collapse: only offered when a row overflows sideways
    function initializeRowToggles() {
      const rows = Array.from(document.querySelectorAll('.col'));
      function refresh() {
        rows.forEach(col => {
          const body = col.querySelector('.col-body');
          const btn = col.querySelector('.col-toggle');
          if (!body || !btn) return;
          btn.hidden = !col.classList.contains('expanded') && body.scrollWidth <= body.clientWidth + 1;
        });
      }
      rows.forEach(col => {
        const btn = col.querySelector('.col-toggle');
        if (!btn) return;
        btn.addEventListener('click', () => {
          const open = col.classList.toggle('expanded');
          btn.textContent = open ? 'Collapse' : 'Show all';
        });
      });
      refresh();
      window.addEventListener('resize', refresh);
    }

    // Category export: one option per category and format
    function initializeCategoryExports() {
      const exportSelect = document.getElementById('category-export-select');
      if (!exportSelect) return;
      const seen = new Set();
      document.querySelectorAll('.col h2').forEach(h2 => {
        const cat = h2.textContent.trim();
        if (!cat || seen.has(cat)) return;
        seen.add(cat);
        const safe = cat.toLowerCase().replace(/[^a-z0-9_-]/g, '_');
        ['csv', 'json'].forEach(fmt => {
          const option = document.createElement('option');
          option.value = 'digest__' + safe + '.' + fmt;
          option.textContent = cat + ' (' + fmt.toUpperCase() + ')';
          exportSelect.appendChild(option);
        });
      });

      exportSelect.addEventListener('change', () => {
        const file = exportSelect.value;
        if (!file) return;
        const a = document.createElement('a');
        const prefix = location.pathname.indexOf('/archive/') !== -1 ? 'exports/' : 'archive/exports/';
        a.href = prefix + file;
        a.download = file;
        document.body.appendChild(a);
        a.click();
        a.remove();
        exportSelect.value = '';
      });
    }

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', () => {
      [populateCategories, populateModules, initializeCategoryExports, initializeSearch, initializeRowToggles, restoreFilterPreference].forEach(fn => {
        try {
          fn();
        } catch (err) {
          console.error(fn.name + ' failed:', err);
        }
      });
    });
  </script>"""


def build_html(articles: list[dict], label: str, history: list[dict] | None = None) -> str:
    buckets  = bucket_articles(articles)
    columns  = []
    dropdown = _build_dropdown()

    for cat, items in buckets.items():
        if not items:
            continue
        color = CATEGORY_COLORS.get(cat, "#95a5a6")
        cards = []
        for a in items:
            date_str    = a["date"].strftime("%Y-%m-%d %H:%M UTC") if a["date"] else "unknown date"
            safe_title  = html.escape(a["title"])
            safe_source = html.escape(a["source"])
            safe_link   = html.escape(a["link"])
            safe_context = html.escape(a.get("context", ""))

            context_html = ""
            if safe_context:
                context_html = f'<p class="card-context">{safe_context}</p>'

            modules = a.get("modules") or []
            modules_attr = html.escape("|".join(modules))
            shown = [m for m in modules if m not in (MODULE_OTHER, MODULE_NA)]
            modules_html = ""
            if shown:
                modules_html = '<div class="card-modules">' + " &middot; ".join(html.escape(m) for m in shown) + "</div>"

            cards.append(f"""
            <div class="card" data-modules="{modules_attr}">
              <div class="card-meta">
                <span class="source">{safe_source}</span>
                <span class="date">{date_str}<button type="button" class="card-details" aria-label="Details and export"></button></span>
              </div>
              <a class="card-title" href="{safe_link}" target="_blank">{safe_title}</a>
              {modules_html}
              {context_html}
            </div>""")

        columns.append(f"""
      <div class="col">
        <div class="col-header" style="border-left:4px solid {color};">
          <h2>{html.escape(cat)}</h2>
          <span class="count">{len(items)} article(s)</span>
          <button type="button" class="col-toggle" hidden>Show all</button>
        </div>
        <div class="col-body">
          {"".join(cards)}
        </div>
      </div>""")

    dash_modal_js = DASH_MODAL_JS.replace("__FULLTEXT_BASE__", REPORT_URL + "archive/data/fulltext/")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cyber Competitive Daily Feed — {label}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #0d0e17;
    color: #e0e0e0;
    padding: 0;
  }}

  /* ── Top bar ── */
  .topbar {{
    background: #13141f;
    border-bottom: 3px solid #DA291C;
    padding: 16px 24px;
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 20px;
    align-items: start;
  }}
  .topbar-left h1 {{
    font-size: 1.4rem;
    color: #fff;
    font-weight: 700;
    letter-spacing: 0.3px;
  }}
  .topbar-left h1 span {{
    color: #DA291C;
  }}
  .topbar-left p {{
    font-size: 0.82rem;
    color: #666;
    margin-top: 3px;
  }}
  .topbar-right {{
    display: flex;
    flex-direction: row;
    gap: 10px 14px;
    align-items: center;
    flex-wrap: wrap;
  }}
  @media (max-width: 1600px) {{
    .topbar {{
      grid-template-columns: 1fr;
    }}
    .topbar-right {{
      width: 100%;
      margin-top: 12px;
    }}
  }}

  /* ── Filter dropdowns ── */
  .dropdown-bar {{
    display: flex;
    align-items: center;
    gap: 10px 12px;
    flex-wrap: wrap;
    font-size: 0.82rem;
    color: #888;
  }}
  .dropdown-group {{
    display: flex;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
  }}
  .dropdown-group label {{
    white-space: nowrap;
    font-size: 0.75rem;
  }}
  .dropdown-group select {{
    background: #1e2030;
    color: #e0e0e0;
    border: 1px solid #2a2d3e;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 0.75rem;
    cursor: pointer;
    outline: none;
    min-width: 140px;
  }}
  .dropdown-group select:hover {{
    border-color: #DA291C;
  }}
  .dropdown-group select:focus {{
    border-color: #DA291C;
    box-shadow: 0 0 0 2px rgba(218, 41, 28, 0.1);
  }}

  /* ── Export buttons ── */
  .export-buttons {{
    display: flex;
    gap: 6px;
    align-items: center;
  }}
  .export-btn.explorer-link {{ background: #1e2030; border: 1px solid #DA291C; }}
  .export-btn {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #DA291C;
    color: #fff;
    padding: 5px 10px;
    border-radius: 4px;
    text-decoration: none;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    border: none;
    transition: all 0.2s ease;
    white-space: nowrap;
  }}
  .export-btn:hover {{
    background: #f04e3f;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(218, 41, 28, 0.3);
  }}
  .export-btn:active {{
    transform: translateY(0);
  }}

  /* ── Search bar ── */
  .search-bar {{
    display: flex;
    align-items: center;
    gap: 6px;
    background: #1e2030;
    border: 1px solid #2a2d3e;
    border-radius: 4px;
    padding: 5px 10px;
    min-width: 200px;
    white-space: nowrap;
  }}
  .search-bar input {{
    background: transparent;
    border: none;
    color: #e0e0e0;
    font-size: 0.75rem;
    outline: none;
    flex: 1;
    min-width: 100px;
  }}
  .search-bar input::placeholder {{
    color: #666;
  }}
  .search-bar input:focus {{
    outline: none;
  }}
  .search-bar:focus-within {{
    border-color: #DA291C;
    box-shadow: 0 0 0 2px rgba(218, 41, 28, 0.1);
  }}
  .search-clear {{
    background: none;
    border: none;
    color: #666;
    cursor: pointer;
    font-size: 1rem;
    padding: 0;
  }}
  .search-clear:hover {{
    color: #DA291C;
  }}

  /* ── Main content ── */
  .content {{ padding: 24px; }}

  /* ── Column grid ── */
  .grid {{
    display: flex;
    flex-direction: column;
    gap: 14px;
  }}
  @media (max-width: 640px) {{
    .topbar {{ flex-direction: column; align-items: flex-start; }}
  }}

  /* ── Column ── */
  .col {{
    background: #13161f;
    border-radius: 10px;
    overflow: hidden;
  }}
  .col.search-hidden {{ display: none !important; }}
  .card.hide-search, .card.hide-module {{ display: none; }}
  .card-meta .source {{ min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .card-meta .date {{ display: inline-flex; align-items: center; white-space: nowrap; }}
  {MODAL_CSS}
  .card-modules {{
    font-size: 0.7rem;
    color: #7d8299;
    line-height: 1.4;
    margin-bottom: 8px;
  }}
  .col-header {{
    display: flex;
    align-items: baseline;
    gap: 12px;
    padding: 10px 16px;
    background: #1a1d27;
  }}
  .col-toggle {{
    margin-left: auto;
    background: transparent;
    color: #aaa;
    border: 1px solid #2a2d3e;
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 0.72rem;
    cursor: pointer;
    white-space: nowrap;
  }}
  .col-toggle:hover {{ color: #fff; border-color: #DA291C; }}
  .col-header h2 {{
    font-size: 0.88rem;
    color: #fff;
    font-weight: 700;
    line-height: 1.4;
  }}
  .count {{
    font-size: 0.74rem;
    color: #555;
    white-space: nowrap;
  }}
  .col-body {{
    display: flex;
    gap: 10px;
    padding: 12px;
    overflow-x: auto;
    scroll-snap-type: x proximity;
    scrollbar-width: thin;
    scrollbar-color: #2a2d3e transparent;
  }}
  .col.expanded .col-body {{
    flex-wrap: wrap;
    overflow-x: visible;
  }}

  /* ── Article card ── */
  .card {{
    background: #1a1d27;
    border-radius: 7px;
    padding: 12px 14px;
    flex: 0 0 320px;
    max-width: 320px;
    scroll-snap-align: start;
  }}
  .card-meta {{
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 4px;
    font-size: 0.72rem;
    color: #555;
    margin-bottom: 6px;
  }}
  .source {{ color: #DA291C; font-weight: 600; }}
  .card-title {{
    color: #d8d8d8;
    text-decoration: none;
    font-size: 0.88rem;
    line-height: 1.5;
    display: block;
    margin-bottom: 8px;
  }}
  .card-title:hover {{ color: #fff; text-decoration: underline; }}
  .card-context {{
    font-size: 0.78rem;
    color: #888;
    line-height: 1.4;
    margin: 0;
    padding: 8px 0 0 0;
    border-top: 1px solid #222;
  }}

  footer {{
    margin-top: 40px;
    padding: 20px 24px;
    font-size: 0.75rem;
    color: #333;
    text-align: center;
    border-top: 1px solid #1a1d27;
  }}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-left">
    <h1><span>Cyber</span> Competitive Daily Feed</h1>
    <p>{label} &nbsp;·&nbsp; {len(articles)} article(s) in the last {LOOKBACK_HOURS // 24} day(s)</p>
  </div>
  <div class="topbar-right">
    {dropdown}
    <div class="export-buttons">
      <a href="{EXPLORER_URL}" class="export-btn explorer-link" title="Browse every stored article by period, category and module, then export">All articles &rarr;</a>
      <a href="{REPORT_URL}archive/exports/digest.json" download="digest.json" class="export-btn export-json" title="Download all as JSON">⬇ JSON</a>
      <a href="{REPORT_URL}archive/exports/digest.csv" download="digest.csv" class="export-btn export-csv" title="Download all as CSV">⬇ CSV</a>
      <select id="category-export-select" class="export-btn" style="padding: 5px 10px; font-size: 0.75rem; cursor: pointer;">
        <option value="">⬇ Category</option>
      </select>
    </div>
    <div class="search-bar">
      <input type="text" id="search-input" placeholder="Search articles..." class="search-input">
      <button class="search-clear" id="search-clear" title="Clear search" style="display:none;">✕</button>
    </div>
  </div>
</div>

<div class="content">
  <div class="grid">
    {"".join(columns)}
  </div>
</div>

<footer>Updated twice daily · 6:00 AM &amp; 6:00 PM PHT · lukan47/RSS</footer>
{MODAL_HTML}
<script>
{MODAL_JS}
{dash_modal_js}
</script>
</body>
</html>"""

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Article details popup (shared by the dashboard and the all-articles page).
# Exports are generated in the browser when a button is clicked; no static files.
# ---------------------------------------------------------------------------

MODAL_CSS = r"""
  body.am-open { overflow: hidden; }
  .am-overlay { position: fixed; inset: 0; background: rgba(5,6,12,.72); display: flex; align-items: center;
                justify-content: center; padding: 16px; z-index: 1000; }
  .am-overlay[hidden] { display: none; }
  .am-dialog { background: #171a26; border: 1px solid #2a2d3e; border-top: 3px solid #DA291C; border-radius: 8px;
               width: min(680px, 100%); max-height: 90vh; overflow: auto; padding: 20px 22px; color: #e0e0e0;
               box-shadow: 0 20px 60px rgba(0,0,0,.5); }
  .am-head { display: flex; gap: 12px; align-items: flex-start; justify-content: space-between; }
  .am-title { font-size: 1.05rem; line-height: 1.4; color: #fff; font-weight: 700; }
  .am-close { background: transparent; border: 1px solid #2a2d3e; color: #aaa; border-radius: 4px; width: 30px;
              height: 30px; cursor: pointer; font-size: 1.1rem; flex: 0 0 auto; line-height: 1; }
  .am-close:hover { color: #fff; border-color: #DA291C; }
  .am-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 12px; font-size: .78rem; color: #8a8fa3; margin: 12px 0 8px; }
  .am-chip { color: #fff; border-radius: 3px; padding: 1px 8px; font-weight: 600; font-size: .7rem; background: #555a70; }
  .am-src { color: #ff5a4d; font-weight: 600; }
  .am-mods { font-size: .78rem; color: #7d8299; margin-bottom: 12px; }
  .am-ctx { font-size: .88rem; line-height: 1.6; color: #c9cbd6; background: #1e2030; border-radius: 6px;
            padding: 12px 14px; margin-bottom: 16px; white-space: pre-wrap; }
  .am-ctx.empty { color: #6b7088; font-style: italic; }
  .am-actions { display: flex; flex-wrap: wrap; gap: 10px 12px; align-items: center; }
  .am-btn { background: #DA291C; color: #fff; border: none; border-radius: 4px; padding: 7px 14px; font-size: .78rem;
            font-weight: 600; cursor: pointer; text-decoration: none; white-space: nowrap; font-family: inherit; }
  .am-btn:hover:not(:disabled) { background: #f0352a; }
  .am-btn:disabled { opacity: .4; cursor: not-allowed; }
  .am-btn.secondary { background: #1e2030; border: 1px solid #2a2d3e; }
  .am-btn.secondary:hover:not(:disabled) { background: #262a3d; border-color: #DA291C; }
  .am-chk { display: flex; align-items: center; gap: 6px; font-size: .78rem; color: #c9cbd6; cursor: pointer; margin-left: auto; }
  .am-status { font-size: .75rem; color: #8a8fa3; min-height: 1.3em; margin-top: 10px; }
  .am-dialog button:focus-visible, .am-dialog a:focus-visible, .am-dialog input:focus-visible { outline: 2px solid #DA291C; outline-offset: 1px; }
  .card-details { margin-left: 10px; background: transparent; color: #8a8fa3; border: 1px solid #2a2d3e; border-radius: 3px;
                  padding: 0 7px; font-size: .68rem; cursor: pointer; font-family: inherit; line-height: 1.6; }
  .card-details::after { content: "Details"; }
  .card-details:hover, .card-details:focus-visible { color: #fff; border-color: #DA291C; outline: none; }
"""

MODAL_HTML = """
<div class="am-overlay" id="am-overlay" hidden>
  <div class="am-dialog" id="am-dialog" role="dialog" aria-modal="true" aria-labelledby="am-title">
    <div class="am-head">
      <h2 class="am-title" id="am-title"></h2>
      <button type="button" class="am-close" id="am-close" aria-label="Close">&times;</button>
    </div>
    <div class="am-meta" id="am-meta"></div>
    <div class="am-mods" id="am-mods"></div>
    <p class="am-ctx" id="am-ctx"></p>
    <div class="am-actions">
      <a class="am-btn" id="am-open" href="#" target="_blank" rel="noopener noreferrer">Open article &#8599;</a>
      <button type="button" class="am-btn secondary" id="am-json">&darr; JSON</button>
      <button type="button" class="am-btn secondary" id="am-csv">&darr; CSV</button>
      <label class="am-chk"><input type="checkbox" id="am-fulltext"> Include full article text</label>
    </div>
    <div class="am-status" id="am-status" role="status" aria-live="polite"></div>
  </div>
</div>
"""

MODAL_JS = r"""
(function () {
  'use strict';
  var overlay = document.getElementById('am-overlay');
  if (!overlay) return;
  var $ = function (id) { return document.getElementById(id); };
  var el = { title: $('am-title'), meta: $('am-meta'), mods: $('am-mods'), ctx: $('am-ctx'), open: $('am-open'),
             ft: $('am-fulltext'), json: $('am-json'), csv: $('am-csv'), status: $('am-status'),
             close: $('am-close'), dialog: $('am-dialog') };
  var CSV_CELL_LIMIT = 32000;
  var current = null, base = '', lastFocus = null, shards = {};

  function setStatus(msg, isError) { el.status.textContent = msg || ''; el.status.style.color = isError ? '#ff7b72' : ''; }

  function openModal(a, opts) {
    current = a; base = (opts && opts.fullTextBase) || '';
    el.title.textContent = a.title;
    el.meta.textContent = '';
    if (a.category) {
      var chip = document.createElement('span'); chip.className = 'am-chip'; chip.textContent = a.category;
      if (a.color) chip.style.background = a.color;
      el.meta.appendChild(chip);
    }
    var src = document.createElement('span'); src.className = 'am-src'; src.textContent = a.source; el.meta.appendChild(src);
    var when = document.createElement('span');
    when.textContent = a.date ? a.date.slice(0, 16).replace('T', ' ') + ' UTC' : 'Date unknown';
    el.meta.appendChild(when);
    var mods = a.modules || [];
    el.mods.textContent = mods.length ? 'Modules: ' + mods.join(' \u00b7 ') : '';
    el.mods.hidden = !mods.length;
    el.ctx.textContent = a.context || 'No summary was extracted for this article.';
    el.ctx.className = 'am-ctx' + (a.context ? '' : ' empty');
    el.open.href = a.link;
    el.ft.checked = false; setStatus('');
    el.json.disabled = el.csv.disabled = false;
    lastFocus = document.activeElement;
    overlay.hidden = false; document.body.classList.add('am-open');
    el.close.focus();
  }

  function closeModal() {
    if (overlay.hidden) return;
    overlay.hidden = true; document.body.classList.remove('am-open');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  async function savedText(a) {
    var month = a.date ? a.date.slice(0, 7) : 'undated';
    if (!shards[month]) {
      var res = await fetch(base + month + '.json');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      shards[month] = await res.json();
    }
    var entry = shards[month][a.link];
    return entry && entry.text ? entry.text : '';
  }

  function csvCell(v) {
    v = v == null ? '' : String(v);
    return /[",\r\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  }

  function download(name, mime, content) {
    var url = URL.createObjectURL(new Blob([content], { type: mime }));
    var a = document.createElement('a'); a.href = url; a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
  }

  async function exportAs(fmt) {
    var withText = el.ft.checked, note = '';
    var rec = { date: current.date, category: current.category || '', modules: current.modules || [], source: current.source,
                title: current.title, link: current.link, context: current.context || '' };
    el.json.disabled = el.csv.disabled = true;
    try {
      if (withText) {
        setStatus('Loading saved article text\u2026');
        try { rec.full_text = await savedText(current); } catch (e) { rec.full_text = ''; note = ' (could not load saved text: ' + e.message + ')'; }
        if (!rec.full_text && !note) note = ' (no saved text for this article)';
      }
      var slug = current.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60) || 'article';
      if (fmt === 'json') {
        download('article_' + slug + '.json', 'application/json',
                 JSON.stringify({ exported: new Date().toISOString(), article: rec }, null, 2));
      } else {
        var head = ['Date', 'Category', 'Modules', 'Source', 'Title', 'Link', 'Context'].concat(withText ? ['Full Text'] : []);
        var cells = [rec.date ? rec.date.slice(0, 16).replace('T', ' ') + ' UTC' : '', rec.category, rec.modules.join('; '),
                     rec.source, rec.title, rec.link, rec.context];
        if (withText) {
          var t = rec.full_text;
          cells.push(t.length > CSV_CELL_LIMIT ? t.slice(0, CSV_CELL_LIMIT) + ' [truncated for CSV - use JSON for the full text]' : t);
        }
        download('article_' + slug + '.csv', 'text/csv;charset=utf-8',
                 '\ufeff' + head.join(',') + '\r\n' + cells.map(csvCell).join(',') + '\r\n');
      }
      setStatus('Exported as ' + fmt.toUpperCase() + note + '.', !!note && note.indexOf('could not') !== -1);
    } catch (e) {
      setStatus('Export failed: ' + e.message, true);
    } finally {
      el.json.disabled = el.csv.disabled = false;
    }
  }

  el.close.addEventListener('click', closeModal);
  overlay.addEventListener('mousedown', function (e) { if (e.target === overlay) closeModal(); });
  el.json.addEventListener('click', function () { exportAs('json'); });
  el.csv.addEventListener('click', function () { exportAs('csv'); });
  document.addEventListener('keydown', function (e) {
    if (overlay.hidden) return;
    if (e.key === 'Escape') { e.preventDefault(); closeModal(); return; }
    if (e.key !== 'Tab') return;
    var f = Array.prototype.filter.call(el.dialog.querySelectorAll('a[href], button, input'), function (n) { return !n.disabled; });
    if (!f.length) return;
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });
  window.ArticleModal = { open: openModal, close: closeModal };
})();
"""

DASH_MODAL_JS = r"""
document.addEventListener('click', function (e) {
  var btn = e.target.closest ? e.target.closest('.card-details') : null;
  if (!btn || !window.ArticleModal) return;
  var card = btn.closest('.card'), col = card.closest('.col');
  var title = card.querySelector('.card-title');
  var m = /^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) UTC$/.exec((card.querySelector('.date').textContent || '').trim());
  var header = col && col.querySelector('.col-header');
  var ctx = card.querySelector('.card-context');
  window.ArticleModal.open({
    title: title.textContent.trim(),
    link: title.href,
    source: card.querySelector('.source').textContent.trim(),
    date: m ? m[1] + 'T' + m[2] + ':00+00:00' : null,
    category: col ? col.querySelector('h2').textContent.trim() : '',
    color: header ? getComputedStyle(header).borderLeftColor : '',
    modules: (card.dataset.modules || '').split('|').filter(Boolean),
    context: ctx ? ctx.textContent.trim() : ''
  }, { fullTextBase: '__FULLTEXT_BASE__' });
});
"""


def write_explorer() -> None:
    """Render explorer_template.html into archive/data/explorer.html."""
    try:
        with open(EXPLORER_TEMPLATE, encoding="utf-8") as f:
            template = f.read()
    except OSError as exc:
        print(f"  [WARN] explorer template missing: {exc}", file=sys.stderr)
        return
    page = (template.replace("__CATEGORY_COLORS__", json.dumps(CATEGORY_COLORS))
            .replace("__MODAL_CSS__", MODAL_CSS)
            .replace("__MODAL_HTML__", MODAL_HTML)
            .replace("__MODAL_JS__", MODAL_JS))
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(EXPLORER_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)


def main() -> None:
    pht_now   = datetime.now(PHT)
    label     = pht_now.strftime("%Y-%m-%d %H:%M PHT")
    arch_name = pht_now.strftime("%Y-%m-%d-%H%M") + ".html"
    arch_url  = f"{REPORT_URL}archive/{arch_name}"

    print("Fetching feeds...", file=sys.stderr)
    articles = fetch_all_feeds()
    print(f"Fetched {len(articles)} total articles.", file=sys.stderr)

    recent = filter_recent(articles)
    if not recent:
        print("  [INFO] No articles in last 24h, showing all fetched articles.", file=sys.stderr)
        recent = articles

    recent = deduplicate(recent)
    print(f"  {len(recent)} unique article(s) after deduplication.", file=sys.stderr)

    # ── Master store: every article ever seen (feeds + archive backfill) ──────────────────
    master = load_master()
    merge_into_master(master, recent)
    entries = sorted(master.values(), key=lambda a: a.get("date") or "", reverse=True)

    # ── Full article text (saved for exports only, never rendered) + dashboard snippets ──
    obtained = attach_full_text(entries)
    have_text = sum(1 for a in entries if a["full_text"])
    print(f"  Full text: {obtained} collected this run, {have_text}/{len(entries)} stored articles have it.", file=sys.stderr)
    for entry in entries:
        if not entry.get("context"):
            entry["context"] = extract_context(entry)
        entry["modules"] = classify_modules(entry)
    for article in recent:
        stored = master.get(article.get("link", ""))
        if stored:
            article["full_text"] = stored["full_text"]
            article["modules"] = stored["modules"]
            if not article.get("context"):
                article["context"] = stored.get("context", "")
    save_master(master, label)
    write_explorer()
    print(f"  Article store: {len(master)} article(s) -> {ARTICLES_FILE}", file=sys.stderr)

    # ── Export latest acquisition and top announcements to GitHub Actions env ───────────────────
    buckets    = bucket_articles(recent)
    acq_list   = buckets.get("Company & Service Acquisitions", [])

    # Find top vendor announcements (for GitHub Actions notifications)
    top_announcements = []
    for cat in ["CrowdStrike", "Palo Alto Networks", "Microsoft Security", "Fortinet", "SentinelOne", "Trend Micro"]:
        if cat in buckets and buckets[cat]:
            top_announcements.append(buckets[cat][0])

    github_env = os.environ.get("GITHUB_ENV", "")
    if github_env:
        if acq_list:
            acq_title = acq_list[0]["title"].replace("\n", " ")
            acq_link  = acq_list[0]["link"]
            acq_context = acq_list[0].get("context", "").replace("\n", " ")
            acq_found = "true"
        else:
            acq_title = ""
            acq_link  = ""
            acq_context = ""
            acq_found = "false"

        with open(github_env, "a", encoding="utf-8") as f:
            f.write(f"LATEST_ACQ_TITLE={acq_title}\n")
            f.write(f"LATEST_ACQ_LINK={acq_link}\n")
            f.write(f"LATEST_ACQ_CONTEXT={acq_context}\n")
            f.write(f"LATEST_ACQ_FOUND={acq_found}\n")

            # Export top vendor announcements with context
            if top_announcements:
                top_ann = top_announcements[0]
                top_title = top_ann["title"].replace("\n", " ")
                top_link = top_ann["link"]
                top_context = top_ann.get("context", "").replace("\n", " ")
                top_source = top_ann["source"]
                f.write(f"TOP_ANNOUNCEMENT_SOURCE={top_source}\n")
                f.write(f"TOP_ANNOUNCEMENT_TITLE={top_title}\n")
                f.write(f"TOP_ANNOUNCEMENT_LINK={top_link}\n")
                f.write(f"TOP_ANNOUNCEMENT_CONTEXT={top_context}\n")

    # ── Save archive snapshot first so load_history() picks it up ────────
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    arch_path = os.path.join(ARCHIVE_DIR, arch_name)
    with open(arch_path, "w", encoding="utf-8") as f:
        f.write(build_html(recent, label))
    print(f"Archive saved: {arch_path}", file=sys.stderr)

    # ── Load history from archive dir (includes the file just written) ────
    history = load_history()

    # ── Write history.json so all pages can fetch it dynamically ─────────
    save_history(history)

    # ── Save index.html ───────────────────────────────────────────────────
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(build_html(recent, label))
    print(f"Done. Published: {REPORT_URL}", file=sys.stderr)

    # ── Export digest as JSON for programmatic access ────────────────────
    json_export = export_digest_json(recent, label)
    os.makedirs(EXPORT_DIR, exist_ok=True)
    json_file = os.path.join(EXPORT_DIR, "digest.json")
    with open(json_file, "w", encoding="utf-8") as f:
        f.write(json_export)
    print(f"Digest exported: {json_file}", file=sys.stderr)

    # ── Export digest as CSV for spreadsheet access ───────────────────────
    csv_export = export_digest_csv(recent, label)
    csv_file = os.path.join(EXPORT_DIR, "digest.csv")
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        f.write(csv_export)
    print(f"Digest exported: {csv_file}", file=sys.stderr)

    # ── Export by category (separate CSV and JSON for each) ────────────────
    category_exports = export_by_category(recent, label)
    for cat, (csv_content, json_content) in category_exports.items():
        # Sanitize category name for filename
        safe_cat = "".join(c if c.isalnum() or c in "-_" else "_" for c in cat).lower()

        # Save CSV
        csv_cat_file = os.path.join(EXPORT_DIR, f"digest__{safe_cat}.csv")
        with open(csv_cat_file, "w", encoding="utf-8", newline="") as f:
            f.write(csv_content)

        # Save JSON
        json_cat_file = os.path.join(EXPORT_DIR, f"digest__{safe_cat}.json")
        with open(json_cat_file, "w", encoding="utf-8") as f:
            f.write(json_content)

    print(f"Category exports created: {len(category_exports)} categories", file=sys.stderr)


if __name__ == "__main__":
    main()
