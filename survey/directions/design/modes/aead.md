# 认证加密 (AEAD)

## 方向概述

AEAD（Authenticated Encryption with Associated Data）同时提供保密性和完整性保护，是现代密码学应用的核心原语。

## 关键问题

- Nonce-misuse resistance 设计
- 在线/离线模式的安全性分析
- 基于置换的 AEAD（如 sponge 模式）

## 代表方案

Ascon-AEAD, GIFT-COFB, OCB, GCM, CCM, SUNDAE-GIFT

## 论文列表

（见 `papers.yaml` 中 `directions` 含 `aead` 的条目）
