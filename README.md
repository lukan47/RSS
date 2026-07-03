# Cyber Competitive Daily Feed

A GitHub Actions-powered cybersecurity news aggregator that fetches articles from 77 RSS feeds, deduplicates them, categorizes by company/topic, and publishes an auto-updating HTML page twice daily.

**Live page:** https://lukan47.github.io/RSS/

---

## Features

- Pulls from 77 RSS feeds across security news, government advisories, threat intel, and vendor blogs
- Dedicated columns per competitor/company — only shown when there's news
- Article deduplication (URL match, string similarity, keyword overlap)
- First-match categorization: Zero-Day → Acquisitions → Company columns → General News
- Updates automatically at **6:00 AM and 6:00 PM PHT** via GitHub Actions
- History dropdown to browse previous digests (last 30 runs)
- Email notification via Gmail on each update

---

## RSS Feeds (77)

### General Security News (16)

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
| 12 | Infosecurity Magazine | https://www.infosecurity-magazine.com/rss/news/ |
| 13 | Help Net Security | https://www.helpnetsecurity.com/feed/ |
| 14 | SC Magazine | https://www.scmagazine.com/feed |
| 15 | Graham Cluley | https://grahamcluley.com/feed/ |
| 16 | The CyberWire | https://thecyberwire.com/feeds/rss.xml |

### Government / Advisories (6)

| # | Source | Feed URL |
|---|---|---|
| 17 | CISA Alerts | https://www.cisa.gov/uscert/ncas/alerts.xml |
| 18 | CISA ICS Advisories | https://www.cisa.gov/uscert/ics/advisories/advisories.xml |
| 19 | US-CERT | https://www.cisa.gov/uscert/ncas/current-activity.xml |
| 20 | NCSC UK | https://www.ncsc.gov.uk/api/1/services/v1/report-rss-feed.xml |
| 21 | NIST NVD CVEs | https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml |
| 22 | Australian ACSC | https://www.cyber.gov.au/rss.xml |

### Threat Intelligence (8)

| # | Source | Feed URL |
|---|---|---|
| 23 | Talos Intelligence | https://blog.talosintelligence.com/rss/ |
| 24 | Google Project Zero | https://googleprojectzero.blogspot.com/feeds/posts/default |
| 25 | Exploit-DB | https://www.exploit-db.com/rss.xml |
| 26 | Mandiant Blog | https://www.mandiant.com/resources/blog/rss.xml |
| 27 | Recorded Future | https://www.recordedfuture.com/feed |
| 28 | Check Point Research | https://research.checkpoint.com/feed/ |
| 29 | Cyble | https://cyble.com/blog/feed/ |
| 30 | VirusTotal Blog | https://blog.virustotal.com/feeds/posts/default |

### Vendor / Competitor Blogs (47)

