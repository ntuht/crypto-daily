"""
download_pdfs.py — Batch download PDFs for papers in papers.yaml.

Downloads from ePrint URLs, organizes by first direction tag.

Usage:
    python survey/scripts/download_pdfs.py [--limit N] [--force]
"""

import yaml
import time
import sys
import re
import urllib.request
import urllib.error
from pathlib import Path

SURVEY_DIR = Path(__file__).resolve().parent.parent
PAPERS_FILE = SURVEY_DIR / "papers.yaml"
PDFS_DIR = SURVEY_DIR / "pdfs"


def load_papers():
    with open(PAPERS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def get_pdf_url(paper_url):
    """Convert paper URL to PDF download URL."""
    if not paper_url:
        return None

    # ePrint: https://eprint.iacr.org/2024/977 -> .pdf
    eprint_match = re.search(r'eprint\.iacr\.org/(\d{4}/\d+)', paper_url)
    if eprint_match:
        return f"https://eprint.iacr.org/{eprint_match.group(1)}.pdf"

    return None


def download_pdf(url, save_path, timeout=30):
    """Download a PDF file."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "CryptoLLM-Survey/1.0"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()

            if not content[:4] == b'%PDF':
                return False, "Not a PDF file"

            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(content)

            size_kb = len(content) / 1024
            return True, f"{size_kb:.0f} KB"

    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)[:50]


def main():
    limit = None
    force = "--force" in sys.argv

    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    data = load_papers()
    papers = data.get("papers", [])

    # Collect downloadable papers
    downloadable = []
    already_have = 0

    for p in papers:
        url = p.get("url", "")
        if not url:
            continue

        pdf_url = get_pdf_url(url)
        if not pdf_url:
            continue

        pid = p.get("id", "unknown")
        directions = p.get("directions", ["misc"])
        direction = directions[0] if directions else "misc"

        save_path = PDFS_DIR / direction / f"{pid}.pdf"

        if save_path.exists() and not force:
            already_have += 1
            continue

        downloadable.append({
            "id": pid,
            "title": p.get("title", ""),
            "pdf_url": pdf_url,
            "save_path": save_path,
            "direction": direction,
        })

    if limit:
        downloadable = downloadable[:limit]

    total = len(downloadable)

    print(f"Total papers: {len(papers)}")
    print(f"With ePrint URLs: {already_have + total}")
    print(f"Already downloaded: {already_have}")
    print(f"To download: {total}")
    print("=" * 60)

    if total == 0:
        print("Nothing to download.")
        return

    success = 0
    failed = 0

    for i, item in enumerate(downloadable):
        print(f"\n[{i+1}/{total}] {item['id']}: {item['title'][:50]}...")
        print(f"  -> {item['pdf_url']}")

        ok, msg = download_pdf(item["pdf_url"], item["save_path"])

        if ok:
            rel = item["save_path"].relative_to(SURVEY_DIR)
            print(f"  + Saved ({msg}) -> {rel}")
            success += 1
        else:
            print(f"  x Failed: {msg}")
            failed += 1

        if i < total - 1:
            time.sleep(2)

    print("\n" + "=" * 60)
    print(f"Downloaded: {success}")
    print(f"Failed: {failed}")
    print(f"PDFs directory: {PDFS_DIR}")


if __name__ == "__main__":
    main()
