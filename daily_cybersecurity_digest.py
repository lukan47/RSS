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
                "context": ""
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
                "context": ""
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


class _HTMLTextExtractor(HTMLParser):
    """Extract plain text from HTML, preserving paragraph structure."""
    def __init__(self):
        super().__init__()
        self.text = []
        self.in_script = False
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            setattr(self, f"in_{tag}", True)

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            setattr(self, f"in_{tag}", False)
        elif tag in ("p", "div", "br"):
            if self.text and self.text[-1] != "\n":
                self.text.append("\n")

    def handle_data(self, data):
        if not self.in_script and not self.in_style:
            text = data.strip()
            if text:
                self.text.append(text)

    def get_text(self):
        return " ".join(self.text).strip()


def _fetch_article_text(url: str, timeout: int = 8) -> str:
    """Fetch article URL and extract plain text content."""
    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urlopen(req, timeout=timeout) as resp:
            html_content = resp.read().decode("utf-8", errors="ignore")

        # Extract text from HTML
        parser = _HTMLTextExtractor()
        parser.feed(html_content)
        return parser.get_text()
    except Exception as e:
        print(f"  [DEBUG] Failed to fetch {url}: {e}", file=sys.stderr)
        return ""


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
    """Extract key findings/context from article verbatim snippet.

    Fetches the article URL and pulls out a relevant sentence or snippet
    containing important information (partnership, capability, threat, etc).
    Only processes articles from tracked vendor blogs and key security sources.
    """
    # Expanded list of key competitors and security research sources
    key_sources = [
        "CrowdStrike Blog", "CrowdStrike IR News", "Palo Alto Unit 42", "Palo Alto IR News",
        "Microsoft Security Blog", "Microsoft Security", "SentinelOne Blog", "SentinelOne",
        "Fortinet Threat Research", "Fortinet IR News", "Trend Micro Research", "Trend Micro",
        "Google Project Zero", "Talos Intelligence", "Recorded Future",
        "Check Point Research", "Check Point Blog", "Google Threat Intel (Mandiant)", "Mandiant",
        "Cisco Security", "Cisco Talos", "Sophos", "ESET", "Bitdefender", "Kaspersky",
        "Rapid7 Blog", "Tenable Blog", "Qualys Blog", "Zscaler ThreatLabz",
        "Wiz Blog", "Orca Security Blog", "Darktrace Blog", "Vectra AI Blog",
        "Proofpoint Blog", "Cybereason Blog", "Elastic Security Labs", "Okta Blog",
        "CyberArk Blog", "BeyondTrust Blog", "Aqua Security Blog", "Snyk Blog",
        "Arctic Wolf Blog", "Huntress Blog", "Rubrik Blog", "Claroty Blog"
    ]

    if article["source"] not in key_sources:
        return ""

    # Don't fetch if no URL
    if not article.get("link"):
        return ""

    try:
        # Fetch article content
        article_text = _fetch_article_text(article["link"])

        if not article_text:
            print(f"  [DEBUG] Empty text from {article['source']}: {article['title'][:50]}", file=sys.stderr)
            return ""

        # Extract key sentence from the article
        context = _extract_key_sentence(article_text, article.get("title", ""))

        if context:
            print(f"  [INFO] Context extracted from {article['source']}: {context[:60]}...", file=sys.stderr)
        else:
            print(f"  [DEBUG] No context found in {article['source']}: {article['title'][:50]}", file=sys.stderr)

        return context

    except Exception as e:
        print(f"  [DEBUG] Could not extract context from {article['link']}: {e}", file=sys.stderr)
        return ""

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
                "context": a.get("context", "")
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
    writer.writerow(["Date", "Category", "Source", "Title", "Link", "Context"])

    # Write articles
    buckets = bucket_articles(articles)
    for cat, items in buckets.items():
        for article in items:
            date_str = article["date"].strftime("%Y-%m-%d %H:%M UTC") if article["date"] else ""
            writer.writerow([
                date_str,
                cat,
                article["source"],
                article["title"],
                article["link"],
                article.get("context", "")
            ])

    return output.getvalue()

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
      <label for="category-select">Filter by category:</label>
      <select id="category-select" onchange="filterByCategory(this.value);">
        <option value="">-- All categories --</option>
      </select>
    </div>
    <div class="dropdown-group">
      <label for="history-select">Previous digests:</label>
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

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', () => {
      populateCategories();
      restoreFilterPreference();
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

            cards.append(f"""
            <div class="card">
              <div class="card-meta">
                <span class="source">{safe_source}</span>
                <span class="date">{date_str}</span>
              </div>
              <a class="card-title" href="{safe_link}" target="_blank">{safe_title}</a>
              {context_html}
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
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
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

  /* ── Filter dropdowns ── */
  .dropdown-bar {{
    display: flex;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
    font-size: 0.82rem;
    color: #888;
  }}
  .dropdown-group {{
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .dropdown-group label {{
    white-space: nowrap;
  }}
  .dropdown-group select {{
    background: #1e2030;
    color: #e0e0e0;
    border: 1px solid #2a2d3e;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 0.82rem;
    cursor: pointer;
    outline: none;
    min-width: 180px;
  }}
  .dropdown-group select:hover {{
    border-color: #DA291C;
  }}
  .dropdown-group select:focus {{
    border-color: #DA291C;
    box-shadow: 0 0 0 2px rgba(218, 41, 28, 0.1);
  }}

  /* ── Main content ── */
  .content {{ padding: 24px; }}

  /* ── Column grid ── */
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
    align-items: start;
  }}
  @media (max-width: 640px) {{
    .grid {{ grid-template-columns: 1fr; }}
    .topbar {{ flex-direction: column; align-items: flex-start; }}
  }}

  /* ── Column ── */
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
  {dropdown}
</div>

<div class="content">
  <div class="grid">
    {"".join(columns)}
  </div>
</div>

<footer>Updated twice daily · 6:00 AM &amp; 6:00 PM PHT · lukan47/RSS</footer>
</body>
</html>"""

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

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

    # ── Extract context for key articles (top 20 only to avoid timeout) ──────────────────────
    print("  Extracting context from top articles...", file=sys.stderr)
    top_articles = recent[:20]  # Limit to first 20 articles to save time
    context_count = 0
    for article in top_articles:
        if article.get("link"):
            ctx = extract_context(article)
            if ctx:
                article["context"] = ctx
                context_count += 1
    print(f"  Context extracted for {context_count} article(s).", file=sys.stderr)

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
    json_file = "digest.json"
    with open(json_file, "w", encoding="utf-8") as f:
        f.write(json_export)
    print(f"Digest exported: {json_file}", file=sys.stderr)

    # ── Export digest as CSV for spreadsheet access ───────────────────────
    csv_export = export_digest_csv(recent, label)
    csv_file = "digest.csv"
    with open(csv_file, "w", encoding="utf-8") as f:
        f.write(csv_export)
    print(f"Digest exported: {csv_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
