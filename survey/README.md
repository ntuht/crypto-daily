# 对称密码研究论文策展 (Symmetric Cipher Survey)

系统性收集、整理对称密码设计与分析领域的研究论文，组织成可操作的研究方向条目。

## 分类体系

论文按两大一级方向组织：

### 算法设计 (`design/`)

| 子类 | 说明 |
|------|------|
| **组件** | S-box、置换层、线性扩散层、轮函数结构、密钥编排 |
| **算法** | 按优化目标分：低时延、高吞吐、硬件友好、软件友好、轻量级 |
| **工作模式** | AEAD、哈希/XOF、可调密码 |

### 算法分析 (`analysis/`)

| 子类 | 说明 |
|------|------|
| **建模方法** | MILP/SAT/CP 建模、ML/LLM 辅助、自动化搜索框架 |
| **攻击技术** | 差分、不可能差分、回旋镖、线性、零相关、积分/Division Property、代数、中间相遇、相关密钥、不变量 |

## 文件说明

| 文件/目录 | 用途 |
|-----------|------|
| `taxonomy.yaml` | 分类体系定义 |
| `papers.yaml` | 论文数据库（结构化条目） |
| `directions/` | 每个研究方向的详细 markdown |
| `pdfs/` | 下载的论文 PDF（按方向分目录） |
| `site/` | 本地浏览网页（由 `build_site.py` 生成） |
| `scripts/` | 自动化脚本 |
| `weekly_reports/` | 每周自动生成的总结 |

## 使用方法

### 浏览论文

```bash
# 生成本地浏览站点
python survey/scripts/build_site.py
# 用浏览器打开 survey/site/index.html
```

### 每日抓取新论文

```bash
python survey/scripts/daily_fetch.py
```

### 导出 BibTeX

```bash
python survey/scripts/export_bibtex.py                    # 全量导出
python survey/scripts/export_bibtex.py --direction differential  # 按方向
```

### 生成概览

```bash
python survey/scripts/render_overview.py
```

## 论文条目格式

每篇论文在 `papers.yaml` 中的格式：

```yaml
- id: sun2014milp
  title: "Automatic Security Evaluation..."
  authors: [Siwei Sun, Lei Hu, Peng Wang]
  venue: ASIACRYPT 2014
  year: 2014
  url: "https://eprint.iacr.org/2014/747"
  directions: [differential, milp_sat_cp]
  ciphers: [SIMON, PRESENT, GIFT]
  significance: high       # high / medium / low
  summary: "首次系统性将 MILP 应用于自动差分特征搜索"
  status: reviewed          # reviewed / pending_review
```

## 贡献指南

1. 在 `papers.yaml` 中添加条目
2. 将 PDF 下载到 `pdfs/{direction}/` 对应目录
3. 更新对应的 `directions/*.md` 方向文件
4. 运行 `python survey/scripts/build_site.py` 重新生成站点
