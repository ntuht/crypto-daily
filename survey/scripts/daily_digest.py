"""
daily_digest.py — LLM-powered curated daily paper digest.

Three-stage pipeline:
  Stage 1: Heuristic scoring (no API calls) — ~50 papers → ~20
  Stage 2: LLM relevance ranking (1 API call) — ~20 → 10
  Stage 3: LLM Chinese analysis (1 API call) — Top 3 detailed + 7 brief

Usage:
    python survey/scripts/daily_digest.py [YYYY-MM-DD]
    python survey/scripts/daily_digest.py --no-llm       # heuristic only
    python survey/scripts/daily_digest.py --stage1-only   # debug scoring
"""

import json
import re
import sys
import yaml
from datetime import datetime
from pathlib import Path
from collections import defaultdict

SURVEY_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = SURVEY_DIR.parent
PAPERS_FILE = SURVEY_DIR / "papers.yaml"
REPORTS_DIR = SURVEY_DIR / "reports" / "daily"
BACKLOG_FILE = SURVEY_DIR / "backlog.yaml"
CONFIG_FILE = PROJECT_DIR / "config.yaml"


def parse_json_response(text, expect_array=True):
    """
    Robustly extract JSON from an LLM response.
    Handles: ```json blocks, thinking text, whitespace, BOM.
    """
    if not text:
        return None

    # Strip BOM and whitespace
    clean = text.strip().lstrip("\ufeff")

    # Strip markdown code blocks (```json ... ``` or ``` ... ```)
    if "```" in clean:
        # Extract content between first ``` and last ```
        parts = clean.split("```")
        # Take odd-indexed parts (inside blocks)
        for i in range(1, len(parts), 2):
            block = parts[i]
            # Remove language tag on first line (e.g., "json\n")
            if block and block.split("\n")[0].strip().isalpha():
                block = "\n".join(block.split("\n")[1:])
            block = block.strip()
            if block:
                try:
                    return json.loads(block)
                except json.JSONDecodeError:
                    continue

    # Try direct parse
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # Bracket-matching extraction
    opener = "[" if expect_array else "{"
    closer = "]" if expect_array else "}"
    start = clean.find(opener)
    if start < 0:
        return None

    depth = 0
    in_string = False
    escape_next = False
    for i in range(start, len(clean)):
        c = clean[i]
        if escape_next:
            escape_next = False
            continue
        if c == "\\":
            escape_next = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(clean[start:i+1])
                except json.JSONDecodeError:
                    return None
    return None

# ── Stage 1: Heuristic Scoring ──────────────────────────────────────

# Core symmetric crypto keywords (high signal)
CORE_KEYWORDS = {
    "block cipher", "stream cipher", "symmetric", "sbox", "s-box",
    "round function", "key schedule", "feistel", "spn", "arx",
    "differential cryptanalysis", "linear cryptanalysis", "boomerang",
    "impossible differential", "integral attack", "division property",
    "zero-correlation", "truncated differential", "algebraic attack",
    "cube attack", "slide attack", "related-key", "meet-in-the-middle",
    "aead", "authenticated encryption", "hash function", "sponge",
    "permutation-based", "tweakable", "mode of operation",
    "lightweight cipher", "low-latency", "high-throughput",
    "milp", "sat solver", "cp model", "automated search",
    "neural cryptanalysis", "deep learning cryptanalysis",
    "active s-box", "differential probability", "linear hull",
    "branch number", "diffusion layer", "mds matrix",
    "commitment security", "committing security",
}

# Specific cipher names (medium signal)
CIPHER_NAMES = {
    "aes", "gift", "skinny", "simon", "speck", "ascon", "grain",
    "trivium", "chacha", "salsa", "gimli", "xoodoo", "keccak",
    "sha-3", "sha3", "blake", "midori", "prince", "mantis",
    "craft", "warp", "pyjamask", "saturnin", "sparkle", "photon",
    "elephant", "isap", "romulus", "schwaemm", "esch", "subterranean",
    "aegis", "rocca", "tiaoxin", "deoxys", "skinny-aead", "forkskinny",
    "knot", "ace", "orange", "wage", "sneik", "xoodyak",
    "aradi", "chilow", "poseidon", "griffin", "anemoi", "rescue",
    "hctr", "hctr2", "xctr", "och",
}

