# 差分分析

## 方向概述

差分分析是最基本也最重要的对称密码分析技术之一。通过研究明文对的差分如何通过密码传播，搜索高概率差分特征来构建区分器或密钥恢复攻击。1991 年由 Biham 和 Shamir 正式提出，至今仍是评估密码安全性的首要指标。

## 关键问题

- 最优差分路径搜索（truncated → exact → clustering）
- 差分特征 clustering 效应（多条路径概率汇聚）
- 差分概率的精确计算（依赖性、马尔可夫假设）
- 比特级密码的大规模搜索可扩展性（SAT/MILP 瓶颈）

## 里程碑论文

| 年份 | 论文 | 贡献 |
|------|------|------|
| 1991 | Biham & Shamir | **差分分析的提出**，对 DES 的攻击 |
| 1991 | Lai, Massey & Murphy | 建立 Markov 密码理论框架，差分概率计算基础 |
| 1994 | Chabaud & Vaudenay | 揭示差分与线性分析的对偶关系 |
| 1995 | Knudsen | **Truncated differential** 概念，扩展分析范围 |
| 1994 | Matsui | 分支定界搜索算法（自动化差分搜索先驱） |
| 2011 | Mouha et al. | 首次 MILP 自动差分搜索 |
| 2014 | Sun et al. | 比特级 MILP 差分搜索通用框架 |
| 2019 | Gohr | 神经网络差分区分器（SPECK） |
| 2022 | Song et al. | Ascon 差分安全性下界（MILP+DFS） |

## 当前前沿 (2024-2026)

- ML 引导的差分路径搜索（Beam Search）
- 差分 clustering 的精确评估
- LLM 辅助策略选择（CryptoLLM）
- 大状态密码的可扩展分析（Ascon 等）

## 与 CryptoLLM 的关联

- **已实现**: truncated + exact differential skills, DFS trail search
- **已验证**: GIFT-64 9轮18活跃S-box, Ascon 3轮15活跃S-box
- **核心方向**: CryptoLLM 的主要分析功能

## 论文列表

（见 `papers.yaml` 中 `directions` 含 `differential` 的条目）
