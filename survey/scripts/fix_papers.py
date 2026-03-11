"""
fix_papers.py — One-time cleanup: remove duplicates, fix URLs.
"""

import yaml
from pathlib import Path

SURVEY_DIR = Path(__file__).resolve().parent.parent
PAPERS_FILE = SURVEY_DIR / "papers.yaml"


def load_papers():
    with open(PAPERS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_papers(data):
    with open(PAPERS_FILE, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True,
                  sort_keys=False, width=120)


def main():
    data = load_papers()
    papers = data.get("papers", [])
    print(f"Before: {len(papers)} papers")

    # 1. Remove entries that are exact duplicates added in Phase 3/4
    #    when the same paper was already in Phase 1/2
    remove_ids = {
        # Phase 3/4 duplicates of Phase 1/2 entries:
        "craft2019",           # duplicate of beierle2020craft
        "gift2017",            # duplicate of banik2017gift
        "present2007",         # duplicate of bogdanov2007present
        "skinny2016",          # duplicate of beierle2016skinny
        "simon_speck2013",     # duplicate of beaulieu2015simon_speck
        "rectangle2015",       # duplicate of zhang2015rectangle
        "daemen2001aes",       # duplicate of daemen2001rijndael
        "prince2012",          # duplicate of borghoff2012prince
    }
    
    # Also remove the second occurrence of exact ID duplicates
    seen_ids = set()
    indices_to_remove = set()
    for i, p in enumerate(papers):
        pid = p.get("id", "")
        if pid in remove_ids:
            indices_to_remove.add(i)
            print(f"  Remove duplicate: [{i}] {pid}")
        elif pid in seen_ids:
            # Exact ID duplicate - remove later one
            indices_to_remove.add(i)
            print(f"  Remove ID duplicate: [{i}] {pid}")
        else:
            seen_ids.add(pid)

    # Also handle the TWEAKEY duplicate
    # jean2014tweakey and jean2014tweakey_ks are actually different aspects
    # (framework vs key schedule) — keep both but verify

    papers = [p for i, p in enumerate(papers) if i not in indices_to_remove]
    print(f"After removing duplicates: {len(papers)} papers")

    # 2. Fix wrong URLs assigned by fill_metadata.py
    #    The ePrint search was not precise — it matched wrong papers
    
    # URLs that are clearly wrong assignments (ePrint search returned 
    # a different paper with similar keywords)
    wrong_url_fixes = {
        # These ePrint URLs point to completely different papers
        "lai1991markov": "",       # 2025/2205 is wrong (different paper)
        "biham2002rectangle": "",  # 2025/158 is wrong
        "delaune2020boomerang_milp": "",  # same wrong URL as above
        "cho2010linear": "",       # 2024/1363 is wrong
        "fu2016sat": "",           # 2024/2003 is wrong
        "biryukov2014survey": "",  # same wrong URL
        "luby1988prp": "",         # 2025/2291 is wrong (that's ZIP cipher)
        "bernstein2008chacha": "", # 2025/2128 is wrong
        "dl_chacha_2024": "",      # same wrong URL
        "chen2025beam": "",        # 2025/2205 is wrong
        "salsa_2024": "",          # 2024/1363 is wrong
    }
    
    # Truncated ePrint URLs (just year, no paper number) — obviously wrong
    truncated_urls = {
        "https://eprint.iacr.org/2022",
        "https://eprint.iacr.org/2023",
        "https://eprint.iacr.org/2024",
        "https://eprint.iacr.org/2025",
    }
    
    # Also SKINNY and MANTIS share the same ePrint — that's actually correct
    # (they were published in the same paper), so DON'T clear those
    
    cleared = 0
    for p in papers:
        pid = p.get("id", "")
        url = p.get("url", "")
        
        # Fix specific wrong URLs
        if pid in wrong_url_fixes:
            if url:
                print(f"  Clear wrong URL: {pid} <- {url}")
                p["url"] = wrong_url_fixes[pid]
                cleared += 1
        
        # Fix truncated ePrint URLs
        if url in truncated_urls:
            print(f"  Clear truncated URL: {pid} <- {url}")
            p["url"] = ""
            cleared += 1

    # 3. Fix the difflinear_boom2024 / dl_boomerang_multi2024 shared URL
    # difflinear_boom2024 was the earlier Phase 2 entry, 
    # dl_boomerang_multi2024 is the Phase 4 entry for the same CRYPTO 2024 paper
    # They're actually the SAME paper — remove the Phase 2 one
    papers = [p for p in papers if p.get("id") != "difflinear_boom2024"]
    print(f"  Removed difflinear_boom2024 (duplicate of dl_boomerang_multi2024)")

    # 4. Fix gift_ml_dist2024 / ascon_ml2024 sharing ePrint 2024/1370
    # These are likely different papers but ePrint search matched the same one
    # Check if they're really different papers
    for p in papers:
        if p.get("id") == "ascon_ml2024" and p.get("url") == "https://eprint.iacr.org/2024/1370":
            p["url"] = ""  # clear wrong URL for Ascon ML paper
            print(f"  Clear shared URL: ascon_ml2024")

    # 5. baksi2022ml / pyjamask_integral2022 sharing ePrint 2021/1572
    # 2021/1572 is "Cube-like Attack on Round-Reduced Pyjamask" — matches pyjamask_integral
    for p in papers:
        if p.get("id") == "baksi2022ml" and p.get("url") == "https://eprint.iacr.org/2021/1572":
            p["url"] = ""  # clear wrong URL for ML survey
            print(f"  Clear shared URL: baksi2022ml")

    data["papers"] = papers
    save_papers(data)
    print(f"\nFinal: {len(papers)} papers")
    print(f"Cleared {cleared} wrong/truncated URLs")
    print(f"Saved to {PAPERS_FILE}")


if __name__ == "__main__":
    main()
