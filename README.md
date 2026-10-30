# Cyber Competitive Daily Feed

A GitHub Actions-powered cybersecurity news aggregator. It fetches articles from the RSS feeds listed below, removes duplicates, sorts them into categories and modules, keeps every article it has ever seen, and publishes an auto-updating dashboard twice daily.

**Dashboard:** https://lukan47.github.io/RSS/
**All articles (filter and export):** https://lukan47.github.io/RSS/archive/data/explorer.html

---

## Features

- Pulls from security news, government advisories, threat intel and vendor blogs (full list below)
- Dashboard shows the last 30 days, one row per company or topic, newest first — rows are only shown when there is news
- Article deduplication (URL match, string similarity, keyword overlap)
- First-match categorization: Zero-Day → Acquisitions → Company rows → General News
- **Module tagging** — each article is tagged with one or more security module types by keyword rules (no AI), shown on cards and usable as a filter
- **All-articles page** — every article ever collected, newest first, filterable by period, category, module, source and text; exports the filtered list as JSON or CSV
- **Details popup** — a *Details* button on every card opens the article's details with an *Open article* button and a one-article JSON/CSV export
- **Exports are generated in the browser** when you click a button in the popup or on the all-articles page; nothing is saved per click (the `archive/exports/` files are written on every scheduled run)
- **Full article text** is saved for export only (never shown on the dashboard) and can be included in any export
- Search box (press `/`), category filter, module filter and a history dropdown of previous digests (last 30 runs)
- Updates automatically at **6:00 AM and 6:00 PM PHT** via GitHub Actions
- Email notification via Gmail on each update

---

## How the data is stored

| Path | Contents |
|---|---|
| `index.html` | The current dashboard (last 30 days) |
| `archive/<date>.html` | A snapshot of each past dashboard |
| `archive/data/articles.json` | Every article ever collected: ID, title, link, source, date, category, modules, summary |
| `archive/data/fulltext/YYYY-MM.json` | Saved article text, one file per month, keyed by article ID |
| `archive/data/explorer.html` | The all-articles page (built from `explorer_template.html`) |
| `archive/exports/` | `digest.json` / `digest.csv` (last 30 days) and one file pair per category |

**Article IDs.** Every article has a stable 12-character ID (the first 12 hex characters of a SHA-256 of its cleaned-up URL: no scheme, `www.`, `#fragment`, `utm_*`/`fbclid`/`gclid` tracking parameters or trailing slash). The same URL always produces the same ID, so nothing has to be stored to keep IDs stable. The ID is the first field in every JSON export and the first column in every CSV export. The Details popup shows it and has a *Copy link* button; opening `archive/data/explorer.html#<id>` jumps straight to that article, and the all-articles search also matches IDs. If a publisher moves an article to a different URL it is treated as a new article.

`articles.json` was first built from the archived dashboards, so history starts at the oldest snapshot and has gaps where no snapshot exists. Article text is downloaded from each article page (or taken from the feed when it carries the full article); sites that block automated requests will have no saved text.

---

<!-- feeds:start -->
## RSS Feeds (90)

### General security news (18)

| # | Source | Feed URL |
|---|---|---|
| 1 | Krebs on Security | https://krebsonsecurity.com/feed/ |
| 2 | The Hacker News | https://feeds.feedburner.com/TheHackersNews |
| 3 | Bleeping Computer | https://www.bleepingcomputer.com/feed/ |
| 4 | SANS ISC | https://isc.sans.edu/rssfeed_full.xml |
| 5 | SecurityWeek | https://feeds.feedburner.com/securityweek |
| 6 | Dark Reading | https://www.darkreading.com/rss.xml |
| 7 | Schneier on Security | https://www.schneier.com/feed/atom/ |
| 8 | Wired Security | https://www.wired.com/feed/category/security/latest/rss |
| 9 | Ars Technica Security | https://arstechnica.com/tag/security/feed/ |
| 10 | Troy Hunt | https://feeds.feedburner.com/TroyHunt |
| 11 | Infosecurity Magazine | https://www.infosecurity-magazine.com/rss/news/ |
| 12 | Help Net Security | https://www.helpnetsecurity.com/feed/ |
| 13 | SC Magazine | https://www.scmagazine.com/feed |
| 14 | Graham Cluley | https://grahamcluley.com/feed/ |
| 15 | The CyberWire | https://thecyberwire.com/feeds/rss.xml |
| 16 | Security Affairs | https://securityaffairs.com/feed |
| 17 | CSO Online | https://www.csoonline.com/feed/ |
| 18 | Risky Business News | https://risky.biz/feeds/risky-business-news/ |

