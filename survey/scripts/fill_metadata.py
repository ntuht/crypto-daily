"""
fill_metadata.py — Auto-fill missing authors and URLs in papers.yaml.

Uses DBLP API to search by title, then falls back to ePrint search.
Updates papers.yaml in-place, adding authors and URLs where missing.

Usage:
    python survey/scripts/fill_metadata.py [--dry-run]
"""

import yaml
import time
import sys
import re
import json
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

SURVEY_DIR = Path(__file__).resolve().parent.parent
PAPERS_FILE = SURVEY_DIR / "papers.yaml"


def load_papers():
    with open(PAPERS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def save_papers(data):
    with open(PAPERS_FILE, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True,
                  sort_keys=False, width=120)


def fetch_url(url, timeout=10):
    """Fetch URL content with error handling."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "CryptoLLM-Survey/1.0"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def search_dblp(title):
    """Search DBLP for a paper by title, return (authors, url) or (None, None)."""
    clean_title = re.sub(r'[^\w\s]', ' ', title).strip()
    query = clean_title[:80]
    encoded = urllib.parse.quote(query)
    api_url = f"https://dblp.org/search/publ/api?q={encoded}&format=json&h=3"

    content = fetch_url(api_url)
    if not content:
        return None, None

    try:
        data = json.loads(content)
        hits = data.get("result", {}).get("hits", {}).get("hit", [])
        if not hits:
            return None, None

        title_lower = title.lower().strip()
        for hit in hits:
            info = hit.get("info", {})
            dblp_title = info.get("title", "").strip().rstrip(".")

            title_words = set(title_lower.split())
            dblp_words = set(dblp_title.lower().split())
            overlap = len(title_words & dblp_words)

            if overlap >= min(3, len(title_words) * 0.5):
                authors_data = info.get("authors", {}).get("author", [])
                if isinstance(authors_data, dict):
                    authors_data = [authors_data]

                authors = []
                for a in authors_data:
                    name = a.get("text", "") if isinstance(a, dict) else str(a)
                    if name:
                        authors.append(name)

                url = info.get("ee", "")
                if isinstance(url, list):
                    url = url[0] if url else ""

                return authors if authors else None, url if url else None

    except (json.JSONDecodeError, KeyError):
        pass

    return None, None


def search_eprint(title):
    """Try to find paper on ePrint by searching the title."""
    clean_title = re.sub(r'[^\w\s]', ' ', title).strip()
    query = clean_title[:60]
    encoded = urllib.parse.quote(query)
    search_url = f"https://eprint.iacr.org/search?q={encoded}"

    content = fetch_url(search_url, timeout=15)
    if not content:
        return None

    matches = re.findall(r'href="(/(\d{4}/\d+))"', content)
    if matches:
        return f"https://eprint.iacr.org/{matches[0][1]}"
    return None


def extract_eprint_id(url):
    """Extract ePrint ID like '2024/977' from a URL."""
    if not url:
        return None
    match = re.search(r'eprint\.iacr\.org/(\d{4}/\d+)', url)
    return match.group(1) if match else None


def get_eprint_metadata(eprint_id):
    """Get metadata from ePrint page."""
    url = f"https://eprint.iacr.org/{eprint_id}"
    content = fetch_url(url)
    if not content:
        return None, url

    authors = []
    for m in re.finditer(r'<meta name="citation_author" content="([^"]+)"', content):
        authors.append(m.group(1))

    return authors if authors else None, url


def main():
    dry_run = "--dry-run" in sys.argv

    data = load_papers()
    papers = data.get("papers", [])

    total = len(papers)
    missing_authors = sum(1 for p in papers if not p.get("authors"))
    missing_urls = sum(1 for p in papers if not p.get("url"))

    print(f"Total papers: {total}")
    print(f"Missing authors: {missing_authors}")
    print(f"Missing URLs: {missing_urls}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    print("=" * 60)

    updated_authors = 0
    updated_urls = 0

    for i, paper in enumerate(papers):
        pid = paper.get("id", "?")
        title = paper.get("title", "")
        has_authors = bool(paper.get("authors"))
        has_url = bool(paper.get("url"))

        if has_authors and has_url:
            continue

        print(f"\n[{i+1}/{total}] {pid}: {title[:60]}...")

        current_url = paper.get("url", "")
        eprint_id = extract_eprint_id(current_url)

        found_authors = None
        found_url = None

        # Strategy 1: ePrint metadata if we have an ID
        if eprint_id and not has_authors:
            print(f"  -> Fetching ePrint {eprint_id}...")
            ea, eu = get_eprint_metadata(eprint_id)
            if ea:
                found_authors = ea
                print(f"  + ePrint authors: {', '.join(ea[:3])}{'...' if len(ea) > 3 else ''}")
            time.sleep(0.5)

        # Strategy 2: DBLP search
        if not found_authors or not has_url:
            print(f"  -> Searching DBLP...")
            da, du = search_dblp(title)
            if da and not found_authors:
                found_authors = da
                print(f"  + DBLP authors: {', '.join(da[:3])}{'...' if len(da) > 3 else ''}")
            if du and not has_url:
                found_url = du
                print(f"  + DBLP URL: {du[:60]}")
            time.sleep(1.0)

        # Strategy 3: ePrint search for URL
        if not has_url and not found_url:
            print(f"  -> Searching ePrint...")
            eu = search_eprint(title)
            if eu:
                found_url = eu
                print(f"  + ePrint URL: {eu}")
            time.sleep(1.0)

        # Apply
        if found_authors and not has_authors:
            if not dry_run:
                paper["authors"] = found_authors
            updated_authors += 1

        if found_url and not has_url:
            if not dry_run:
                paper["url"] = found_url
            updated_urls += 1

        if not found_authors and not has_authors:
            print(f"  x No authors found")
        if not found_url and not has_url:
            print(f"  x No URL found")

    print("\n" + "=" * 60)
    print(f"Authors filled: {updated_authors}")
    print(f"URLs filled: {updated_urls}")

    if not dry_run and (updated_authors > 0 or updated_urls > 0):
        save_papers(data)
        print(f"\nSaved to {PAPERS_FILE}")
    elif dry_run:
        print(f"\n(Dry run - no changes saved)")


if __name__ == "__main__":
    main()
