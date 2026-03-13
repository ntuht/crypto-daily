"""
build_site.py — Generate a local static HTML site from papers.yaml + taxonomy.yaml.

Usage:
    python survey/scripts/build_site.py

Output:
    survey/site/index.html   (main page with search, filter, stats)
    survey/site/style.css    (styles)
"""

import os
import sys
import yaml
import html
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict

SURVEY_DIR = Path(__file__).resolve().parent.parent
SITE_DIR = SURVEY_DIR / "site"
PAPERS_FILE = SURVEY_DIR / "papers.yaml"
TAXONOMY_FILE = SURVEY_DIR / "taxonomy.yaml"


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_direction_name(taxonomy, direction_id):
    """Recursively search taxonomy for direction name."""
    def _search(node, target):
        if isinstance(node, dict):
            for key, val in node.items():
                if key == target:
                    if isinstance(val, dict) and "name" in val:
                        return val["name"]
                    elif isinstance(val, str):
                        return val
                    else:
                        return target
                result = _search(val, target)
                if result:
                    return result
        return None

    return _search(taxonomy.get("taxonomy", {}), direction_id) or direction_id


def get_direction_category(taxonomy, direction_id):
    """Return the top-level category (design/analysis) for a direction."""
    def _search(node, target, path=""):
        if isinstance(node, dict):
            for key, val in node.items():
                if key == target:
                    return path
                result = _search(val, target, path or key)
                if result:
                    return result
        return None

    return _search(taxonomy.get("taxonomy", {}), direction_id) or "other"


def escape(text):
    return html.escape(str(text)) if text else ""


