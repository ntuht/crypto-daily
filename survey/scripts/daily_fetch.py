"""
daily_fetch.py — Fetch new papers from ePrint Archive RSS and DBLP.

Filters by symmetric cipher keywords, appends candidates to papers.yaml,
and downloads PDFs into pdfs/{direction}/.

Usage:
    python survey/scripts/daily_fetch.py [--no-download]
"""

import os
import sys
import re
import json
import yaml
import hashlib
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

SURVEY_DIR = Path(__file__).resolve().parent.parent
PAPERS_FILE = SURVEY_DIR / "papers.yaml"
TAXONOMY_FILE = SURVEY_DIR / "taxonomy.yaml"
PDFS_DIR = SURVEY_DIR / "pdfs"
FETCH_LOG = SURVEY_DIR / "scripts" / ".fetch_log.json"

EPRINT_RSS_URL = "https://eprint.iacr.org/rss/rss.xml"
DBLP_API_URL = "https://dblp.org/search/publ/api"

# DBLP table-of-contents paths for IACR venues
DBLP_SOURCES = {
    "tosc":      {"path": "journals/tosc/tosc{year}",      "venue_label": "TOSC"},
    "tches":     {"path": "journals/tches/tches{year}",    "venue_label": "TCHES/CHES"},
    "crypto":    {"path": "conf/crypto/crypto{year}",       "venue_label": "CRYPTO"},
    "eurocrypt": {"path": "conf/eurocrypt/eurocrypt{year}",  "venue_label": "EUROCRYPT"},
    "asiacrypt": {"path": "conf/asiacrypt/asiacrypt{year}",  "venue_label": "ASIACRYPT"},
    "cic":       {"path": "journals/cic/cic{year}",         "venue_label": "CIC"},
}

# Core keywords for filtering — union of all direction keywords
FILTER_KEYWORDS = [
    # Analysis keywords
    "differential", "linear cryptanalysis", "impossible differential",
    "boomerang", "rectangle attack", "division property", "integral attack",
    "algebraic attack", "cube attack", "meet-in-the-middle", "MITM",
    "zero-correlation", "invariant", "subspace trail",
    "related-key", "related key",
    # Modeling keywords
    "MILP", "mixed-integer", "SAT", "constraint programming",
    "automated search", "neural distinguisher", "machine learning",
    # Design keywords
    "block cipher", "lightweight cipher", "S-box", "substitution box",
    "permutation", "diffusion", "MDS", "branch number",
    "ARX", "Feistel", "SPN",
    "AEAD", "authenticated encryption", "tweakable",
    "low latency", "lightweight",
    # Specific ciphers
    "AES", "GIFT", "PRESENT", "SKINNY", "SIMON", "SPECK",
    "Ascon", "ChaCha", "RECTANGLE", "Midori", "PRINCE",
    "PHOTON", "LED", "KATAN", "CRAFT",
]


def load_yaml_file(path):
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yaml_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)


def load_fetch_log():
    if FETCH_LOG.exists():
        with open(FETCH_LOG, "r") as f:
            return json.load(f)
    return {"last_fetch": None, "seen_ids": []}


def save_fetch_log(log):
    FETCH_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(FETCH_LOG, "w") as f:
        json.dump(log, f, indent=2)