| # | Source | Feed URL |
|---|---|---|
| 31 | Trend Micro Research | https://feeds.trendmicro.com/TrendMicroResearch |
| 32 | CrowdStrike Blog | https://www.crowdstrike.com/blog/feed/ |
| 33 | Palo Alto Unit 42 | https://unit42.paloaltonetworks.com/feed/ |
| 34 | Fortinet Threat Research | https://feeds.fortinet.com/fortinet/blog/threat-research |
| 35 | Microsoft Security Blog | https://www.microsoft.com/en-us/security/blog/feed/ |
| 36 | Naked Security (Sophos) | https://nakedsecurity.sophos.com/feed/ |
| 37 | SentinelOne Blog | https://www.sentinelone.com/blog/feed/ |
| 38 | Rapid7 Blog | https://blog.rapid7.com/rss/ |
| 39 | Tenable Blog | https://www.tenable.com/blog/feed |
| 40 | Qualys Blog | https://blog.qualys.com/feed |
| 41 | Zscaler ThreatLabz | https://www.zscaler.com/blogs/security-research/feed |
| 42 | Kaspersky Blog | https://www.kaspersky.com/blog/feed/ |
| 43 | Securelist (Kaspersky) | https://securelist.com/feed/ |
| 44 | Cybereason Blog | https://www.cybereason.com/blog/rss.xml |
| 45 | Barracuda Blog | https://blog.barracuda.com/feed/ |
| 46 | Falco / Sysdig Blog | https://sysdig.com/blog/feed/ |
| 47 | Wiz Blog | https://www.wiz.io/feed/rss.xml |
| 48 | Orca Security Blog | https://orca.security/resources/blog/feed/ |
| 49 | Trellix Blog | https://www.trellix.com/blogs/feed/ |
| 50 | Darktrace Blog | https://www.darktrace.com/blog/index.xml |
| 51 | ExtraHop Blog | https://www.extrahop.com/blog/feed/ |
| 52 | Vectra AI Blog | https://www.vectra.ai/blog/feed/ |
| 53 | Proofpoint Blog | https://www.proofpoint.com/us/rss.xml |
| 54 | Broadcom/Symantec Blog | https://symantec-enterprise-blogs.security.com/blogs/rss/v1/blogs/rss.xml/221 |
| 55 | The Register Security | https://www.theregister.com/security/headlines.atom |
| 56 | Databreaches.net | https://www.databreaches.net/feed/ |
| 57 | This Week in 4n6 | https://thisweekin4n6.com/feed/atom/ |
| 58 | Okta Blog | https://www.okta.com/blog/feed/ |
| 59 | CyberArk Blog | https://www.cyberark.com/resources/threat-research-blog/feed/ |
| 60 | IBM Security Intelligence | https://securityintelligence.com/feed/ |
| 61 | Elastic Security Labs | https://www.elastic.co/security-labs/rss/feed.xml |
| 62 | Rubrik Blog | https://www.rubrik.com/blog/feed/ |
| 63 | Arctic Wolf Blog | https://arcticwolf.com/resources/category/blog/feed/ |
| 64 | Abnormal Security Blog | https://abnormalsecurity.com/blog/feed/ |
| 65 | Huntress Blog | https://www.huntress.com/blog/rss.xml |
| 66 | Lacework Blog | https://www.lacework.com/blog/feed/ |
| 67 | Aqua Security Blog | https://blog.aquasec.com/feed/ |
| 68 | Snyk Blog | https://snyk.io/blog/feed/ |
| 69 | WithSecure Blog | https://labs.withsecure.com/feed.rss |
| 70 | Secureworks Blog | https://www.secureworks.com/rss/research |
| 71 | Blackberry Threat Intel | https://blogs.blackberry.com/en/category/research-and-intelligence/feed |
| 72 | BeyondTrust Blog | https://www.beyondtrust.com/blog/rss.xml |
| 73 | Delinea Blog | https://delinea.com/blog/rss.xml |
| 74 | Netskope Blog | https://www.netskope.com/blog/feed |
| 75 | Cato Networks Blog | https://www.catonetworks.com/blog/feed/ |
| 76 | Dragos Blog | https://www.dragos.com/blog/feed/ |
| 77 | Claroty Blog | https://claroty.com/team82/blog/feed |

---

## Categories & Tracked Companies

Articles are categorized in priority order — first match wins.

| Priority | Category | Description |
|---|---|---|
| 1 | Zero-Day Exploits & Vulnerabilities | CVEs, RCEs, patch Tuesday, PoCs, etc. |
| 2 | Company & Service Acquisitions | M&A, funding rounds, IPOs (with false-positive exclusions) |
| 3 | Company columns (47 total) | Dedicated column per competitor — hidden when empty |
| 4 | General Security News | Catch-all for everything else |

### Tracked Companies (47)

| # | Company | # | Company |
|---|---|---|---|
| 1 | Trend Micro | 25 | CyberArk |
| 2 | CrowdStrike | 26 | IBM Security |
| 3 | Palo Alto Networks | 27 | Elastic Security |
| 4 | Fortinet | 28 | Rubrik |
| 5 | SentinelOne | 29 | Arctic Wolf |
| 6 | Microsoft Security | 30 | Abnormal Security |
| 7 | Mandiant | 31 | Huntress |
| 8 | Sophos | 32 | Lacework |
| 9 | Check Point | 33 | Aqua Security |
| 10 | Recorded Future | 34 | Snyk |
| 11 | Cisco Security | 35 | Rapid7 |
| 12 | Wiz | 36 | Tenable |
| 13 | Orca Security | 37 | Qualys |
| 14 | Trellix | 38 | Zscaler |
| 15 | Darktrace | 39 | WithSecure |
| 16 | ExtraHop | 40 | Secureworks |
| 17 | Vectra AI | 41 | Blackberry / Cylance |
| 18 | Proofpoint | 42 | BeyondTrust |
| 19 | Broadcom / Symantec | 43 | Delinea |
| 20 | Kaspersky | 44 | Netskope |
| 21 | Cybereason | 45 | Cato Networks |
| 22 | Barracuda | 46 | Dragos |
| 23 | Falco / Sysdig | 47 | Claroty |
| 24 | Okta | | |

---

## Setup

### GitHub Secrets required

| Secret | Description |
|---|---|
| `GMAIL_USERNAME` | Gmail address used to send notifications |
| `GMAIL_APP_PASSWORD` | 16-character Gmail App Password |

### Workflow

The workflow is defined in `.github/workflows/notify.yml` and runs on schedule or manually via **Actions → Cybersecurity Digest → Run workflow**.
