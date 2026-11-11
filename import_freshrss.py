"""Backfill the article store from a FreshRSS export (one JSON file per feed, plus the starred file).

    python import_freshrss.py "G:\\path\\to\\freshrss_export_folder" [--dry-run]

Only articles from feeds this script tracks (or the aliases below, which are the same publications under another
feed URL) are imported, and only when neither their URL ID nor their title is already in archive/data/articles.json.
It is safe to run again. The next scheduled run classifies and groups the new articles and fetches their full text.
"""
import glob
import html
import importlib.util
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
spec = importlib.util.spec_from_file_location("digest", os.path.join(HERE, "daily_cybersecurity_digest.py"))
digest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(digest)

# The same publications as a tracked feed, reached through another feed URL
ALIASES = {
    "thehackernews.com/feeds/posts/default": "The Hacker News",
    "securityweek.com/feed": "SecurityWeek",
    "rapid7.com/rss.xml": "Rapid7 Blog",
    "feeds.feedburner.com/tenable/qaxl": "Tenable Blog",
    "crowdstrike.com/en-us/blog/feed": "CrowdStrike Blog",
}


def feed_key(url: str) -> str:
    p = urlsplit(url.strip())
    return p.netloc.lower().removeprefix("www.") + p.path.rstrip("/").lower() + ("?" + p.query.lower() if p.query else "")


def title_key(title: str) -> str:
    return re.sub(r"\W+", " ", (title or "").lower()).strip()


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if not args:
        sys.exit(__doc__)
    folder = args[0]
    sources = {feed_key(url): name for name, url in digest.FEEDS}
    for alias, name in ALIASES.items():
        if name not in dict(digest.FEEDS):
            sys.exit(f"Alias target {name!r} is not in FEEDS")
        sources[alias] = name

    master = digest.load_master()
    known_titles = {title_key(a["title"]) for a in master.values()}
    files = sorted(glob.glob(os.path.join(folder, "feed_*.json"))) + glob.glob(os.path.join(folder, "starred_*.json"))
    if not files:
        sys.exit(f"No feed_*.json files in {folder}")

    added, skipped = Counter(), Counter()
    for path in files:
        with open(path, encoding="utf-8") as f:
            items = json.load(f)["items"]
        for it in items:
            link = (it.get("canonical") or it.get("alternate") or [{}])[0].get("href", "")
            source = sources.get(feed_key((it.get("origin") or {}).get("feedUrl", "")))
            if not link or not source:
                skipped["not a tracked feed"] += 1
                continue
            aid = digest.article_id(link)
            title = html.unescape(it.get("title", "")).strip()
            if aid in master:
                skipped["already stored"] += 1
                continue
            if title_key(title) in known_titles:
                skipped["same title already stored"] += 1
                continue
            published = it.get("published")
            date = datetime.fromtimestamp(int(published), timezone.utc).isoformat() if published else None
            excerpt = " ".join(html.unescape((it.get("content") or {}).get("content", "")).split())
            entry = {"id": aid, "source": source, "title": title, "link": link, "date": date,
                     "context": "" if excerpt.startswith("http") or len(excerpt) < 40 else excerpt[:300], "podcast": False, "story": aid}
            entry["category"] = digest.categorize(entry)
            entry["vendor"] = digest.vendor_of(entry)
            entry["modules"] = digest.classify_modules({**entry, "full_text": ""})
            master[aid] = entry
            known_titles.add(title_key(title))
            added[source] += 1

    print(f"{sum(added.values())} articles to add, from {len(added)} feeds ({'dry run, nothing saved' if dry else 'saving'}):")
    for source, n in added.most_common():
        print(f"  {n:5d}  {source}")
    print("skipped:", dict(skipped))
    if not dry and added:
        digest.save_master(master, datetime.now(digest.PHT).strftime("%Y-%m-%d %H:%M PHT"))
        print(f"Saved {len(master)} articles to {digest.ARTICLES_FILE}")


if __name__ == "__main__":
    main()
