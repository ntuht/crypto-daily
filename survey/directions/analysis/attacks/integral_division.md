# 积分与 Division Property

## 方向概述

积分攻击利用大量明文在密码操作下的代数性质（balance/unknown/constant）构建区分器。2015 年 Todo 提出 Division Property 将其推广为精确的代数传播分析，2016 年进一步扩展到比特级。借助 MILP/SAT 自动化搜索，成为近年最活跃的分析方向之一。

## 关键问题

- Bit-based Division Property 的高效 MILP/SAT 建模
- Division Property 传播规则的完备性
- Cube Attack 与 Division Property 的深层联系
- 超多项式（superpoly）的精确恢复

## 里程碑论文

| 年份 | 论文 | 贡献 |
|------|------|------|
| 1997 | Daemen, Knudsen & Rijmen | **Square 攻击**（积分攻击前身） |
| 2002 | Knudsen & Wagner | 积分攻击的**通用框架** |
| 2009 | Dinur & Shamir | **Cube Attack**（关联 superpoly） |
| 2012 | Bogdanov et al. | 零相关 ↔ 积分 ↔ 多维线性的理论联系 |
| 2015 | Todo | **Division Property** 的提出 |
| 2016 | Todo & Morii | **Bit-based Division Property** |
| 2016 | Xiang et al. | **MILP 自动搜索 Division Property** |
| 2017 | Todo et al. | Division Property + Cube Attack 结合 |

## 与 CryptoLLM 的关联

- **计划中**: Integral/Division Property skill
- **技术基础**: MILP 建模框架可直接扩展

## 论文列表

（见 `papers.yaml` 中 `directions` 含 `integral_division` 的条目）
