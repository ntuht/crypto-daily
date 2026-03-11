# 回旋镖与 Rectangle 攻击

## 方向概述

回旋镖攻击将密码分成上下两半，分别利用两条短差分特征组合攻击，有效绕过了单条长路径概率过低的问题。Rectangle attack 将其从自适应选择明文推广到选择明文模型。2018 年 BCT 的提出使得回旋镖分析达到新的精度。

## 关键问题

- BCT/UBCT/LBCT 的高效计算与分析
- 基于 MILP 的回旋镖区分器自动搜索
- 回旋镖 switch 的精确建模
- 与差分 clustering 的结合

## 里程碑论文

| 年份 | 论文 | 贡献 |
|------|------|------|
| 1999 | Wagner | **回旋镖攻击**的提出 |
| 2000 | Kelsey, Kohno & Schneier | Amplified boomerang 变体 |
| 2002 | Biham, Dunkelman & Keller | **Rectangle attack**（选择明文模型） |
| 2018 | Cid et al. | **BCT**（精确刻画 S-box 回旋镖兼容性） |
| 2019 | Song, Qin & Hu | UBCT/LBCT 细化分析精度 |
| 2020 | Wang & Peyrin | MILP 自动搜索回旋镖区分器 |

## 论文列表

（见 `papers.yaml` 中 `directions` 含 `boomerang` 的条目）
