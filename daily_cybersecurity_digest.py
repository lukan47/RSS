#!/usr/bin/env python3
"""
CI Overwatch
Fetches cybersecurity RSS feeds concurrently, saves an HTML report to GitHub Pages.
Email notification is handled by GitHub Actions (.github/workflows/notify.yml).
"""

import collections
import hashlib
import http.client
import email.utils
import html
import json
import os
import re
import socket
import ssl
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlsplit, parse_qsl, urlencode, quote
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
    ("Wired Security",          "https://www.wired.com/feed/category/security/latest/rss"),
    ("Ars Technica Security", "https://arstechnica.com/tag/security/feed/"),
    ("Troy Hunt",               "https://feeds.feedburner.com/TroyHunt"),
    ("Infosecurity Magazine",   "https://www.infosecurity-magazine.com/rss/news/"),
    ("Help Net Security",       "https://www.helpnetsecurity.com/feed/"),
    ("SC Magazine",             "https://www.scmagazine.com/feed"),
    ("Graham Cluley",           "https://grahamcluley.com/feed/"),
    ("The CyberWire",           "https://thecyberwire.com/feeds/rss.xml"),
    ("Security Affairs",                "https://securityaffairs.com/feed"),
    ("CSO Online",                      "https://www.csoonline.com/feed/"),
    ("Risky Business News",             "https://risky.biz/feeds/risky-business-news/"),
    # ── Government / advisories ──────────────────────────────────────────
    ("CISA Advisories", "https://www.cisa.gov/cybersecurity-advisories/all.xml"),
    ("NCSC UK",                 "https://www.ncsc.gov.uk/api/1/services/v1/all-rss-feed.xml"),
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
    ("Zero Day Initiative Blog",        "https://www.zerodayinitiative.com/blog/?format=rss"),
    ("ZDI Published Advisories",        "https://www.zerodayinitiative.com/rss/published/"),
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
    ("Trend Micro Newsroom",            "https://newsroom.trendmicro.com/news-releases?pagetemplate=rss"),
    ("Malwarebytes Labs",               "https://www.malwarebytes.com/blog/feed/index.xml"),
    ("AWS Security Blog",               "https://aws.amazon.com/blogs/security/feed/"),
    ("Cloudflare Security",             "https://blog.cloudflare.com/tag/security/rss/"),
    ("Datadog Security Labs",           "https://securitylabs.datadoghq.com/rss/feed.xml"),
    ("GitHub Security Blog",            "https://github.blog/security/feed/"),
    ("Socket",                          "https://socket.dev/api/blog/feed.atom"),
    ("JFrog Blog",                      "https://jfrog.com/blog/feed/"),
    ("Sonatype Blog",                   "https://www.sonatype.com/blog/rss.xml"),
    ("Varonis Blog",                    "https://www.varonis.com/blog/rss.xml"),
    ("Silverfort Blog",                 "https://www.silverfort.com/blog/feed/"),
    ("KnowBe4 Blog",                    "https://blog.knowbe4.com/rss.xml"),
    ("Cofense Blog",                    "https://cofense.com/feed/"),
    ("Cato Networks Blog",              "https://www.catonetworks.com/blog/feed/"),
    ("Sophos Blogs",                    "https://www.sophos.com/en-us/blog/feed?id=blt6f15f4f7deaf4242"),
    ("Fortinet Blog",                   "https://feeds.fortinet.com/fortinet/blogs"),
    ("Cisco Newsroom",                  "https://newsroom.cisco.com/c/services/i/servlets/newsroom/rssfeed.json"),  # serves RSS despite the .json name
    ("Cloudflare Blog",                 "https://blog.cloudflare.com/rss/"),
    ("Tenable Cyber Exposure Alerts",   "https://www.tenable.com/blog/cyber-exposure-alerts/feed"),
    ("Tenable in the News",             "https://www.tenable.com/media/in-the-news/feed"),
    ("Tenable Product Security Advisories", "https://www.tenable.com/security/feed"),
    ("Trend Micro Media Coverage",      "https://newsroom.trendmicro.com/media-coverage?pagetemplate=rss"),
    ("Microsoft Official Blog",         "https://blogs.microsoft.com/feed/"),
    # ── Podcasts ─────────────────────────────────────────────────────────
    ("CyberWire Daily",         "https://rss.pdrl.fm/85df76/feeds.megaphone.fm/cyberwire-daily-podcast"),
    ("Darknet Diaries",         "https://feeds.megaphone.fm/darknetdiaries"),
    ("Talos Takes",             "https://rss.buzzsprout.com/2018149.rss"),
    ("Security Now",            "https://feeds.twit.tv/sn.xml"),
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
SOURCES_TEMPLATE   = "sources_template.html"
SOURCES_FILE       = os.path.join(DATA_DIR, "sources.html")
SOURCES_URL        = REPORT_URL + "archive/data/sources.html"
SOURCE_HEALTH_FILE = os.path.join(DATA_DIR, "source_health.json")
MOVERS_FILE        = os.path.join(DATA_DIR, "movers.json")
WATCHLIST_FILE     = "watchlist.json"
WATCH_ALERT_HOURS  = 9        # a watchlist match this recent goes in the e-mail (runs are 8 hours apart, plus start-up delay)
STALE_SOURCE_DAYS  = 14       # a feed with no new article for this long is flagged Stale
FEED_STATUS: dict = {}        # source name -> {"ok", "error", "items"} for this run (filled by fetch_feed)
LEGACY_FULLTEXT_CACHE = os.path.join(ARCHIVE_DIR, "_cache", "fulltext_cache.json")
FULLTEXT_BUDGET_S  = int(os.environ.get("FULLTEXT_BUDGET_S", "420"))  # stop starting new downloads after this many seconds
FULLTEXT_WORKERS   = 12
FULLTEXT_MAX_TRANSIENT = 10   # temporary failures (timeouts, 5xx, rate limits) are retried more often than hard failures
BROWSER_CONCURRENCY = 3
BROWSER_BUDGET_S   = int(os.environ.get("BROWSER_BUDGET_S", "300"))  # time limit for the optional browser pass
FULLTEXT_MAX_ATTEMPTS = 3
FULLTEXT_MAX_CHARS = 60000
FEED_FULLTEXT_MIN  = 1500     # a feed body this long is treated as the whole article
MIN_FULLTEXT_CHARS = 200
CSV_CELL_LIMIT     = 32000    # Excel cannot hold more than 32,767 characters per cell
HISTORY_FILE = "history.json"
MAX_HISTORY  = 30
PHT          = timezone(timedelta(hours=8))

# Topic categories answer "what is this article about?"; vendors (VENDORS below) answer "who is it about?".
# The two are independent: an article has one of each. Priority order = insertion order, first match wins:
# Vulnerabilities > Business > Policy > Product & Roadmap > Attacks > fallback.
# A keyword starting with "~" only matches as a whole word ("~rce" does not match "source").
ACQUISITION_KEYWORDS = [
    "acqui", "acquisition", "acquired", "acquires",
    "merger", "merges with", "has merged",
    "bought", "buys", "purchase of", "to purchase", "asset purchase", "deal worth",
    "hostile takeover", "corporate takeover",
    "investment round", "investor", "investing in",
    "funding round", "series a", "series b", "series c", "seed round", "raises $", "raised $", "secures $",
    "funding", "valuation", "~ipo", "goes public", "go private", "take-private", "private equity", "spin-off", "divest",
]

# Generic announcement verbs: only trusted when the title has no threat vocabulary ("Mustang Panda Adds Rootkit" is an attack).
PRODUCT_VERBS = [
    "launches", "unveils", "introduces", "introducing", "debuts", "announces", "rolls out", "rolling out",
    "adds support", "now supports", "enhances", "unifies", "~expands", "~adds", "~extends", "now protects", "now offers", "now includes",
]

CATEGORIES = {
    "Vulnerabilities & Patching": [
        "zero-day", "zero day", "0-day", "0day",
        "exploit", "exploited", "exploitation",
        "remote code execution", "~rce", "arbitrary code",
        "cve-", "~nvd", "cvss", "known exploited", "~kev", "patch tuesday", "out-of-band patch",
        "unpatched", "proof of concept", "proof-of-concept", "~poc",
        "privilege escalation", "sql injection", "command injection", "code injection", "buffer overflow",
        "use-after-free", "heap overflow", "out-of-bounds", "memory corruption", "authentication bypass", "auth bypass",
        "path traversal", "cross-site scripting", "~xss", "~csrf", "deserialization",
        "vulnerab", "flaw", "security update", "security patch", "security advisory", "hotfix",
        "~patch", "~patches", "~patched", "~patching", "~bug", "~bugs", "bug bounty", "pwn2own",
        "bypass", "sandbox escape", "cumulative update", "kb5", "secure boot",
    ],
    "Business & Industry News": [
        *ACQUISITION_KEYWORDS,
        "earnings", "quarterly results", "fiscal", "revenue", "layoffs", "lays off", "job cuts", "restructuring",
        "appoints", "names new", "new ceo", "new cto", "new ciso", "new chief", "steps down", "resigns", "joins as", "promoted to",
        "partnership", "partners with", "~teams up", "strategic alliance",
        "magic quadrant", "forrester wave", "named a leader", "named leader", "idc marketscape", "market share", "market guide",
        "wins award", "awards", "exits stealth", "emerges from stealth", "out of stealth", "launches with $", "m&a", "deals announced",
        "as chief", "as ciso", "as cto", "as ceo", "appointed", "~hires", "~hired",
    ],
    "Policy, Legal & Compliance": [
        "regulat", "compliance", "gdpr", "hipaa", "ccpa", "cpra", "pci dss", "pci-dss", "~sox", "iso 27001", "soc 2",
        "~nist", "cmmc", "fedramp", "nis2", "nis 2", "~dora", "cyber resilience act", "ai act",
        "privacy law", "privacy act", "privacy regulation", "privacy commissioner", "data protection authority", "data protection commission",
        "information commissioner", "~ico", "~ftc", "~sec", "securities and exchange",
        "~doj", "department of justice", "justice department", "~fbi", "europol", "interpol", "law enforcement",
        "arrest", "indict", "~charged", "~charges", "sentenced", "convicted", "pleads guilty", "pleaded guilty", "extradit", "prosecut",
        "lawsuit", "~sues", "~sued", "class action", "class-action", "~court", "~judge", "settlement", "~settles",
        "~fined", "~fines", "penalty", "penalties", "sanction", "ofac",
        "legislation", "lawmakers", "~senate", "~congress", "executive order", "new bill", "senate bill", "house bill", "bill would",
        "parliament", "european commission", "export controls", "~banned", "policymakers", "white house",
        "takedown", "seized", "seizure", "dismantle", "operation endgame",
        "online safety act", "chat control",
        "guidance", "~mandate", "~mandates", "directive", "~cisa", "~ncsc", "~nsa", "~eu", "european union", "pentagon",
        "national security", "~nato", "antitrust", "~appeal", "eu fine",
    ],
    "Product & Roadmap": [
        "roadmap", "road map", "coming soon", "public preview", "private preview", "~beta", "early access",
        "retire", "deprecat", "sunset", "end of support", "end-of-support", "end-of-life", "~eol", "later this year", "will begin", "to begin",
        "general availability", "generally available", "now available", "~ga",
        *PRODUCT_VERBS,
        "new feature", "new features", "new capabilities", "release notes", "what's new", "integrates with", "~integration",
    ],
    "Attacks, Breaches & Threat Intel": [
        "ransomware", "ransom", "breach", "data leak", "leak", "hack", "attack", "malware", "phishing", "spearphish", "smishing", "vishing",
        "botnet", "backdoor", "trojan", "spyware", "stalkerware", "infostealer", "stealer", "~rat", "rootkit", "wiper", "~worm",
        "ddos", "denial of service", "supply chain", "supply-chain",
        "threat actor", "threat group", "threat intel", "threat report", "threat landscape", "threat research",
        "state-sponsored", "nation-state", "nation state", "hacktivist", "~apt",
        "apt28", "apt29", "apt41", "apt42", "apt37", "apt36", "apt10", "lazarus", "kimsuky", "sandworm", "turla",
        "typhoon", "blizzard", "sandstorm", "scattered spider", "lockbit", "shinyhunters", "lapsus",
        "cyberattack", "cybercrime", "cybercriminal", "cyber crime", "~campaign", "~campaigns",
        "~targets", "~targeting", "compromise", "stolen", "~steal", "~steals", "stealing", "theft", "heist", "extortion",
        "scam", "fraud", "impersonat", "deepfake", "espionage", "~spy", "~spies", "exfiltrat",
        "credential", "account takeover", "hijack", "dark web", "darknet", "access broker", "~c2", "command-and-control",
        "~ioc", "~iocs", "indicators of compromise", "~ttps", "mitre att&ck", "attack chain", "kill chain",
        "~incident", "~incidents", "malicious", "~rogue", "typosquat", "poisoned", "trojanized", "weaponiz", "~abused", "~abuses",
        "insider threat", "social engineering", "~fake", "harvest", "~targeted", "~exposed", "skimmer", "magecart", "drainer", "sim swap", "swatting", "cyberwar",
    ],
}

# Threat-research feeds, investor-relations feeds and advisory feeds say what an article is even when the title does not.
SOURCE_CATEGORY = {
    "Talos Intelligence": "Attacks, Breaches & Threat Intel", "Palo Alto Unit 42": "Attacks, Breaches & Threat Intel",
    "Google Threat Intel (Mandiant)": "Attacks, Breaches & Threat Intel", "Securelist (Kaspersky)": "Attacks, Breaches & Threat Intel",
    "SentinelLabs": "Attacks, Breaches & Threat Intel", "Check Point Research": "Attacks, Breaches & Threat Intel",
    "Fortinet Threat Research": "Attacks, Breaches & Threat Intel", "Trend Micro Research": "Attacks, Breaches & Threat Intel",
    "Zscaler ThreatLabz": "Attacks, Breaches & Threat Intel", "Sophos News - Threat Research": "Attacks, Breaches & Threat Intel",
    "ESET WeLiveSecurity": "Attacks, Breaches & Threat Intel", "Elastic Security Labs": "Attacks, Breaches & Threat Intel",
    "Datadog Security Labs": "Attacks, Breaches & Threat Intel", "Malwarebytes Labs": "Attacks, Breaches & Threat Intel",
    "Cyble": "Attacks, Breaches & Threat Intel", "Databreaches.net": "Attacks, Breaches & Threat Intel",
    "Recorded Future": "Attacks, Breaches & Threat Intel", "VirusTotal Blog": "Attacks, Breaches & Threat Intel",
    "CrowdStrike IR News": "Business & Industry News", "Fortinet IR News": "Business & Industry News",
    "Palo Alto IR News": "Business & Industry News", "Qualys IR News": "Business & Industry News",
    "Trend Micro Newsroom": "Business & Industry News",
    "CISA Advisories": "Vulnerabilities & Patching", "Exploit-DB": "Vulnerabilities & Patching",
    "ZDI Published Advisories": "Vulnerabilities & Patching", "Zero Day Initiative Blog": "Vulnerabilities & Patching",
    "Tenable Product Security Advisories": "Vulnerabilities & Patching",
    "CIRCL KEV (exploited CVEs)": "Vulnerabilities & Patching", "Google Project Zero": "Vulnerabilities & Patching",
}
FALLBACK_CATEGORY = "General Security News"

NO_VENDOR = "No Specific Vendor"