### Government / advisories (4)

| # | Source | Feed URL |
|---|---|---|
| 19 | CISA Advisories | https://www.cisa.gov/cybersecurity-advisories/all.xml |
| 20 | NCSC UK | https://www.ncsc.gov.uk/api/1/services/v1/all-rss-feed.xml |
| 21 | CIRCL KEV (exploited CVEs) | https://vulnerability.circl.lu/known-exploited-vulnerabilities.rss |
| 22 | Australian ACSC | https://www.cyber.gov.au/rss.xml |

### Threat intelligence (10)

| # | Source | Feed URL |
|---|---|---|
| 23 | Talos Intelligence | https://blog.talosintelligence.com/rss/ |
| 24 | Google Project Zero | https://googleprojectzero.blogspot.com/feeds/posts/default |
| 25 | Exploit-DB | https://www.exploit-db.com/rss.xml |
| 26 | Google Threat Intel (Mandiant) | https://cloudblog.withgoogle.com/topics/threat-intelligence/rss/ |
| 27 | Recorded Future | https://www.recordedfuture.com/feed |
| 28 | Check Point Research | https://research.checkpoint.com/feed/ |
| 29 | Cyble | https://cyble.com/blog/feed/ |
| 30 | VirusTotal Blog | https://blog.virustotal.com/feeds/posts/default |
| 31 | Zero Day Initiative Blog | https://www.zerodayinitiative.com/blog/?format=rss |
| 32 | ZDI Published Advisories | https://www.zerodayinitiative.com/rss/published/ |

### Vendor blogs (58)

