"""Regenerate the feed, category and module sections of README.md from daily_cybersecurity_digest.py.

Run after changing FEEDS, CATEGORIES or MODULE_TYPES:  python update_readme.py
Only the text between the <!-- name:start --> / <!-- name:end --> markers is replaced.
"""
import importlib.util
import re
import sys

SCRIPT = "daily_cybersecurity_digest.py"
README = "README.md"
CATEGORY_NOTES = {
    "Vulnerabilities & Patching": "Zero-days, CVEs, PoCs, Patch Tuesday, advisories and patches",
    "Business & Industry News": "M&A, funding, earnings, executive changes, partnerships, analyst recognition (acquisition keywords have false-positive exclusions)",
    "Policy, Legal & Compliance": "Regulation, law enforcement, lawsuits and fines, privacy laws, standards and government guidance",
    "Product & Roadmap": "Vendor launches, new features, GA / preview / beta, integrations, roadmap and end-of-life announcements",
    "Attacks, Breaches & Threat Intel": "Ransomware, breaches and data leaks, cybercrime, malware analysis, threat actors and campaigns",
}


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
    vendors = list(digest.VENDORS)
    out = [
        "## Categories & Vendors", "",
        "Every article has one **category** (what it is about) and one **vendor** (who it is about, or none). The two are independent: "
        "a CrowdStrike zero-day is *Vulnerabilities & Patching* and *CrowdStrike*. Both are decided from the title by keyword rules in "
        "`daily_cybersecurity_digest.py` (`CATEGORIES`, `VENDORS`); a keyword starting with `~` only matches as a whole word, e.g. "
        "`~armis` does not match \"alarmist\". The dashboard shows one row per category or per vendor (*Rows by* switch) and filters by both. "
        "Every run re-applies the current rules to the whole history.", "",
        "### Categories", "",
        "Priority order — the first match wins. Titles that match nothing fall back to the category of the feed they came from "
        "(`SOURCE_CATEGORY`, e.g. threat-research blogs → Attacks), then to *General Security News*.", "",
        "| Priority | Category | Covers |", "|---|---|---|",
    ]
    for i, name in enumerate(digest.CATEGORIES, 1):
        out.append(f"| {i} | {name} | {CATEGORY_NOTES.get(name, '')} |")
    out.append(f"| {len(digest.CATEGORIES) + 1} | {digest.FALLBACK_CATEGORY} | Catch-all for everything else |")
    out += [
        "", f"### Tracked Vendors ({len(vendors)})", "",
        "An article from a vendor's own blog or news feed that names no vendor in its title is filed under that vendor (`SOURCE_VENDOR`). "
        "Articles that name no tracked vendor show as *" + digest.NO_VENDOR + "*.", "",
        "| # | Vendor | # | Vendor |", "|---|---|---|---|",
    ]
    half = (len(vendors) + 1) // 2
    for i in range(half):
        left = f"| {i + 1} | {vendors[i]} "
        j = i + half
        right = f"| {j + 1} | {vendors[j]} |" if j < len(vendors) else "| | |"
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
    print(f"README updated: {len(digest.FEEDS)} feeds, {len(digest.CATEGORIES)} categories, {len(digest.VENDORS)} vendors, {len(digest.MODULE_TYPES)} module types")


if __name__ == "__main__":
    main()