# Vendors answer "who is this article about?" (first match wins, matched on the title). Articles from a vendor's own feed
# fall back to that vendor through SOURCE_VENDOR below.
VENDORS = {
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
        "~eset", "welivesecurity", "we live security", "nod32",
    ],
    "Bitdefender": [
        "bitdefender", "gravityzone",
    ],
    "Check Point": [
        "check point", "~checkpoint", "harmony endpoint",
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
        "~falco", "sysdig", "falcosecurity",
    ],
    "Okta": [
        "okta", "okta identity", "okta workforce",
    ],
    "CyberArk": [
        "cyberark", "~privileged access", "conjur",
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
        "tenable one", "~lumin",
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
    # A keyword starting with "~" must match as a whole word ("~armis" does not match "alarmist").
    "1Password": [
        "1password",
    ],
    "Akamai Technologies": [
        "akamai",
    ],
    "Armis": [
        "~armis",
    ],
    "Automox": [
        "automox",
    ],
    "Bitwarden": [
        "bitwarden",
    ],
    "Checkmarx": [
        "checkmarx",
    ],
    "Cloudflare": [
        "cloudflare",
    ],
    "Cohesity": [
        "cohesity",
    ],
    "F5": [
        "~f5", "big-ip", "f5 networks", "f5 distributed cloud",
    ],
    "Flashpoint": [
        "~flashpoint",
    ],
    "Forescout": [
        "forescout",
    ],
    "Juniper Networks": [
        "juniper networks", "~juniper", "junos",
    ],
    "Mimecast": [
        "mimecast",
    ],
    "Nozomi Networks": [
        "nozomi",
    ],
    "Ping Identity": [
        "ping identity", "pingidentity", "pingone", "pingfederate",
    ],
    "Splunk": [
        "splunk",
    ],
    "Varonis": [
        "varonis",
    ],
    "Veracode": [
        "veracode",
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

_XML_ILLEGAL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_XML_BARE_AMP = re.compile(r"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)")
_HTML_ENTITY = re.compile(r"&(nbsp|mdash|ndash|rsquo|lsquo|ldquo|rdquo|hellip|copy|reg|trade|bull|laquo|raquo);")


def _sanitize_xml(raw: bytes) -> bytes:
    """Repair common feed defects: control characters, bare '&', HTML-only entities."""
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"^\s*<\?xml[^>]*\?>", "", text)  # bytes are re-encoded as UTF-8 below
    text = _XML_ILLEGAL.sub("", text)
    text = _HTML_ENTITY.sub(lambda m: html.unescape(m.group(0)), text)
    text = _XML_BARE_AMP.sub("&amp;", text)
    return text.encode("utf-8")


def _item_link(item) -> str:
    """Episode URL. Some podcast feeds leave <link> empty, so fall back to the guid, then the audio file."""
    link = _text(item, "link")
    if link:
        return link
    guid = _text(item, "guid")
    if guid.startswith("http"):
        return guid
    for child in item:
        if isinstance(child.tag, str) and child.tag.endswith("}transcript"):
            m = re.match(r"^(https://www\.buzzsprout\.com/\d+/\d+)/transcript", child.get("url", ""))
            if m:
                return m.group(1)
    enclosure = item.find("enclosure")
    return enclosure.get("url", "") if enclosure is not None else ""


def fetch_feed(name: str, url: str) -> list[dict]:
    try:
        # Some sites (the investor-relations feeds) answer 403 to a request without an Accept header
        req = Request(url, headers={"User-Agent": "CyberCompetitiveDailyFeed/1.0",
                                    "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5"})
        with urlopen(req, timeout=FETCH_TIMEOUT) as resp:
            raw = resp.read()
    except (URLError, OSError) as exc:
        print(f"  [WARN] {name}: {exc}", file=sys.stderr)
        FEED_STATUS[name] = {"ok": False, "error": str(exc)[:160], "items": 0}
        return []

    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        try:
            root = ET.fromstring(_sanitize_xml(raw))
        except ET.ParseError as exc:
            print(f"  [WARN] {name}: XML parse error - {exc}", file=sys.stderr)
            FEED_STATUS[name] = {"ok": False, "error": ("XML parse error - " + str(exc))[:160], "items": 0}
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
                "link":  _item_link(item),
                "date":  _parse_date(
                    _text(item, "pubDate") or
                    _text(item, "{http://purl.org/dc/elements/1.1/}date")
                ),
                "context": "",
                "feed_text": _fragment_to_text(_raw_text(item, (
                    "{http://purl.org/rss/1.0/modules/content/}encoded",
                    "description"))),
            }
            enclosure = item.find("enclosure")
            if enclosure is not None and (enclosure.get("type", "").startswith("audio")
                                          or re.search(r"\.(mp3|m4a|aac|ogg)(\?|$)", enclosure.get("url", ""), re.I)):
                article["podcast"] = True
            transcripts = [(c.get("type", ""), c.get("url", "")) for c in item
                           if isinstance(c.tag, str) and c.tag.endswith("}transcript") and c.get("url")]
            if transcripts:
                transcripts.sort(key=lambda t: _TRANSCRIPT_PREFERENCE.index(t[0]) if t[0] in _TRANSCRIPT_PREFERENCE else 99)
                article["transcript_type"], article["transcript_url"] = transcripts[0]
                article["podcast"] = True
            articles.append(article)

    FEED_STATUS[name] = {"ok": True, "error": "", "items": len(articles)}
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


_TRANSIENT_HTTP = {429, 500, 502, 503, 504}
_BROWSER_ERRORS = {"HTTP 401", "HTTP 403", "HTTP 406", "HTTP 451", "ssl", "thin"}
LAST_TEXT_ERRORS: collections.Counter = collections.Counter()


def _classify_error(exc: Exception) -> str:
    """Short label for why a download failed: 'HTTP 403', 'timeout', 'ssl', 'connection', 'error'."""
    if isinstance(exc, HTTPError):
        return f"HTTP {exc.code}"
    reason = getattr(exc, "reason", exc)
    msg = str(reason).lower()
    if isinstance(exc, (socket.timeout, TimeoutError)) or isinstance(reason, (socket.timeout, TimeoutError)) or "timed out" in msg:
        return "timeout"
    if isinstance(reason, ssl.SSLCertVerificationError) or "certificate" in msg:
        return "ssl"
    if isinstance(exc, (ConnectionError, http.client.HTTPException)) or "reset" in msg or "refused" in msg:
        return "connection"
    return "error"


def _is_transient(error: str) -> bool:
    return error in ("timeout", "connection") or (error.startswith("HTTP ") and int(error[5:]) in _TRANSIENT_HTTP)


def fetch_page_text(url: str, timeout: int = 15) -> tuple[str, str]:
    """Download an article page. Returns (text, error); error is '' on success.

    Temporary failures (timeouts, 5xx, rate limits) get one more try after a short pause.
    """
    from urllib.parse import quote
    url = quote(url, safe=":/?&=%#+@,;~!*()'[]$")
    error = "error"
    for attempt in (1, 2):
        try:
            req = Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            })
            with urlopen(req, timeout=timeout) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                raw = resp.read(3_000_000)
            text = _html_to_text(raw.decode(charset, errors="replace"))
            if len(text) < MIN_FULLTEXT_CHARS:
                return "", "thin"
            return text[:FULLTEXT_MAX_CHARS], ""
        except Exception as exc:
            error = _classify_error(exc)
            if attempt == 1 and _is_transient(error):
                time.sleep(2)
                continue
            break
    print(f"  [DEBUG] Failed to fetch {url}: {error}", file=sys.stderr)
    return "", error


def fetch_full_text(url: str, timeout: int = 15) -> str:
    """Article body text, or '' on failure."""
    return fetch_page_text(url, timeout)[0]


def _browser_available() -> bool:
    import importlib.util
    return os.environ.get("USE_BROWSER", "auto") != "0" and importlib.util.find_spec("playwright") is not None


_CHALLENGE_RX = re.compile(r"just a moment|checking your browser|verify you are human|enable javascript and cookies|attention required", re.I)


def _browser_fetch(items: list, deadline: float) -> dict:
    """Load pages in headless Chromium (Playwright). items: [(key, url)] -> {key: (text, error)}.

    A plain browser: it does not solve CAPTCHAs or hide that it is automated, so pages that
    show a challenge are reported as 'challenge' and left without text.
    """
    import asyncio
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {}

    async def run():
        results = {}
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            context = await browser.new_context(ignore_https_errors=True, locale="en-US")
            gate = asyncio.Semaphore(BROWSER_CONCURRENCY)

            async def one(key, url):
                async with gate:
                    if time.monotonic() > deadline:
                        return
                    page = await context.new_page()
                    try:
                        resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                        await page.wait_for_timeout(1500)
                        text = _html_to_text(await page.content())
                        status = resp.status if resp else 0
                        if _CHALLENGE_RX.search(text[:600]):
                            results[key] = ("", "challenge")
                        elif status >= 400 and len(text) < 600:
                            results[key] = ("", f"browser HTTP {status}")
                        elif len(text) < MIN_FULLTEXT_CHARS:
                            results[key] = ("", "thin")
                        else:
                            results[key] = (text[:FULLTEXT_MAX_CHARS], "")
                    except Exception as exc:
                        results[key] = ("", "browser " + type(exc).__name__)
                    finally:
                        await page.close()

            await asyncio.gather(*(one(k, u) for k, u in items))
            await context.close()
            await browser.close()
        return results

    try:
        return asyncio.run(run())
    except Exception as exc:
        print(f"  [WARN] browser fallback unavailable: {exc}", file=sys.stderr)
        return {}


_TRACKING_PARAM = re.compile(r"^(utm_.*|fbclid|gclid|mc_cid|mc_eid|igshid|ref_src)$", re.I)


def normalize_url(url: str) -> str:
    """Canonical form of an article URL: no scheme, 'www.', fragment, tracking params or trailing slash."""
    parts = urlsplit((url or "").strip())
    host = re.sub(r":(80|443)$", "", parts.netloc.lower())
    if host.startswith("www."):
        host = host[4:]
    path = parts.path or "/"
    if len(path) > 1:
        path = path.rstrip("/") or "/"
    query = sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not _TRACKING_PARAM.match(k))
    return host + path + ("?" + urlencode(query) if query else "")


def article_id(url: str) -> str:
    """Stable 12-character article ID: the same article URL always yields the same ID."""
    return hashlib.sha256(normalize_url(url).encode("utf-8")).hexdigest()[:12]


def _month_key(date_iso) -> str:
    return date_iso[:7] if date_iso else "undated"


def load_fulltext_cache() -> dict:
    """Merge every monthly shard (plus the legacy single-file cache) into {article_id: entry}.

    Older files were keyed by URL; those keys are converted to article IDs here.
    """
    cache: dict = {}
    paths = []
    if os.path.isdir(FULLTEXT_DIR):
        paths += [os.path.join(FULLTEXT_DIR, f) for f in sorted(os.listdir(FULLTEXT_DIR)) if f.endswith(".json")]
    if os.path.exists(LEGACY_FULLTEXT_CACHE):
        paths.append(LEGACY_FULLTEXT_CACHE)
    for path in paths:
        try:
            with open(path, encoding="utf-8") as f:
                shard = json.load(f)
        except (OSError, ValueError):
            continue
        for key, entry in shard.items():
            if key.startswith(("http://", "https://")):
                key = article_id(key)
            if key not in cache or (entry.get("text") and not cache[key].get("text")):
                cache[key] = entry
    return cache


def save_fulltext_cache(cache: dict, months: dict) -> None:
    """Write {article_id: entry} back as one file per month; months maps article_id -> 'YYYY-MM'."""
    shards: dict = {}
    for key, entry in cache.items():
        if key in months:
            shards.setdefault(months[key], {})[key] = entry
    os.makedirs(FULLTEXT_DIR, exist_ok=True)
    for month, entries in shards.items():
        with open(os.path.join(FULLTEXT_DIR, month + ".json"), "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False)
    if os.path.exists(LEGACY_FULLTEXT_CACHE):
        os.remove(LEGACY_FULLTEXT_CACHE)


def _is_stale(entry: dict) -> bool:
    if entry.get("source") in ("backup", "feed-excerpt"):
        return True  # partial text: try to replace with the real page text
    return entry.get("source") == "page" and entry.get("v", 1) < EXTRACT_VERSION


TRANSCRIPT_MAX_ATTEMPTS = 14  # transcripts often appear days after an episode, so they get their own, larger budget


def _wants_transcript(a: dict, entry: dict) -> bool:
    return (bool(a.get("podcast")) and entry.get("source") != "transcript"
            and entry.get("tattempts", 0) < TRANSCRIPT_MAX_ATTEMPTS and bool(transcript_url_for(a)[0]))


def attach_full_text(articles: list[dict]) -> int:
    """Set article['full_text'], reusing the on-disk cache and fetching what is missing.

    Order of preference: a long body already in the feed item, then the article page,
    then (if Playwright is installed) the page loaded in a headless browser, then a short
    feed body as a last resort. Newest articles go first within a time budget. Hard failures
    (403, SSL, empty page) use up one of FULLTEXT_MAX_ATTEMPTS; temporary ones (timeouts,
    5xx, rate limits) are counted separately and retried far more often.
    Returns the number of texts obtained this run.
    """
    cache = load_fulltext_cache()
    LAST_TEXT_ERRORS.clear()
    pending = [
        a for a in articles
        if a.get("link") and (
            (cache.get(a["id"], {}).get("attempts", 0) < FULLTEXT_MAX_ATTEMPTS
             and cache.get(a["id"], {}).get("transient", 0) < FULLTEXT_MAX_TRANSIENT
             and (not cache.get(a["id"], {}).get("text") or _is_stale(cache[a["id"]])))
            or _wants_transcript(a, cache.get(a["id"], {})))
    ]
    by_key = {a["id"]: a for a in pending}
    deadline = time.monotonic() + FULLTEXT_BUDGET_S

    def work(article):
        key, feed_text = article["id"], article.get("feed_text", "")
        if article.get("podcast"):
            url, hint = transcript_url_for(article)
            if url:
                transcript, _ = fetch_transcript(url, hint)
                if transcript:
                    return key, transcript, "transcript", ""
        if len(feed_text) >= FEED_FULLTEXT_MIN:
            return key, feed_text[:FULLTEXT_MAX_CHARS], "feed", ""
        if time.monotonic() > deadline:
            return key, None, "", ""
        page_text, error = fetch_page_text(article["link"])
        if page_text:
            return key, page_text, "page", ""
        if len(feed_text) >= MIN_FULLTEXT_CHARS:
            return key, feed_text[:FULLTEXT_MAX_CHARS], "feed-excerpt", error
        return key, "", "", error

    obtained, browser_queue = 0, []
    if pending:
        print(f"  Collecting full text for {len(pending)} article(s)...", file=sys.stderr)
        with ThreadPoolExecutor(max_workers=FULLTEXT_WORKERS) as pool:
            for key, text, source, error in pool.map(work, pending):
                if text is None:
                    continue
                entry = cache.setdefault(key, {"text": "", "attempts": 0})
                if _wants_transcript(by_key[key], entry):
                    entry["tattempts"] = entry.get("tattempts", 0) + 1
                if not text and _is_transient(error):
                    entry["transient"] = entry.get("transient", 0) + 1
                elif entry.get("attempts", 0) < FULLTEXT_MAX_ATTEMPTS:
                    entry["attempts"] = entry.get("attempts", 0) + 1
                if text:
                    entry["text"] = text
                    entry["v"] = EXTRACT_VERSION
                    entry["source"] = source
                    entry["fetched"] = datetime.now(timezone.utc).isoformat()
                    obtained += 1
                if error:
                    entry["error"] = error
                    LAST_TEXT_ERRORS[error] += 1
                    if error in _BROWSER_ERRORS:
                        browser_queue.append(key)
                else:
                    entry.pop("error", None)

    if browser_queue and _browser_available():
        links = {a["id"]: a["link"] for a in pending}
        print(f"  Retrying {len(browser_queue)} blocked article(s) in a headless browser...", file=sys.stderr)
        for key, (text, error) in _browser_fetch([(k, links[k]) for k in browser_queue], time.monotonic() + BROWSER_BUDGET_S).items():
            entry = cache[key]
            if text:
                entry.update(text=text, v=EXTRACT_VERSION, source="browser", fetched=datetime.now(timezone.utc).isoformat())
                entry.pop("error", None)
                LAST_TEXT_ERRORS["recovered by browser"] += 1
                obtained += 1
            elif error:
                entry["error"] = error

    months = {a["id"]: _month_key(a.get("date")) for a in articles if a.get("link")}
    save_fulltext_cache(cache, months)

    for a in articles:
        a["full_text"] = _trim_trailer(cache.get(a["id"], {}).get("text", ""))
        a.pop("feed_text", None)
        kind = cache.get(a["id"], {}).get("source", "")
        if kind != "transcript" and a.get("podcast") and _EMBEDDED_TRANSCRIPT_RX.search(a["full_text"]):
            kind = "transcript"  # the episode page itself carries the transcript
        a["text_source"] = kind
    return obtained


_CONTEXT_KEYWORDS = {
    "announced", "partnership", "acquired", "released", "vulnerability",
    "discovered", "found", "exploit", "threat", "malware", "attack",
    "detection", "capability", "feature", "certification", "award",
    "collaboration", "integration", "supported", "available", "launch",
    "first", "only", "breakthrough", "critical", "severe", "zero-day"
}

# ---- podcasts ---------------------------------------------------------------------------------------
_PODCAST_SOURCES = {"CyberWire Daily", "Security Now", "Risky Business News", "Darknet Diaries", "Talos Takes"}
_PODCAST_TITLE_RX = re.compile(r"^\s*ISC Stormcast\b|\bpodcast\s*#?\d+\b|^\s*podcast\s*:|^\s*SN\s?\d{3,4}\s*:", re.I)
_PODCAST_LINK_RX = re.compile(r"/podcastdetail/|twit\.tv/shows/|thecyberwire\.com/podcasts/", re.I)
_TRANSCRIPT_PREFERENCE = ("text/plain", "text/html", "application/srt", "text/srt", "text/vtt", "application/json")
TRANSCRIPT_MAX_CHARS = 150000
_EMBEDDED_TRANSCRIPT_RX = re.compile(r"Show full transcript|This transcript was generated automatically[^\n]*", re.I)


def is_podcast(a: dict) -> bool:
    """True for podcast episodes: flagged by the feed (audio file), a known podcast source, or an episode-style title/link."""
    return bool(a.get("podcast")) or a.get("source") in _PODCAST_SOURCES \
        or bool(_PODCAST_TITLE_RX.search(a.get("title", ""))) or bool(_PODCAST_LINK_RX.search(a.get("link", "")))


_STORMCAST_TITLE_RX = re.compile(r"^(.*?)\s+https?://isc\.sans\.edu/podcastdetail/(\d+),?\s*(\([^)]*\))?\s*$")


def tidy_podcast_title(entry: dict) -> None:
    """SANS Stormcast titles end with the episode URL and date; keep the transcript link, drop the clutter."""
    m = _STORMCAST_TITLE_RX.match(entry.get("title", ""))
    if m:
        entry["transcript_url"] = f"https://isc.sans.edu/podcasttranscript.html?id={m.group(2)}"
        entry["transcript_type"] = "text/plain"
        entry["title"] = m.group(1).strip()


def transcript_url_for(a: dict) -> tuple[str, str]:
    """(url, type) of a published transcript for an episode, or ('', '')."""
    if a.get("transcript_url"):
        return a["transcript_url"], a.get("transcript_type", "")
    title, link = a.get("title", ""), a.get("link", "")
    m = re.search(r"isc\.sans\.edu/podcastdetail/(\d+)", title + " " + link)
    if m:
        return f"https://isc.sans.edu/podcasttranscript.html?id={m.group(1)}", "text/plain"
    m = re.match(r"\s*SN\s?(\d{3,4})\b", title) or re.search(r"twit\.tv/shows/security-now/episodes/(\d+)", link)
    if m:
        return f"https://www.grc.com/sn/sn-{m.group(1)}.txt", "text/plain"
    if re.search(r"thecyberwire\.com/podcasts/[^/]+/\d+/notes", link):
        return link.replace("/notes", "/transcript"), "text/html"
    return "", ""


def parse_transcript(raw: str, hint: str = "") -> str:
    """Plain text of a transcript delivered as WebVTT, SRT, Podcasting 2.0 JSON, HTML or plain text."""
    t = raw.lstrip("\ufeff")
    head = t[:400].lstrip()
    if head.startswith("WEBVTT") or "-->" in t[:600]:
        lines = []
        for line in t.splitlines():
            line = line.strip()
            if not line or line == "WEBVTT" or "-->" in line or re.fullmatch(r"\d+", line) or line.startswith(("NOTE", "STYLE", "Kind:", "Language:")):
                continue
            lines.append(re.sub(r"<[^>]+>", "", line))
        return " ".join(lines)
    if head.startswith(("{", "[")):
        try:
            data = json.loads(t)
        except ValueError:
            return ""
        segments = data.get("segments", []) if isinstance(data, dict) else data
        out, last = [], None
        for seg in segments:
            if not isinstance(seg, dict) or not seg.get("body"):
                continue
            speaker = seg.get("speaker") or ""
            out.append((f"{speaker}: " if speaker and speaker != last else "") + str(seg["body"]).strip())
            last = speaker
        return " ".join(out)
    if re.search(r"<(html|body|p|div)[\s>]", head, re.I) or hint == "text/html":
        return _html_to_text(t)
    paragraphs = re.split(r"\n\s*\n", t)
    return "\n\n".join(" ".join(line.strip() for line in p.splitlines() if line.strip()) for p in paragraphs if p.strip())


def fetch_transcript(url: str, hint: str = "") -> tuple[str, str]:
    """Download and parse a transcript. Returns (text, error)."""
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                                    "Accept": "text/plain,text/html,application/json,*/*;q=0.8"})
        with urlopen(req, timeout=20) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            raw = resp.read(6_000_000).decode(charset, errors="replace")
        text = parse_transcript(raw, hint)
    except Exception as exc:
        return "", _classify_error(exc)
    return (text[:TRANSCRIPT_MAX_CHARS], "") if len(text) >= 500 else ("", "thin")


