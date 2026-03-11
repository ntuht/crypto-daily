# 软件友好密码设计

## 方向概述

软件友好密码针对通用处理器优化，利用 CPU 原生指令（加法、移位、异或）实现高效加密。ARX 结构和 bitslice 技术是典型设计手段。

## 关键问题

- ARX 结构的安全性证明方法
- 跨平台（x86, ARM, RISC-V）性能一致性
- Bitslice 实现与常规实现的权衡

## 代表算法

ChaCha20, Salsa20, SPECK, Chaskey, NORX

## 里程碑论文

| 年份 | 论文 | 贡献 | 备注 |
|------|------|------|------|
| | | | |

## 论文列表

（见 `papers.yaml` 中 `directions` 含 `software_friendly` 的条目）
