"""
dedup.py — Cross-source paper deduplication.

Uses title normalization + Jaccard word similarity to detect
the same paper appearing on ePrint and in a conference/journal.
"""

import re
import unicodedata


def normalize_title(title):
    """
    Normalize a paper title for comparison.
    - Lowercase
    - Remove LaTeX math ($...$, \\mathit{}, etc.)
    - Remove punctuation and special chars
    - Collapse whitespace
    """
    t = title.lower()
    # Remove LaTeX inline math
    t = re.sub(r'\$[^$]*\$', '', t)
    # Remove LaTeX commands
    t = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', t)
    t = re.sub(r'\\[a-zA-Z]+', '', t)
    # Remove accents
    t = unicodedata.normalize('NFKD', t)
    t = ''.join(c for c in t if not unicodedata.combining(c))
    # Remove punctuation
    t = re.sub(r'[^a-z0-9\s]', ' ', t)
    # Collapse whitespace
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def title_words(title):
    """Get set of meaningful words (len >= 3) from normalized title."""
    normalized = normalize_title(title)
    return {w for w in normalized.split() if len(w) >= 3}


def jaccard_similarity(set_a, set_b):
    """Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def is_duplicate(new_paper, existing_papers, threshold=0.7):
    """
    Check if new_paper is a duplicate of any existing paper.

    Returns (is_dup, matched_paper_or_None).
    """
    new_url = new_paper.get("url", "")
    new_words = title_words(new_paper.get("title", ""))

    for existing in existing_papers:
        # 1. URL exact match (same ePrint ID)
        if new_url and new_url == existing.get("url", ""):
            return True, existing

        # 2. ePrint ID cross-reference
        new_eprint = _extract_eprint_id(new_url)
        existing_eprint = _extract_eprint_id(existing.get("url", ""))
        if new_eprint and existing_eprint and new_eprint == existing_eprint:
            return True, existing

        # 3. Title similarity
        existing_words = title_words(existing.get("title", ""))
        sim = jaccard_similarity(new_words, existing_words)
        if sim >= threshold:
            return True, existing

    return False, None


def _extract_eprint_id(url):
    """Extract ePrint ID (e.g., '2026/439') from URL."""
    if not url:
        return None
    m = re.search(r'eprint\.iacr\.org/(\d{4}/\d+)', url)
    return m.group(1) if m else None


# Source authority ranking (higher = more authoritative)
SOURCE_AUTHORITY = {
    "crypto": 10,
    "eurocrypt": 10,
    "asiacrypt": 10,
    "tosc": 9,
    "tches": 9,
    "cic": 8,
    "eprint": 5,
}


def pick_authoritative(paper_a, paper_b):
    """Return the more authoritative version of two duplicate papers."""
    src_a = paper_a.get("source", "eprint")
    src_b = paper_b.get("source", "eprint")
    auth_a = SOURCE_AUTHORITY.get(src_a, 0)
    auth_b = SOURCE_AUTHORITY.get(src_b, 0)
    return paper_a if auth_a >= auth_b else paper_b