# Exclusion terms (strong negative signal)
EXCLUSION_TERMS = {
    "blockchain", "smart contract", "decentralized", "defi",
    "zero-knowledge proof", "zksnark", "zk-snark", "zkp", "groth16",
    "post-quantum", "lattice-based", "isogeny", "code-based",
    "learning with errors", "lwe", "rlwe", "kyber", "dilithium", "falcon",
    "multiparty computation", "mpc", "secret sharing",
    "fully homomorphic", "fhe", "bgv", "ckks", "tfhe",
    "voting", "e-voting", "election",
    "signature scheme", "digital signature", "group signature",
    "public key encryption", "pke", "kem",
    "oblivious ram", "oram", "garbled circuit",
    "ntt", "number theoretic transform",
    "attribute-based encryption", "abe",
    "proxy re-encryption",
    "byzantine", "consensus protocol",
    "functional encryption",
    "genomic", "medical device",
}

# Keywords that alone don't indicate symmetric crypto relevance
WEAK_ONLY_KEYWORDS = {"PRESENT", "LED", "PRINCE"}


def score_heuristic(paper):
    """
    Score a paper's relevance to symmetric cryptography.
    Returns (score, reasons) tuple.
    """
    title = paper.get("title", "").lower()
    summary = paper.get("summary", "").lower()
    matched_kw = [kw.lower() for kw in paper.get("matched_keywords", [])]
    ciphers = [c.lower() for c in paper.get("ciphers", [])]
    directions = paper.get("directions", [])
    text = f"{title} {summary}"

    score = 0
    reasons = []

    # ── Positive signals ──

    # Core keyword in title (strong)
    for kw in CORE_KEYWORDS:
        if kw in title:
            score += 12
            reasons.append(f"+12 title:'{kw}'")
            break  # count once

    # Core keyword in abstract
    core_in_abstract = sum(1 for kw in CORE_KEYWORDS if kw in summary)
    if core_in_abstract >= 2:
        score += 8
        reasons.append(f"+8 abstract:{core_in_abstract} core keywords")
    elif core_in_abstract == 1:
        score += 4
        reasons.append(f"+4 abstract:1 core keyword")

    # Specific cipher name mentioned
    cipher_hits = [c for c in CIPHER_NAMES if c in text]
    if cipher_hits:
        score += 6
        reasons.append(f"+6 ciphers:{','.join(cipher_hits[:3])}")

    # Analysis-type directions
    analysis_dirs = {"differential", "boomerang", "linear", "integral_division",
                     "algebraic", "meet_in_the_middle", "impossible_differential",
                     "related_key", "zero_correlation", "invariant", "ml_aided"}
    dir_hits = set(directions) & analysis_dirs
    if dir_hits:
        score += 6
        reasons.append(f"+6 directions:{','.join(dir_hits)}")

    # Design-type directions
    design_dirs = {"sbox", "round_function", "linear_diffusion", "key_schedule",
                   "hardware_friendly", "software_friendly", "low_latency",
                   "high_throughput", "lightweight", "tweakable", "aead", "hash_xof"}
    design_hits = set(directions) & design_dirs
    if design_hits:
        score += 5
        reasons.append(f"+5 design:{','.join(design_hits)}")

    # matched_keywords contains analysis terms
    analysis_kw = {"differential", "linear", "boomerang", "integral", "algebraic",
                   "cube", "meet-in-the-middle", "mitm", "related-key", "impossible"}
    kw_hits = [kw for kw in matched_kw if any(a in kw for a in analysis_kw)]
    if kw_hits:
        score += 5
        reasons.append(f"+5 analysis_kw:{','.join(kw_hits[:3])}")

    # ── Negative signals ──

    # Exclusion terms in title or abstract
    for term in EXCLUSION_TERMS:
        if term in text:
            score -= 15
            reasons.append(f"-15 exclusion:'{term}'")
            break  # one is enough

    # Paper matched only weak keywords (PRESENT/LED as cipher names, not crypto)
    raw_kw = set(paper.get("matched_keywords", []))
    if raw_kw and raw_kw <= WEAK_ONLY_KEYWORDS:
        score -= 12
        reasons.append(f"-12 weak_only:{','.join(raw_kw)}")

    return score, reasons