| # | Source | Feed URL |
|---|---|---|
| 33 | Trend Micro Research | https://feeds.feedburner.com/TrendMicroResearch |
| 34 | CrowdStrike Blog | https://www.crowdstrike.com/blog/feed/ |
| 35 | Palo Alto Unit 42 | https://unit42.paloaltonetworks.com/feed/ |
| 36 | Fortinet Threat Research | https://feeds.fortinet.com/fortinet/blog/threat-research |
| 37 | Microsoft Security Blog | https://www.microsoft.com/en-us/security/blog/feed/ |
| 38 | SentinelOne Blog | https://www.sentinelone.com/blog/feed/ |
| 39 | Rapid7 Blog | https://blog.rapid7.com/rss/ |
| 40 | Tenable Blog | https://www.tenable.com/blog/feed |
| 41 | Qualys Blog | https://blog.qualys.com/feed |
| 42 | Zscaler ThreatLabz | https://www.zscaler.com/blogs/feeds/security-research |
| 43 | Kaspersky Blog | https://www.kaspersky.com/blog/feed/ |
| 44 | Securelist (Kaspersky) | https://securelist.com/feed/ |
| 45 | Sophos News - Threat Research | https://news.sophos.com/en-us/category/threat-research/feed/ |
| 46 | Sophos News - SecOps | https://news.sophos.com/en-us/category/security-operations/feed/ |
| 47 | ESET WeLiveSecurity | https://feeds.feedburner.com/eset/blog |
| 48 | SentinelLabs | https://www.sentinelone.com/labs/feed/ |
| 49 | Check Point Blog | https://blog.checkpoint.com/feed/ |
| 50 | Bitdefender Business Insights | https://businessinsights.bitdefender.com/rss.xml |
| 51 | Trend Micro SimplySecurity | https://feeds.feedburner.com/TrendMicroSimplySecurity |
| 52 | CrowdStrike IR News | https://ir.crowdstrike.com/rss/news-releases.xml |
| 53 | Fortinet IR News | https://investor.fortinet.com/rss/news-releases.xml |
| 54 | Palo Alto IR News | https://investors.paloaltonetworks.com/rss/news-releases.xml |
| 55 | Qualys IR News | https://investor.qualys.com/rss/news-releases.xml |
| 56 | Cybereason Blog | https://www.cybereason.com/blog/rss.xml |
| 57 | Falco / Sysdig Blog | https://sysdig.com/feed/ |
| 58 | Wiz Blog | https://www.wiz.io/feed/rss.xml |
| 59 | Orca Security Blog | https://orca.security/resources/blog/feed/ |
| 60 | Darktrace Blog | https://www.darktrace.com/blog/rss.xml |
| 61 | Vectra AI Blog | https://www.vectra.ai/blog/rss.xml |
| 62 | Proofpoint Blog | https://www.proofpoint.com/us/rss.xml |
| 63 | Broadcom/Symantec Blog | https://symantec-enterprise-blogs.security.com/blogs/rss/v1/blogs/rss.xml/221 |
| 64 | The Register Security | https://www.theregister.com/security/headlines.atom |
| 65 | Databreaches.net | https://www.databreaches.net/feed/ |
| 66 | This Week in 4n6 | https://thisweekin4n6.com/feed/atom/ |
| 67 | Okta Blog | https://sec.okta.com/rss.xml |
| 68 | CyberArk Blog | https://www.cyberark.com/feed/ |
| 69 | Elastic Security Labs | https://www.elastic.co/security-labs/rss/feed.xml |
| 70 | Rubrik Blog | https://www.rubrik.com/blog/feed/ |
| 71 | Arctic Wolf Blog | https://arcticwolf.com/resources/category/blog/feed/ |
| 72 | Huntress Blog | https://www.huntress.com/blog/rss.xml |
| 73 | Aqua Security Blog | https://www.aquasec.com/feed/ |
| 74 | Snyk Blog | https://snyk.io/blog/feed/ |
| 75 | BeyondTrust Blog | https://www.beyondtrust.com/blog/rss.xml |
| 76 | Delinea Blog | https://delinea.com/blog/rss.xml |
| 77 | Trend Micro Newsroom | https://newsroom.trendmicro.com/news-releases?pagetemplate=rss |
| 78 | Malwarebytes Labs | https://www.malwarebytes.com/blog/feed/index.xml |
| 79 | AWS Security Blog | https://aws.amazon.com/blogs/security/feed/ |
| 80 | Cloudflare Security | https://blog.cloudflare.com/tag/security/rss/ |
| 81 | Datadog Security Labs | https://securitylabs.datadoghq.com/rss/feed.xml |
| 82 | GitHub Security Blog | https://github.blog/security/feed/ |
| 83 | Socket | https://socket.dev/api/blog/feed.atom |
| 84 | JFrog Blog | https://jfrog.com/blog/feed/ |
| 85 | Sonatype Blog | https://www.sonatype.com/blog/rss.xml |
| 86 | Varonis Blog | https://www.varonis.com/blog/rss.xml |
| 87 | Silverfort Blog | https://www.silverfort.com/blog/feed/ |
| 88 | KnowBe4 Blog | https://blog.knowbe4.com/rss.xml |
| 89 | Cofense Blog | https://cofense.com/feed/ |
| 90 | Cato Networks Blog | https://www.catonetworks.com/blog/feed/ |
<!-- feeds:end -->

---

<!-- categories:start -->
## Categories & Tracked Companies

Articles are categorized by title keywords in priority order — first match wins.

| Priority | Category | Description |
|---|---|---|
| 1 | Zero-Day Exploits & Vulnerabilities | CVEs, RCEs, patch Tuesday, PoCs, etc. |
| 2 | Company & Service Acquisitions | M&A, funding rounds, IPOs (with false-positive exclusions) |
| 3 | Company rows (49 total) | One row per tracked company — hidden when empty |
| 4 | General Security News | Catch-all for everything else |

### Tracked Companies (49)

| # | Company | # | Company |
|---|---|---|---|
| 1 | Trend Micro | 26 | Okta |
| 2 | CrowdStrike | 27 | CyberArk |
| 3 | Palo Alto Networks | 28 | IBM Security |
| 4 | Fortinet | 29 | Elastic Security |
| 5 | SentinelOne | 30 | Rubrik |
| 6 | Microsoft Security | 31 | Arctic Wolf |
| 7 | Mandiant | 32 | Abnormal Security |
| 8 | Sophos | 33 | Huntress |
| 9 | ESET | 34 | Lacework |
| 10 | Bitdefender | 35 | Aqua Security |
| 11 | Check Point | 36 | Snyk |
| 12 | Recorded Future | 37 | Rapid7 |
| 13 | Cisco Security | 38 | Tenable |
| 14 | Wiz | 39 | Qualys |
| 15 | Orca Security | 40 | Zscaler |
| 16 | Trellix | 41 | WithSecure |
| 17 | Darktrace | 42 | Secureworks |
| 18 | ExtraHop | 43 | Blackberry / Cylance |
| 19 | Vectra AI | 44 | BeyondTrust |
| 20 | Proofpoint | 45 | Delinea |
| 21 | Broadcom / Symantec | 46 | Netskope |
| 22 | Kaspersky | 47 | Cato Networks |
| 23 | Cybereason | 48 | Dragos |
| 24 | Barracuda | 49 | Claroty |
| 25 | Falco / Sysdig | | |
<!-- categories:end -->

