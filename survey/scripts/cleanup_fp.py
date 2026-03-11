"""
cleanup_fp.py — Remove false-positive (non-symmetric-crypto) papers
from papers.yaml that were picked up by overly broad keyword matching.

Also fixes duplicate entries.

Usage:
    python survey/scripts/cleanup_fp.py
"""

import yaml
import re
from pathlib import Path

SURVEY_DIR = Path(__file__).resolve().parent.parent
PAPERS_FILE = SURVEY_DIR / "papers.yaml"

# Titles or partial titles of known false positives to remove
# These are non-symmetric-crypto papers that matched broad keywords
FALSE_POSITIVE_TITLE_PATTERNS = [
    r"censorship resistance.*bft",
    r"proofs of no intrusion",
    r"two-round 2pc ecdsa",
    r"sqisign",
    r"optimized implementations.*msp430",
    r"post-quantum anonymous signatures.*lattice",
    r"revisiting the security of sparkle",  # Schnorr signature, not Sparkle hash
    r"post-quantum privacy.*traceable",
    r"faster bootstrapping.*ckks",
    r"lattice-based multi-message",
    r"on the cca security.*homomorphic",
    r"oblivious single access machines",
    r"flexible.*polynomial.*ckks",
    r"short signatures.*ddh",
    r"trace.*client-side account",
    r"survey of isogeny-based signature",
    r"implementation.*post-quantum.*group key",
    r"leakage-diagrams.*random probing",  # masking theory, borderline
    r"prism.*pinch of salt.*isogen",
    r"updatable private set intersection",
    r"information-theoretic.*traceable secret sharing",
    r"round-optimal threshold blind signatures",
    r"finite field arithmetic.*ml-kem.*zech",
    r"efficient private range queries",
    r"encrypted matrix.*secret dual codes",
    r"beyond the 1/2 bound.*biprimality",
    r"theoretical limits.*model extraction",
    r"fuzzy private set intersection",
    r"sprint.*isogeny proofs",
    r"interactive proofs.*batch polynomial",
    r"quantum-safe.*private group.*signal",
    r"non-adaptive one-way to hiding",
    r"efficient single-server.*pir.*format-preserving",
    r"post-quantum security.*keyed sum of permutations",
]

def should_remove(paper):
    """Check if a paper is a false positive."""
    title = paper.get("title", "")
    for pattern in FALSE_POSITIVE_TITLE_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            return True
    return False


def main():
    with open(PAPERS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    papers = data.get("papers", [])
    print(f"Total papers before cleanup: {len(papers)}")

    # Remove false positives
    removed_fp = []
    kept = []
    for p in papers:
        if should_remove(p):
            removed_fp.append(p.get("title", "unknown"))
        else:
            kept.append(p)

    print(f"\nRemoved {len(removed_fp)} false positives:")
    for t in removed_fp:
        print(f"  ✗ {t[:80]}")

    # Remove exact title duplicates (keep first occurrence)
    seen_titles = set()
    deduped = []
    removed_dupes = 0
    for p in kept:
        t = " ".join(p.get("title", "").lower().strip().rstrip(".").split())
        if t in seen_titles:
            removed_dupes += 1
            print(f"  ✗ [DUP] {p.get('title', '')[:80]}")
        else:
            seen_titles.add(t)
            deduped.append(p)

    print(f"\nRemoved {removed_dupes} duplicate entries")

    data["papers"] = deduped
    with open(PAPERS_FILE, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True,
                  sort_keys=False, width=120)

    print(f"\nTotal papers after cleanup: {len(deduped)}")
    print(f"Saved to {PAPERS_FILE}")


if __name__ == "__main__":
    main()
