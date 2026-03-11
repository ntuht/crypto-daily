"""
export_bibtex.py — Export papers.yaml to BibTeX format.

Usage:
    python survey/scripts/export_bibtex.py                        # Full export
    python survey/scripts/export_bibtex.py --direction differential  # By direction
    python survey/scripts/export_bibtex.py --cipher GIFT           # By cipher
    python survey/scripts/export_bibtex.py --output refs.bib       # Custom output
"""

import sys
import re
import yaml
import argparse
from pathlib import Path

SURVEY_DIR = Path(__file__).resolve().parent.parent
PAPERS_FILE = SURVEY_DIR / "papers.yaml"


def load_papers():
    with open(PAPERS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("papers", [])


def guess_entry_type(venue):
    """Guess BibTeX entry type from venue string."""
    venue_lower = str(venue).lower() if venue else ""
    if any(kw in venue_lower for kw in ["journal", "toc", "joc", "ieee", "acm", "science"]):
        return "article"
    if any(kw in venue_lower for kw in ["eprint", "arxiv", "cryptology"]):
        return "misc"
    return "inproceedings"


def escape_bibtex(text):
    """Escape special BibTeX characters."""
    if not text:
        return ""
    text = str(text)
    # Protect uppercase letters in titles
    text = text.replace("{", "\\{").replace("}", "\\}")
    return text


def paper_to_bibtex(paper):
    """Convert a paper dict to a BibTeX entry string."""
    pid = paper.get("id", "unknown")
    title = paper.get("title", "")
    authors = paper.get("authors", [])
    venue = paper.get("venue", "")
    year = paper.get("year", "")
    url = paper.get("url", "")

    entry_type = guess_entry_type(venue)
    author_str = " and ".join(authors) if authors else "Unknown"

    lines = [f"@{entry_type}{{{pid},"]
    lines.append(f"  title = {{{escape_bibtex(title)}}},")
    lines.append(f"  author = {{{escape_bibtex(author_str)}}},")
    lines.append(f"  year = {{{year}}},")

    if entry_type == "inproceedings":
        lines.append(f"  booktitle = {{{escape_bibtex(venue)}}},")
    elif entry_type == "article":
        lines.append(f"  journal = {{{escape_bibtex(venue)}}},")
    else:
        lines.append(f"  howpublished = {{{escape_bibtex(venue)}}},")

    if url:
        lines.append(f"  url = {{{url}}},")

    lines.append("}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Export papers to BibTeX")
    parser.add_argument("--direction", "-d", help="Filter by direction")
    parser.add_argument("--cipher", "-c", help="Filter by cipher name")
    parser.add_argument("--significance", "-s", help="Filter by significance (high/medium/low)")
    parser.add_argument("--output", "-o", help="Output file path")
    args = parser.parse_args()

    papers = load_papers()

    # Apply filters
    if args.direction:
        papers = [p for p in papers if args.direction in p.get("directions", [])]
    if args.cipher:
        papers = [p for p in papers if args.cipher.upper() in [c.upper() for c in p.get("ciphers", [])]]
    if args.significance:
        papers = [p for p in papers if p.get("significance") == args.significance]

    if not papers:
        print("No papers match the filter criteria.")
        return

    # Generate BibTeX
    entries = [paper_to_bibtex(p) for p in papers]
    bibtex_content = "\n\n".join(entries) + "\n"

    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(bibtex_content)
        print(f"Exported {len(papers)} papers to {output_path}")
    else:
        # Default output
        output_path = SURVEY_DIR / "references.bib"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(bibtex_content)
        print(f"Exported {len(papers)} papers to {output_path}")


if __name__ == "__main__":
    main()
