# S-box 设计与评估

## 方向概述

S-box 是对称密码中唯一的非线性组件，其密码学性质直接决定了算法的安全性。研究涉及 S-box 的构造方法、安全性指标（差分均匀度、非线性度、代数度、APN 性质）以及实现成本的权衡。4-bit S-box 已被完整分类，8-bit S-box 的系统构造仍是开放问题。

## 关键问题

- 安全性指标与硬件/软件实现成本的最优平衡
- 大尺寸 S-box（8-bit）的系统构造方法
- APN 置换在偶数维度上的存在性（Big APN Problem）
- S-box 的代数结构与抗攻击能力的关系
- BCT（回旋镖兼容性表）分析

## 里程碑论文

| 年份 | 论文 | 贡献 |
|------|------|------|
| 1994 | Nyberg | **差分均匀度概念**的形式化 |
| 2007 | Leander & Poschmann | **4-bit S-box 完整分类**（仿射等价） |
| 2011 | Ullrich et al. | 最优 bitslice S-box 实现搜索 |
| 2016 | Canteaut et al. | 统一 S-box 安全性评估框架 |
| 2018 | Cid et al. | BCT 分析 S-box 回旋镖性质 |

## 与 CryptoLLM 的关联

- **已实现**: DDT/LAT 自动计算 (`cdl/components.py`)
- **可扩展**: S-box 安全性自动评估、BCT 计算
- **研究机会**: LLM 辅助 S-box 设计空间探索

## 论文列表

（见 `papers.yaml` 中 `directions` 含 `sbox` 的条目）