# ── Stage 2: LLM Relevance Ranking ─────────────────────────────────

RANKING_SYSTEM_PROMPT = """你是一位对称密码学领域的研究助手。你的任务是评估论文与 **对称密码学研究** 的相关性。

对称密码学包括：
- 分组密码、流密码、Hash 函数、AEAD 方案的设计与分析
- 差分分析、线性分析、积分攻击、代数攻击、中间相遇攻击等密码分析技术
- S-box、轮函数、扩散层等组件设计
- MILP/SAT/CP 建模自动化搜索
- 基于深度学习的密码分析
- 轻量级密码、硬件友好设计

**不属于**对称密码学的：
- 公钥密码、格密码、后量子密码
- 多方计算、全同态加密、零知识证明
- 区块链、智能合约
- 数字签名、密钥交换"""

RANKING_USER_TEMPLATE = """请为以下论文评估与对称密码学的相关性（1-10分）。

评分标准：
- 9-10: 直接研究对称密码算法或分析技术
- 7-8: 涉及对称密码组件或应用
- 4-6: 间接相关
- 1-3: 几乎无关

请直接返回 JSON 数组，格式：
[{{"id": "论文ID", "score": 分数, "reason": "5字以内理由"}}]

论文列表：
{papers_text}"""


def format_papers_for_ranking(papers):
    """Format papers for LLM ranking prompt."""
    lines = []
    for p in papers:
        pid = p["id"]
        title = p["title"]
        summary = p.get("summary", "")[:200].strip()
        kw = ", ".join(p.get("matched_keywords", [])[:5])
        lines.append(f"ID: {pid}\nTitle: {title}\nKeywords: {kw}\nAbstract: {summary}\n")
    return "\n---\n".join(lines)


def llm_rank(papers, llm, max_papers=10):
    """
    Stage 2: Use LLM to rank papers by relevance.
    Returns top `max_papers` papers sorted by LLM score.
    """
    if not papers:
        return []

    papers_text = format_papers_for_ranking(papers)
    prompt = RANKING_USER_TEMPLATE.format(papers_text=papers_text)

    llm.set_system_prompt(RANKING_SYSTEM_PROMPT)
    llm.reset_conversation()

    print(f"  Stage 2: Sending {len(papers)} papers to LLM for ranking...")
    response = llm.query(prompt)

    rankings = parse_json_response(response, expect_array=True)
    if rankings is None:
        print(f"  [WARN] Failed to parse LLM ranking, using heuristic order")
        print(f"  [DEBUG] Response preview: {response[:300]}")
        return papers[:max_papers]

    # Build score map
    score_map = {}
    reason_map = {}
    for r in rankings:
        pid = str(r.get("id", ""))
        score_map[pid] = r.get("score", 5)
        reason_map[pid] = r.get("reason", "")

    # Sort papers by LLM score
    def get_sort_key(p):
        return score_map.get(p["id"], 5)

    sorted_papers = sorted(papers, key=get_sort_key, reverse=True)

    # Attach LLM scores
    for p in sorted_papers:
        p["_llm_score"] = score_map.get(p["id"], 5)
        p["_llm_reason"] = reason_map.get(p["id"], "")

    top = sorted_papers[:max_papers]
    print(f"  Stage 2 complete: Top {len(top)} papers selected")
    for p in top:
        print(f"    [{p['_llm_score']}] {p['title'][:60]}")

    return top


# ── Stage 3: LLM Chinese Analysis ──────────────────────────────────

ANALYSIS_SYSTEM_PROMPT = """你是一位对称密码学领域的研究员，擅长用简洁的中文解读论文。
请根据论文标题和摘要生成分析，语言要专业但易懂。"""

