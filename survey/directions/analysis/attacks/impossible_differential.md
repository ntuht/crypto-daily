# 不可能差分

## 方向概述

不可能差分利用概率恰好为零的差分传播构建区分器。核心思想是 miss-in-the-middle：从加密和解密两个方向分别推导差分传播，在中间找到矛盾。由于不依赖概率估计，通常比普通差分攻击覆盖更多轮数。

## 关键问题

- 自动化不可能差分搜索（MILP/SAT 精确编码）
- 不可能差分到密钥恢复的转换效率优化
- 与 truncated differential 结合的分析方法
- U 方法和 UID 方法的自动化

## 里程碑论文

| 年份 | 论文 | 贡献 |
|------|------|------|
| 1998 | Knudsen | **不可能差分概念**（Twofish 分析） |
| 1999 | Biham, Biryukov & Shamir | **Miss-in-the-middle 系统化**（Skipjack 攻击） |
| 2003 | Kim et al. | 推广到通用分组密码结构 |
| 2017 | Sasaki & Todo | **MILP 自动搜索不可能差分** |
| 2020 | Hu & Wang | 统一 MILP 框架（不可能差分 + 零相关） |

## 与 CryptoLLM 的关联

- **计划中**: Impossible differential skill (Roadmap)
- **可利用**: 现有 MILP 框架可直接扩展

## 论文列表

（见 `papers.yaml` 中 `directions` 含 `impossible_differential` 的条目）