def generate_css():
    return """
:root {
    --bg-primary: #0f0f23;
    --bg-secondary: #1a1a36;
    --bg-card: #1e1e3a;
    --bg-hover: #2a2a4a;
    --accent: #6c63ff;
    --accent-light: #8b83ff;
    --accent-glow: rgba(108, 99, 255, 0.3);
    --text-primary: #e8e8f0;
    --text-secondary: #a0a0c0;
    --text-muted: #6a6a8a;
    --border: #2a2a4a;
    --tag-design: #10b981;
    --tag-analysis: #f59e0b;
    --tag-high: #ef4444;
    --tag-medium: #f59e0b;
    --tag-low: #6b7280;
    --font-main: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: var(--font-main);
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px;
}

/* Header */
header {
    background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
    border-bottom: 1px solid var(--border);
    padding: 32px 0;
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(20px);
}

header h1 {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--accent-light), #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}

header .subtitle {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

/* Stats bar */
.stats-bar {
    display: flex;
    gap: 24px;
    margin-top: 16px;
    flex-wrap: wrap;
}

.stat-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: var(--bg-card);
    border-radius: 8px;
    border: 1px solid var(--border);
    font-size: 0.85rem;
}

.stat-value {
    font-weight: 700;
    color: var(--accent-light);
    font-family: var(--font-mono);
    font-size: 1.1rem;
}

/* Search & Filter */
.controls {
    display: flex;
    gap: 12px;
    margin: 24px 0;
    flex-wrap: wrap;
    align-items: center;
}

.search-box {
    flex: 1;
    min-width: 300px;
    padding: 12px 16px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    color: var(--text-primary);
    font-size: 0.95rem;
    font-family: var(--font-main);
    transition: all 0.2s;
}

.search-box:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
}

.filter-btn {
    padding: 8px 16px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 0.85rem;
    transition: all 0.2s;
    font-family: var(--font-main);
}

.filter-btn:hover, .filter-btn.active {
    background: var(--accent);
    color: white;
    border-color: var(--accent);
}

/* Paper list */
.paper-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding-bottom: 48px;
}

.paper-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    transition: all 0.2s;
    cursor: default;
}

.paper-card:hover {
    background: var(--bg-hover);
    border-color: var(--accent);
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.paper-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 6px;
}

.paper-title a {
    color: inherit;
    text-decoration: none;
}

.paper-title a:hover {
    color: var(--accent-light);
}

.paper-meta {
    display: flex;
    gap: 16px;
    font-size: 0.82rem;
    color: var(--text-muted);
    margin-bottom: 8px;
    flex-wrap: wrap;
}

.paper-authors {
    color: var(--text-secondary);
    font-size: 0.85rem;
    margin-bottom: 8px;
}

.paper-summary {
    color: var(--text-secondary);
    font-size: 0.88rem;
    line-height: 1.5;
    margin-bottom: 10px;
}

.paper-tags {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}

.tag {
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
}

.tag-direction {
    background: rgba(108, 99, 255, 0.15);
    color: var(--accent-light);
    border: 1px solid rgba(108, 99, 255, 0.3);
}

.tag-cipher {
    background: rgba(16, 185, 129, 0.15);
    color: var(--tag-design);
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.tag-significance-high {
    background: rgba(239, 68, 68, 0.15);
    color: var(--tag-high);
    border: 1px solid rgba(239, 68, 68, 0.3);
}

.tag-significance-medium {
    background: rgba(245, 158, 11, 0.15);
    color: var(--tag-medium);
    border: 1px solid rgba(245, 158, 11, 0.3);
}

.tag-significance-low {
    background: rgba(107, 114, 128, 0.15);
    color: var(--tag-low);
    border: 1px solid rgba(107, 114, 128, 0.3);
}

/* Direction sidebar */
.main-layout {
    display: grid;
    grid-template-columns: 280px 1fr;
    gap: 24px;
    margin-top: 24px;
}

.sidebar {
    position: sticky;
    top: 140px;
    align-self: start;
    max-height: calc(100vh - 160px);
    overflow-y: auto;
}

.sidebar h3 {
    font-size: 0.85rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 8px;
    margin-top: 16px;
}

.sidebar h3:first-child { margin-top: 0; }

.dir-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.15s;
    color: var(--text-secondary);
}

.dir-item:hover, .dir-item.active {
    background: var(--bg-hover);
    color: var(--text-primary);
}

.dir-item .count {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--text-muted);
    background: var(--bg-primary);
    padding: 1px 6px;
    border-radius: 4px;
}

.no-results {
    text-align: center;
    padding: 48px;
    color: var(--text-muted);
    font-size: 1rem;
}

/* Responsive */
@media (max-width: 900px) {
    .main-layout {
        grid-template-columns: 1fr;
    }
    .sidebar {
        position: static;
        max-height: none;
    }
}

.result-count {
    color: var(--text-muted);
    font-size: 0.85rem;
    margin-bottom: 12px;
}
"""


