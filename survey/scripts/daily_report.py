"""
daily_report.py — Generate a daily markdown report of newly fetched papers.

Usage:
    python survey/scripts/daily_report.py [YYYY-MM-DD]

If no date is given, defaults to today.
Outputs: survey/reports/daily/YYYY-MM-DD.md
"""

import yaml
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

SURVEY_DIR = Path(__file__).resolve().parent.parent
PAPERS_FILE = SURVEY_DIR / "papers.yaml"
REPORTS_DIR = SURVEY_DIR / "reports" / "daily"


def load_papers():
    with open(PAPERS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("papers", [])


def main():
    # Determine report date
    if len(sys.argv) > 1:
        report_date = sys.argv[1]
    else:
        report_date = datetime.now().strftime("%Y-%m-%d")

    papers = load_papers()

    # Find papers added by daily_fetch (they have 'matched_keywords' field)
    new_papers = [p for p in papers if "matched_keywords" in p]

    if not new_papers:
        print("No new papers from daily fetch found.")
        return

    # Group by direction
    by_direction = defaultdict(list)
    for p in new_papers:
        dirs = p.get("directions", ["uncategorized"])
        for d in dirs:
            by_direction[d].append(p)

    # Direction display names
    dir_names = {
        "differential": "差分分析",
        "boomerang": "回旋镖/Rectangle",
        "linear": "线性分析",
        "integral_division": "积分/Division Property",
        "algebraic": "代数/Cube 攻击",
        "meet_in_the_middle": "中间相遇",
        "milp_sat_cp": "MILP/SAT/CP 建模",
        "ml_aided": "ML 辅助分析",
        "automated_search": "自动化搜索",
        "related_key": "相关密钥",
        "impossible_differential": "不可能差分",
        "zero_correlation": "零相关",
        "invariant": "不变量",
        "sbox": "S-box 设计",
        "round_function": "轮函数",
        "linear_diffusion": "线性扩散层",
        "key_schedule": "密钥调度",
        "hardware_friendly": "硬件友好",
        "software_friendly": "软件友好",
        "low_latency": "低时延",
        "high_throughput": "高吞吐",
        "lightweight": "轻量级",
        "tweakable": "可调密码",
        "aead": "AEAD",
        "hash_xof": "Hash/XOF",
        "permutation_layer": "置换层",
    }

    # Build report
    lines = []
    lines.append(f"# 每日新论文报告 — {report_date}")
    lines.append("")
    lines.append(f"> 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"> 数据来源：ePrint RSS")
    lines.append(f"> 新增论文：**{len(new_papers)} 篇**")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary table
    lines.append("## 📊 概览")
    lines.append("")
    lines.append("| 方向 | 数量 |")
    lines.append("|------|------|")
    for d in sorted(by_direction.keys()):
        name = dir_names.get(d, d)
        count = len(by_direction[d])
        lines.append(f"| {name} | {count} |")
    lines.append("")

    # Detailed sections
    lines.append("## 📄 论文详情")
    lines.append("")

    for d in sorted(by_direction.keys()):
        name = dir_names.get(d, d)
        lines.append(f"### {name}")
        lines.append("")

        seen = set()
        for p in by_direction[d]:
            pid = p["id"]
            if pid in seen:
                continue
            seen.add(pid)

            title = p["title"]
            url = p.get("url", "")
            kw = p.get("matched_keywords", [])
            summary = p.get("summary", "")
            ciphers = p.get("ciphers", [])
            year = p.get("year", "")
            venue = p.get("venue", "")

            if url:
                lines.append(f"**[{title}]({url})**")
            else:
                lines.append(f"**{title}**")
            lines.append("")
            
            meta_parts = []
            if venue:
                meta_parts.append(f"📍 {venue}")
            if kw:
                meta_parts.append(f"🔑 {', '.join(kw[:5])}")
            if ciphers:
                meta_parts.append(f"🔐 {', '.join(ciphers)}")
            if meta_parts:
                lines.append(f"> {' | '.join(meta_parts)}")
                lines.append("")
            
            if summary:
                # Clean up HTML from RSS descriptions
                import re
                clean = re.sub(r'<[^>]+>', '', summary)
                clean = clean.strip()[:300]
                if clean:
                    lines.append(f"{clean}")
                    lines.append("")

        lines.append("---")
        lines.append("")

    # Footer
    lines.append(f"*共 {len(new_papers)} 篇新论文，按研究方向分类。状态：pending_review*")

    # Save report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{report_date}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Report generated: {report_path}")
    print(f"  {len(new_papers)} papers, {len(by_direction)} directions")


if __name__ == "__main__":
    main()
