# 硬件友好密码设计

## 方向概述

硬件友好密码针对 ASIC/FPGA 实现优化，追求最小化面积（门等效数 GE）、功耗和能耗。PRESENT (2007) 开创了超轻量级 SPN 范式，后续 GIFT、SKINNY 等在安全性/面积比上持续改进。NIST LWC 竞赛使该方向达到高潮。

## 关键问题

- 面积-安全性-吞吐量的帕累托优化
- 串行化实现 vs 展开实现的权衡
- 侧信道防护（DPA/DFA）的硬件成本
- 理论安全轮数 vs 实现轮数的差距

## 里程碑论文

| 年份 | 论文 | 贡献 | GE |
|------|------|------|-----|
| 2007 | Bogdanov et al. | **PRESENT**（超轻量级 SPN 开创者） | 1570 |
| 2009 | De Cannière et al. | **KATAN/KTANTAN**（极小面积） | 462-1054 |
| 2011 | Guo et al. | **LED**（无密钥编排 AES-like） | 966 |
| 2013 | Beaulieu et al. | **SIMON**（硬件友好 Feistel） | ~842 |
| 2015 | Zhang et al. | **RECTANGLE**（bitslice 友好） | 1600 |
| 2016 | Beierle et al. | **SKINNY/MANTIS**（TBC + Tweakey） | ~1223 |
| 2017 | Banik et al. | **GIFT**（PRESENT 继承者，更好安全性） | ~928 |
| 2019 | Beierle et al. | **CRAFT**（DFA 防护 TBC） | |
| 2021 | Dobraunig et al. | **Ascon**（NIST LWC 标准） | |

## 论文列表

（见 `papers.yaml` 中 `directions` 含 `hardware_friendly` 的条目）