ANALYSIS_USER_TEMPLATE = """请为以下论文生成中文分析。

**A 类论文（详细分析，每篇约 150-200 字）：**
请包含：
- 🔬 研究背景（1 句）
- 🔧 方法与贡献（2-3 句）
- 🎯 意义或启发（1 句）

{detailed_papers}

---

**B 类论文（简要摘要，每篇约 30 字）：**
请生成一句话中文摘要。

{brief_papers}

---

请返回 JSON（不要 markdown 代码块），格式：
{{
  "detailed": [
    {{"id": "ID", "title_cn": "中文名", "background": "...", "method": "...", "significance": "..."}}
  ],
  "brief": [
    {{"id": "ID", "summary_cn": "一句话摘要"}}
  ]
}}"""


def llm_analyze(top_papers, other_papers, llm):
    """
    Stage 3: Generate Chinese analysis for selected papers.
    """
    # Format detailed papers (top 3)
    detailed_lines = []
    for i, p in enumerate(top_papers):
        summary = p.get("summary", "")[:500].strip()
        detailed_lines.append(
            f"A{i+1}. ID: {p['id']}\n"
            f"Title: {p['title']}\n"
            f"Abstract: {summary}\n"
        )
    detailed_text = "\n".join(detailed_lines)

    # Format brief papers (remaining)
    brief_lines = []
    for i, p in enumerate(other_papers):
        summary = p.get("summary", "")[:150].strip()
        brief_lines.append(
            f"B{i+1}. ID: {p['id']}\n"
            f"Title: {p['title']}\n"
            f"Abstract: {summary}\n"
        )
    brief_text = "\n".join(brief_lines) if brief_lines else "(无)"

    prompt = ANALYSIS_USER_TEMPLATE.format(
        detailed_papers=detailed_text,
        brief_papers=brief_text,
    )

    llm.set_system_prompt(ANALYSIS_SYSTEM_PROMPT)
    llm.reset_conversation()

    print(f"  Stage 3: Generating Chinese analysis ({len(top_papers)} detailed + {len(other_papers)} brief)...")
    response = llm.query(prompt)

    analysis = parse_json_response(response, expect_array=False)
    if analysis is None:
        print(f"  [WARN] Failed to parse LLM analysis, using fallback")
        print(f"  [DEBUG] Response preview: {response[:300]}")
        analysis = {"detailed": [], "brief": []}

    return analysis


# ── Markdown Rendering ──────────────────────────────────────────────