def generate_html(papers, taxonomy):
    # Compute stats
    directions_count = Counter()
    ciphers_count = Counter()
    years = []
    for p in papers:
        for d in p.get("directions", []):
            directions_count[d] += 1
        for c in p.get("ciphers", []):
            ciphers_count[c] += 1
        if p.get("year"):
            years.append(p["year"])

    high_count = sum(1 for p in papers if p.get("significance") == "high")
    year_range = f"{min(years)}-{max(years)}" if years else "N/A"

    # Build direction groups from taxonomy
    def collect_directions(node, result=None, category=""):
        if result is None:
            result = {}
        if isinstance(node, dict):
            for key, val in node.items():
                if isinstance(val, dict) and "name" in val:
                    result[key] = {
                        "name": val["name"],
                        "category": category,
                        "count": directions_count.get(key, 0),
                    }
                else:
                    collect_directions(val, result, category or key)
        return result

    all_directions = collect_directions(taxonomy.get("taxonomy", {}))

    # Build sidebar HTML
    design_dirs = {k: v for k, v in all_directions.items() if v["category"] == "design"}
    analysis_dirs = {k: v for k, v in all_directions.items() if v["category"] == "analysis"}

    sidebar_html = '<div class="sidebar">\n'
    sidebar_html += '  <div class="dir-item" data-dir="all" onclick="filterDir(\'all\')">'
    sidebar_html += f'全部 <span class="count">{len(papers)}</span></div>\n'

    sidebar_html += '  <h3>📐 算法设计</h3>\n'
    for did, info in sorted(design_dirs.items(), key=lambda x: -x[1]["count"]):
        if info["count"] > 0:
            sidebar_html += f'  <div class="dir-item" data-dir="{did}" onclick="filterDir(\'{did}\')">'
            sidebar_html += f'{escape(info["name"])} <span class="count">{info["count"]}</span></div>\n'

    sidebar_html += '  <h3>🔍 算法分析</h3>\n'
    for did, info in sorted(analysis_dirs.items(), key=lambda x: -x[1]["count"]):
        if info["count"] > 0:
            sidebar_html += f'  <div class="dir-item" data-dir="{did}" onclick="filterDir(\'{did}\')">'
            sidebar_html += f'{escape(info["name"])} <span class="count">{info["count"]}</span></div>\n'

    sidebar_html += '</div>\n'

    # Build paper cards
    cards_html = ""
    for p in sorted(papers, key=lambda x: -(x.get("year") or 0)):
        pid = escape(p.get("id", ""))
        title = escape(p.get("title", ""))
        url = p.get("url", "")
        authors = escape(", ".join(p.get("authors", [])))
        year = p.get("year", "")
        venue = escape(p.get("venue", ""))
        summary = escape(p.get("summary", "").strip())
        significance = p.get("significance", "")
        dirs_json = ",".join(p.get("directions", []))
        ciphers = p.get("ciphers", [])

        title_html = f'<a href="{escape(url)}" target="_blank">{title}</a>' if url else title

        tags = ""
        if significance:
            tags += f'<span class="tag tag-significance-{significance}">{significance}</span>'
        for d in p.get("directions", []):
            dname = all_directions.get(d, {}).get("name", d)
            tags += f'<span class="tag tag-direction">{escape(dname)}</span>'
        for c in ciphers:
            tags += f'<span class="tag tag-cipher">{escape(c)}</span>'

        cards_html += f'''
<div class="paper-card" data-id="{pid}" data-dirs="{dirs_json}"
     data-year="{year}" data-significance="{significance}"
     data-search="{title.lower()} {authors.lower()} {" ".join(c.lower() for c in ciphers)} {summary.lower()}">
  <div class="paper-title">{title_html}</div>
  <div class="paper-meta">
    <span>📅 {year}</span>
    <span>📖 {venue}</span>
  </div>
  <div class="paper-authors">{authors}</div>
  <div class="paper-summary">{summary}</div>
  <div class="paper-tags">{tags}</div>
</div>
'''

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>对称密码研究论文库</title>
  <link rel="stylesheet" href="style.css">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