def fetch_eprint_rss():
    """Fetch and parse ePrint RSS feed."""
    print(f"Fetching ePrint RSS from {EPRINT_RSS_URL}...")
    try:
        req = urllib.request.Request(EPRINT_RSS_URL, headers={
            "User-Agent": "CryptoLLM-Survey/1.0"
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        root = ET.fromstring(data)
    except Exception as e:
        print(f"Error fetching RSS: {e}")
        return []

    entries = []
    # RSS 2.0 format
    for item in root.iter("item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        description = item.findtext("description", "").strip()
        pub_date = item.findtext("pubDate", "").strip()

        # Extract ePrint ID from link
        eprint_match = re.search(r"/(\d{4}/\d+)", link)
        eprint_id = eprint_match.group(1) if eprint_match else ""

        entries.append({
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date,
            "eprint_id": eprint_id,
        })

    print(f"  Found {len(entries)} entries in RSS feed")
    return entries


def fetch_dblp_source(source_name, year):
    """
    Fetch papers from a DBLP table-of-contents for a given year.
    Returns list of entry dicts in same format as fetch_eprint_rss.
    """
    source = DBLP_SOURCES[source_name]
    toc_path = source["path"].format(year=year)
    venue_label = source["venue_label"]

    query = f'toc:db/{toc_path}.bht:'
    url = f"{DBLP_API_URL}?q={urllib.parse.quote(query)}&h=1000&format=json"

    print(f"  Fetching {venue_label} {year} from DBLP...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CryptoLLM-Survey/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  Error fetching DBLP {source_name}: {e}")
        return []

    hits = data.get("result", {}).get("hits", {})
    total = int(hits.get("@total", 0))
    if total == 0:
        print(f"  No entries for {venue_label} {year}")
        return []

    entries = []
    for hit in hits.get("hit", []):
        info = hit.get("info", {})
        title = info.get("title", "").rstrip(".")
        dblp_key = info.get("key", "")
        doi = info.get("doi", "")
        ee = info.get("ee", "")  # electronic edition URL

        # Extract authors
        authors_data = info.get("authors", {}).get("author", [])
        if isinstance(authors_data, dict):
            authors_data = [authors_data]
        authors = [a.get("text", "") for a in authors_data]

        # Build link — prefer DOI, fallback to ee
        link = f"https://doi.org/{doi}" if doi else ee

        entries.append({
            "title": title,
            "link": link,
            "description": "",  # DBLP doesn't provide abstracts
            "pub_date": "",
            "eprint_id": "",
            "dblp_key": dblp_key,
            "authors": authors,
            "year": int(info.get("year", year)),  # actual publication year
            "source": source_name,
            "venue_label": f"{venue_label} {year}",
        })

    print(f"  Found {len(entries)} entries for {venue_label} {year}")
    return entries


def matches_keywords(text):
    """Check if text contains any of our keywords."""
    text_lower = text.lower()
    matched = []
    for kw in FILTER_KEYWORDS:
        if kw.lower() in text_lower:
            matched.append(kw)
    return matched


def guess_directions(matched_keywords):
    """Guess research directions from matched keywords."""
    keyword_to_direction = {
        "differential": "differential",
        "truncated differential": "differential",
        "impossible differential": "impossible_differential",
        "boomerang": "boomerang",
        "rectangle attack": "boomerang",
        "linear cryptanalysis": "linear",
        "zero-correlation": "zero_correlation",
        "division property": "integral_division",
        "integral attack": "integral_division",
        "algebraic attack": "algebraic",
        "cube attack": "algebraic",
        "meet-in-the-middle": "meet_in_the_middle",
        "MITM": "meet_in_the_middle",
        "related-key": "related_key",
        "related key": "related_key",
        "invariant": "invariant",
        "subspace trail": "invariant",
        "MILP": "milp_sat_cp",
        "mixed-integer": "milp_sat_cp",
        "SAT": "milp_sat_cp",
        "constraint programming": "milp_sat_cp",
        "neural distinguisher": "ml_aided",
        "machine learning": "ml_aided",
        "automated search": "automated_search",
        "S-box": "sbox",
        "substitution box": "sbox",
        "MDS": "linear_diffusion",
        "branch number": "linear_diffusion",
        "diffusion": "linear_diffusion",
        "permutation": "permutation_layer",
        "Feistel": "round_function",
        "SPN": "round_function",
        "ARX": "software_friendly",
        "low latency": "low_latency",
        "lightweight cipher": "lightweight",
        "lightweight": "lightweight",
        "block cipher": "lightweight",
        "AEAD": "aead",
        "authenticated encryption": "aead",
        "tweakable": "tweakable",
    }

    dirs = set()
    for kw in matched_keywords:
        for pattern, direction in keyword_to_direction.items():
            if pattern.lower() in kw.lower():
                dirs.add(direction)
    return list(dirs) or ["differential"]  # default


def generate_paper_id(title, year=None):
    """Generate a short ID from title."""
    words = re.sub(r'[^a-zA-Z0-9\s]', '', title.lower()).split()[:3]
    short = "_".join(words)
    if year:
        short = f"{short}_{year}"
    return short


def download_pdf(url, save_path):
    """Download PDF from URL."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "CryptoLLM-Survey/1.0"
        })
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(data)
        print(f"  Downloaded: {save_path.name}")
        return True
    except Exception as e:
        print(f"  Download failed: {e}")
        return False


def main():
    no_download = "--no-download" in sys.argv

    fetch_log = load_fetch_log()
    seen_ids = set(fetch_log.get("seen_ids", []))

    # Load existing papers
    papers_data = load_yaml_file(PAPERS_FILE)
    existing_papers = papers_data.get("papers", [])
    existing_ids = {p["id"] for p in existing_papers if "id" in p}

    # Import dedup
    from dedup import is_duplicate, pick_authoritative

    # ── Collect entries from all sources ──
    all_entries = []

    # Source 1: ePrint RSS
    eprint_entries = fetch_eprint_rss()
    for e in eprint_entries:
        e.setdefault("source", "eprint")
        e.setdefault("venue_label", "ePrint")
        e.setdefault("authors", [])
    all_entries.extend(eprint_entries)

    # Source 2-7: DBLP venues (current year only — older papers already captured)
    current_year = datetime.now().year
    for source_name in DBLP_SOURCES:
        entries = fetch_dblp_source(source_name, current_year)
        all_entries.extend(entries)

    print(f"\nTotal entries across all sources: {len(all_entries)}")

    new_papers = []
    skipped_dup = 0
    for entry in all_entries:
        source = entry.get("source", "eprint")
        # Build a unique seen key per source
        if source == "eprint":
            seen_key = f"eprint:{entry['eprint_id']}"
            if entry["eprint_id"] in seen_ids or seen_key in seen_ids:
                continue
        else:
            seen_key = f"dblp:{entry.get('dblp_key', entry['title'][:50])}"
            if seen_key in seen_ids:
                continue

        # Check keyword match
        text = f"{entry['title']} {entry['description']}"
        matched = matches_keywords(text)

        if not matched:
            seen_ids.add(seen_key)
            continue

        # Cross-source dedup: check if this paper already exists
        candidate = {
            "title": entry["title"],
            "url": entry["link"],
            "source": source,
        }
        is_dup, existing_match = is_duplicate(candidate, existing_papers)
        if is_dup:
            # If new source is more authoritative, update the existing entry
            better = pick_authoritative(candidate, existing_match)
            if better is candidate and existing_match:
                existing_match["source"] = source
                existing_match["venue"] = entry.get("venue_label", existing_match.get("venue", ""))
                print(f"  UPGRADE: {entry['title'][:60]}... ({existing_match.get('source','?')} -> {source})")
            skipped_dup += 1
            seen_ids.add(seen_key)
            continue

        # Use actual publication year from source (DBLP has it; ePrint = current year)
        pub_year = entry.get("year", datetime.now().year)
        paper_id = generate_paper_id(entry["title"], pub_year)

        # Avoid duplicate IDs
        base_id = paper_id
        counter = 1
        while paper_id in existing_ids:
            paper_id = f"{base_id}_{counter}"
            counter += 1

        directions = guess_directions(matched)

        paper = {
            "id": paper_id,
            "title": entry["title"],
            "authors": entry.get("authors", []),
            "venue": entry.get("venue_label", f"ePrint {entry.get('eprint_id', '')}"),
            "year": pub_year,
            "url": entry["link"],
            "directions": directions,
            "ciphers": [],
            "significance": "medium",
            "summary": entry["description"][:200] if entry["description"] else "",
            "status": "pending_review",
            "matched_keywords": matched,
            "fetched_date": datetime.now().strftime("%Y-%m-%d"),
            "source": source,
        }

        new_papers.append(paper)
        existing_ids.add(paper_id)
        existing_papers.append(paper)  # for dedup of subsequent entries
        seen_ids.add(seen_key)

        src_tag = f"[{source.upper()}]" if source != "eprint" else "[ePrint]"
        print(f"  NEW {src_tag}: {entry['title'][:70]}...")
        print(f"       Keywords: {', '.join(matched[:5])}")

        # Download PDF (ePrint only)
        if not no_download and source == "eprint" and entry["link"]:
            pdf_url = entry["link"].rstrip("/") + ".pdf"
            direction = directions[0] if directions else "uncategorized"
            pdf_path = PDFS_DIR / direction / f"{paper_id}.pdf"
            download_pdf(pdf_url, pdf_path)

    # Save results
    if new_papers:
        papers_data["papers"] = existing_papers
        save_yaml_file(PAPERS_FILE, papers_data)
        print(f"\n✅ Added {len(new_papers)} new papers to {PAPERS_FILE}")
    else:
        print("\nNo new matching papers found.")

    if skipped_dup > 0:
        print(f"  ({skipped_dup} duplicates skipped across sources)")

    # Update fetch log
    fetch_log["last_fetch"] = datetime.now().isoformat()
    fetch_log["seen_ids"] = list(seen_ids)
    save_fetch_log(fetch_log)

    print(f"Total papers in database: {len(existing_papers)}")
    return len(new_papers)


if __name__ == "__main__":
    main()

