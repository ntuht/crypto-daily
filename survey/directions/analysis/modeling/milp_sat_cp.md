# MILP/SAT/CP 建模技术

## 方向概述

将密码分析问题编码为数学规划（MILP）、布尔可满足性（SAT）或约束编程（CP）问题，利用通用求解器自动搜索最优特征或证明安全性下界。这是现代自动化密码分析的技术基础，自 2011 年首次提出以来，已成为评估新密码安全性的标准方法。

## 关键问题

- 编码紧致性（tightness）与求解效率的权衡
- 大规模比特级模型的可扩展性瓶颈
- 不同求解器（MILP vs SAT vs CP-SAT）的最优适用场景
- S-box 约束的凸包精确化
- 多轮组合搜索的分解策略

## 里程碑论文

| 年份 | 论文 | 贡献 |
|------|------|------|
| 2011 | Mouha et al. | **首次 MILP 差分/线性建模** |
| 2014 | Sun et al. | **比特级 MILP 通用框架 + S-box DDT 凸包** |
| 2015 | Todo | Division Property 的 MILP 编码 |
| 2016 | Todo & Morii | Bit-based DP 的 MILP 编码 |
| 2016 | Xiang et al. | MILP 自动搜索 Division Property（6个密码） |
| 2016 | Fu et al. | SAT 编码 ARX 差分传播 |
| 2017 | Sun et al. | **CP 方法与 MILP 对比** |
| 2017 | Sasaki & Todo | MILP 搜索不可能差分 |
| 2020 | Boura & Coggia | 更紧致的 S-box MILP 约束 |

## 当前前沿 (2024-2026)

- SAT/SMT 在大规模实例上的应用
- CP-SAT 混合求解策略
- 模型简化与预处理技术
- LLM 辅助建模选择（CryptoLLM 方向）

## 与 CryptoLLM 的关联

- **已实现**: MILP Generator, SAT Generator, Gurobi/HiGHS 后端
- **核心相关**: CryptoLLM 的技术基础
- **研究机会**: LLM 辅助模型选择、参数优化、求解器切换

## 论文列表

（见 `papers.yaml` 中 `directions` 含 `milp_sat_cp` 的条目）