</head>
<body>
  <header>
    <div class="container">
      <h1>🔐 对称密码研究论文库</h1>
      <div class="subtitle">Symmetric Cipher Research Paper Collection · Last updated: {now}</div>
      <div class="stats-bar">
        <div class="stat-item"><span class="stat-value">{len(papers)}</span> 论文</div>
        <div class="stat-item"><span class="stat-value">{len(all_directions)}</span> 方向</div>
        <div class="stat-item"><span class="stat-value">{high_count}</span> 高影响</div>
        <div class="stat-item"><span class="stat-value">{year_range}</span> 年份跨度</div>
        <div class="stat-item"><span class="stat-value">{len(ciphers_count)}</span> 密码算法</div>
        <a href="daily/index.html" class="stat-item" style="text-decoration:none;background:linear-gradient(135deg,rgba(108,99,255,0.25),rgba(167,139,250,0.15));border-color:var(--accent);cursor:pointer;">📄 <span class="stat-value">每日精选</span></a>
      </div>
    </div>
  </header>

  <div class="container">
    <div class="controls">
      <input type="text" class="search-box" id="searchInput"
             placeholder="🔍 搜索论文标题、作者、密码、关键词..."
             oninput="filterPapers()">
      <button class="filter-btn" onclick="filterSignificance('all')">全部</button>
      <button class="filter-btn" onclick="filterSignificance('high')">🔴 High</button>
      <button class="filter-btn" onclick="filterSignificance('medium')">🟡 Medium</button>
    </div>

    <div class="main-layout">
      {sidebar_html}
      <div>
        <div class="result-count" id="resultCount">显示 {len(papers)} 篇论文</div>
        <div class="paper-list" id="paperList">
          {cards_html}
        </div>
        <div class="no-results" id="noResults" style="display:none">
          没有匹配的论文
        </div>
      </div>
    </div>
  </div>

  <script>
    let currentDir = 'all';
    let currentSignificance = 'all';

    function filterPapers() {{
      const query = document.getElementById('searchInput').value.toLowerCase();
      const cards = document.querySelectorAll('.paper-card');
      let visible = 0;

      cards.forEach(card => {{
        const matchSearch = !query || card.dataset.search.includes(query);
        const matchDir = currentDir === 'all' || card.dataset.dirs.split(',').includes(currentDir);
        const matchSig = currentSignificance === 'all' || card.dataset.significance === currentSignificance;

        if (matchSearch && matchDir && matchSig) {{
          card.style.display = '';
          visible++;
        }} else {{
          card.style.display = 'none';
        }}
      }});

      document.getElementById('resultCount').textContent = `显示 ${{visible}} 篇论文`;
      document.getElementById('noResults').style.display = visible === 0 ? '' : 'none';
    }}

    function filterDir(dir) {{
      currentDir = dir;
      document.querySelectorAll('.dir-item').forEach(el => {{
        el.classList.toggle('active', el.dataset.dir === dir);
      }});
      filterPapers();
    }}

    function filterSignificance(sig) {{
      currentSignificance = sig;
      document.querySelectorAll('.filter-btn').forEach(btn => {{
        btn.classList.remove('active');
      }});
      event.target.classList.add('active');
      filterPapers();
    }}

    // Initialize
    filterDir('all');
  </script>