def render_digest_md(report_date, top_papers, other_papers, analysis, stats):
    """Render the curated daily digest as Markdown."""
    lines = []
    lines.append(f"# 每日精选 — {report_date}")
    lines.append("")
    lines.append(f"> 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"> 数据来源：ePrint RSS → 启发式筛选 → LLM 评分")
    lines.append(f"> 候选池 {stats['total']} 篇 → 启发式 {stats['after_heuristic']} 篇 → 精选 **{stats['final']} 篇**")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Build analysis lookup
    detailed_map = {}
    if analysis and "detailed" in analysis:
        for d in analysis["detailed"]:
            detailed_map[str(d.get("id", ""))] = d

    brief_map = {}
    if analysis and "brief" in analysis:
        for b in analysis["brief"]:
            brief_map[str(b.get("id", ""))] = b

    # ── Top papers (detailed) ──
    lines.append("## ⭐ 重点推荐")
    lines.append("")

    for i, p in enumerate(top_papers):
        pid = p["id"]
        title = p["title"]
        url = p.get("url", f"https://eprint.iacr.org/{pid}")
        score = p.get("_llm_score", "?")

        lines.append(f"### {i+1}. [{title}]({url})")
        lines.append("")
        lines.append(f"> ePrint {pid} | 相关性 {score}/10")
        lines.append("")

        info = detailed_map.get(pid, {})
        if info:
            if info.get("background"):
                lines.append(f"🔬 **背景**：{info['background']}")
                lines.append("")
            if info.get("method"):
                lines.append(f"🔧 **方法与贡献**：{info['method']}")
                lines.append("")
            if info.get("significance"):
                lines.append(f"🎯 **意义**：{info['significance']}")
                lines.append("")
        else:
            # Fallback to LLM reason
            reason = p.get("_llm_reason", "")
            if reason:
                lines.append(f"{reason}")
                lines.append("")

        lines.append("---")
        lines.append("")

    # ── Other papers (brief) ──
    if other_papers:
        lines.append("## 📄 其他值得关注")
        lines.append("")

        for p in other_papers:
            pid = p["id"]
            title = p["title"]
            url = p.get("url", f"https://eprint.iacr.org/{pid}")
            score = p.get("_llm_score", "?")

            info = brief_map.get(pid, {})
            summary_cn = info.get("summary_cn", p.get("_llm_reason", ""))

            lines.append(f"**[{title}]({url})**")
            lines.append("")
            if summary_cn:
                lines.append(f"> {summary_cn}")
            else:
                lines.append(f"> ePrint {pid}")
            lines.append("")

    lines.append(f"*精选自 {stats['total']} 篇 ePrint 候选论文*")

    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────

def load_backlog():
    """Load backlog pool from backlog.yaml."""
    if BACKLOG_FILE.exists():
        with open(BACKLOG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"papers": []}
    return {"papers": []}


def save_backlog(data):
    """Save backlog pool to backlog.yaml."""
    with open(BACKLOG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)


def expire_backlog(pool_papers, max_age_days=30):
    """Remove pool entries older than max_age_days."""
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=max_age_days)).strftime("%Y-%m-%d")
    kept = [p for p in pool_papers if p.get("added_date", "2099-01-01") >= cutoff]
    expired = len(pool_papers) - len(kept)
    if expired > 0:
        print(f"  Expired {expired} papers from backlog pool (>{max_age_days} days old)")
    return kept


