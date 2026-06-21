# Cyber Competitive Daily Feed

A GitHub Actions-powered cybersecurity news aggregator that fetches articles from 47 RSS feeds, deduplicates them, categorizes by company/topic, and publishes an auto-updating HTML page twice daily.

**Live page:** https://lukan47.github.io/RSS/

---

## Features

- Pulls from 47 RSS feeds across security news, government advisories, threat intel, and vendor blogs
- Dedicated columns per competitor/company — only shown when there's news
- Article deduplication (URL match, string similarity, keyword overlap)
- First-match categorization: Zero-Day → Acquisitions → Company columns → General News
- Updates automatically at **6:00 AM and 6:00 PM PHT** via GitHub Actions
- History dropdown to browse previous digests (last 30 runs)
- Email notification via Gmail on each update

---

## RSS Feeds (47)

### General Security News (11)

| # | Source | Feed URL |
|---|---|---|
| 1 | Krebs on Security | https://krebsonsecurity.com/feed/ |
| 2 | The Hacker News | https://feeds.feedburner.com/TheHackersNews |
| 3 | Bleeping Computer | https://www.bleepingcomputer.com/feed/ |
| 4 | SANS ISC | https://isc.sans.edu/rssfeed_full.xml |
| 5 | SecurityWeek | https://feeds.feedburner.com/securityweek |
| 6 | Dark Reading | https://www.darkreading.com/rss.xml |
| 7 | Schneier on Security | https://www.schneier.com/feed/atom/ |
| 8 | ThreatPost | https://threatpost.com/feed/ |
| 9 | Wired Security | https://www.wired.com/feed/category/security/latest/rss |
| 10 | Ars Technica Security | https://feeds.arstechnica.com/arstechnica/security |
| 11 | Troy Hunt | https://feeds.feedburner.com/TroyHunt |

### Government / Advisories (3)

| # | Source | Feed URL |
|---|---|---|
| 12 | CISA Alerts | https://www.cisa.gov/uscert/ncas/alerts.xml |
| 13 | CISA ICS Advisories | https://www.cisa.gov/uscert/ics/advisories/advisories.xml |
| 14 | US-CERT | https://www.cisa.gov/uscert/ncas/current-activity.xml |

### Threat Intelligence (6)

| # | Source | Feed URL |
|---|---|---|
| 15 | Talos Intelligence | https://blog.talosintelligence.com/rss/ |
| 16 | Google Project Zero | https://googleprojectzero.blogspot.com/feeds/posts/default |
| 17 | Exploit-DB | https://www.exploit-db.com/rss.xml |
| 18 | Mandiant Blog | https://www.mandiant.com/resources/blog/rss.xml |
| 19 | Recorded Future | https://www.recordedfuture.com/feed |
| 20 | Check Point Research | https://research.checkpoint.com/feed/ |

### Vendor / Competitor Blogs (27)

| # | Source | Feed URL |
|---|---|---|
| 21 | Trend Micro Research | https://feeds.trendmicro.com/TrendMicroResearch |
| 22 | CrowdStrike Blog | https://www.crowdstrike.com/blog/feed/ |
| 23 | Palo Alto Unit 42 | https://unit42.paloaltonetworks.com/feed/ |
| 24 | Fortinet Threat Research | https://feeds.fortinet.com/fortinet/blog/threat-research |
| 25 | Microsoft Security Blog | https://www.microsoft.com/en-us/security/blog/feed/ |
| 26 | Naked Security (Sophos) | https://nakedsecurity.sophos.com/feed/ |
| 27 | SentinelOne Blog | https://www.sentinelone.com/blog/feed/ |
| 28 | Rapid7 Blog | https://blog.rapid7.com/rss/ |
| 29 | Tenable Blog | https://www.tenable.com/blog/feed |
| 30 | Qualys Blog | https://blog.qualys.com/feed |
| 31 | Zscaler ThreatLabz | https://www.zscaler.com/blogs/security-research/feed |
| 32 | Kaspersky Blog | https://www.kaspersky.com/blog/feed/ |
| 33 | Securelist (Kaspersky) | https://securelist.com/feed/ |
| 34 | Cybereason Blog | https://www.cybereason.com/blog/rss.xml |
| 35 | Barracuda Blog | https://blog.barracuda.com/feed/ |
| 36 | Falco / Sysdig Blog | https://sysdig.com/blog/feed/ |
| 37 | Wiz Blog | https://www.wiz.io/feed/rss.xml |
| 38 | Orca Security Blog | https://orca.security/resources/blog/feed/ |
| 39 | Trellix Blog | https://www.trellix.com/blogs/feed/ |
| 40 | Darktrace Blog | https://www.darktrace.com/blog/index.xml |
| 41 | ExtraHop Blog | https://www.extrahop.com/blog/feed/ |
| 42 | Vectra AI Blog | https://www.vectra.ai/blog/feed/ |
| 43 | Proofpoint Blog | https://www.proofpoint.com/us/rss.xml |
| 44 | Broadcom/Symantec Blog | https://symantec-enterprise-blogs.security.com/blogs/rss/v1/blogs/rss.xml/221 |
| 45 | The Register Security | https://www.theregister.com/security/headlines.atom |
| 46 | Databreaches.net | https://www.databreaches.net/feed/ |
| 47 | This Week in 4n6 | https://thisweekin4n6.com/feed/atom/ |

---

## Setup

### GitHub Secrets required

| Secret | Description |
|---|---|
| `GMAIL_USERNAME` | Gmail address used to send notifications |
| `GMAIL_APP_PASSWORD` | 16-character Gmail App Password |

### Workflow

The workflow is defined in `.github/workflows/notify.yml` and runs on schedule or manually via **Actions → Cybersecurity Digest → Run workflow**.
