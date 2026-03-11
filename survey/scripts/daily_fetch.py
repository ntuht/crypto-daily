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

    # Fetch new entries
    entries = fetch_eprint_rss()

    new_papers = []
    for entry in entries:
        if entry["eprint_id"] in seen_ids:
            continue

        # Check keyword match
        text = f"{entry['title']} {entry['description']}"
        matched = matches_keywords(text)

        if not matched:
            seen_ids.add(entry["eprint_id"])
            continue

        # Create paper entry
        year = datetime.now().year
        paper_id = generate_paper_id(entry["title"], year)

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
            "authors": [],  # RSS doesn't always have authors
            "venue": f"ePrint {entry['eprint_id']}",
            "year": year,
            "url": entry["link"],
            "directions": directions,
            "ciphers": [],
            "significance": "medium",
            "summary": entry["description"][:200] if entry["description"] else "",
            "status": "pending_review",
            "matched_keywords": matched,
            "fetched_date": datetime.now().strftime("%Y-%m-%d"),
        }

        new_papers.append(paper)
        existing_ids.add(paper_id)
        seen_ids.add(entry["eprint_id"])

        print(f"  NEW: {entry['title'][:80]}...")
        print(f"       Keywords: {', '.join(matched[:5])}")
        print(f"       Directions: {', '.join(directions)}")

        # Download PDF
        if not no_download and entry["link"]:
            pdf_url = entry["link"].rstrip("/") + ".pdf"
            direction = directions[0] if directions else "uncategorized"
            pdf_path = PDFS_DIR / direction / f"{paper_id}.pdf"
            download_pdf(pdf_url, pdf_path)

    # Save results
    if new_papers:
        existing_papers.extend(new_papers)
        papers_data["papers"] = existing_papers
        save_yaml_file(PAPERS_FILE, papers_data)
        print(f"\n✅ Added {len(new_papers)} new papers to {PAPERS_FILE}")
    else:
        print("\nNo new matching papers found.")

    # Update fetch log
    fetch_log["last_fetch"] = datetime.now().isoformat()
    fetch_log["seen_ids"] = list(seen_ids)
    save_fetch_log(fetch_log)

    print(f"Total papers in database: {len(existing_papers)}")
    return len(new_papers)


if __name__ == "__main__":
    main()
