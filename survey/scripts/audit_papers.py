"""
audit_papers.py — Find duplicate entries and suspicious URLs in papers.yaml.
Outputs a report and optionally fixes issues.

Usage:
    python survey/scripts/audit_papers.py [--fix]
"""

import yaml
import sys
from collections import Counter
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


def main():
    fix_mode = "--fix" in sys.argv

    data = load_papers()
    papers = data.get("papers", [])
    print(f"Total papers: {len(papers)}")

    # 1. Find duplicate IDs
    ids = [p.get("id", "") for p in papers]
    id_counts = Counter(ids)
    dupes_by_id = {k: v for k, v in id_counts.items() if v > 1}
    print(f"\n=== Duplicate IDs ({len(dupes_by_id)}) ===")
    for did, cnt in sorted(dupes_by_id.items()):
        indices = [i for i, p in enumerate(papers) if p.get("id") == did]
        print(f"  {did}: {cnt}x at indices {indices}")

    # 2. Find duplicate titles (normalized)
    title_map = {}
    for i, p in enumerate(papers):
        t = p.get("title", "").lower().strip().rstrip(".")
        # Further normalize: remove extra spaces
        t = " ".join(t.split())
        if t in title_map:
            title_map[t].append((i, p.get("id", "")))
        else:
            title_map[t] = [(i, p.get("id", ""))]
    title_dupes = {k: v for k, v in title_map.items() if len(v) > 1}
    print(f"\n=== Duplicate titles ({len(title_dupes)}) ===")
    for t, entries in sorted(title_dupes.items()):
        print(f'  "{t[:70]}..."')
        for idx, pid in entries:
            print(f"    [{idx}] id={pid}")

    # 3. Find URLs used by multiple papers (likely wrong assignments)
    url_map = {}
    for i, p in enumerate(papers):
        u = p.get("url", "")
        if u:
            if u not in url_map:
                url_map[u] = []
            url_map[u].append((i, p.get("id", "")))
    url_dupes = {k: v for k, v in url_map.items() if len(v) > 1}
    print(f"\n=== URLs used by multiple papers ({len(url_dupes)}) ===")
    for u, entries in sorted(url_dupes.items()):
        print(f"  {u}")
        for idx, pid in entries:
            print(f"    [{idx}] id={pid}")

    # 4. Count papers with empty/missing URLs
    no_url = sum(1 for p in papers if not p.get("url"))
    print(f"\n=== Papers without URL: {no_url} ===")

    # 5. Count papers with empty authors
    no_authors = sum(1 for p in papers if not p.get("authors"))
    print(f"=== Papers without authors: {no_authors} ===")

    if fix_mode:
        print("\n=== Applying fixes ===")
        removed = 0

        # Remove exact duplicate IDs (keep first occurrence)
        seen_ids = set()
        new_papers = []
        for p in papers:
            pid = p.get("id", "")
            if pid in seen_ids and pid in dupes_by_id:
                print(f"  Removing duplicate: {pid}")
                removed += 1
            else:
                seen_ids.add(pid)
                new_papers.append(p)

        # Clear URLs that are shared by multiple papers
        # (they're likely wrong auto-assigned URLs)
        cleared_urls = 0
        url_to_clear = set(url_dupes.keys())
        for p in new_papers:
            u = p.get("url", "")
            if u in url_to_clear:
                # Keep URL only for the first paper that has it
                url_to_clear.discard(u)  # keep first
                # Actually, let's clear ALL shared URLs since they're likely wrong
        
        # Better approach: clear all shared URLs
        shared_urls = set(url_dupes.keys())
        for p in new_papers:
            u = p.get("url", "")
            if u in shared_urls:
                p["url"] = ""
                cleared_urls += 1

        data["papers"] = new_papers
        save_papers(data)
        print(f"\n  Removed {removed} duplicate entries")
        print(f"  Cleared {cleared_urls} shared/suspicious URLs")
        print(f"  New total: {len(new_papers)} papers")
        print(f"  Saved to {PAPERS_FILE}")


if __name__ == "__main__":
    main()