def load_config():
    """Load config from config.yaml."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def main():
    no_llm = "--no-llm" in sys.argv
    stage1_only = "--stage1-only" in sys.argv

    # Determine report date
    date_args = [a for a in sys.argv[1:] if not a.startswith("--")]
    report_date = date_args[0] if date_args else datetime.now().strftime("%Y-%m-%d")

    config = load_config()
    digest_config = config.get("survey", {}).get("digest", {})
    max_papers = digest_config.get("max_papers", 10)
    detailed_count = digest_config.get("detailed_count", 3)

    # Load papers
    with open(PAPERS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    all_papers = data.get("papers", [])

    # Find papers from daily fetch — only those fetched on report_date
    all_fetched = [p for p in all_papers if "matched_keywords" in p]
    new_papers = [p for p in all_fetched if p.get("fetched_date") == report_date]
    if not new_papers:
        # Fallback for legacy papers without fetched_date
        new_papers = all_fetched
    print(f"Total daily-fetched papers: {len(new_papers)}")

    # ── Load backlog pool ──
    backlog = load_backlog()
    pool_papers = backlog.get("papers", [])
    # Expire old pool entries (>30 days)
    pool_papers = expire_backlog(pool_papers, max_age_days=30)
    pool_ids = {p["id"] for p in pool_papers}
    new_ids = {p["id"] for p in new_papers}
    # Add pool papers that aren't already in today's fetch
    from_pool = [p for p in pool_papers if p["id"] not in new_ids]
    if from_pool:
        print(f"  Adding {len(from_pool)} papers from backlog pool")
        new_papers.extend(from_pool)

    if not new_papers:
        print("No new papers from daily fetch.")
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORTS_DIR / f"{report_date}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# 每日精选 — {report_date}\n\n> 今日无新论文\n")
        print(f"Empty report: {report_path}")
        return

    # ── Stage 1: Heuristic scoring ──
    print("\n=== Stage 1: Heuristic Scoring ===")
    scored = []
    for p in new_papers:
        score, reasons = score_heuristic(p)
        p["_heuristic_score"] = score
        p["_heuristic_reasons"] = reasons
        scored.append(p)

    scored.sort(key=lambda x: x["_heuristic_score"], reverse=True)

    # Filter by threshold
    threshold = 5
    passed = [p for p in scored if p["_heuristic_score"] >= threshold]
    print(f"  Passed (score >= {threshold}): {len(passed)} / {len(scored)}")

    if stage1_only:
        # Debug output
        print(f"\n{'='*70}")
        print(f"{'Score':>6} | {'Title':<60} | Reasons")
        print(f"{'='*70}")
        for p in scored[:30]:
            s = p["_heuristic_score"]
            t = p["title"][:58]
            r = "; ".join(p["_heuristic_reasons"])[:50]
            marker = "✓" if s >= threshold else "✗"
            print(f"  {s:>4} {marker} | {t:<60} | {r}")
        return

    # ── Stage 2 & 3: LLM processing ──
    analysis = None
    if no_llm or not passed:
        # Skip LLM, use heuristic top N
        selected = passed[:max_papers]
        print(f"\n=== LLM Skipped (--no-llm) ===")
        print(f"  Using heuristic top {len(selected)}")
    else:
        # Create LLM backend (import directly to avoid strategy/__init__.py)
        llm_config = config.get("llm", {}).copy()
        import importlib.util
        backends_path = PROJECT_DIR / "strategy" / "llm_backends.py"
        spec = importlib.util.spec_from_file_location("llm_backends", backends_path)
        llm_mod = importlib.util.module_from_spec(spec)
        sys.modules["llm_backends"] = llm_mod  # register before exec for dataclass
        spec.loader.exec_module(llm_mod)

        # Override: use fast model for digest (Pro is too slow)
        llm_config["model"] = "gemini-2.5-flash"
        llm_config["temperature"] = 0.3
        llm_config["max_tokens"] = 8192  # need room for thinking + output
        llm = llm_mod.create_llm_backend(llm_config)
        print(f"  LLM backend: {llm.model_name}")

        # Stage 2: LLM ranking
        print(f"\n=== Stage 2: LLM Relevance Ranking ===")
        selected = llm_rank(passed, llm, max_papers=max_papers)

        # Stage 3: LLM analysis
        if selected:
            print(f"\n=== Stage 3: LLM Chinese Analysis ===")
            top = selected[:detailed_count]
            others = selected[detailed_count:]
            analysis = llm_analyze(top, others, llm)
            print(f"  LLM usage: {llm.usage.summary()}")

    # ── Render report ──
    top_papers = selected[:detailed_count]
    other_papers = selected[detailed_count:]

    stats = {
        "total": len(new_papers),
        "after_heuristic": len(passed),
        "final": len(selected),
    }

    report_md = render_digest_md(report_date, top_papers, other_papers, analysis, stats)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{report_date}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"\nDigest generated: {report_path}")
    print(f"  {len(selected)} papers ({len(top_papers)} detailed + {len(other_papers)} brief)")

    # ── Update backlog pool ──
    selected_ids = {p["id"] for p in selected}
    # Save unselected papers that passed heuristic back to pool
    new_pool = []
    for p in passed:
        if p["id"] not in selected_ids:
            pool_entry = {
                "id": p["id"],
                "title": p.get("title", ""),
                "url": p.get("url", ""),
                "source": p.get("source", "eprint"),
                "venue": p.get("venue", ""),
                "matched_keywords": p.get("matched_keywords", []),
                "directions": p.get("directions", []),
                "summary": p.get("summary", ""),
                "heuristic_score": p.get("_heuristic_score", 0),
                "added_date": p.get("fetched_date", report_date),
                "authors": p.get("authors", []),
            }
            new_pool.append(pool_entry)
    # Also keep pool entries that weren't in today's candidates at all
    candidate_ids = {p["id"] for p in passed}
    for p in pool_papers:
        if p["id"] not in candidate_ids and p["id"] not in selected_ids:
            new_pool.append(p)
    save_backlog({"papers": new_pool})
    if new_pool:
        print(f"  Backlog pool: {len(new_pool)} papers saved for future use")


if __name__ == "__main__":
    main()
