"""Regenerate the feed, category and module sections of README.md from daily_cybersecurity_digest.py.

Run after changing FEEDS, CATEGORIES or MODULE_TYPES:  python update_readme.py
Only the text between the <!-- name:start --> / <!-- name:end --> markers is replaced.
"""
import importlib.util
import re
import sys

SCRIPT = "daily_cybersecurity_digest.py"
README = "README.md"
SPECIAL_CATEGORIES = ("Zero-Day Exploits & Vulnerabilities", "Company & Service Acquisitions")


def load_script():
    spec = importlib.util.spec_from_file_location("digest", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def feed_groups(source: str) -> dict:
    """Group FEEDS entries by the '# ── Heading ──' comments above them in the script source."""
    start = source.index("FEEDS = [")
    block = source[start:source.index("\n]\n", start)]
    groups, current = {}, None
    for line in block.splitlines():
        heading = re.match(r"\s*#\s*\W+\s*(.+?)\s*\W{2,}\s*$", line)
        if heading:
            name = heading.group(1).strip()
            current = name[0].upper() + name[1:]
            groups[current] = []
            continue
        entry = re.match(r'\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)', line)
        if entry and current:
            groups[current].append((entry.group(1), entry.group(2)))
    return groups


def feeds_block(digest, groups: dict) -> str:
    total = sum(len(v) for v in groups.values())
    if total != len(digest.FEEDS):
        sys.exit(f"Parsed {total} feeds from the script source but FEEDS has {len(digest.FEEDS)}")
    out = [f"## RSS Feeds ({total})", ""]
    number = 1
    for title, feeds in groups.items():
        out += [f"### {title} ({len(feeds)})", "", "| # | Source | Feed URL |", "|---|---|---|"]
        for name, url in feeds:
            out.append(f"| {number} | {name} | {url} |")
            number += 1
        out.append("")
    return "\n".join(out).rstrip()


def categories_block(digest) -> str:
    companies = [c for c in digest.CATEGORIES if c not in SPECIAL_CATEGORIES]
    out = [
        "## Categories & Tracked Companies", "",
        "Articles are categorized by title keywords in priority order — first match wins.", "",
        "| Priority | Category | Description |", "|---|---|---|",
        "| 1 | Zero-Day Exploits & Vulnerabilities | CVEs, RCEs, patch Tuesday, PoCs, etc. |",
        "| 2 | Company & Service Acquisitions | M&A, funding rounds, IPOs (with false-positive exclusions) |",
        f"| 3 | Company rows ({len(companies)} total) | One row per tracked company — hidden when empty |",
        "| 4 | General Security News | Catch-all for everything else |", "",
        f"### Tracked Companies ({len(companies)})", "",
        "| # | Company | # | Company |", "|---|---|---|---|",
    ]
    half = (len(companies) + 1) // 2
    for i in range(half):
        left = f"| {i + 1} | {companies[i]} "
        j = i + half
        right = f"| {j + 1} | {companies[j]} |" if j < len(companies) else "| | |"
        out.append(left + right)
    return "\n".join(out)


def modules_block(digest) -> str:
    out = ["### Module types", "",
           f"Every article is tagged with up to {digest.MODULE_MAX_PER_ARTICLE} of these (strongest first):", ""]
    out += [f"- {m}" for m in digest.MODULE_TYPES]
    return "\n".join(out)


def replace_block(text: str, name: str, content: str) -> str:
    pattern = re.compile(rf"(<!-- {name}:start -->\n).*?(\n<!-- {name}:end -->)", re.S)
    if not pattern.search(text):
        sys.exit(f"Marker <!-- {name}:start --> ... <!-- {name}:end --> not found in {README}")
    return pattern.sub(lambda m: m.group(1) + content + m.group(2), text)


def main():
    digest = load_script()
    with open(SCRIPT, encoding="utf-8") as f:
        groups = feed_groups(f.read())
    with open(README, encoding="utf-8") as f:
        text = f.read()
    text = replace_block(text, "feeds", feeds_block(digest, groups))
    text = replace_block(text, "categories", categories_block(digest))
    text = replace_block(text, "modules", modules_block(digest))
    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"README updated: {len(digest.FEEDS)} feeds, {len(digest.CATEGORIES) - 2} companies, {len(digest.MODULE_TYPES)} module types")


if __name__ == "__main__":
    main()