_INLINE_SPEAKER_RX = re.compile(r"^[A-Z][A-Z .'\-]{1,30}:\s+")
_SPEAKER_TURN_RX = re.compile(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+){0,2}\s+\d{1,2}:\d{2}(?::\d{2})?(?=\s)")  # "Martin Lee 5:28"
_INLINE_TIMESTAMP_RX = re.compile(r"\s\d{1,2}:\d{2}(?::\d{2})?(?=\s)")
_SPEAKER_LINE_RX = re.compile(r"^[A-Z][A-Z .'\-]{2,40}:?$")
_HEADER_LINE_RX = re.compile(r"^(SERIES|EPISODE|DATE|TITLE|HOSTS?|SOURCE|ARCHIVE|DESCRIPTION|SPONSORS?|TRANSCRIPT)\s*:", re.I)
_TIMESTAMP_RX = re.compile(r"^\[?\(?\d{1,2}:\d{2}(:\d{2})?\)?\]?$")
_FILLER_RX = re.compile(r"^(hello|hi\b|hey\b|welcome|good (morning|afternoon|evening)|this is\b|you're listening|thanks for|thank you for|my name is|i'm your host)", re.I)


def podcast_context(text: str, limit: int = 320) -> str:
    """Up to two of the most informative sentences from a transcript (no greetings, speaker labels or timestamps)."""
    marker = _EMBEDDED_TRANSCRIPT_RX.search(text)
    if marker:
        text = text[marker.end():]
    lines = []
    for line in text.replace("\n\n", "\n").splitlines():
        line = line.strip()
        if not line or _SPEAKER_LINE_RX.match(line) or _HEADER_LINE_RX.match(line) or _TIMESTAMP_RX.match(line):
            continue
        lines.append(line)
    body = _INLINE_TIMESTAMP_RX.sub(" ", _SPEAKER_TURN_RX.sub(" ", " ".join(lines)))
    sentences = []
    for chunk in re.split(r"(?<=[.!?])\s+", body[:60000]):
        chunk = _INLINE_SPEAKER_RX.sub("", chunk.strip())
        if 40 <= len(chunk) <= 260 and not _FILLER_RX.match(chunk):
            sentences.append(chunk)
    scored = [(sum(1 for kw in _CONTEXT_KEYWORDS if kw in s_.lower()), -i, s_) for i, s_ in enumerate(sentences)]
    picked = sorted((x for x in scored if x[0] > 0), reverse=True)[:2] or [(0, -i, s_) for i, s_ in enumerate(sentences[:2])]
    picked.sort(key=lambda x: -x[1])  # back into reading order
    return shorten(" ".join(x[2] for x in picked), width=limit, placeholder="...") if picked else ""


def _extract_key_sentence(text: str, title: str = "") -> str:
    """Extract a key sentence from article text containing important context.

    Looks for sentences with keywords related to security findings, partnerships,
    or significant announcements. Returns a truncated sentence (up to 180 chars).
    """
    if not text:
        return ""

    keywords = _CONTEXT_KEYWORDS

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
    limit = MODULE_BODY_CHARS * 3 if article.get("text_source") == "transcript" else MODULE_BODY_CHARS
    body = " ".join((context + " " + article.get("full_text", "")[:limit]).split())
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
# Stories: articles about the same event are grouped, and the busiest ones are "trending"
# ---------------------------------------------------------------------------

STORY_WINDOW_DAYS = 7      # two articles can only belong to one story if published this close together
STORY_GAP_DAYS = 4         # a gap longer than this inside a group starts a new story
TRENDING_DAYS = 7
TRENDING_POOL = 9          # stories kept for the carousel (shown three at a time)
TRENDING_MIN_SOURCES = 3
_STORY_STOP = frozenset(
    "a an the and or for of in on at to is are was were be been have has had with from by as its not but this that over after new says said via how why "
    "what when who your you our their into out up down more most than can will may could would about against between during attack attacks flaw bug hackers "
    "hacker security cyber vulnerability vulnerabilities exploited exploit exploits patch patches update updates critical week weekly recap news podcast "
    "now just here there still also first one two three amid new using used use gets get got makes make made".split())
_STORY_ROUNDUP_RX = re.compile(
    r"week in review|weekly (recap|roundup|round-up|news|update)|week in (security|vulnerabilities)|a week in security|patch tuesday|newsletter|"
    r"in other news|news roundup|security news|this week in|upcoming speaking|friday squid|monthly (recap|roundup)|"
    r"bulletin|threatsday|digest|threat intelligence report|weekly|recap|round-?up|week in|this week|top stories|the week", re.I)
_STORY_TEMPLATED_SOURCES = {"Exploit-DB", "ZDI Published Advisories", "CISA Advisories", "CIRCL KEV (exploited CVEs)"}
_STORY_BRANDS = {
    "openai", "github", "wordpress", "powershell", "linkedin", "youtube", "chatgpt", "javascript", "typescript", "iphone", "whatsapp", "sharepoint",
    "onedrive", "microsoft", "android", "macos", "windows", "linux", "google", "apple", "amazon", "cloudflare", "telegram", "facebook", "instagram",
    "tiktok", "deepseek", "gemini", "copilot", "anthropic", "kubernetes", "docker", "bitcoin", "ethereum", "binance", "paypal", "salesforce",
    "servicenow", "oracle", "cisco", "vmware", "fortinet", "fortigate", "ivanti", "netscaler", "citrix", "sophos", "kaspersky", "bitdefender",
}
_STORY_EXPLOIT_RX = re.compile(r"actively exploited|exploited in the wild|zero-?day|0-day|known exploited|\bkev\b|emergency (patch|update)|under attack", re.I)
_STORY_CVE_RX = re.compile(r"CVE-\d{4}-\d{4,7}", re.I)


def _title_tokens(title: str) -> tuple[set, set]:
    """(significant lowercase words, coined names such as PHP2Shell or FortiBleed) of a title."""
    words, names = set(), set()
    for raw in re.findall(r"[A-Za-z0-9][A-Za-z0-9+#\-]*", title):
        w = raw.lower().strip("-")
        if len(w) < 3 or w.isdigit() or w in _STORY_STOP or _STORY_CVE_RX.fullmatch(raw):
            continue
        words.add(w)
        if len(w) >= 5 and "-" not in raw and ((re.search(r"[A-Za-z]", raw) and re.search(r"\d", raw)) or re.search(r"[a-z][A-Z]", raw)):
            names.add(w)
    return words, names


