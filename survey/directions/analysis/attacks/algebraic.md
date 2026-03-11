# 代数攻击

## 方向概述

代数攻击将密码转化为代数方程组求解问题。主要方法包括 XL/XSL 算法、Gröbner 基方法、Cube Attack（利用超多项式恢复密钥）和插值攻击。2017 年 Todo 等人将 Division Property 与 Cube Attack 结合，实现了 superpoly 的精确恢复，极大增强了攻击能力。

## 里程碑论文

| 年份 | 论文 | 贡献 |
|------|------|------|
| 2000 | Courtois et al. | **XL/XSL 算法**（多变量方程组求解） |
| 2009 | Dinur & Shamir | **Cube Attack**（超多项式恢复密钥） |
| 2017 | Todo et al. | **Division Property + Cube Attack 结合** |
| 2020 | Hao et al. | 改进代数 superpoly 恢复方法 |

## 论文列表

（见 `papers.yaml` 中 `directions` 含 `algebraic` 的条目）