---

## Modules

Modules describe which part of a security product an article is about. An article can belong to several. They are assigned by keyword rules in `daily_cybersecurity_digest.py` (`_MODULE_RULES`): a specific term in the title qualifies on its own, while body-only evidence needs several mentions. Articles that match nothing are **Other/General**, or **N/A** when there was no text beyond the title.

<!-- modules:start -->
### Module types

Every article is tagged with up to 4 of these (strongest first):

- AI Security
- Attack Path Prediction
- Attack Surface Discovery
- Cloud IPS
- Cloud Risk Management
- Cloud Security Posture Management
- Code Security
- Compliance Management
- Container Security
- Cyber Risk Quantification
- Data Security Posture Management
- Email and Collaboration Security
- Endpoint Security
- File Security
- Identity Security Posture Management
- Mobile Security
- Network Security
- Phishing Simulations
- Server & Workload Protection
- Threat Intelligence
- Threat and Exposure Management
- Vulnerability Management
- Zero Trust Secure Access
- Other/General
- N/A
<!-- modules:end -->

---

## Keeping this README accurate

The feed, category and module sections above are generated from the script. After editing `FEEDS`, `CATEGORIES` or `MODULE_TYPES`, run:

```bash
python update_readme.py
```

---

## Setup

### GitHub Secrets required

| Secret | Description |
|---|---|
| `GMAIL_USERNAME` | Gmail address used to send notifications |
| `GMAIL_APP_PASSWORD` | 16-character Gmail App Password |

### Workflow

The workflow is defined in `.github/workflows/notify.yml` and runs on schedule or manually via **Actions → Cybersecurity Digest → Run workflow**.

### Running locally

The script uses only the Python standard library (Python 3.10+). From the repository folder:

```bash
python daily_cybersecurity_digest.py
```

Set `FULLTEXT_BUDGET_S` (seconds, default 420) to allow longer article-text downloads on a run.

### How download failures are counted

Each failed download is recorded with its reason (`archive/data/fulltext/*.json`, field `error`). Hard failures (403, empty page, SSL certificate errors) use up one of an article's 3 attempts. Temporary ones (timeouts, 5xx, rate limits) are retried after a short pause and counted separately, so a slow site does not use up an article's attempts.

### Optional: headless-browser fallback

Some sites reject plain downloads but accept a real browser. If [Playwright](https://playwright.dev/python/) is installed, pages that fail with 401/403/406/451, an SSL certificate error or an empty page are retried once in headless Chromium. Without Playwright nothing changes.

```bash
pip install playwright
playwright install chromium
```

Set `USE_BROWSER=0` to switch it off and `BROWSER_BUDGET_S` (default 300 seconds per run) to change its time limit. It is a plain browser: it does not solve CAPTCHAs or hide that it is automated, so sites that block headless browsers stay without text. In a test it recovered CISA pages but not Dark Reading, databreaches.net, CrowdStrike investor news, Fortra or Fortinet investor news.

To use it in GitHub Actions, add these steps to `.github/workflows/notify.yml` before the step that runs the script:

```yaml
      - name: Cache Playwright browser
        uses: actions/cache@v4
        with:
          path: ~/.cache/ms-playwright
          key: playwright-chromium-${{ runner.os }}-v1

      - name: Install Playwright (optional browser fallback)
        continue-on-error: true
        run: |
          pip install playwright
          playwright install --with-deps chromium
```

### Retrying articles with missing or partial text

Each run tries to download the text of articles that have none, up to 3 attempts per article; after that an article is left alone (typically a site that blocks automated downloads). To try them all again, ignoring the attempt limit, run from a normal internet connection (a home connection is blocked less often than GitHub's servers):

```bash
python daily_cybersecurity_digest.py --retry-text
```

This only re-downloads article text — it does not fetch feeds or rebuild any page. Articles with no text go first, then ones holding only a feed excerpt or text imported from a backup. The default time limit is 30 minutes (`FULLTEXT_BUDGET_S` overrides it). Afterwards commit `archive/data/` (the article store and `fulltext/` files) and push.
