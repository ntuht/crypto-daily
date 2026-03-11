"""
weekly_report.py — Generate a weekly summary report from papers.yaml.

Usage:
    python survey/scripts/weekly_report.py
"""

import yaml
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict

SURVEY_DIR = Path(__file__).resolve().parent.parent
PAPERS_FILE = SURVEY_DIR / "papers.yaml"
TAXONOMY_FILE = SURVEY_DIR / "taxonomy.yaml"
REPORTS_DIR = SURVEY_DIR / "weekly_reports"


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def collect_direction_names(taxonomy):
    result = {}
    def _walk(node, category=""):
        if isinstance(node, dict):
            for key, val in node.items():
                if isinstance(val, dict) and "name" in val:
                    result[key] = val["name"]
                else:
                    _walk(val, category or key)
    _walk(taxonomy.get("taxonomy", {}))
    return result


def main():
    papers_data = load_yaml(PAPERS_FILE)
    taxonomy_data = load_yaml(TAXONOMY_FILE)
    papers = papers_data.get("papers", [])
    dir_names = collect_direction_names(taxonomy_data)

    # Filter pending_review papers (newly added)
    pending = [p for p in papers if p.get("status") == "pending_review"]
    reviewed = [p for p in papers if p.get("status") != "pending_review"]

    now = datetime.now()
    week_id = now.strftime("%Y-W%W")

    lines = []
    lines.append(f"# 周报 {week_id}")
    lines.append(f"")
    lines.append(f"生成时间: {now.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"")

    # Stats
    lines.append(f"## 数据库统计")
    lines.append(f"")
    lines.append(f"- 总论文数: **{len(papers)}**")
    lines.append(f"- 待审阅: **{len(pending)}**")
    lines.append(f"- 已审阅: **{len(reviewed)}**")
    lines.append(f"")

    # Pending papers
    if pending:
        lines.append(f"## 待审阅论文 ({len(pending)})")
        lines.append(f"")

        by_dir = defaultdict(list)
        for p in pending:
            for d in p.get("directions", ["uncategorized"]):
                by_dir[d].append(p)

        for d, plist in sorted(by_dir.items()):
            dname = dir_names.get(d, d)
            lines.append(f"### {dname}")
            lines.append(f"")
            for p in plist:
                title = p.get("title", "")
                url = p.get("url", "")
                link = f"[{title}]({url})" if url else title
                lines.append(f"- {link}")
                if p.get("summary"):
                    lines.append(f"  > {p['summary'].strip()[:150]}")
            lines.append(f"")

    # Direction activity
    lines.append(f"## 方向活跃度")
    lines.append(f"")
    dir_counts = Counter()
    for p in papers:
        for d in p.get("directions", []):
            dir_counts[d] += 1

    lines.append(f"| 方向 | 论文数 |")
    lines.append(f"|------|--------|")
    for d, c in dir_counts.most_common():
        dname = dir_names.get(d, d)
        lines.append(f"| {dname} | {c} |")
    lines.append(f"")

    content = "\n".join(lines)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{week_id}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Generated weekly report: {report_path}")


if __name__ == "__main__":
    main()
