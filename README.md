# CI Overwatch

A GitHub Actions-powered cybersecurity news aggregator. It fetches articles from the RSS feeds listed below, removes duplicates, sorts them into categories and modules, keeps every article it has ever seen, and publishes an auto-updating dashboard three times a day.

**Dashboard:** https://lukan47.github.io/RSS/
**All articles (filter and export):** https://lukan47.github.io/RSS/archive/data/explorer.html

---

## Features

- Pulls from security news, government advisories, threat intel and vendor blogs (full list below)
- Dashboard shows the last 30 days, newest first, with one row per **category** or one row per **vendor** (the *Rows by* switch) — rows are only shown when there is news
- One stored entry per article URL. Articles that cover the same story are all kept and grouped into a story (see *Stories* below); nothing is dropped for being similar
- **Categories and vendors are separate.** Every article has one category (what it is about: Vulnerabilities & Patching, Attacks / Breaches / Threat Intel, Business & Industry News, Policy / Legal / Compliance, Product & Roadmap) and one vendor (who it is about, if a tracked vendor is named). Both come from keyword rules on the title; see *Categories & Vendors* below
- **Trending this week** — a carousel above the rows shows the stories covered by the most distinct sources in the last 7 days, three at a time (arrows, dots, or automatic rotation that pauses on hover). *View coverage* lists every article in the story, and can export the whole story as JSON or CSV (optionally with the saved full text)
- **Same-topic grouping** — articles about the same event form a *story*. A *Group same topic* button on the dashboard shows one card per story in each row with a *+N related* badge (click it to see the whole story); turning it off shows every article. The all-articles page has a *Topics* view with search, sort (most covered / newest) and an "only topics with 2+ articles" option. Nothing is deleted — grouping only changes what is shown
- **Historical baseline** — the *Baseline* view on the all-articles page compares the last 7, 14 or 30 days with the daily average of the previous 4, 8 or 12 weeks, per category, vendor or module, and recalculates against the newest article every time the page loads. Each row shows the count, the expected count, the change, a 12-week sparkline and a status (Spike: 50%+ above baseline and 2+ standard deviations; Up: 25%+ and 1+; Down; New; Normal). Feeds that were not yet collected during the baseline period and weeks with no collection are left out, and the page says so. Click a row to see its articles; the export buttons export the table
- **Movers strip** — under the carousel, the vendors, modules and categories that rose furthest above their baseline this week (same maths as the Baseline view, computed on every run into `archive/data/movers.json`). Each chip opens the matching articles
- **Roadmap view** — on the all-articles page, *Product & Roadmap* news as a timeline per vendor, tagged Launch / Preview / General availability / Integration / Retirement from the title; filter by kind, include untracked vendors, export as JSON or CSV
- **Weekly briefing** — *Briefing .md* and *Briefing .doc* on the all-articles page build a briefing for the newest 7 days: week-on-week volume, spikes against the baseline, top stories, each category's headlines, and watchlist hits. The Word file is an HTML document saved as `.doc`; Word opens it directly
- **Saved views** — *Copy link* gives a URL that reopens the all-articles page with the same view and filters (for example `explorer.html#view=baseline&by=vendor&win=14`); *Save view* keeps named views in your browser
- **Watchlist** — vendors and keywords in `watchlist.json` get a star on matching cards, a *Watchlist* filter on the dashboard and the all-articles page, a section in the briefing, and an alert in the e-mail (see below)
- **Source health** — `archive/data/sources.html` lists every feed with its latest fetch result, failures in a row, latest article and 7 / 30-day counts, and flags feeds that are Failing, Stale (no new article for 14 days) or Retired
- **Module tagging** — each article is tagged with one or more security module types by keyword rules (no AI), shown on cards and usable as a filter
- **All-articles page** — every article ever collected, newest first, filterable by period, category, vendor, module, source and text; exports the filtered list as JSON or CSV
- **Details popup** — a *Details* button on every card opens the article's details with an *Open article* button and a one-article JSON/CSV export. All of an article's tags are shown as chips: its category, its vendor, every module, and *Podcast* / *Transcript available* where they apply
- **Podcasts** — episodes carry a microphone icon on cards and a *Podcast* tag, can be filtered on the all-articles page (*Type*), and have a `podcast` field in JSON exports and a `Type` column in CSV exports. Where a transcript is published (feed transcript tag, or the show's own transcript page: SANS Stormcast, CyberWire, Security Now, Smashing Security), it is saved as the episode's text and the card's summary snippet and module tags are taken from it
- **Exports are generated in the browser** when you click a button in the popup or on the all-articles page; nothing is saved per click (the `archive/exports/` files are written on every scheduled run)
- **Full article text** is saved for export only (never shown on the dashboard) and can be included in any export
- Search box (press `/`), category, vendor and module filters and a history dropdown of previous digests (last 30 runs)
- Updates automatically three times a day, at about **6 AM, 2 PM and 10 PM PHT**, via GitHub Actions
- Email notification via Gmail on each update

## Watchlist and e-mail alert

`watchlist.json` (repository root) lists what to watch:

```json
{ "vendors": ["Trend Micro", "CrowdStrike"], "keywords": ["vision one", "~kev"] }
```

Vendors must be spelled as in the tracked-vendor list below. Keywords match the article title; a keyword starting with `~` only matches as a whole word. Edit the file on GitHub; the next run picks it up.

Each run also writes `WATCHLIST_FOUND`, `WATCHLIST_COUNT`, `WATCHLIST_TEXT` and `WATCHLIST_HTML` (matches from the last 9 hours) to the workflow environment. To put them in the e-mail, edit `.github/workflows/notify.yml` on GitHub (the push token cannot change workflow files) and add to the *Send Gmail notification* step:

```yaml
          subject: "Cybersecurity Digest — ${{ env.TODAY }} (${{ env.WATCHLIST_COUNT }} watchlist)"
          body: |
            Your cybersecurity digest has been updated.
            View it here: https://lukan47.github.io/RSS/
            Watchlist matches: ${{ env.WATCHLIST_TEXT }}
          html_body: |
            <p style="font-family:Arial,sans-serif;font-size:15px;">Your cybersecurity digest has been updated.</p>
            <p style="font-family:Arial,sans-serif;font-size:15px;"><b>Watchlist matches (${{ env.WATCHLIST_COUNT }}):</b></p>
            ${{ env.WATCHLIST_HTML }}
```

(Keep the existing *View Digest* button in `html_body`.)

---

## How the data is stored

| Path | Contents |
|---|---|
| `index.html` | The current dashboard (last 30 days) |
| `archive/<date>.html` | A snapshot of each past dashboard |
| `archive/data/articles.json` | Every article ever collected: ID, story ID, title, link, source, date, category, vendor, modules, summary, `podcast` / `transcript` flags |
| `archive/data/fulltext/YYYY-MM.json` | Saved article text, one file per month, keyed by article ID |
| `archive/data/explorer.html` | The all-articles page (built from `explorer_template.html`) |
| `archive/data/sources.html`, `source_health.json` | The source-health page (from `sources_template.html`) and its data |
| `archive/data/movers.json` | The groups shown in the dashboard's movers strip |
| `watchlist.json` | Vendors and keywords to watch (edited by hand) |
| `archive/exports/` | `digest.json` / `digest.csv` (last 30 days) and one file pair per category (`digest__category__*`) and per vendor (`digest__vendor__*`) |

**Article IDs.** Every article has a stable 12-character ID (the first 12 hex characters of a SHA-256 of its cleaned-up URL: no scheme, `www.`, `#fragment`, `utm_*`/`fbclid`/`gclid` tracking parameters or trailing slash). The same URL always produces the same ID, so nothing has to be stored to keep IDs stable. The ID is the first field in every JSON export and the first column in every CSV export. The Details popup shows it and has a *Copy link* button; opening `archive/data/explorer.html#<id>` jumps straight to that article, and the all-articles search also matches IDs. If a publisher moves an article to a different URL it is treated as a new article.

**Stories.** Every article also carries a `story` ID (the ID of the story's earliest article); it is the second field/column in exports. Two articles join the same story when they were published within 7 days of each other and share a CVE ID, a coined name (e.g. `PHP2Shell`, `FortiBleed`), or enough distinctive title words. Podcasts, weekly roundups and templated advisory feeds (Exploit-DB, CISA, ZDI) only join a story through a shared CVE ID, and a gap of more than 4 days starts a new story. The trending score is 2 per distinct source, +3 if the coverage mentions active exploitation or a zero-day, +2 if the newest article is under 48 hours old (+1 under 96 hours), and a small bonus per article; a story needs at least 3 sources in the last 7 days to qualify. The rules are in `assign_stories` and `trending_stories` in `daily_cybersecurity_digest.py`.

`articles.json` was first built from the archived dashboards, so history starts at the oldest snapshot and has gaps where no snapshot exists. Article text is downloaded from each article page (or taken from the feed when it carries the full article); sites that block automated requests will have no saved text.

---

<!-- feeds:start -->
## RSS Feeds (101)

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

### Vendor blogs (65)

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
| 45 | ESET WeLiveSecurity | https://feeds.feedburner.com/eset/blog |
| 46 | SentinelLabs | https://www.sentinelone.com/labs/feed/ |
| 47 | Check Point Blog | https://blog.checkpoint.com/feed/ |
| 48 | Bitdefender Business Insights | https://businessinsights.bitdefender.com/rss.xml |
| 49 | Trend Micro SimplySecurity | https://feeds.feedburner.com/TrendMicroSimplySecurity |
| 50 | CrowdStrike IR News | https://ir.crowdstrike.com/rss/news-releases.xml |
| 51 | Fortinet IR News | https://investor.fortinet.com/rss/news-releases.xml |
| 52 | Palo Alto IR News | https://investors.paloaltonetworks.com/rss/news-releases.xml |
| 53 | Qualys IR News | https://investor.qualys.com/rss/news-releases.xml |
| 54 | Cybereason Blog | https://www.cybereason.com/blog/rss.xml |
| 55 | Falco / Sysdig Blog | https://sysdig.com/feed/ |
| 56 | Wiz Blog | https://www.wiz.io/feed/rss.xml |
| 57 | Orca Security Blog | https://orca.security/resources/blog/feed/ |
| 58 | Darktrace Blog | https://www.darktrace.com/blog/rss.xml |
| 59 | Vectra AI Blog | https://www.vectra.ai/blog/rss.xml |
| 60 | Proofpoint Blog | https://www.proofpoint.com/us/rss.xml |
| 61 | Broadcom/Symantec Blog | https://symantec-enterprise-blogs.security.com/blogs/rss/v1/blogs/rss.xml/221 |
| 62 | The Register Security | https://www.theregister.com/security/headlines.atom |
| 63 | Databreaches.net | https://www.databreaches.net/feed/ |
| 64 | This Week in 4n6 | https://thisweekin4n6.com/feed/atom/ |
| 65 | Okta Blog | https://sec.okta.com/rss.xml |
| 66 | CyberArk Blog | https://www.cyberark.com/feed/ |
| 67 | Elastic Security Labs | https://www.elastic.co/security-labs/rss/feed.xml |
| 68 | Rubrik Blog | https://www.rubrik.com/blog/feed/ |
| 69 | Arctic Wolf Blog | https://arcticwolf.com/resources/category/blog/feed/ |
| 70 | Huntress Blog | https://www.huntress.com/blog/rss.xml |
| 71 | Aqua Security Blog | https://www.aquasec.com/feed/ |
| 72 | Snyk Blog | https://snyk.io/blog/feed/ |
| 73 | BeyondTrust Blog | https://www.beyondtrust.com/blog/rss.xml |
| 74 | Delinea Blog | https://delinea.com/blog/rss.xml |
| 75 | Trend Micro Newsroom | https://newsroom.trendmicro.com/news-releases?pagetemplate=rss |
| 76 | Malwarebytes Labs | https://www.malwarebytes.com/blog/feed/index.xml |
| 77 | AWS Security Blog | https://aws.amazon.com/blogs/security/feed/ |
| 78 | Cloudflare Security | https://blog.cloudflare.com/tag/security/rss/ |
| 79 | Datadog Security Labs | https://securitylabs.datadoghq.com/rss/feed.xml |
| 80 | GitHub Security Blog | https://github.blog/security/feed/ |
| 81 | Socket | https://socket.dev/api/blog/feed.atom |
| 82 | JFrog Blog | https://jfrog.com/blog/feed/ |
| 83 | Sonatype Blog | https://www.sonatype.com/blog/rss.xml |
| 84 | Varonis Blog | https://www.varonis.com/blog/rss.xml |
| 85 | Silverfort Blog | https://www.silverfort.com/blog/feed/ |
| 86 | KnowBe4 Blog | https://blog.knowbe4.com/rss.xml |
| 87 | Cofense Blog | https://cofense.com/feed/ |
| 88 | Cato Networks Blog | https://www.catonetworks.com/blog/feed/ |
| 89 | Sophos Blogs | https://www.sophos.com/en-us/blog/feed?id=blt6f15f4f7deaf4242 |
| 90 | Fortinet Blog | https://feeds.fortinet.com/fortinet/blogs |
| 91 | Cisco Newsroom | https://newsroom.cisco.com/c/services/i/servlets/newsroom/rssfeed.json |
| 92 | Cloudflare Blog | https://blog.cloudflare.com/rss/ |
| 93 | Tenable Cyber Exposure Alerts | https://www.tenable.com/blog/cyber-exposure-alerts/feed |
| 94 | Tenable in the News | https://www.tenable.com/media/in-the-news/feed |
| 95 | Tenable Product Security Advisories | https://www.tenable.com/security/feed |
| 96 | Trend Micro Media Coverage | https://newsroom.trendmicro.com/media-coverage?pagetemplate=rss |
| 97 | Microsoft Official Blog | https://blogs.microsoft.com/feed/ |

### Podcasts (4)

| # | Source | Feed URL |
|---|---|---|
| 98 | CyberWire Daily | https://rss.pdrl.fm/85df76/feeds.megaphone.fm/cyberwire-daily-podcast |
| 99 | Darknet Diaries | https://feeds.megaphone.fm/darknetdiaries |
| 100 | Talos Takes | https://rss.buzzsprout.com/2018149.rss |
| 101 | Security Now | https://feeds.twit.tv/sn.xml |
<!-- feeds:end -->

---

<!-- categories:start -->
## Categories & Vendors

Every article has one **category** (what it is about) and one **vendor** (who it is about, or none). The two are independent: a CrowdStrike zero-day is *Vulnerabilities & Patching* and *CrowdStrike*. Both are decided from the title by keyword rules in `daily_cybersecurity_digest.py` (`CATEGORIES`, `VENDORS`); a keyword starting with `~` only matches as a whole word, e.g. `~armis` does not match "alarmist". The dashboard shows one row per category or per vendor (*Rows by* switch) and filters by both. Every run re-applies the current rules to the whole history.

### Categories

Priority order — the first match wins. Titles that match nothing fall back to the category of the feed they came from (`SOURCE_CATEGORY`, e.g. threat-research blogs → Attacks), then to *General Security News*.

| Priority | Category | Covers |
|---|---|---|
| 1 | Vulnerabilities & Patching | Zero-days, CVEs, PoCs, Patch Tuesday, advisories and patches |
| 2 | Business & Industry News | M&A, funding, earnings, executive changes, partnerships, analyst recognition (acquisition keywords have false-positive exclusions) |
| 3 | Policy, Legal & Compliance | Regulation, law enforcement, lawsuits and fines, privacy laws, standards and government guidance |
| 4 | Product & Roadmap | Vendor launches, new features, GA / preview / beta, integrations, roadmap and end-of-life announcements |
| 5 | Attacks, Breaches & Threat Intel | Ransomware, breaches and data leaks, cybercrime, malware analysis, threat actors and campaigns |
| 6 | General Security News | Catch-all for everything else |

### Tracked Vendors (67)

An article from a vendor's own blog or news feed that names no vendor in its title is filed under that vendor (`SOURCE_VENDOR`). Articles that name no tracked vendor show as *No Specific Vendor*.

| # | Vendor | # | Vendor |
|---|---|---|---|
| 1 | 1Password | 35 | Huntress |
| 2 | Abnormal Security | 36 | IBM Security |
| 3 | Akamai Technologies | 37 | Juniper Networks |
| 4 | Aqua Security | 38 | Kaspersky |
| 5 | Arctic Wolf | 39 | Lacework |
| 6 | Armis | 40 | Mandiant |
| 7 | Automox | 41 | Microsoft Security |
| 8 | Barracuda | 42 | Mimecast |
| 9 | BeyondTrust | 43 | Netskope |
| 10 | Bitdefender | 44 | Nozomi Networks |
| 11 | Bitwarden | 45 | Okta |
| 12 | Blackberry / Cylance | 46 | Orca Security |
| 13 | Broadcom / Symantec | 47 | Palo Alto Networks |
| 14 | Cato Networks | 48 | Ping Identity |
| 15 | Check Point | 49 | Proofpoint |
| 16 | Checkmarx | 50 | Qualys |
| 17 | Cisco Security | 51 | Rapid7 |
| 18 | Claroty | 52 | Recorded Future |
| 19 | Cloudflare | 53 | Rubrik |
| 20 | Cohesity | 54 | Secureworks |
| 21 | CrowdStrike | 55 | SentinelOne |
| 22 | CyberArk | 56 | Snyk |
| 23 | Cybereason | 57 | Sophos |
| 24 | Darktrace | 58 | Splunk |
| 25 | Delinea | 59 | Tenable |
| 26 | Dragos | 60 | Trellix |
| 27 | Elastic Security | 61 | Trend Micro |
| 28 | ESET | 62 | Varonis |
| 29 | ExtraHop | 63 | Vectra AI |
| 30 | F5 | 64 | Veracode |
| 31 | Falco / Sysdig | 65 | WithSecure |
| 32 | Flashpoint | 66 | Wiz |
| 33 | Forescout | 67 | Zscaler |
| 34 | Fortinet | | |
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

The workflow is defined in `.github/workflows/notify.yml` and is the only workflow in the repository. It runs three times a day, at 6:07 AM, 2:07 PM and 10:07 PM PHT (cron `7 22`, `7 6` and `7 14` in UTC; the minute avoids GitHub's busiest moment at the top of the hour), or manually via **Actions → Cybersecurity Digest → Run workflow**.

### Backfilling from a FreshRSS export

`python import_freshrss.py "<export folder>"` adds articles from a FreshRSS export (the per-feed `feed_*.json` files and the starred file) to `archive/data/articles.json`. It only imports feeds this script tracks, plus the aliases listed at the top of the file (the same publication under another feed URL), and skips anything whose URL or title is already stored. Add `--dry-run` to preview. It is safe to run again; the next scheduled run classifies and groups the new articles and fetches their text over the following runs.

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
