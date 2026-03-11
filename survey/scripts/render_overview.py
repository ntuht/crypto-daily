"""
render_overview.py — Generate a markdown overview from papers.yaml + taxonomy.yaml.

Usage:
    python survey/scripts/render_overview.py
    python survey/scripts/render_overview.py --output overview.md
"""

import sys
import yaml
import argparse
from pathlib import Path
from collections import Counter, defaultdict

SURVEY_DIR = Path(__file__).resolve().parent.parent
PAPERS_FILE = SURVEY_DIR / "papers.yaml"
TAXONOMY_FILE = SURVEY_DIR / "taxonomy.yaml"


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def collect_direction_names(taxonomy):
    """Recursively collect direction_id -> name mappings."""
    result = {}

    def _walk(node, category=""):
        if isinstance(node, dict):
            for key, val in node.items():
                if isinstance(val, dict) and "name" in val:
                    result[key] = {"name": val["name"], "category": category}
                else:
                    _walk(val, category or key)

    _walk(taxonomy.get("taxonomy", {}))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", help="Output file path")
    args = parser.parse_args()

    papers_data = load_yaml(PAPERS_FILE)
    taxonomy_data = load_yaml(TAXONOMY_FILE)

    papers = papers_data.get("papers", [])
    dir_names = collect_direction_names(taxonomy_data)

    # Count by direction
    dir_counts = Counter()
    dir_papers = defaultdict(list)
    cipher_counts = Counter()
    year_counts = Counter()

    for p in papers:
        for d in p.get("directions", []):
            dir_counts[d] += 1
            dir_papers[d].append(p)
        for c in p.get("ciphers", []):
            cipher_counts[c] += 1
        if p.get("year"):
            year_counts[p["year"]] += 1

    high_papers = [p for p in papers if p.get("significance") == "high"]

    # Generate markdown
    lines = []
    lines.append("# 对称密码研究论文概览")
    lines.append("")
    lines.append(f"📊 **总计**: {len(papers)} 篇论文 | "
                 f"{len(dir_counts)} 个方向 | "
                 f"{len(cipher_counts)} 个密码算法 | "
                 f"{len(high_papers)} 篇高影响力论文")
    lines.append("")

    # Year distribution
    lines.append("## 年份分布")
    lines.append("")
    if year_counts:
        for year in sorted(year_counts.keys()):
            bar = "█" * year_counts[year]
            lines.append(f"- **{year}**: {bar} ({year_counts[year]})")
    lines.append("")

    # Design directions
    lines.append("## 算法设计")
    lines.append("")
    design_dirs = {k: v for k, v in dir_names.items() if v["category"] == "design"}
    for did in sorted(design_dirs.keys(), key=lambda x: -dir_counts.get(x, 0)):
        count = dir_counts.get(did, 0)
        name = design_dirs[did]["name"]
        if count > 0:
            lines.append(f"### {name} ({count} 篇)")
            lines.append("")
            for p in sorted(dir_papers[did], key=lambda x: -(x.get("year") or 0)):
                sig = {"high": "🔴", "medium": "🟡", "low": "⚪"}.get(p.get("significance", ""), "")
                ciphers = ", ".join(p.get("ciphers", []))
                cipher_str = f" [{ciphers}]" if ciphers else ""
                lines.append(f"- {sig} **{p.get('year', '?')}** — {p.get('title', '')}{cipher_str}")
            lines.append("")

    # Analysis directions
    lines.append("## 算法分析")
    lines.append("")
    analysis_dirs = {k: v for k, v in dir_names.items() if v["category"] == "analysis"}
    for did in sorted(analysis_dirs.keys(), key=lambda x: -dir_counts.get(x, 0)):
        count = dir_counts.get(did, 0)
        name = analysis_dirs[did]["name"]
        if count > 0:
            lines.append(f"### {name} ({count} 篇)")
            lines.append("")
            for p in sorted(dir_papers[did], key=lambda x: -(x.get("year") or 0)):
                sig = {"high": "🔴", "medium": "🟡", "low": "⚪"}.get(p.get("significance", ""), "")
                ciphers = ", ".join(p.get("ciphers", []))
                cipher_str = f" [{ciphers}]" if ciphers else ""
                lines.append(f"- {sig} **{p.get('year', '?')}** — {p.get('title', '')}{cipher_str}")
            lines.append("")

    # Top ciphers
    lines.append("## 涉及最多的密码算法")
    lines.append("")
    lines.append("| 密码 | 论文数 |")
    lines.append("|------|--------|")
    for cipher, count in cipher_counts.most_common(15):
        lines.append(f"| {cipher} | {count} |")
    lines.append("")

    content = "\n".join(lines)

    output_path = Path(args.output) if args.output else SURVEY_DIR / "OVERVIEW.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Generated overview: {output_path}")
    print(f"  {len(papers)} papers, {len(dir_counts)} active directions")


if __name__ == "__main__":
    main()