def assign_stories(entries: list[dict]) -> None:
    """Set entry['story'] (the ID of the story's earliest article). Never removes anything.

    Articles are linked when published within STORY_WINDOW_DAYS and they share a CVE ID, a coined
    name (e.g. PHP2Shell), or enough distinctive title words. Podcasts, roundups and templated
    advisory feeds (Exploit-DB, CISA, ZDI) only ever join a story through a shared CVE ID.
    """
    for e in entries:
        e["story"] = e["id"]
    items = []
    for e in entries:
        if not e.get("date") or e.get("podcast") or _STORY_ROUNDUP_RX.search(e["title"]):
            continue
        words, names = _title_tokens(e["title"])
        words -= set(re.findall(r"[a-z0-9]+", e["source"].lower()))
        items.append({"e": e, "dt": datetime.fromisoformat(e["date"]), "words": words, "names": names,
                      "cves": {c.upper() for c in _STORY_CVE_RX.findall(e["title"] + " " + e.get("context", ""))},
                      "templated": e["source"] in _STORY_TEMPLATED_SOURCES or e["source"].startswith("CISA")})
    df = collections.Counter(w for it in items for w in it["words"])
    brand_words = {t for kws in (*CATEGORIES.values(), *VENDORS.values()) for kw in kws for t in re.findall(r"[a-z0-9]+", kw.lower())} | _STORY_BRANDS
    for it in items:
        it["names"] = {n for n in it["names"] if n not in brand_words and df[n] <= 80}
    word_index, cve_index = collections.defaultdict(list), collections.defaultdict(list)
    for i, it in enumerate(items):
        for w in it["words"]:
            if df[w] <= 120:
                word_index[w].append(i)
        for c in it["cves"]:
            cve_index[c].append(i)
    parent = list(range(len(items)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, a in enumerate(items):
        candidates = set()
        for w in a["words"]:
            candidates.update(j for j in word_index.get(w, ()) if j > i)
        for c in a["cves"]:
            candidates.update(j for j in cve_index[c] if j > i)
        for j in candidates:
            b = items[j]
            if abs((a["dt"] - b["dt"]).days) > STORY_WINDOW_DAYS:
                continue
            linked = bool(a["cves"] & b["cves"])
            if not linked and not (a["templated"] or b["templated"]):
                shared = a["words"] & b["words"]
                union = a["words"] | b["words"]
                rare = [w for w in shared if df[w] <= 20 and w not in brand_words]
                linked = (bool(a["names"] & b["names"])
                          or (len(shared) / max(1, len(union)) >= 0.5)
                          or (len(rare) >= 2 and len(shared) / max(1, min(len(a["words"]), len(b["words"]))) >= 0.5))
            if linked:
                parent[find(i)] = find(j)
    groups = collections.defaultdict(list)
    for i, it in enumerate(items):
        groups[find(i)].append(it)
    for members in groups.values():
        members.sort(key=lambda m: (m["dt"], m["e"]["id"]))
        parts = [[members[0]]]
        for m in members[1:]:
            if (m["dt"] - parts[-1][-1]["dt"]).days > STORY_GAP_DAYS:
                parts.append([m])
            else:
                parts[-1].append(m)
        for part in parts:
            for m in part:
                m["e"]["story"] = part[0]["e"]["id"]


def trending_stories(entries: list[dict], now=None, days: int = TRENDING_DAYS, limit: int = TRENDING_POOL,
                     min_sources: int = TRENDING_MIN_SOURCES) -> list[dict]:
    """Stories covered by the most distinct sources in the last `days` days, best first."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    by_story = collections.defaultdict(list)
    for e in entries:
        by_story[e.get("story", e["id"])].append(e)
    ranked = []
    for sid, members in by_story.items():
        recent = [m for m in members if m.get("date") and not m.get("podcast") and datetime.fromisoformat(m["date"]) >= cutoff]
        sources = {m["source"] for m in recent}
        if len(sources) < min_sources:
            continue
        latest = max(datetime.fromisoformat(m["date"]) for m in recent)
        age_h = (now - latest).total_seconds() / 3600
        exploited = any(_STORY_EXPLOIT_RX.search(m["title"] + " " + m.get("context", "")) for m in recent)
        score = 2 * len(sources) + (3 if exploited else 0) + (2 if age_h <= 48 else 1 if age_h <= 96 else 0) + 0.2 * len(recent)
        recent.sort(key=lambda m: m["date"])
        lead = next((m for m in recent if m["source"] not in _STORY_TEMPLATED_SOURCES and not m["source"].startswith("CISA")), recent[0])
        mod_count = collections.Counter(x for m in recent for x in m.get("modules", []) if x not in (MODULE_OTHER, MODULE_NA))
        ranked.append({
            "id": sid, "title": lead["title"], "link": lead["link"], "source": lead["source"], "date": lead["date"],
            "context": lead.get("context", ""), "category": collections.Counter(m.get("category", "") for m in recent).most_common(1)[0][0],
            "vendor": next(iter(collections.Counter(m["vendor"] for m in recent if m.get("vendor")).most_common(1)), ("",))[0],
            "modules": [m for m, _ in mod_count.most_common(3)],
            # shown on the card and in the coverage popup, so both count the same articles (the score above uses the last `days` only)
            "sources": sorted({m["source"] for m in members}), "articles": len(members),
            "members": [{"id": m["id"], "story": m.get("story", m["id"]), "source": m["source"], "title": m["title"], "link": m["link"],
                         "date": m.get("date"), "context": (m.get("context") or "")[:300], "category": m.get("category", ""),
                         "vendor": m.get("vendor", ""), "modules": m.get("modules", []), "podcast": bool(m.get("podcast")),
                         "transcript": m.get("text_source") == "transcript"}
                        for m in sorted(members, key=lambda m: m.get("date") or "", reverse=True)],
            "recent_articles": len(recent), "latest": latest.isoformat(), "exploited": exploited, "score": round(score, 1),
        })
    ranked.sort(key=lambda t: (-t["score"], t["latest"]), reverse=False)
    return ranked[:limit]


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


def _absorb(master: dict, a: dict) -> None:
    """Add an article to the store; articles whose URLs normalise to one ID are merged."""
    key = article_id(a["link"])
    a["id"] = key
    old = master.get(key)
    if old is None:
        master[key] = a
        return
    if a.get("date") and (not old.get("date") or a["date"] < old["date"]):
        old["date"] = a["date"]
    for field in ("context", "category"):
        if not old.get(field) and a.get(field):
            old[field] = a[field]


def load_master() -> dict:
    """{article_id: article} from articles.json; backfilled from archive/*.html when missing."""
    master: dict = {}
    try:
        with open(ARTICLES_FILE, encoding="utf-8") as f:
            for a in json.load(f)["articles"]:
                _absorb(master, a)
        return master
    except (OSError, ValueError, KeyError):
        pass
    snapshots = sorted(f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".html")) if os.path.isdir(ARCHIVE_DIR) else []
    print(f"  Backfilling article store from {len(snapshots)} archive snapshot(s)...", file=sys.stderr)
    for name in snapshots:  # oldest first, so later snapshots refine earlier entries
        for a in parse_archive_html(os.path.join(ARCHIVE_DIR, name)):
            _absorb(master, a)
    return master


def merge_into_master(master: dict, live: list[dict]) -> None:
    """Add/refresh today's articles. Category is recomputed for live items only."""
    for a in live:
        link = a.get("link")
        if not link:
            continue
        key = article_id(link)
        entry = master.setdefault(key, {"id": key, "source": a["source"], "title": a["title"], "link": link,
                                        "date": a["date"].isoformat() if a["date"] else None, "context": ""})
        entry["category"] = categorize(a)
        entry["vendor"] = vendor_of(a)
        if a.get("context") and not entry.get("context"):
            entry["context"] = a["context"]
        if a.get("feed_text"):
            entry["feed_text"] = a["feed_text"]
        if a.get("podcast"):
            entry["podcast"] = True
        if a.get("transcript_url"):
            entry["transcript_url"], entry["transcript_type"] = a["transcript_url"], a.get("transcript_type", "")


def save_master(master: dict, label: str) -> None:
    items = sorted(master.values(), key=lambda a: a.get("date") or "", reverse=True)
    dated = [a for a in items if a.get("date")]
    items = dated + [a for a in items if not a.get("date")]
    slim = [{"id": a["id"], "source": a["source"], "category": a.get("category", ""), "vendor": a.get("vendor", ""), "title": a["title"],
             "link": a["link"], "date": a.get("date"), "context": a.get("context", ""),
             "modules": a.get("modules", []), "podcast": bool(a.get("podcast")),
             "story": a.get("story", a["id"]), "transcript": a.get("text_source") == "transcript",
             **({"transcript_url": a["transcript_url"], "transcript_type": a.get("transcript_type", "")} if a.get("transcript_url") else {})}
            for a in items]
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


def unique_by_url(articles: list[dict]) -> list[dict]:
    """One entry per article URL (the same URL as an article ID). Articles that cover the same story are all kept:
    assign_stories() groups them and the dashboard shows one card per story, so nothing is thrown away here."""
    seen: set[str] = set()
    unique: list[dict] = []
    for article in articles:
        key = article_id(article["link"]) if article.get("link") else ""
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        unique.append(article)
    return unique


_ACQ_EXCLUSIONS = {
    "scam", "fraud", "phishing", "ransomware", "malware", "attack",
    "tactic", "threat", "hack", "hacked", "breach", "breached", "exploit", "vulnerability",
    "stolen", "theft", "criminal", "gang", "arrest", "indicted",
    "leak", "leaked", "compromised", "extortion", "ransom", "victim", "cyberattack",
    "scams", "attacks", "attackers", "hackers", "breaches", "victims", "threats", "leaks", "criminals", "gangs", "arrests",
}
_THREAT_WORDS = {
    "malware", "rootkit", "backdoor", "ransomware", "botnet", "trojan", "phishing", "campaign", "campaigns", "attack", "attacks",
    "attackers", "hackers", "hacker", "apt", "actor", "actors", "spyware", "infostealer", "stealer", "wiper", "vulnerability",
    "vulnerabilities", "exploit", "exploited", "zero-day", "breach", "breaches", "hack", "hacked", "scam", "scams", "fraud",
    "leak", "leaked", "stolen", "targeting", "targets", "targeted", "espionage", "extortion",
}
# (keywords, words that cancel them): "Mustang Panda Adds Rootkit" is an attack, "Fake Merger & Acquisition Scams" is a scam.
_KEYWORD_GUARDS = [(set(ACQUISITION_KEYWORDS), _ACQ_EXCLUSIONS), (set(PRODUCT_VERBS), _THREAT_WORDS)]

# An article from a vendor's own blog or news feed that names no vendor in its title is filed under that vendor
# (vendor posts rarely name themselves in their titles).
SOURCE_VENDOR = {
    "Trend Micro Research": "Trend Micro", "Trend Micro SimplySecurity": "Trend Micro", "Trend Micro Newsroom": "Trend Micro",
    "CrowdStrike Blog": "CrowdStrike", "CrowdStrike IR News": "CrowdStrike",
    "Palo Alto Unit 42": "Palo Alto Networks", "Palo Alto IR News": "Palo Alto Networks",
    "Fortinet Threat Research": "Fortinet", "Fortinet IR News": "Fortinet",
    "Microsoft Security Blog": "Microsoft Security",
    "SentinelOne Blog": "SentinelOne", "SentinelLabs": "SentinelOne",
    "Rapid7 Blog": "Rapid7", "Tenable Blog": "Tenable", "Qualys Blog": "Qualys", "Qualys IR News": "Qualys",
    "Zscaler ThreatLabz": "Zscaler",
    "Kaspersky Blog": "Kaspersky", "Securelist (Kaspersky)": "Kaspersky",
    "Sophos Blogs": "Sophos", "Fortinet Blog": "Fortinet", "Cisco Newsroom": "Cisco Security", "Cloudflare Blog": "Cloudflare",
    "Tenable Cyber Exposure Alerts": "Tenable", "Tenable in the News": "Tenable", "Tenable Product Security Advisories": "Tenable",
    "Trend Micro Media Coverage": "Trend Micro",
    "ESET WeLiveSecurity": "ESET",
    "Check Point Blog": "Check Point", "Check Point Research": "Check Point",
    "Bitdefender Business Insights": "Bitdefender",
    "Cybereason Blog": "Cybereason",
    "Falco / Sysdig Blog": "Falco / Sysdig",
    "Wiz Blog": "Wiz", "Orca Security Blog": "Orca Security",
    "Darktrace Blog": "Darktrace", "Vectra AI Blog": "Vectra AI",
    "Proofpoint Blog": "Proofpoint",
    "Broadcom/Symantec Blog": "Broadcom / Symantec",
    "Okta Blog": "Okta", "CyberArk Blog": "CyberArk",
    "Elastic Security Labs": "Elastic Security",
    "Rubrik Blog": "Rubrik", "Arctic Wolf Blog": "Arctic Wolf", "Huntress Blog": "Huntress",
    "Aqua Security Blog": "Aqua Security", "Snyk Blog": "Snyk",
    "BeyondTrust Blog": "BeyondTrust", "Delinea Blog": "Delinea",
    "Cato Networks Blog": "Cato Networks",
    "Google Threat Intel (Mandiant)": "Mandiant",
    "Recorded Future": "Recorded Future",
    "Talos Intelligence": "Cisco Security", "Talos Takes": "Cisco Security",
    "Cloudflare Security": "Cloudflare", "Varonis Blog": "Varonis",
}


def _keyword_in(keyword: str, haystack: str) -> bool:
    if keyword.startswith("~"):
        return re.search(r"(?<![a-z0-9])" + re.escape(keyword[1:]) + r"(?![a-z0-9])", haystack) is not None
    return keyword in haystack


def _title_haystack(article: dict) -> str:
    """Lower-cased title. Feeds that publish URL slugs as titles ("us-seizes-x.html") are read as words."""
    title = article["title"].lower()
    if " " not in title.strip():
        title = re.sub(r"\.html?$", "", title).replace("-", " ").replace("_", " ")
    return title


def _title_words(haystack: str) -> set:
    # Tokenize the same way as _keywords so trailing punctuation (e.g. "breach;") doesn't defeat the guard check.
    return set(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", haystack))


def categorize(article: dict) -> str:
    """Return the first matching topic category (priority order = CATEGORIES insertion order)."""
    haystack = _title_haystack(article)
    words = _title_words(haystack)
    for cat, kws in CATEGORIES.items():
        for kw in kws:
            if not _keyword_in(kw, haystack):
                continue
            if any(kw in guarded and words & guard for guarded, guard in _KEYWORD_GUARDS):
                continue
            return cat
    return SOURCE_CATEGORY.get(article.get("source", ""), FALLBACK_CATEGORY)


def vendor_of(article: dict) -> str:
    """The vendor a title names (first match in VENDORS), else the vendor whose own feed it came from, else ''."""
    haystack = _title_haystack(article)
    for vendor, kws in VENDORS.items():
        if any(_keyword_in(kw, haystack) for kw in kws):
            return vendor
    return SOURCE_VENDOR.get(article.get("source", ""), "")


def is_acquisition(article: dict) -> bool:
    """M&A and funding news. The acquisition alert uses this because it cuts across the categories."""
    haystack = _title_haystack(article)
    return any(_keyword_in(kw, haystack) for kw in ACQUISITION_KEYWORDS) and not _title_words(haystack) & _ACQ_EXCLUSIONS


def bucket_articles(articles: list[dict], by: str = "category") -> dict[str, list[dict]]:
    """Group articles by topic category or by vendor, in dashboard order."""
    if by == "vendor":
        buckets: dict[str, list[dict]] = {name: [] for name in VENDOR_ORDER}
        key = lambda a: vendor_of(a) or NO_VENDOR
    else:
        buckets = {name: [] for name in CATEGORY_COLORS}
        key = categorize
    for a in articles:
        buckets.setdefault(key(a), []).append(a)
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
                "id": article_id(a["link"]),
                "story": a.get("story", article_id(a["link"])),
                "podcast": bool(a.get("podcast")),
                "vendor": vendor_of(a),
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
    writer.writerow(["ID", "Story", "Date", "Category", "Vendor", "Modules", "Type", "Source", "Title", "Link", "Context", "Full Text"])

    # Write articles
    buckets = bucket_articles(articles)
    for cat, items in buckets.items():
        for article in items:
            date_str = article["date"].strftime("%Y-%m-%d %H:%M UTC") if article["date"] else ""
            writer.writerow([
                article_id(article["link"]),
                article.get("story", article_id(article["link"])),
                date_str,
                cat,
                vendor_of(article),
                "; ".join(article.get("modules", [])),
                "Podcast" if article.get("podcast") else "Article",
                article["source"],
                article["title"],
                article["link"],
                article.get("context", ""),
                _csv_text(article.get("full_text", ""))
            ])

    return output.getvalue()


def export_by_group(articles: list[dict], label: str, by: str = "category") -> dict[str, tuple[str, str]]:
    """Export digest split by category or by vendor as separate CSV and JSON files.

    Returns dict mapping group names to (csv_content, json_content) tuples.
    """
    import io
    import csv as csv_module

    buckets = bucket_articles(articles, by)
    exports = {}

    for name, items in buckets.items():
        if not items:
            continue

        csv_output = io.StringIO()
        csv_writer = csv_module.writer(csv_output)
        csv_writer.writerow(["ID", "Story", "Date", "Category", "Vendor", "Source", "Modules", "Type", "Title", "Link", "Context", "Full Text"])
        for article in items:
            date_str = article["date"].strftime("%Y-%m-%d %H:%M UTC") if article["date"] else ""
            csv_writer.writerow([
                article_id(article["link"]),
                article.get("story", article_id(article["link"])),
                date_str,
                categorize(article),
                vendor_of(article),
                article["source"],
                "; ".join(article.get("modules", [])),
                "Podcast" if article.get("podcast") else "Article",
                article["title"],
                article["link"],
                article.get("context", ""),
                _csv_text(article.get("full_text", ""))
            ])
        csv_content = csv_output.getvalue()

        json_content = json.dumps({
            by: name,
            "generated": label,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "article_count": len(items),
            "articles": [
                {
                    "id": article_id(a["link"]),
                    "story": a.get("story", article_id(a["link"])),
                    "podcast": bool(a.get("podcast")),
                    "date": a["date"].isoformat() if a["date"] else None,
                    "category": categorize(a),
                    "vendor": vendor_of(a),
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

        exports[name] = (csv_content, json_content)

    return exports

# ---------------------------------------------------------------------------
# HTML report — Trend Micro branding + column layout + history dropdown
# ---------------------------------------------------------------------------

CATEGORY_COLORS = {
    "Vulnerabilities & Patching":          "#DA291C",  # red
    "Attacks, Breaches & Threat Intel":    "#e67e22",  # orange
    "Business & Industry News":            "#3498db",  # blue
    "Policy, Legal & Compliance":          "#8e6bd6",  # violet
    "Product & Roadmap":                   "#1abc9c",  # teal
    FALLBACK_CATEGORY:                     "#95a5a6",  # grey
}

VENDOR_COLORS = {
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
    "1Password":                           "#0572ec",
    "Akamai Technologies":                 "#0099cc",
    "Armis":                               "#d6336c",
    "Automox":                             "#f26522",
    "Bitwarden":                           "#175ddc",
    "Checkmarx":                           "#54b848",
    "Cloudflare":                          "#f6821f",
    "Cohesity":                            "#6cc24a",
    "F5":                                  "#e4002b",
    "Flashpoint":                          "#005eb8",
    "Forescout":                           "#ef4136",
    "Juniper Networks":                    "#84b135",
    "Mimecast":                            "#e8590c",
    "Nozomi Networks":                     "#00a3e0",
    "Ping Identity":                       "#b3282d",
    "Splunk":                              "#65a637",
    "Varonis":                             "#0d9bd7",
    "Veracode":                            "#00b0b9",
    NO_VENDOR:                            "#95a5a6",  # grey
}

# Every list shows vendors alphabetically, with "No Specific Vendor" first.
VENDOR_ORDER = [NO_VENDOR] + sorted((v for v in VENDOR_COLORS if v != NO_VENDOR), key=str.lower)


def _build_dropdown() -> str:
    """Filter bar shell and its script. Rows are regrouped in the browser (by category or by vendor);
    the group lists and colors come from window.CI_GROUPS / CI_COLORS, written by build_html()."""
    return """
  <div class="dropdown-bar">
    <div class="dropdown-group">
      <label>Rows by:</label>
      <div class="view-switch" role="group" aria-label="Group rows by">
        <button type="button" id="view-category" aria-pressed="true">Category</button>
        <button type="button" id="view-vendor" aria-pressed="false">Vendor</button>
      </div>
    </div>
    <div class="dropdown-group">
      <label for="category-select">Category:</label>
      <select id="category-select" onchange="filterByCategory(this.value);">
        <option value="">-- All categories --</option>
      </select>
    </div>
    <div class="dropdown-group">
      <label for="vendor-select">Vendor:</label>
      <select id="vendor-select" onchange="filterByVendor(this.value);">
        <option value="">-- All vendors --</option>
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
    const SHOWN = ':not(.hide-search):not(.hide-module):not(.hide-category):not(.hide-vendor):not(.hide-watch)';

    function store(key, value) {
      try { if (value) localStorage.setItem(key, value); else localStorage.removeItem(key); } catch (err) { /* storage blocked */ }
    }
    function stored(key) {
      try { return localStorage.getItem(key) || ''; } catch (err) { return ''; }
    }

    // Alphabetical, with "No Specific Vendor" first
    function sortNames(names) {
      const none = window.CI_NO_VENDOR;
      return names.slice().sort((a, b) => a === none ? -1 : b === none ? 1 : a.localeCompare(b, undefined, { sensitivity: 'base' }));
    }

    // Category and vendor filters: every tracked name is listed, with the number of cards on this page (0 when none)
    function fillGroupSelect(selectId, attr) {
      const counts = {};
      document.querySelectorAll('.card').forEach(card => {
        const k = card.dataset[attr];
        if (k) counts[k] = (counts[k] || 0) + 1;
      });
      const listed = (window.CI_GROUPS && window.CI_GROUPS[attr]) || [];
      const names = sortNames(listed.concat(Object.keys(counts).filter(k => listed.indexOf(k) === -1)));
      const sel = document.getElementById(selectId);
      names.forEach(name => {
        const opt = document.createElement('option');
        opt.value = name;
        opt.textContent = name + ' (' + (counts[name] || 0) + ')';
        sel.appendChild(opt);
      });
    }

    function populateFilters() {
      fillGroupSelect('category-select', 'category');
      fillGroupSelect('vendor-select', 'vendor');
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
      Object.keys(counts).sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' })).forEach(m => {
        const opt = document.createElement('option');
        opt.value = m;
        opt.textContent = m + ' (' + counts[m] + ')';
        sel.appendChild(opt);
      });
    }

    let groupOn = true;
    try { groupOn = localStorage.getItem('groupSameTopic') !== 'off'; } catch (err) { /* storage blocked */ }

    function applyGrouping() {
      const cards = document.querySelectorAll('.card');
      cards.forEach(c => {
        c.classList.remove('hide-group');
        const b = c.querySelector('.story-badge');
        if (b) b.hidden = true;
      });
      if (!groupOn) return;
      const visible = document.querySelectorAll('.card' + SHOWN);
      const perStory = {};
      visible.forEach(c => { const s = c.dataset.story; if (s) perStory[s] = (perStory[s] || 0) + 1; });
      document.querySelectorAll('.col').forEach(col => {
        const first = {};
        col.querySelectorAll('.card' + SHOWN).forEach(card => {
          const s = card.dataset.story;
          if (!s) return;
          if (first[s]) card.classList.add('hide-group'); else first[s] = card;
        });
        Object.keys(first).forEach(s => {
          const others = perStory[s] - 1, badge = first[s].querySelector('.story-badge');
          if (badge && others > 0) { badge.textContent = '+' + others + ' related'; badge.hidden = false; }
        });
      });
    }

    function initializeGrouping() {
      const btn = document.getElementById('group-toggle');
      if (!btn) return;
      function paint() {
        btn.setAttribute('aria-pressed', groupOn ? 'true' : 'false');
        btn.textContent = 'Group same topic: ' + (groupOn ? 'on' : 'off');
      }
      paint();
      btn.addEventListener('click', () => {
        groupOn = !groupOn;
        try { localStorage.setItem('groupSameTopic', groupOn ? 'on' : 'off'); } catch (err) { /* storage blocked */ }
        paint();
        updateRows();
      });
      updateRows();
    }

    function updateRows() {
      applyGrouping();
      document.querySelectorAll('.col').forEach(col => {
        const any = col.querySelector('.card' + SHOWN + ':not(.hide-group)') !== null;
        col.classList.toggle('search-hidden', !any);
      });
      refreshToggles();
    }

    function filterByModule(mod) {
      document.querySelectorAll('.card').forEach(card => {
        const mods = (card.dataset.modules || '').split('|');
        card.classList.toggle('hide-module', mod !== '' && mods.indexOf(mod) === -1);
      });
      updateRows();
    }

    function filterByCategory(category) {
      document.querySelectorAll('.card').forEach(card => {
        card.classList.toggle('hide-category', category !== '' && card.dataset.category !== category);
      });
      store('ciCategory', category);
      updateRows();
    }

    function filterByVendor(vendor) {
      document.querySelectorAll('.card').forEach(card => {
        card.classList.toggle('hide-vendor', vendor !== '' && card.dataset.vendor !== vendor);
      });
      store('ciVendor', vendor);
      updateRows();
    }

    // Restore saved filters (only if that option still exists)
    function restoreFilterPreference() {
      [['category-select', 'ciCategory', filterByCategory], ['vendor-select', 'ciVendor', filterByVendor]].forEach(item => {
        const sel = document.getElementById(item[0]), saved = stored(item[1]);
        if (!sel || !saved) return;
        if (Array.from(sel.options).some(o => o.value === saved)) {
          sel.value = saved;
          item[2](saved);
        }
      });
    }

    // Rows: one per category or one per vendor; the cards move between rows in the browser
    let viewBy = stored('ciViewBy') === 'vendor' ? 'vendor' : 'category';

    function buildRow(name, items) {
      const col = document.createElement('div');
      col.className = 'col';
      const head = document.createElement('div');
      head.className = 'col-header';
      head.style.borderLeft = '4px solid ' + ((window.CI_COLORS && window.CI_COLORS[name]) || '#95a5a6');
      const h2 = document.createElement('h2');
      h2.textContent = name;
      const count = document.createElement('span');
      count.className = 'count';
      count.textContent = items.length + ' article(s)';
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'col-toggle';
      btn.hidden = true;
      btn.textContent = 'Show all';
      head.appendChild(h2);
      head.appendChild(count);
      head.appendChild(btn);
      const body = document.createElement('div');
      body.className = 'col-body';
      items.forEach(card => body.appendChild(card));
      col.appendChild(head);
      col.appendChild(body);
      return col;
    }

    function regroup(mode) {
      viewBy = mode;
      const grid = document.querySelector('.grid');
      const cards = Array.from(document.querySelectorAll('.card'));
      cards.sort((a, b) => Number(b.dataset.ts || 0) - Number(a.dataset.ts || 0));
      const buckets = {};
      cards.forEach(card => {
        const k = card.dataset[mode] || '';
        (buckets[k] = buckets[k] || []).push(card);
      });
      const listed = (window.CI_GROUPS && window.CI_GROUPS[mode]) || [];
      const order = listed.filter(k => buckets[k]).concat(Object.keys(buckets).filter(k => listed.indexOf(k) === -1));
      grid.textContent = '';
      order.forEach(name => grid.appendChild(buildRow(name, buckets[name])));
      grid.classList.toggle('view-category', mode === 'category');
      grid.classList.toggle('view-vendor', mode === 'vendor');
      ['category', 'vendor'].forEach(m => {
        const b = document.getElementById('view-' + m);
        if (b) b.setAttribute('aria-pressed', m === mode ? 'true' : 'false');
      });
      store('ciViewBy', mode === 'vendor' ? 'vendor' : '');
      updateRows();
    }

    function initializeViewSwitch() {
      ['category', 'vendor'].forEach(m => {
        const b = document.getElementById('view-' + m);
        if (b) b.addEventListener('click', () => { if (viewBy !== m) regroup(m); });
      });
      if (viewBy !== 'category') regroup(viewBy);
    }

    // Watchlist: show only the cards that match watchlist.json
    function initializeWatch() {
      const btn = document.getElementById('watch-toggle');
      if (!btn) return;
      let on = stored('ciWatch') === '1';
      function apply() {
        btn.setAttribute('aria-pressed', on ? 'true' : 'false');
        document.querySelectorAll('.card').forEach(card => card.classList.toggle('hide-watch', on && card.dataset.watch !== '1'));
        updateRows();
      }
      btn.addEventListener('click', () => { on = !on; store('ciWatch', on ? '1' : ''); apply(); });
      if (on) apply();
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
        const totalVisible = document.querySelectorAll('.card' + SHOWN).length;
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
    function refreshToggles() {
      document.querySelectorAll('.col').forEach(col => {
        const body = col.querySelector('.col-body');
        const btn = col.querySelector('.col-toggle');
        if (!body || !btn) return;
        btn.hidden = !col.classList.contains('expanded') && body.scrollWidth <= body.clientWidth + 1;
      });
    }

    function initializeRowToggles() {
      const grid = document.querySelector('.grid');
      grid.addEventListener('click', e => {
        const btn = e.target.closest('.col-toggle');
        if (!btn) return;
        const open = btn.closest('.col').classList.toggle('expanded');
        btn.textContent = open ? 'Collapse' : 'Show all';
      });
      window.addEventListener('resize', refreshToggles);
      refreshToggles();
    }

    // Export: one option per category and per vendor, in both formats
    function initializeCategoryExports() {
      const exportSelect = document.getElementById('category-export-select');
      if (!exportSelect) return;
      [['category', 'By category'], ['vendor', 'By vendor']].forEach(kind => {
        const present = {};
        document.querySelectorAll('.card').forEach(card => { present[card.dataset[kind[0]]] = true; });
        const group = document.createElement('optgroup');
        group.label = kind[1];
        sortNames((window.CI_GROUPS && window.CI_GROUPS[kind[0]]) || []).forEach(name => {
          if (!present[name]) return;
          const safe = name.toLowerCase().replace(/[^a-z0-9_-]/g, '_');
          ['csv', 'json'].forEach(fmt => {
            const option = document.createElement('option');
            option.value = 'digest__' + kind[0] + '__' + safe + '.' + fmt;
            option.textContent = name + ' (' + fmt.toUpperCase() + ')';
            group.appendChild(option);
          });
        });
        exportSelect.appendChild(group);
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
      [populateFilters, populateModules, initializeCategoryExports, initializeSearch, initializeRowToggles, initializeViewSwitch, restoreFilterPreference, initializeWatch, initializeGrouping].forEach(fn => {
        try {
          fn();
        } catch (err) {
          console.error(fn.name + ' failed:', err);
        }
      });
    });
  </script>"""


def build_html(articles: list[dict], label: str, history: list[dict] | None = None, trending: list[dict] | None = None,
               watchlist: dict | None = None, movers: list[dict] | None = None) -> str:
    buckets  = bucket_articles(articles)
    columns  = []
    dropdown = _build_dropdown()
    wl = watchlist if watchlist is not None else load_watchlist()
    watching = bool(wl["vendors"] or wl["keywords"])
    n_watch = 0

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

            pod_badge = POD_BADGE_HTML if a.get("podcast") else ""
            modules = a.get("modules") or []
            modules_attr = html.escape("|".join(modules))
            shown = [m for m in modules if m not in (MODULE_OTHER, MODULE_NA)]
            modules_html = ""
            if shown:
                modules_html = '<div class="card-modules">' + " &middot; ".join(html.escape(m) for m in shown) + "</div>"

            vendor = vendor_of(a) or NO_VENDOR
            tags = [f'<span class="tag tag-category" style="background:{CATEGORY_COLORS.get(cat, "#555a70")}">{html.escape(cat)}</span>']
            if vendor != NO_VENDOR:
                tags.append(f'<span class="tag tag-vendor" style="background:{VENDOR_COLORS.get(vendor, "#555a70")}">{html.escape(vendor)}</span>')
            tags_html = '<div class="card-tags">' + "".join(tags) + "</div>"
            stamp = int(a["date"].timestamp()) if a["date"] else 0
            safe_cat, safe_vendor = html.escape(cat), html.escape(vendor)
            why = watch_reason(a, wl) if watching else ""
            n_watch += bool(why)
            watch_star = f'<span class="watch-star" title="Watchlist: {html.escape(why)}">&#9733;</span>' if why else ""

            cards.append(f"""
            <div class="card{" watched" if why else ""}" data-watch="{"1" if why else "0"}" data-id="{article_id(a["link"])}" data-category="{safe_cat}" data-vendor="{safe_vendor}" data-ts="{stamp}" data-modules="{modules_attr}" data-podcast="{"1" if a.get("podcast") else "0"}" data-transcript="{"1" if a.get("text_source") == "transcript" else "0"}" data-story="{a.get("story") or article_id(a["link"])}">
              <div class="card-meta">
                <span class="source">{pod_badge}{safe_source}{watch_star}</span>
                <span class="date">{date_str}<button type="button" class="story-badge" hidden></button><button type="button" class="card-details" aria-label="Details and export"></button></span>
              </div>
              <a class="card-title" href="{safe_link}" target="_blank">{safe_title}</a>
              {tags_html}
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

    dash_modal_js = (DASH_MODAL_JS.replace("__FULLTEXT_BASE__", REPORT_URL + "archive/data/fulltext/")
                     .replace("__EXPLORER_URL__", EXPLORER_URL)) + CAROUSEL_JS.replace(
        "__FULLTEXT_BASE_JS__", json.dumps(REPORT_URL + "archive/data/fulltext/"))
    trending_html = _trending_html(trending or [])
    movers_html = _movers_html(movers or [])
    watch_btn = (f'<button type="button" id="watch-toggle" class="export-btn explorer-link" aria-pressed="false" '
                 f'title="Show only articles that match watchlist.json">&#9733; Watchlist ({n_watch})</button>') if watching else ""
    globals_js = ("window.CI_GROUPS=" + json.dumps({"category": list(CATEGORY_COLORS), "vendor": VENDOR_ORDER})
                  + ";window.CI_COLORS=" + json.dumps({**CATEGORY_COLORS, **VENDOR_COLORS})
                  + ";window.CI_NO_VENDOR=" + json.dumps(NO_VENDOR)
                  + ";window.CI_STORIES=" + json.dumps({st["id"]: st["members"] for st in (trending or [])}).replace("</", "<\\/") + ";")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CI Overwatch — {label}</title>
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
  .filterbar {{
    padding: 18px 24px 0;
  }}
  .topbar-right {{
    display: flex;
    flex-direction: row;
    gap: 10px 14px;
    align-items: center;
    flex-wrap: wrap;
  }}
  @media (max-width: 640px) {{
    .filterbar {{ padding: 14px 16px 0; }}
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
  .card.hide-search, .card.hide-module, .card.hide-group, .card.hide-category, .card.hide-vendor, .card.hide-watch {{ display: none; }}
  .card-meta .source {{ min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .card-meta .date {{ display: inline-flex; align-items: center; white-space: nowrap; }}
  {MODAL_CSS}
  {DASH_EXTRA_CSS}
  {DASH_VIEW_CSS}
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
<script>{globals_js}</script>

<div class="topbar">
  <div class="topbar-left">
    <h1><span>CI</span> Overwatch</h1>
    <p>{label} &nbsp;·&nbsp; {len(articles)} article(s) in the last {LOOKBACK_HOURS // 24} day(s)</p>
  </div>
  <div class="topbar-links">
    <a class="back" href="{EXPLORER_URL}" title="Browse every stored article by period, category, vendor and module, then export">All articles &rarr;</a>
    <a class="back" href="{SOURCES_URL}" title="Which feeds work, which are failing or stale">Source health</a>
  </div>
</div>

{trending_html}
{movers_html}
<div class="filterbar">
  <div class="topbar-right">
    {dropdown}
    <div class="export-buttons">
      {watch_btn}
      <button type="button" id="group-toggle" class="export-btn explorer-link" aria-pressed="true" title="Show one card per story in each row, with a +N related badge">Group same topic: on</button>
      <a href="{REPORT_URL}archive/exports/digest.json" download="digest.json" class="export-btn export-json" title="Download all as JSON">⬇ JSON</a>
      <a href="{REPORT_URL}archive/exports/digest.csv" download="digest.csv" class="export-btn export-csv" title="Download all as CSV">⬇ CSV</a>
      <select id="category-export-select" class="export-btn" style="padding: 5px 10px; font-size: 0.75rem; cursor: pointer;">
        <option value="">⬇ By group</option>
      </select>
    </div>
    <div class="search-bar">
      <input type="text" id="search-input" placeholder="Search articles..." class="search-input">
      <button class="search-clear" id="search-clear" title="Clear search" style="display:none;">✕</button>
    </div>
  </div>
</div>

<div class="content">
  <div class="grid view-category">
    {"".join(columns)}
  </div>
</div>

<footer>Updated three times daily · about 6 AM, 2 PM &amp; 10 PM PHT · lukan47/RSS</footer>
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

POD_ICON_SVG = ('<svg class="pod-icon" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" '
                'd="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2z"/></svg>')
POD_BADGE_HTML = '<span class="pod-badge" title="Podcast">' + POD_ICON_SVG + '</span>'

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
  .am-id { font-family: Consolas, monospace; color: #6b7088; }
  .am-tags { display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 14px; }
  .am-tag { display: inline-flex; align-items: center; gap: 5px; font-size: .72rem; line-height: 1.5; border-radius: 999px;
            padding: 1px 10px; border: 1px solid #343850; color: #c9cbd6; background: #1b1e2d; }
  .am-tag.category, .am-tag.vendor { color: #fff; border-color: transparent; font-weight: 600; background: #555a70; }
  .am-tag.podcast { color: #ff8a80; border-color: #6b2a27; background: #2a1a1b; font-weight: 600; }
  .am-tag.transcript { color: #9fd3a8; border-color: #2c4a33; background: #17241b; }
  .am-tag.muted { color: #6b7088; font-style: italic; }
  #am-overlay { z-index: 1100; }
  .sm-list { list-style: none; display: flex; flex-direction: column; gap: 8px; margin-top: 4px; }
  .sm-item { background: #1e2030; border-radius: 6px; padding: 9px 12px; display: grid; grid-template-columns: 1fr auto; gap: 2px 10px; align-items: start; }
  .sm-row { grid-column: 1 / 2; font-size: .7rem; color: #8a8fa3; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
  .sm-src { color: #ff5a4d; font-weight: 600; }
  .sm-link { grid-column: 1 / 2; color: #d8d8d8; text-decoration: none; font-size: .84rem; line-height: 1.45; }
  .sm-link:hover, .sm-link:focus-visible { color: #fff; text-decoration: underline; outline: none; }
  .sm-details { grid-column: 2 / 3; grid-row: 1 / 3; align-self: center; background: transparent; color: #8a8fa3; border: 1px solid #2a2d3e; border-radius: 3px;
                padding: 2px 9px; font-size: .68rem; cursor: pointer; font-family: inherit; }
  .sm-details:hover, .sm-details:focus-visible { color: #fff; border-color: #DA291C; outline: none; }
  .pod-badge { display: inline-flex; vertical-align: -2px; margin-right: 5px; color: #ff5a4d; }
  .pod-icon { width: 12px; height: 12px; }
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
<div class="am-overlay" id="sm-overlay" hidden>
  <div class="am-dialog" id="sm-dialog" role="dialog" aria-modal="true" aria-labelledby="sm-title">
    <div class="am-head">
      <h2 class="am-title" id="sm-title"></h2>
      <button type="button" class="am-close" id="sm-close" aria-label="Close">&times;</button>
    </div>
    <div class="am-meta" id="sm-meta"></div>
    <div class="am-tags" id="sm-tags"></div>
    <div class="am-actions sm-actions">
      <button type="button" class="am-btn secondary" id="sm-json">&darr; JSON</button>
      <button type="button" class="am-btn secondary" id="sm-csv">&darr; CSV</button>
      <label class="am-chk"><input type="checkbox" id="sm-ft"> Include full article text</label>
    </div>
    <div class="am-status" id="sm-status" role="status" aria-live="polite"></div>
    <ul class="sm-list" id="sm-list"></ul>
  </div>
</div>
<div class="am-overlay" id="am-overlay" hidden>
  <div class="am-dialog" id="am-dialog" role="dialog" aria-modal="true" aria-labelledby="am-title">
    <div class="am-head">
      <h2 class="am-title" id="am-title"></h2>
      <button type="button" class="am-close" id="am-close" aria-label="Close">&times;</button>
    </div>
    <div class="am-meta" id="am-meta"></div>
    <div class="am-tags" id="am-tags"></div>
    <p class="am-ctx" id="am-ctx"></p>
    <div class="am-actions">
      <a class="am-btn" id="am-open" href="#" target="_blank" rel="noopener noreferrer">Open article &#8599;</a>
      <button type="button" class="am-btn secondary" id="am-json">&darr; JSON</button>
      <button type="button" class="am-btn secondary" id="am-csv">&darr; CSV</button>
      <button type="button" class="am-btn secondary" id="am-copy">Copy link</button>
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
  var el = { title: $('am-title'), meta: $('am-meta'), tags: $('am-tags'), ctx: $('am-ctx'), open: $('am-open'),
             ft: $('am-fulltext'), json: $('am-json'), csv: $('am-csv'), copy: $('am-copy'), status: $('am-status'),
             close: $('am-close'), dialog: $('am-dialog') };
  var CSV_CELL_LIMIT = 32000;
  var POD_ICON = '__POD_ICON__';
  var current = null, base = '', lastFocus = null, shards = {};

  function setStatus(msg, isError) { el.status.textContent = msg || ''; el.status.style.color = isError ? '#ff7b72' : ''; }

  function openModal(a, opts) {
    current = a; base = (opts && opts.fullTextBase) || '';
    el.title.textContent = a.title;
    el.meta.textContent = '';
    var src = document.createElement('span'); src.className = 'am-src'; src.textContent = a.source; el.meta.appendChild(src);
    var when = document.createElement('span');
    when.textContent = a.date ? a.date.slice(0, 16).replace('T', ' ') + ' UTC' : 'Date unknown';
    el.meta.appendChild(when);
    if (a.id) { var idEl = document.createElement('span'); idEl.className = 'am-id'; idEl.textContent = 'ID ' + a.id; el.meta.appendChild(idEl); }
    el.tags.textContent = '';
    function addTag(label, cls, icon) {
      var t = document.createElement('span'); t.className = 'am-tag ' + cls;
      if (icon) t.innerHTML = icon + ' ';
      t.appendChild(document.createTextNode(label));
      el.tags.appendChild(t);
      return t;
    }
    if (a.category) { var c = addTag(a.category, 'category'); if (a.color) c.style.background = a.color; }
    if (a.vendor) { var v = addTag(a.vendor, 'vendor'); if (a.vendorColor) v.style.background = a.vendorColor; }
    if (a.podcast) addTag('Podcast', 'podcast', POD_ICON);
    if (a.transcript) addTag('Transcript available', 'transcript');
    (a.modules || []).forEach(function (m) { addTag(m, m === 'Other/General' || m === 'N/A' ? 'muted' : ''); });
    el.tags.hidden = !el.tags.children.length;
    el.ctx.textContent = a.context || 'No summary was extracted for this article.';
    el.ctx.className = 'am-ctx' + (a.context ? '' : ' empty');
    el.open.href = a.link;
    el.copy.hidden = !a.shareUrl;
    el.ft.checked = false; setStatus('');
    el.json.disabled = el.csv.disabled = false;
    lastFocus = document.activeElement;
    overlay.hidden = false; document.body.classList.add('am-open');
    el.close.focus();
  }

  function closeModal() {
    if (overlay.hidden) return;
    overlay.hidden = true;
    var story = document.getElementById('sm-overlay');
    if (!story || story.hidden) document.body.classList.remove('am-open');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  async function savedText(a, root) {
    var month = a.date ? a.date.slice(0, 7) : 'undated';
    if (!shards[month]) {
      var res = await fetch((root !== undefined ? root : base) + month + '.json');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      shards[month] = await res.json();
    }
    var entry = shards[month][a.id] || shards[month][a.link];
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
    var rec = { id: current.id || '', story: current.story || '', date: current.date, category: current.category || '', vendor: current.vendor || '', modules: current.modules || [], source: current.source,
                podcast: !!current.podcast, title: current.title, link: current.link, context: current.context || '' };
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
        var head = ['ID', 'Story', 'Date', 'Category', 'Vendor', 'Modules', 'Type', 'Source', 'Title', 'Link', 'Context'].concat(withText ? ['Full Text'] : []);
        var cells = [rec.id, rec.story, rec.date ? rec.date.slice(0, 16).replace('T', ' ') + ' UTC' : '', rec.category, rec.vendor, rec.modules.join('; '), rec.podcast ? 'Podcast' : 'Article',
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
  el.copy.addEventListener('click', async function () {
    try { await navigator.clipboard.writeText(current.shareUrl); setStatus('Link copied.'); }
    catch (e) { setStatus('Could not copy automatically. Link: ' + current.shareUrl, true); }
  });
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
  window.ArticleModal = { open: openModal, close: closeModal, kit: { savedText: savedText, csvCell: csvCell, download: download, csvLimit: CSV_CELL_LIMIT } };
})();

(function () {
  'use strict';
  var overlay = document.getElementById('sm-overlay');
  if (!overlay) return;
  var $ = function (id) { return document.getElementById(id); };
  var el = { title: $('sm-title'), meta: $('sm-meta'), tags: $('sm-tags'), list: $('sm-list'), close: $('sm-close'), dialog: $('sm-dialog'),
             json: $('sm-json'), csv: $('sm-csv'), ft: $('sm-ft'), status: $('sm-status') };
  var opts = {}, lastFocus = null, shown = { id: '', title: '', members: [] };

  function setStatus(msg, isError) { el.status.textContent = msg || ''; el.status.style.color = isError ? '#ff7b72' : ''; }

  // Export every article in the story (newest first), optionally with the saved full text
  async function exportStory(fmt) {
    var kit = window.ArticleModal && window.ArticleModal.kit;
    if (!kit || !shown.members.length) return;
    var withText = el.ft.checked, list = shown.members, failed = 0, missing = 0, recs = [];
    el.json.disabled = el.csv.disabled = true;
    try {
      for (var i = 0; i < list.length; i++) {
        var m = list[i];
        var rec = { id: m.id || '', story: m.story || shown.id || '', date: m.date, category: m.category || '', vendor: m.vendor || '', modules: m.modules || [],
                    source: m.source, podcast: !!m.podcast, title: m.title, link: m.link, context: m.context || '' };
        if (withText) {
          setStatus('Loading saved article text ' + (i + 1) + ' of ' + list.length + '…');
          try { rec.full_text = await kit.savedText(m, opts.fullTextBase); } catch (e) { rec.full_text = ''; failed++; }
          if (!rec.full_text) missing++;
        }
        recs.push(rec);
      }
      var slug = (shown.title || 'story').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60) || 'story';
      if (fmt === 'json') {
        kit.download('story_' + slug + '.json', 'application/json',
                     JSON.stringify({ exported: new Date().toISOString(), story: { id: shown.id, title: shown.title }, count: recs.length, articles: recs }, null, 2));
      } else {
        var head = ['ID', 'Story', 'Date', 'Category', 'Vendor', 'Modules', 'Type', 'Source', 'Title', 'Link', 'Context'].concat(withText ? ['Full Text'] : []);
        var lines = [head.join(',')];
        recs.forEach(function (r) {
          var cells = [r.id, r.story, r.date ? r.date.slice(0, 16).replace('T', ' ') + ' UTC' : '', r.category, r.vendor, r.modules.join('; '), r.podcast ? 'Podcast' : 'Article',
                       r.source, r.title, r.link, r.context];
          if (withText) {
            var t = r.full_text;
            cells.push(t.length > kit.csvLimit ? t.slice(0, kit.csvLimit) + ' [truncated for CSV - use JSON for the full text]' : t);
          }
          lines.push(cells.map(kit.csvCell).join(','));
        });
        kit.download('story_' + slug + '.csv', 'text/csv;charset=utf-8', '﻿' + lines.join('\r\n') + '\r\n');
      }
      setStatus('Exported ' + recs.length + ' article' + (recs.length === 1 ? '' : 's') + ' as ' + fmt.toUpperCase() +
                (withText ? (failed ? ' (could not load saved text for some months)' : missing ? ' (' + missing + ' without saved text)' : ' with full text') : '') + '.', failed > 0);
    } catch (e) {
      setStatus('Export failed: ' + e.message, true);
    } finally {
      el.json.disabled = el.csv.disabled = false;
    }
  }

  function openStory(story, o) {
    opts = o || {};
    var members = (story.members || []).slice().sort(function (a, b) { return (b.date || '').localeCompare(a.date || ''); });
    shown = { id: story.id || '', title: story.title || (members[0] && members[0].title) || '', members: members };
    el.ft.checked = false; setStatus('');
    el.json.disabled = el.csv.disabled = !members.length;
    var sources = {};
    members.forEach(function (m) { sources[m.source] = 1; });
    var dated = members.filter(function (m) { return m.date; });
    el.title.textContent = story.title || (members[0] && members[0].title) || '';
    var bits = [members.length + ' article' + (members.length === 1 ? '' : 's') + ' from ' + Object.keys(sources).length + ' source' + (Object.keys(sources).length === 1 ? '' : 's')];
    if (dated.length) {
      var first = dated[dated.length - 1].date.slice(0, 10), last = dated[0].date.slice(0, 10);
      bits.push(first === last ? first : first + ' to ' + last);
    }
    el.meta.textContent = bits.join(' \u00b7 ');
    var counts = {};
    members.forEach(function (m) { (m.modules || []).forEach(function (x) { if (x !== 'Other/General' && x !== 'N/A') counts[x] = (counts[x] || 0) + 1; }); });
    el.tags.textContent = '';
    Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; }).slice(0, 4).forEach(function (x) {
      var t = document.createElement('span'); t.className = 'am-tag'; t.textContent = x; el.tags.appendChild(t);
    });
    el.tags.hidden = !el.tags.children.length;
    el.list.textContent = '';
    members.forEach(function (m) {
      var li = document.createElement('li'); li.className = 'sm-item';
      var row = document.createElement('div'); row.className = 'sm-row';
      var src = document.createElement('span'); src.className = 'sm-src'; src.textContent = m.source;
      var when = document.createElement('span'); when.textContent = m.date ? m.date.slice(0, 10) : 'date unknown';
      row.appendChild(src); row.appendChild(when);
      var link = document.createElement('a'); link.className = 'sm-link'; link.href = m.link; link.target = '_blank';
      link.rel = 'noopener noreferrer'; link.textContent = m.title;
      var btn = document.createElement('button'); btn.type = 'button'; btn.className = 'sm-details'; btn.textContent = 'Details';
      btn.addEventListener('click', function () { if (window.ArticleModal) window.ArticleModal.open(m, { fullTextBase: opts.fullTextBase }); });
      li.appendChild(row); li.appendChild(link); li.appendChild(btn); el.list.appendChild(li);
    });
    lastFocus = document.activeElement;
    overlay.hidden = false; document.body.classList.add('am-open');
    el.close.focus();
  }

  function closeStory() {
    if (overlay.hidden) return;
    overlay.hidden = true; document.body.classList.remove('am-open');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  el.close.addEventListener('click', closeStory);
  el.json.addEventListener('click', function () { exportStory('json'); });
  el.csv.addEventListener('click', function () { exportStory('csv'); });
  overlay.addEventListener('mousedown', function (e) { if (e.target === overlay) closeStory(); });
  document.addEventListener('keydown', function (e) {
    if (overlay.hidden || e.defaultPrevented) return;
    if (e.key === 'Escape') { e.preventDefault(); closeStory(); return; }
    if (e.key !== 'Tab') return;
    var f = Array.prototype.filter.call(el.dialog.querySelectorAll('a[href], button, input'), function (n) { return !n.disabled; });
    if (!f.length) return;
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });
  window.StoryModal = { open: openStory, close: closeStory };
})();
"""

MODAL_JS = MODAL_JS.replace("__POD_ICON__", POD_ICON_SVG)

DASH_MODAL_JS = r"""
function cardToArticle(card) {
  var title = card.querySelector('.card-title');
  var m = /^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) UTC$/.exec((card.querySelector('.date').textContent || '').trim());
  var ctx = card.querySelector('.card-context'), colors = window.CI_COLORS || {}, vendor = card.dataset.vendor || '';
  if (vendor === window.CI_NO_VENDOR) vendor = '';
  return {
    id: card.dataset.id || '',
    story: card.dataset.story || '',
    shareUrl: card.dataset.id ? '__EXPLORER_URL__#' + card.dataset.id : '',
    title: title.textContent.trim(),
    link: title.href,
    source: card.querySelector('.source').textContent.trim(),
    date: m ? m[1] + 'T' + m[2] + ':00+00:00' : null,
    category: card.dataset.category || '',
    color: colors[card.dataset.category] || '',
    vendor: vendor,
    vendorColor: colors[vendor] || '',
    modules: (card.dataset.modules || '').split('|').filter(Boolean),
    podcast: card.dataset.podcast === '1',
    transcript: card.dataset.transcript === '1',
    context: ctx ? ctx.textContent.trim() : ''
  };
}

function storyFromDom(id, title) {
  var members = Array.prototype.filter.call(document.querySelectorAll('.card'), function (c) { return c.dataset.story === id; }).map(cardToArticle);
  return { id: id, title: title || (members[0] && members[0].title) || '', members: members };
}

// A trending story's full article list is embedded in the page (window.CI_STORIES): the cards on the page
// leave out articles that deduplication merged, so they cannot be used to list a story's coverage.
function storyFromEmbedded(id, title, list) {
  var colors = window.CI_COLORS || {};
  return { id: id, title: title, members: list.map(function (m) {
    return Object.assign({}, m, { color: colors[m.category] || '', vendorColor: colors[m.vendor] || '', shareUrl: m.id ? '__EXPLORER_URL__#' + m.id : '' });
  }) };
}

document.addEventListener('click', function (e) {
  var t = e.target;
  if (!t || !t.closest) return;
  var details = t.closest('.card-details');
  if (details && window.ArticleModal) {
    window.ArticleModal.open(cardToArticle(details.closest('.card')), { fullTextBase: '__FULLTEXT_BASE__' });
    return;
  }
  var badge = t.closest('.story-badge');
  if (badge && window.StoryModal) {
    var card = badge.closest('.card');
    window.StoryModal.open(storyFromDom(card.dataset.story, card.querySelector('.card-title').textContent.trim()), { fullTextBase: '__FULLTEXT_BASE__' });
  }
});
"""

CAROUSEL_JS = r"""
(function () {
  var track = document.getElementById('tr-track');
  if (!track) return;
  var slides = Array.prototype.slice.call(track.children), n = slides.length, page = 0, per = 3, timer = null;
  var prev = document.getElementById('tr-prev'), next = document.getElementById('tr-next'), dots = document.getElementById('tr-dots');
  var nav = document.getElementById('tr-nav'), section = document.getElementById('trending');
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function perView() { var w = window.innerWidth; return w >= 1100 ? 3 : (w >= 700 ? 2 : 1); }
  function pages() { return Math.max(1, Math.ceil(n / per)); }
  function render() {
    per = perView();
    if (page >= pages()) page = 0;
    track.style.setProperty('--per', per);
    track.style.transform = 'translateX(-' + (page * 100) + '%)';
    slides.forEach(function (s, i) {
      var visible = i >= page * per && i < (page + 1) * per;
      s.setAttribute('aria-hidden', visible ? 'false' : 'true');
      s.inert = !visible;
    });
    dots.textContent = '';
    for (var p = 0; p < pages(); p++) {
      var d = document.createElement('button'); d.type = 'button'; d.className = 'tr-dot';
      d.setAttribute('aria-label', 'Show stories ' + (p * per + 1) + ' to ' + Math.min(n, (p + 1) * per));
      d.setAttribute('aria-current', p === page ? 'true' : 'false');
      (function (target) { d.addEventListener('click', function () { go(target); }); })(p);
      dots.appendChild(d);
    }
    nav.hidden = pages() === 1;
  }
  function go(p) { page = (p + pages()) % pages(); render(); }
  function start() { stop(); if (!reduced && pages() > 1) timer = setInterval(function () { go(page + 1); }, 9000); }
  function stop() { if (timer) { clearInterval(timer); timer = null; } }

  prev.addEventListener('click', function () { go(page - 1); start(); });
  next.addEventListener('click', function () { go(page + 1); start(); });
  section.addEventListener('mouseenter', stop); section.addEventListener('mouseleave', start);
  section.addEventListener('focusin', stop); section.addEventListener('focusout', start);
  window.addEventListener('resize', render);
  track.addEventListener('click', function (e) {
    var btn = e.target.closest ? e.target.closest('.tr-open') : null;
    if (!btn || !window.StoryModal) return;
    var title = btn.closest('.tr-slide').querySelector('.tr-title').textContent.trim();
    var embedded = window.CI_STORIES && window.CI_STORIES[btn.dataset.story];
    window.StoryModal.open(embedded ? storyFromEmbedded(btn.dataset.story, title, embedded) : storyFromDom(btn.dataset.story, title), { fullTextBase: __FULLTEXT_BASE_JS__ });
  });
  render(); start();
})();
"""

DASH_VIEW_CSS = r"""
  .topbar-links { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
  .card.watched { box-shadow: inset 3px 0 0 #f1c40f; }
  .watch-star { color: #f1c40f; margin-left: 5px; }
  #watch-toggle[aria-pressed="true"] { background: #f1c40f; color: #1a1d27; border-color: #f1c40f; }
  .movers { padding: 14px 24px 0; }
  .mv-head { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; }
  .mv-head h2 { font-size: 0.9rem; color: #fff; font-weight: 700; }
  .mv-head p { font-size: 0.74rem; color: #7d8299; }
  .mv-all { margin-left: auto; font-size: 0.74rem; color: #8a8fa3; text-decoration: none; }
  .mv-all:hover, .mv-all:focus-visible { color: #fff; text-decoration: underline; outline: none; }
  .mv-list { display: flex; flex-wrap: wrap; gap: 8px; }
  .mv { display: inline-flex; align-items: baseline; gap: 8px; background: #1a1d27; border: 1px solid #2a2d3e; border-left: 3px solid #e67e22;
        border-radius: 6px; padding: 6px 10px; text-decoration: none; color: #e0e0e0; font-size: 0.8rem; }
  .mv:hover, .mv:focus-visible { border-color: #DA291C; outline: none; }
  .mv-spike { border-left-color: #DA291C; }
  .mv-new { border-left-color: #8e6bd6; }
  .mv-by { font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.06em; color: #6b7088; }
  .mv-name { font-weight: 600; }
  .mv b { color: #ff8a80; font-variant-numeric: tabular-nums; }
  .mv-n { font-size: 0.7rem; color: #7d8299; font-variant-numeric: tabular-nums; }
  @media (max-width: 640px) { .movers { padding: 12px 16px 0; } }
  .back { font-size: 0.78rem; font-weight: 600; text-decoration: none; color: #fff; background: #1e2030;
          border: 1px solid #2a2d3e; border-radius: 4px; padding: 6px 12px; white-space: nowrap; }
  .back:hover, .back:focus-visible { border-color: #DA291C; outline: none; }
  .card-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 8px; }
  .card-tags .tag { font-size: 0.66rem; font-weight: 600; color: #fff; border-radius: 3px; padding: 1px 7px; line-height: 1.5; background: #555a70; }
  .grid.view-category .tag-category, .grid.view-vendor .tag-vendor { display: none; }
  .grid.view-category .card-tags:not(:has(.tag-vendor)) { display: none; }
  .view-switch { display: inline-flex; border: 1px solid #2a2d3e; border-radius: 6px; overflow: hidden; }
  .view-switch button { background: #1e2030; color: #aaa; border: 0; padding: 6px 12px; font-size: 0.75rem; cursor: pointer; font-family: inherit; }
  .view-switch button + button { border-left: 1px solid #2a2d3e; }
  .view-switch button:hover { color: #fff; }
  .view-switch button[aria-pressed="true"] { background: #DA291C; color: #fff; font-weight: 600; }
  .view-switch button:focus-visible { outline: 2px solid #fff; outline-offset: -2px; }
"""

DASH_EXTRA_CSS = r"""
  .export-btn[aria-pressed="false"] { opacity: .65; }
  .story-badge { margin-left: 8px; background: #2a1a1b; color: #ff8a80; border: 1px solid #6b2a27; border-radius: 3px; padding: 0 7px;
                 font-size: .68rem; cursor: pointer; font-family: inherit; line-height: 1.6; white-space: nowrap; }
  .story-badge:hover { color: #fff; border-color: #DA291C; }
  .story-badge[hidden] { display: none; }
  .trending { padding: 18px 24px 0; }
  .trending-head { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }
  .trending-head h2 { font-size: 1rem; color: #fff; font-weight: 700; }
  .trending-head p { font-size: .75rem; color: #7d8299; }
  .trending-nav { margin-left: auto; display: flex; align-items: center; gap: 8px; }
  .trending-nav[hidden] { display: none; }
  .tr-arrow { background: #1e2030; color: #fff; border: 1px solid #2a2d3e; border-radius: 4px; width: 28px; height: 28px; cursor: pointer; font-size: 1rem; line-height: 1; }
  .tr-arrow:hover, .tr-arrow:focus-visible { border-color: #DA291C; outline: none; }
  .tr-dots { display: flex; gap: 6px; }
  .tr-dot { width: 8px; height: 8px; border-radius: 50%; border: none; background: #343850; cursor: pointer; padding: 0; }
  .tr-dot[aria-current="true"] { background: #DA291C; }
  .trending-viewport { overflow: hidden; margin: 0 -6px; }
  .trending-track { display: flex; --per: 3; transition: transform .45s ease; }
  .tr-slide { flex: 0 0 calc(100% / var(--per)); padding: 0 6px; min-width: 0; }
  .tr-card { background: linear-gradient(180deg, #1c1f2e, #171a26); border: 1px solid #2a2d3e; border-top: 3px solid #DA291C; border-radius: 8px;
             padding: 14px 16px; height: 100%; display: flex; flex-direction: column; gap: 8px; }
  .tr-top { display: flex; justify-content: space-between; align-items: center; font-size: .72rem; color: #8a8fa3; }
  .tr-rank { font-weight: 800; color: #DA291C; font-size: .95rem; }
  .tr-count b { color: #fff; font-size: .95rem; }
  .tr-title { font-size: .95rem; line-height: 1.4; font-weight: 600; }
  .tr-title a { color: #fff; text-decoration: none; }
  .tr-title a:hover, .tr-title a:focus-visible { text-decoration: underline; outline: none; }
  .tr-chips, .tr-sources { display: flex; flex-wrap: wrap; gap: 5px; }
  .tr-chip { font-size: .66rem; border-radius: 999px; padding: 1px 8px; border: 1px solid #343850; color: #c9cbd6; background: #1b1e2d; }
  .tr-chip.hot { color: #ff8a80; border-color: #6b2a27; background: #2a1a1b; font-weight: 700; }
  .tr-context { font-size: .78rem; color: #8a8fa3; line-height: 1.45; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
  .tr-src { font-size: .68rem; color: #ff5a4d; }
  .tr-src + .tr-src::before { content: "\00b7"; color: #555a70; margin-right: 5px; }
  .tr-foot { margin-top: auto; display: flex; justify-content: space-between; align-items: center; gap: 8px; padding-top: 4px; }
  .tr-meta { font-size: .7rem; color: #6b7088; }
  .tr-open { background: #DA291C; color: #fff; border: none; border-radius: 4px; padding: 5px 11px; font-size: .72rem; font-weight: 600; cursor: pointer; font-family: inherit; }
  .tr-open:hover, .tr-open:focus-visible { background: #f0352a; outline: none; }
  @media (max-width: 1099px) { .trending-track { --per: 2; } }
  @media (max-width: 699px) { .trending-track { --per: 1; } .trending { padding: 14px 16px 0; } }
  @media (prefers-reduced-motion: reduce) { .trending-track { transition: none; } }
"""


def _trending_html(stories: list[dict]) -> str:
    """The 'Trending this week' carousel; empty when no story is covered by enough sources."""
    if not stories:
        return ""
    esc = html.escape
    slides = []
    for rank, st in enumerate(stories, 1):
        chips = []
        if st["exploited"]:
            chips.append('<span class="tr-chip hot">Exploited</span>')
        if st["category"]:
            chips.append(f'<span class="tr-chip">{esc(st["category"])}</span>')
        if st.get("vendor"):
            chips.append(f'<span class="tr-chip">{esc(st["vendor"])}</span>')
        chips += [f'<span class="tr-chip">{esc(m)}</span>' for m in st["modules"]]
        shown = st["sources"][:5]
        sources = "".join(f'<span class="tr-src">{esc(x)}</span>' for x in shown)
        if len(st["sources"]) > len(shown):
            sources += f'<span class="tr-src">+{len(st["sources"]) - len(shown)} more</span>'
        context = f'<p class="tr-context">{esc(st["context"])}</p>' if st["context"] else ""
        slides.append(
            f'<article class="tr-slide" data-story="{esc(st["id"])}"><div class="tr-card">'
            f'<div class="tr-top"><span class="tr-rank">#{rank}</span><span class="tr-count"><b>{len(st["sources"])}</b> sources</span></div>'
            f'<h3 class="tr-title"><a href="{esc(st["link"])}" target="_blank" rel="noopener noreferrer">{esc(st["title"])}</a></h3>'
            f'<div class="tr-chips">{"".join(chips)}</div>{context}<div class="tr-sources">{sources}</div>'
            f'<div class="tr-foot"><span class="tr-meta">{st["articles"]} articles &middot; latest {st["latest"][:10]}</span>'
            f'<button type="button" class="tr-open" data-story="{esc(st["id"])}">View coverage</button></div>'
            f'</div></article>')
    return (
        '<section class="trending" id="trending" aria-label="Trending this week">'
        '<div class="trending-head"><h2>Trending this week</h2>'
        f'<p>Stories covered by the most sources in the last {TRENDING_DAYS} days</p>'
        '<div class="trending-nav" id="tr-nav"><button type="button" class="tr-arrow" id="tr-prev" aria-label="Previous stories">&lsaquo;</button>'
        '<div class="tr-dots" id="tr-dots"></div>'
        '<button type="button" class="tr-arrow" id="tr-next" aria-label="Next stories">&rsaquo;</button></div></div>'
        f'<div class="trending-viewport"><div class="trending-track" id="tr-track">{"".join(slides)}</div></div></section>')



# ---------------------------------------------------------------------------
# Watchlist, historical baseline (movers) and source health
# ---------------------------------------------------------------------------

def load_watchlist() -> dict:
    """watchlist.json: {"vendors": [...], "keywords": [...]}. Keywords match the title like the category rules do."""
    try:
        with open(WATCHLIST_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {"vendors": [], "keywords": []}
    return {"vendors": [str(v) for v in data.get("vendors", [])], "keywords": [str(k).lower() for k in data.get("keywords", [])]}


def watch_reason(article: dict, watchlist: dict) -> str:
    """Why an article is on the watchlist: its vendor, else the first matching keyword ('' when it is not on it)."""
    vendor = article.get("vendor") or vendor_of(article)
    if vendor and vendor in watchlist["vendors"]:
        return vendor
    haystack = _title_haystack(article)
    for kw in watchlist["keywords"]:
        if _keyword_in(kw, haystack):
            return kw.lstrip("~")
    return ""


def watch_alert(recent: list[dict], watchlist: dict) -> tuple[list, str, str]:
    """Watchlist matches from the last WATCH_ALERT_HOURS hours, as (hits, plain text, html list) for the e-mail."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=WATCH_ALERT_HOURS)
    hits = [(a, why) for a in recent if a.get("date") and a["date"] >= cutoff and (why := watch_reason(a, watchlist))]
    flat = lambda s: " ".join(s.split())
    text = " | ".join(f"{why}: {flat(a['title'])} ({a['link']})" for a, why in hits[:8]) or "No watchlist matches in the last %d hours." % WATCH_ALERT_HOURS
    items = "".join(f'<li><b>{html.escape(why)}</b> &mdash; <a href="{html.escape(a["link"])}">{html.escape(flat(a["title"]))}</a> '
                    f'<span style="color:#888">({html.escape(a["source"])})</span></li>' for a, why in hits[:8])
    html_list = f'<ul style="font-family:Arial,sans-serif;font-size:14px;">{items}</ul>' if items else "<p>No watchlist matches in the last %d hours.</p>" % WATCH_ALERT_HOURS
    return hits, text, html_list


BASELINE_DAYS_KEPT = 120


def _baseline_status(cur: float, exp: float, base: float, z: float) -> str:
    if base == 0 and cur >= 3:
        return "New"
    d = (cur - exp) / exp if exp > 0 else 0
    if cur >= 5 and d >= 0.5 and z >= 2:
        return "Spike"
    if cur >= 3 and d >= 0.25 and z >= 1:
        return "Up"
    if d <= -0.25 and z <= -1:
        return "Down"
    return "Normal"


def _baseline_keys(entry: dict, by: str) -> list[str]:
    if by == "category":
        return [entry.get("category") or "Uncategorised"]
    if by == "vendor":
        return [entry.get("vendor") or NO_VENDOR]
    return [m for m in entry.get("modules", []) if m not in (MODULE_OTHER, MODULE_NA)]


def compute_baseline(entries: list[dict], by: str, window: int = 7, weeks: int = 8) -> dict | None:
    """The last `window` days against the daily average of the `weeks` weeks before them, per category/vendor/module.

    Python twin of computeBaseline() in explorer_template.html; keep the two in step. Feeds that were not yet being
    collected during the baseline, and weeks where collection had a gap, are left out so the comparison stays fair.
    """
    dated = [(date.fromisoformat(e["date"][:10]).toordinal(), e) for e in entries if e.get("date")]
    if not dated:
        return None
    ordinals = sorted(o for o, _ in dated)
    anchor, data_start = ordinals[-1], ordinals[int(len(ordinals) * 0.01)]
    base_days = min(weeks * 7, anchor - data_start + 1 - window)
    if base_days < 7:
        return None
    base_start = anchor - window - base_days + 1
    first: dict = {}
    for o, e in dated:
        first[e["source"]] = min(first.get(e["source"], o), o)
    comparable = lambda e: first[e["source"]] <= base_start + 14
    totals = [0] * BASELINE_DAYS_KEPT
    for o, e in dated:
        idx = anchor - o
        if comparable(e) and 0 <= idx < BASELINE_DAYS_KEPT:
            totals[idx] += 1
    week_sums = [sum(totals[window + wk * 7 + q] for q in range(7)) for wk in range(base_days // 7)]
    median = sorted(week_sums)[len(week_sums) // 2] if week_sums else 0
    use, used, gaps = [True] * BASELINE_DAYS_KEPT, base_days, 0
    for wi, ws in enumerate(week_sums):
        if ws < 0.4 * median:
            gaps, used = gaps + 1, used - 7
            for q in range(7):
                use[window + wi * 7 + q] = False
    daily: dict = collections.defaultdict(lambda: [0] * BASELINE_DAYS_KEPT)
    for o, e in dated:
        idx = anchor - o
        if comparable(e) and 0 <= idx < BASELINE_DAYS_KEPT:
            for key in _baseline_keys(e, by):
                daily[key][idx] += 1
    rows = []
    for key, d in daily.items():
        cur = sum(d[:window])
        vals = [d[i] for i in range(window, window + base_days) if use[i]]
        base = sum(vals)
        mean = base / used if used > 0 else 0
        exp = mean * window
        variance = sum((v - mean) ** 2 for v in vals) / len(vals) if vals else 0
        sd = max(variance ** 0.5, max(mean, 0.05) ** 0.5) * window ** 0.5
        z = (cur - exp) / sd
        if cur == 0 and base == 0:
            continue
        rows.append({"group": key, "current": cur, "expected": round(exp, 2), "delta": (cur - exp) / exp if exp > 0 else None,
                     "z": round(z, 2), "status": _baseline_status(cur, exp, base, z) if used >= 7 else "n/a"})
    start = date.fromordinal(anchor - window + 1).isoformat()
    return {"by": by, "window": window, "weeks": weeks, "anchor": date.fromordinal(anchor).isoformat(), "from": start,
            "gap_weeks": gaps, "rows": rows}


def build_movers(entries: list[dict]) -> list[dict]:
    """The groups that rose furthest above their baseline this week, for the dashboard strip."""
    picks = []
    for by, take in (("vendor", 4), ("module", 3), ("category", 2)):
        res = compute_baseline(entries, by)
        if not res:
            continue
        rows = [r for r in res["rows"] if r["status"] in ("Spike", "Up", "New") and r["group"] not in (NO_VENDOR, FALLBACK_CATEGORY)]
        rows.sort(key=lambda r: r["current"] - r["expected"], reverse=True)
        picks += [{**r, "by": by, "from": res["from"], "anchor": res["anchor"], "window": res["window"], "weeks": res["weeks"]} for r in rows[:take]]
    return picks  # vendors first (what competitive intelligence follows), then modules, then categories


def _movers_html(movers: list[dict]) -> str:
    """The 'Movers vs baseline' strip under the carousel; empty when nothing moved."""
    if not movers:
        return ""
    esc = html.escape
    chips = []
    for m in movers:
        pct = "new" if m["delta"] is None else f'{m["delta"] * 100:+.0f}%'
        href = f'{EXPLORER_URL}#view=articles&{m["by"]}={quote(m["group"])}&period=custom&from={m["from"]}'
        exp = f'{m["expected"]:.1f}' if m["expected"] < 10 else f'{m["expected"]:.0f}'
        chips.append(f'<a class="mv mv-{m["status"].lower()}" href="{esc(href)}" title="{esc(m["by"])}: {m["current"]} articles in the last {m["window"]} days, usually {exp}">'
                     f'<span class="mv-by">{esc(m["by"])}</span><span class="mv-name">{esc(m["group"])}</span>'
                     f'<b>{pct}</b><span class="mv-n">{m["current"]} vs {exp}</span></a>')
    first = movers[0]
    return ('<section class="movers" aria-label="Movers against the historical baseline">'
            '<div class="mv-head"><h2>Movers vs baseline</h2>'
            f'<p>Last {first["window"]} days against the previous {first["weeks"]} weeks, as of {first["anchor"]}</p>'
            f'<a class="mv-all" href="{EXPLORER_URL}#view=baseline">Full baseline &rarr;</a></div>'
            f'<div class="mv-list">{"".join(chips)}</div></section>')


def write_source_health(entries: list[dict]) -> None:
    """archive/data/source_health.json: per-feed fetch result of this run (remembering failures across runs) plus article counts."""
    try:
        with open(SOURCE_HEALTH_FILE, encoding="utf-8") as f:
            prev = {s["name"]: s for s in json.load(f)["sources"]}
    except (OSError, ValueError, KeyError):
        prev = {}
    now = datetime.now(timezone.utc)
    stats: dict = {}
    for e in entries:
        st = stats.setdefault(e["source"], {"total": 0, "last": None, "d7": 0, "d30": 0})
        st["total"] += 1
        if e.get("date"):
            dt = datetime.fromisoformat(e["date"])
            if st["last"] is None or dt > st["last"]:
                st["last"] = dt
            age = (now - dt).days
            st["d7"] += age < 7
            st["d30"] += age < 30
    urls = dict(FEEDS)
    rows = []
    for name in list(urls) + sorted(set(stats) - set(urls)):
        old, cur = prev.get(name, {}), FEED_STATUS.get(name)
        st = stats.get(name, {"total": 0, "last": None, "d7": 0, "d30": 0})
        if cur is None:  # not fetched this run (a retired feed): keep what we knew
            ok, error, items = old.get("ok", True), old.get("error", ""), old.get("items", 0)
            failures, last_ok, checked = old.get("failures", 0), old.get("last_ok"), old.get("checked")
        else:
            ok, error, items = cur["ok"], cur["error"], cur["items"]
            failures = 0 if ok else old.get("failures", 0) + 1
            last_ok = now.isoformat() if ok else old.get("last_ok")
            checked = now.isoformat()
        days_since = (now - st["last"]).days if st["last"] else None
        if name not in urls:
            status = "Retired"
        elif not ok:
            status = "Failing"
        elif days_since is None or days_since > STALE_SOURCE_DAYS:
            status = "Stale"
        else:
            status = "OK"
        rows.append({"name": name, "url": urls.get(name, ""), "status": status, "error": error, "failures": failures,
                     "never_worked": bool(not ok and not last_ok and st["total"] == 0), "items": items, "checked": checked, "last_ok": last_ok,
                     "total": st["total"], "last_article": st["last"].isoformat() if st["last"] else None,
                     "d7": st["d7"], "d30": st["d30"]})
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SOURCE_HEALTH_FILE, "w", encoding="utf-8") as f:
        json.dump({"generated": now.isoformat(), "stale_days": STALE_SOURCE_DAYS, "sources": rows}, f, ensure_ascii=False, indent=1)


def write_sources_page() -> None:
    """Copy sources_template.html to archive/data/sources.html (the page reads source_health.json beside it)."""
    try:
        with open(SOURCES_TEMPLATE, encoding="utf-8") as f:
            page = f.read()
    except OSError as exc:
        print(f"  [WARN] sources template missing: {exc}", file=sys.stderr)
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SOURCES_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)


def write_explorer() -> None:
    """Render explorer_template.html into archive/data/explorer.html."""
    try:
        with open(EXPLORER_TEMPLATE, encoding="utf-8") as f:
            template = f.read()
    except OSError as exc:
        print(f"  [WARN] explorer template missing: {exc}", file=sys.stderr)
        return
    page = (template.replace("__CATEGORY_COLORS__", json.dumps({**CATEGORY_COLORS, **VENDOR_COLORS}))
            .replace("__NO_VENDOR__", json.dumps(NO_VENDOR))
            .replace("__VENDOR_NAMES__", json.dumps(VENDOR_ORDER))
            .replace("__CATEGORY_NAMES__", json.dumps(list(CATEGORY_COLORS)))
            .replace("__MODAL_CSS__", MODAL_CSS)
            .replace("__MODAL_HTML__", MODAL_HTML)
            .replace("__MODAL_JS__", MODAL_JS)
            .replace("__POD_ICON__", POD_ICON_SVG))
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

    recent = unique_by_url(recent)
    print(f"  {len(recent)} unique article(s) by URL.", file=sys.stderr)

    # ── Master store: every article ever seen (feeds + archive backfill) ──────────────────
    master = load_master()
    merge_into_master(master, recent)
    entries = sorted(master.values(), key=lambda a: a.get("date") or "", reverse=True)
    for entry in entries:
        tidy_podcast_title(entry)
        entry["podcast"] = is_podcast(entry)

    # ── Full article text (saved for exports only, never rendered) + dashboard snippets ──
    obtained = attach_full_text(entries)
    have_text = sum(1 for a in entries if a["full_text"])
    print(f"  Full text: {obtained} collected this run, {have_text}/{len(entries)} stored articles have it.", file=sys.stderr)
    if LAST_TEXT_ERRORS:
        print("  Text download problems this run: " + ", ".join(f"{k} x{v}" for k, v in LAST_TEXT_ERRORS.most_common()), file=sys.stderr)
    for entry in entries:
        if not entry.get("context"):
            entry["context"] = extract_context(entry)
        if entry.get("podcast") and entry.get("text_source") == "transcript":
            entry["context"] = podcast_context(entry["full_text"]) or entry["context"]
        entry["modules"] = classify_modules(entry)
        entry["category"] = categorize(entry)
        entry["vendor"] = vendor_of(entry)
    assign_stories(entries)
    trending = trending_stories(entries)
    for article in recent:
        stored = master.get(article_id(article["link"])) if article.get("link") else None
        if stored:
            article["id"] = stored["id"]
            article["full_text"] = stored["full_text"]
            article["modules"] = stored["modules"]
            article["story"] = stored["story"]
            article["podcast"] = bool(stored.get("podcast"))
            article["text_source"] = stored.get("text_source", "")
            article["context"] = stored["context"]
            if not article.get("context"):
                article["context"] = stored.get("context", "")
    save_master(master, label)
    write_explorer()
    write_sources_page()
    write_source_health(entries)
    movers = build_movers(entries)
    with open(MOVERS_FILE, "w", encoding="utf-8") as f:
        json.dump(movers, f, ensure_ascii=False, indent=1)
    print(f"  Movers vs baseline: {len(movers)}", file=sys.stderr)
    print(f"  Article store: {len(master)} article(s) -> {ARTICLES_FILE}", file=sys.stderr)

    # ── Export latest acquisition and top announcements to GitHub Actions env ───────────────────
    acq_list   = [a for a in recent if is_acquisition(a)]

    # Find top vendor announcements (for GitHub Actions notifications): vendor news that is not an acquisition or a vulnerability
    vendor_buckets = bucket_articles([a for a in recent if not is_acquisition(a) and categorize(a) != "Vulnerabilities & Patching"], "vendor")
    top_announcements = []
    for vendor in ["CrowdStrike", "Palo Alto Networks", "Microsoft Security", "Fortinet", "SentinelOne", "Trend Micro"]:
        if vendor_buckets.get(vendor):
            top_announcements.append(vendor_buckets[vendor][0])

    wl = load_watchlist()
    watch_hits, watch_text, watch_html = watch_alert(recent, wl)
    print(f"  Watchlist matches in the last {WATCH_ALERT_HOURS} hours: {len(watch_hits)}", file=sys.stderr)

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
            f.write(f"WATCHLIST_FOUND={'true' if watch_hits else 'false'}\n")
            f.write(f"WATCHLIST_COUNT={len(watch_hits)}\n")
            f.write(f"WATCHLIST_TEXT={watch_text}\n")
            f.write(f"WATCHLIST_HTML={watch_html}\n")

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
        f.write(build_html(recent, label, trending=trending, watchlist=wl, movers=movers))
    print(f"Archive saved: {arch_path}", file=sys.stderr)

    # ── Load history from archive dir (includes the file just written) ────
    history = load_history()

    # ── Write history.json so all pages can fetch it dynamically ─────────
    save_history(history)

    # ── Save index.html ───────────────────────────────────────────────────
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(build_html(recent, label, trending=trending, watchlist=wl, movers=movers))
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

    # ── Export by category and by vendor (separate CSV and JSON for each) ──
    for name in os.listdir(EXPORT_DIR):
        if name.startswith("digest__") and name.endswith((".csv", ".json")):
            os.remove(os.path.join(EXPORT_DIR, name))  # rebuilt below; drops files of retired groups
    for by in ("category", "vendor"):
        group_exports = export_by_group(recent, label, by)
        for group, (csv_content, json_content) in group_exports.items():
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in group).lower()
            with open(os.path.join(EXPORT_DIR, f"digest__{by}__{safe_name}.csv"), "w", encoding="utf-8", newline="") as f:
                f.write(csv_content)
            with open(os.path.join(EXPORT_DIR, f"digest__{by}__{safe_name}.json"), "w", encoding="utf-8") as f:
                f.write(json_content)
        print(f"{by.capitalize()} exports created: {len(group_exports)}", file=sys.stderr)


def retry_text() -> None:
    """Retry saved text for articles that have none or only a partial text, ignoring the attempt limit.

    Does not fetch feeds or rebuild any page. Articles without text go first. Run it from a
    normal internet connection:  python daily_cybersecurity_digest.py --retry-text
    """
    global FULLTEXT_BUDGET_S, BROWSER_BUDGET_S
    FULLTEXT_BUDGET_S = int(os.environ.get("FULLTEXT_BUDGET_S", "1800"))
    BROWSER_BUDGET_S = int(os.environ.get("BROWSER_BUDGET_S", "900"))
    master = load_master()
    entries = sorted(master.values(), key=lambda a: a.get("date") or "", reverse=True)
    for entry in entries:
        tidy_podcast_title(entry)
        entry["podcast"] = is_podcast(entry)
    cache = load_fulltext_cache()
    reset = 0
    for entry in cache.values():
        partial = entry.get("source") in ("backup", "feed-excerpt")
        if (not entry.get("text") or partial) and (entry.get("attempts", 0) or entry.get("transient", 0)):
            entry["attempts"] = 0
            entry["transient"] = 0
            reset += 1
    save_fulltext_cache(cache, {a["id"]: _month_key(a.get("date")) for a in entries})
    entries.sort(key=lambda a: bool(cache.get(a["id"], {}).get("text")))  # stable: no-text articles first
    missing_before = sum(1 for a in entries if not cache.get(a["id"], {}).get("text"))
    print(f"Retrying saved text: {reset} attempt counters reset, {missing_before} articles have no text yet.", file=sys.stderr)

    obtained = attach_full_text(entries)
    for entry in entries:
        if not entry.get("context"):
            entry["context"] = extract_context(entry)
        if entry.get("podcast") and entry.get("text_source") == "transcript":
            entry["context"] = podcast_context(entry["full_text"]) or entry["context"]
        entry["modules"] = classify_modules(entry)
        entry["category"] = categorize(entry)
        entry["vendor"] = vendor_of(entry)
    assign_stories(entries)
    save_master(master, datetime.now(PHT).strftime("%Y-%m-%d %H:%M PHT"))

    still = [a for a in entries if not a["full_text"]]
    hosts = {}
    for a in still:
        host = urlsplit(a["link"]).netloc.lower().removeprefix("www.")
        hosts[host] = hosts.get(host, 0) + 1
    print(f"Done: {obtained} texts obtained this run | {missing_before} -> {len(still)} articles without text.", file=sys.stderr)
    for host, n in sorted(hosts.items(), key=lambda kv: -kv[1])[:8]:
        print(f"  still missing: {n:4d}  {host}", file=sys.stderr)
    saved = load_fulltext_cache()
    reasons = collections.Counter(saved.get(a["id"], {}).get("error", "never reached") for a in still)
    print("  reasons: " + ", ".join(f"{k} x{v}" for k, v in reasons.most_common()), file=sys.stderr)


if __name__ == "__main__":
    if "--retry-text" in sys.argv:
        retry_text()
    else:
        main()
