# 相关密钥攻击

## 方向概述

相关密钥攻击利用不同但有已知关系（如异或差分）的密钥加密产生的信息。密钥编排设计的弱点是此类攻击的主要利用对象。Biryukov & Khovratovich 对完整 AES-192/256 的攻击是该方向最著名的成果。

## 里程碑论文

| 年份 | 论文 | 贡献 |
|------|------|------|
| 1993 | Biham | **相关密钥攻击框架** |
| 2009 | Biryukov & Khovratovich | **完整 AES-192/256 的相关密钥攻击** |
| 2014 | Jean, Nikolić & Peyrin | **TWEAKEY 框架**（统一 key + tweak） |

## 论文列表

（见 `papers.yaml` 中 `directions` 含 `related_key` 的条目）