</body>
</html>"""


def md_to_html_simple(md_text):
    """Convert simple markdown to HTML (tables, headers, bold, links, blockquotes)."""
    import re
    lines = md_text.split('\n')
    html_lines = []
    in_table = False
    in_blockquote = False

    for line in lines:
        stripped = line.strip()

        # Close blockquote if needed
        if in_blockquote and not stripped.startswith('>'):
            html_lines.append('</blockquote>')
            in_blockquote = False

        # Close table if needed
        if in_table and not stripped.startswith('|'):
            html_lines.append('</tbody></table>')
            in_table = False

        # Horizontal rule
        if stripped == '---':
            html_lines.append('<hr>')
            continue

        # Headers
        if stripped.startswith('### '):
            html_lines.append(f'<h3>{escape(stripped[4:])}</h3>')
            continue
        if stripped.startswith('## '):
            html_lines.append(f'<h2>{escape(stripped[3:])}</h2>')
            continue
        if stripped.startswith('# '):
            html_lines.append(f'<h1>{escape(stripped[2:])}</h1>')
            continue

        # Blockquotes
        if stripped.startswith('>'):
            if not in_blockquote:
                html_lines.append('<blockquote>')
                in_blockquote = True
            content = stripped[1:].strip()
            # Process inline formatting
            content = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', escape(content))
            html_lines.append(f'<p>{content}</p>')
            continue

        # Table rows
        if stripped.startswith('|') and stripped.endswith('|'):
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            # Skip separator rows like |------|------|
            if all(c.replace('-', '').replace(':', '') == '' for c in cells):
                continue
            if not in_table:
                html_lines.append('<table><thead><tr>')
                for c in cells:
                    html_lines.append(f'<th>{escape(c)}</th>')
                html_lines.append('</tr></thead><tbody>')
                in_table = True
            else:
                html_lines.append('<tr>')
                for c in cells:
                    html_lines.append(f'<td>{escape(c)}</td>')
                html_lines.append('</tr>')
            continue

        # Bold + links: **[title](url)**
        if stripped.startswith('**'):
            processed = stripped
            # Convert markdown links
            processed = re.sub(
                r'\*\*\[([^\]]+)\]\(([^)]+)\)\*\*',
                r'<strong><a href="\2" target="_blank">\1</a></strong>',
                processed,
            )
            processed = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', processed)
            html_lines.append(f'<p class="paper-entry">{processed}</p>')
            continue

        # Regular paragraph
        if stripped:
            processed = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', escape(stripped))
            processed = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', processed)
            html_lines.append(f'<p>{processed}</p>')
        else:
            html_lines.append('')

    if in_table:
        html_lines.append('</tbody></table>')
    if in_blockquote:
        html_lines.append('</blockquote>')

    return '\n'.join(html_lines)


def generate_daily_report_html(md_content, date_str):
    """Generate a standalone HTML page for a daily report."""
    body_html = md_to_html_simple(md_content)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>每日论文 — {date_str}</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-primary: #0f0f23;
      --bg-secondary: #1a1a36;
      --bg-card: #1e1e3a;
      --accent: #6c63ff;
      --accent-light: #8b83ff;
      --text-primary: #e8e8f0;
      --text-secondary: #a0a0c0;
      --text-muted: #6a6a8a;
      --border: #2a2a4a;
      --font-main: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      --font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: var(--font-main);
      background: var(--bg-primary);
      color: var(--text-primary);
      line-height: 1.7;
      padding: 0;
    }}
    .container {{
      max-width: 800px;
      margin: 0 auto;
      padding: 24px 16px 48px;
    }}
    .nav {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      z-index: 100;
      backdrop-filter: blur(20px);
    }}
    .nav a {{
      color: var(--accent-light);
      text-decoration: none;
      font-size: 0.9rem;
    }}
    .nav a:hover {{ text-decoration: underline; }}
    .nav .date {{
      color: var(--text-muted);
      font-family: var(--font-mono);
      font-size: 0.85rem;
    }}
    h1 {{
      font-size: 1.5rem;
      font-weight: 700;
      background: linear-gradient(135deg, var(--accent-light), #a78bfa);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 24px 0 8px;
    }}
    h2 {{
      font-size: 1.2rem;
      font-weight: 600;
      color: var(--accent-light);
      margin: 28px 0 12px;
      padding-bottom: 6px;
      border-bottom: 1px solid var(--border);
    }}
    h3 {{
      font-size: 1.05rem;
      font-weight: 600;
      color: var(--text-primary);
      margin: 20px 0 10px;
    }}
    p {{
      color: var(--text-secondary);
      font-size: 0.92rem;
      margin-bottom: 8px;
    }}
    p.paper-entry {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px 18px;
      margin: 12px 0 4px;
      transition: border-color 0.2s;
    }}
    p.paper-entry:hover {{
      border-color: var(--accent);
    }}
    p.paper-entry a {{
      color: var(--text-primary);
      text-decoration: none;
    }}
    p.paper-entry a:hover {{
      color: var(--accent-light);
    }}
    blockquote {{
      border-left: 3px solid var(--accent);
      padding: 8px 16px;
      margin: 8px 0 12px;
      background: rgba(108, 99, 255, 0.08);
      border-radius: 0 8px 8px 0;
    }}
    blockquote p {{
      color: var(--text-muted);
      font-size: 0.85rem;
      margin-bottom: 2px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0;
      font-size: 0.88rem;
    }}
    th, td {{
      padding: 8px 12px;
      text-align: left;
      border: 1px solid var(--border);
    }}
    th {{
      background: var(--bg-card);
      color: var(--accent-light);
      font-weight: 600;
    }}
    td {{
      color: var(--text-secondary);
    }}
    hr {{
      border: none;
      border-top: 1px solid var(--border);
      margin: 24px 0;
    }}
    strong {{ color: var(--text-primary); }}
    em {{ color: var(--text-muted); font-style: italic; }}
    @media (max-width: 600px) {{
      .container {{ padding: 12px 8px 32px; }}
      h1 {{ font-size: 1.2rem; }}
      h2 {{ font-size: 1.05rem; }}
      table {{ font-size: 0.8rem; }}
      th, td {{ padding: 6px 8px; }}
    }}
  </style>
</head>
<body>
  <div class="nav">
    <a href="../index.html">← 论文库</a>
    <span class="date">{date_str}</span>
    <a href="index.html">日报列表</a>
  </div>
  <div class="container">
    {body_html}
  </div>
</body>
</html>'''


def generate_daily_index_html(report_dates):
    """Generate an index page listing all daily reports."""
    items = ""
    for d in sorted(report_dates, reverse=True):
        items += f'    <a class="report-link" href="{d}.html">{d}</a>\n'

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>每日论文报告</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-primary: #0f0f23;
      --bg-card: #1e1e3a;
      --accent-light: #8b83ff;
      --text-primary: #e8e8f0;
      --text-secondary: #a0a0c0;
      --border: #2a2a4a;
      --font-main: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', 'Consolas', monospace;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: var(--font-main);
      background: var(--bg-primary);
      color: var(--text-primary);
      padding: 32px 16px;
    }}
    .container {{ max-width: 600px; margin: 0 auto; }}
    h1 {{
      font-size: 1.5rem;
      background: linear-gradient(135deg, var(--accent-light), #a78bfa);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 8px;
    }}
    .subtitle {{ color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 24px; }}
    .back {{ color: var(--accent-light); text-decoration: none; font-size: 0.9rem; }}
    .back:hover {{ text-decoration: underline; }}
    .report-link {{
      display: block;
      padding: 14px 18px;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 10px;
      margin-bottom: 8px;
      color: var(--text-primary);
      text-decoration: none;
      font-family: var(--font-mono);
      font-size: 0.95rem;
      transition: all 0.2s;
    }}
    .report-link:hover {{
      border-color: var(--accent-light);
      transform: translateX(4px);
    }}
  </style>
</head>
<body>
  <div class="container">
    <a class="back" href="../index.html">← 返回论文库</a>
    <h1>📄 每日论文报告</h1>
    <p class="subtitle">共 {len(report_dates)} 份报告</p>
{items}
  </div>
</body>
</html>'''


def build_daily_reports():
    """Build HTML pages for all daily markdown reports."""
    reports_dir = SURVEY_DIR / "reports" / "daily"
    daily_site_dir = SITE_DIR / "daily"
    daily_site_dir.mkdir(parents=True, exist_ok=True)

    if not reports_dir.exists():
        print("No daily reports directory found, skipping.")
        return

    report_dates = []
    for md_file in sorted(reports_dir.glob("*.md")):
        date_str = md_file.stem  # e.g., "2026-03-09"
        report_dates.append(date_str)

        with open(md_file, "r", encoding="utf-8") as f:
            md_content = f.read()

        html_content = generate_daily_report_html(md_content, date_str)
        html_path = daily_site_dir / f"{date_str}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    # Generate daily index
    if report_dates:
        index_html = generate_daily_index_html(report_dates)
        index_path = daily_site_dir / "index.html"
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_html)

    print(f"Generated {len(report_dates)} daily report pages in {daily_site_dir}")


def main():
    SITE_DIR.mkdir(parents=True, exist_ok=True)

    if not PAPERS_FILE.exists():
        print(f"Error: {PAPERS_FILE} not found")
        sys.exit(1)

    if not TAXONOMY_FILE.exists():
        print(f"Error: {TAXONOMY_FILE} not found")
        sys.exit(1)

    papers_data = load_yaml(PAPERS_FILE)
    taxonomy_data = load_yaml(TAXONOMY_FILE)

    papers = papers_data.get("papers", [])
    print(f"Loaded {len(papers)} papers from {PAPERS_FILE}")

    # Generate CSS
    css_path = SITE_DIR / "style.css"
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(generate_css())
    print(f"Generated {css_path}")

    # Generate main HTML
    html_content = generate_html(papers, taxonomy_data)
    html_path = SITE_DIR / "index.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated {html_path}")

    # Generate daily report pages
    build_daily_reports()

    print(f"\nDone! Open {html_path} in your browser.")


if __name__ == "__main__":
    main()
