# 线性分析

## 方向概述

线性分析利用明文、密文和密钥之间的线性逼近关系来恢复密钥信息。1993 年由 Matsui 提出，对 DES 的首次实验攻击确立了其里程碑地位。多维线性、零相关线性等变体进一步扩展了攻击能力。

## 关键问题

- 线性逼近的精确相关值计算
- 多维线性分析的数据复杂度优化
- 线性 hull 效应的精确评估
- 与差分分析的统一理论（如通过 Fourier 分析）

## 里程碑论文

| 年份 | 论文 | 贡献 |
|------|------|------|
| 1993 | Matsui | **线性分析方法**的提出（DES） |
| 1994 | Matsui | Algorithm 2 首次实验攻破 DES |
| 1994 | Chabaud & Vaudenay | 差分与线性的对偶关系 |
| 2008 | Hermelin, Cho & Nyberg | **多维线性分析**系统化 |
| 2010 | Cho | PRESENT 线性分析 |
| 2012 | Bogdanov & Rijmen | 零相关线性分析 |

## 与 CryptoLLM 的关联

- **已实现**: LAT 自动计算（`cdl/components.py`）
- **计划中**: 线性分析 Skill

## 论文列表

（见 `papers.yaml` 中 `directions` 含 `linear` 的条目）
