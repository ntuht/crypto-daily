"""
find_eprint_urls.py — Search ePrint for papers missing URLs and update papers.yaml.
More aggressive than fill_metadata.py — tries multiple search strategies.
"""
import yaml
import urllib.request
import urllib.parse
import urllib.error
import json
import re
import time
from pathlib import Path

SURVEY_DIR = Path(__file__).resolve().parent.parent
PAPERS_FILE = SURVEY_DIR / "papers.yaml"


def search_eprint(title):
    """Search ePrint by title and return URL if found."""
    # Try direct ePrint search
    words = title.split()[:8]  # first 8 words
    query = "+".join(urllib.parse.quote(w) for w in words)
    url = f"https://eprint.iacr.org/search?q={query}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        # Find ePrint IDs in results
        matches = re.findall(r'href="/(\d{4}/\d+)"', html)
        if matches:
            return f"https://eprint.iacr.org/{matches[0]}"
    except Exception:
        pass
    return None


def search_dblp_url(title):
    """Search DBLP for the paper and return its URL."""
    query = urllib.parse.quote(title[:100])
    url = f"https://dblp.org/search/publ/api?q={query}&format=json&h=3"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        hits = data.get("result", {}).get("hits", {}).get("hit", [])
        for hit in hits:
            info = hit.get("info", {})
            dblp_url = info.get("url", "")
            # Check if it has an ee (electronic edition) that points to ePrint
            ee = info.get("ee", "")
            if isinstance(ee, dict):
                ee = ee.get("#text", "")
            if isinstance(ee, list):
                for e in ee:
                    if isinstance(e, dict):
                        e = e.get("#text", "")
                    if "eprint.iacr.org" in str(e):
                        return str(e)
                ee = str(ee[0]) if ee else ""
            if "eprint.iacr.org" in str(ee):
                return str(ee)
            # Return DOI or other URL as fallback
            if ee:
                return str(ee)
    except Exception:
        pass
    return None


def main():
    with open(PAPERS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    papers = data.get("papers", [])
    no_url = [p for p in papers if not p.get("url")]
    print(f"Total papers: {len(papers)}")
    print(f"Papers without URL: {len(no_url)}")
    print("=" * 60)

    filled = 0
    for i, p in enumerate(no_url):
        pid = p["id"]
        title = p["title"]
        print(f"\n[{i+1}/{len(no_url)}] {pid}: {title[:60]}...")

        # Strategy 1: Search ePrint
        url = search_eprint(title)
        if url:
            print(f"  + ePrint: {url}")
            p["url"] = url
            filled += 1
            time.sleep(2)
            continue

        time.sleep(1)

        # Strategy 2: Search DBLP
        url = search_dblp_url(title)
        if url:
            print(f"  + DBLP: {url}")
            p["url"] = url
            filled += 1
            time.sleep(2)
            continue

        print(f"  x Not found")
        time.sleep(1)

    print(f"\n{'=' * 60}")
    print(f"URLs filled: {filled}")

    data["papers"] = papers
    with open(PAPERS_FILE, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True,
                  sort_keys=False, width=120)
    print(f"Saved to {PAPERS_FILE}")


if __name__ == "__main__":
    main()
