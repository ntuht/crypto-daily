# 研究机会：AI 随机数生成器安全性

> 发现日期：2026-03-03  
> 来源论文：[Attacks and Remedies for Randomness in AI](https://eprint.iacr.org/2025/2161) (Leander et al.)  
> 优先级：⭐⭐⭐（高）  
> 状态：待深入调研

## 为什么值得关注

AI/ML 框架（JAX、TensorFlow、PyTorch）广泛使用的 PRNG —— **PHILOX** 和 **THREEFRY** —— 被证明存在实际可利用的安全漏洞。这些 PRNG 是 counter-based 设计（基于精简的分组密码），牺牲安全性换 GPU 并行性能。本文用传统密码分析（差分-线性攻击、乘法差分）直接攻破了它们。

## 核心发现

### PHILOX（TensorFlow/PyTorch 默认 PRNG）

- 基于 **Feistel 结构 + 乘法**，仅 10 轮
- 使用 **乘法差分** 技术攻击
- 安全性远低于密码学级别的 PRNG

### THREEFRY（JAX 默认 PRNG）

- 基于 **Threefish**（SHA-3 候选方案的内部置换）的精简版
- 仅 20 轮（Threefish 原版 72 轮）
- 使用 **差分-线性密码分析** 攻击

### 关键结论

> AI 框架中的 PRNG 选择了性能而非安全性。论文证明可以用密码学安全的替代方案（如基于 AES/ChaCha 的 PRNG）替换，且对 AI/ML 整体工作负载的性能影响 **可忽略不计**。

## 研究机会

### 机会 1：AI 基础设施密码分析 🟢

- **直接应用 CryptoLLM 的密码分析能力**：PHILOX 和 THREEFRY 都是轻量级密码构造
- PHILOX 的 Feistel+乘法结构、THREEFRY 的 ARX 结构都在我们的分析范围内
- 可以尝试用 CryptoLLM 自动化搜索更优的差分/线性路径

### 机会 2：安全 PRNG 替代方案评估 🟡

- 论文推荐使用密码学安全的 PRNG（AES-CTR / ChaCha）
- 可以评估不同替代方案的安全性-性能权衡
- 与 GPU/TPU 并行计算的兼容性分析

### 机会 3：随机性对 AI 训练安全的影响 🟡

- 可预测的 PRNG → 训练数据 shuffle 可被预测 → 梯度信息泄露
- Dropout 的随机性被预测 → 模型架构泄露
- Diffusion model 的噪声可预测 → 生成内容可被还原

## 与 CryptoLLM 的关系

| 维度 | 关联 |
|------|------|
| **直接适用** | PHILOX 和 THREEFRY 是轻量级对称密码构造，可直接用 CryptoLLM 分析 |
| **攻击技术** | 论文使用差分-线性攻击和乘法差分 —— 前者在 CryptoLLM 的技能范围内 |
| **作者团队** | Gregor Leander（Bochum）—— 对称密码顶尖团队，值得持续关注 |

## 相关论文

| 论文 | 来源 | 关键贡献 |
|------|------|---------|
| [Attacks and Remedies for Randomness in AI: Cryptanalysis of PHILOX and THREEFRY](https://eprint.iacr.org/2025/2161) — Leander et al. | ePrint 2025 | ⭐ 核心论文。实际攻破 AI 框架默认 PRNG；调研随机数使用场景；提出密码学安全替代方案 |
| Parallel Random Numbers: As Easy as 1, 2, 3 — Salmon et al. | SC 2011 | PHILOX 和 THREEFRY 的原始设计论文 |

## 下一步行动

- [ ] 精读论文的攻击技术细节（差分-线性 + 乘法差分）
- [ ] 评估 CryptoLLM 对 PHILOX/THREEFRY 的建模可行性（Feistel+乘法、ARX 结构）
- [ ] 调研 AI 训练中随机数被预测的实际安全影响
