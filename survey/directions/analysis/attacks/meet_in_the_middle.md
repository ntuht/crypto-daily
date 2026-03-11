# 中间相遇攻击

## 方向概述

中间相遇（MITM）攻击从加密和解密两个方向独立计算中间状态，在中间碰撞以降低搜索复杂度。1977 年 Diffie & Hellman 提出后，发展出 biclique、splice-and-cut、dissection 等重要变体。Biclique MITM 是对完整 AES 的已知最佳攻击。

## 里程碑论文

| 年份 | 论文 | 贡献 |
|------|------|------|
| 1977 | Diffie & Hellman | **MITM 概念**（双重 DES 不安全） |
| 2008 | Demirci & Selcuk | 对 AES 的新型 MITM 攻击 |
| 2011 | Bogdanov et al. | **Biclique AES 攻击**（完整 AES 首次理论攻击） |
| 2021 | Dong et al. | MILP 自动化 MITM 搜索 |

## 论文列表

（见 `papers.yaml` 中 `directions` 含 `meet_in_the_middle` 的条目）
