# 轮函数结构设计

## 方向概述

轮函数结构决定了密码的整体架构。主要范式包括 SPN（代换置换网络）、Feistel 网络、ARX（加法-旋转-异或）、AND-RX、广义 Feistel 网络（GFN）等。不同结构在安全性证明难度、实现效率和抗特定攻击能力方面各有特点。

## 关键问题

- 不同结构的安全性证明边界（如 Feistel 的 Luby-Rackoff 定理）
- SPN vs Feistel vs ARX 的系统性对比
- 新型轮函数结构的探索（如 AND-RX 用于 Ascon）
- 结构选择对分析复杂度的影响

## 里程碑论文

| 年份 | 论文 | 贡献 |
|------|------|------|
| 1973 | Feistel | **Feistel 结构**的提出（Lucifer/DES） |
| 1988 | Luby & Rackoff | **证明 3 轮 Feistel 是安全 PRP** |
| 1989 | Zheng, Matsumoto & Imai | 广义 Feistel 网络（GFN）理论 |
| 2002 | Daemen & Rijmen | **Wide Trail 策略**（AES/SPN 设计理论） |

## 与 CryptoLLM 的关联

- **已实现**: CDL 支持 SPN、Feistel、ARX 结构描述
- **可扩展**: 更多结构类型的通用建模

## 论文列表

（见 `papers.yaml` 中 `directions` 含 `round_function` 的条目）
