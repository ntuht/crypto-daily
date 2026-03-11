# 研究机会：神经网络密码学（Neural Cryptography）

> 发现日期：2026-03-03  
> 来源论文：[Deep Neural Cryptography](https://eprint.iacr.org/2025/288) (Shamir et al.), [Built-in Crypto Expert](https://eprint.iacr.org/2026/411) (Weng et al.)  
> 优先级：⭐⭐⭐（高）  
> 状态：待深入调研

## 为什么值得关注

密码学与 DNN 的深层融合正在形成一个新的交叉领域。Shamir 2025 年发现 ReLU 实现的 AES-128 可被连续差分攻击（CDA）在线性时间内攻破，揭示了连续域计算对密码学安全假设的根本挑战。这一发现催生了多个有前景的研究机会。

## 机会 1：密码学模型水印 🟢

**痛点**：当前 DNN 水印方案是统计性的（security by obscurity），可被 fine-tuning/蒸馏移除。  
**机会**：利用密码学硬度假设（AES 安全性）实现不可伪造的模型所有权证明。  
**关键开放问题**：
- AES 子网络在 fine-tuning 后的存活性（密码学要求 bit-perfect，与 NN 模糊容错矛盾）
- 蒸馏攻击的防御（黑盒查询训练新模型可完全绕过）
- 实用化的嵌入方案设计

**现有替代方案**：无严格更强的替代方案 → 有理论贡献空间。

## 机会 2：AI 生成内容密码学溯源 🟢

**痛点**：C2PA 元数据可被截屏/裁剪丢失；SynthID 像素水印无密码学安全证明。  
**机会**：在生成模型（diffusion decoder）中嵌入密码学可验证的不可移除水印。  
**产业现状**：Google SynthID、C2PA 已商用，但安全性层级不够 → 有升级空间。

## 机会 3：可验证模型训练（Proof of Training）🟡

**痛点**：模型所有权无法技术性证明；EU AI Act 要求训练可追溯性。  
**商业场景**：模型交易审计、IP 诉讼举证、监管合规。  
**技术瓶颈**：完整 ZK 证明计算量不可行，当前仅有 Commitment Chain 妥协方案。  
**付费方**：模型市场平台、企业采购方、AI 保险公司、监管机构。

## 与 CryptoLLM 的关系

| 维度 | 关联 |
|------|------|
| 互补性 | 本方向从"保护"角度做 Crypto+AI，CryptoLLM 从"分析"角度 |
| 技术复用 | 可微分密码原语（SoftXOR/SoftLUT）对我们建模密码结构有参考价值 |
| 能力优势 | 我们在对称密码分析上的积累可用于评估密码学水印的安全强度 |

## 相关论文

### 子领域 A：DNN 中的密码学实现与安全性（基础理论）

| 论文 | 来源 | 关键贡献 |
|------|------|---------|
| [Deep Neural Cryptography](https://eprint.iacr.org/2025/288) — Gerault, Hambitzer, Ronen, **Shamir** | ePrint 2025 / SAC | ⭐ **奠基性工作**。形式化定义 DNN 密码学的正确性/安全性；发现 CDA 线性时间攻破 ReLU-AES-128（100% 成功率）；Sanitization+Masking 防御方案 |
| [Built-in Crypto Expert for AI](https://eprint.iacr.org/2026/411) — Weng et al. | ePrint 2026 | 将 AES 作为 MoE Expert 嵌入 LLM；SoftXOR/SoftLUT/GF Conv 可微分代理；训练-推理替换机制 |
| [Deep Neural Cryptography](https://eprint.iacr.org/2025/288) (extended related work) | — | 同一方向的相关工作：NN 修改 AES（权重作为密钥）、NN 用于侧信道攻击掩码 AES、NN 复用做高效密码运算 |

### 子领域 B：DNN 模型水印与 IP 保护

| 论文 | 来源 | 关键贡献 |
|------|------|---------|
| [CHIP: Chameleon Hash-based Irreversible Passport](https://arxiv.org/abs/2401.07226) | arXiv 2024 | 用**变色龙哈希**（密码学原语）生成不可逆的模型护照，实现鲁棒所有权验证和主动使用控制 |
| [Fed-PK-Judge: Provably Secure IP Protection for FL](https://ieeexplore.ieee.org/document/10858308) | IEEE 2025 | 联邦学习场景下的 NN 水印框架；结合 PKI 和非对称签名实现可证明安全的所有权验证 |
| Authority Backdoor — 硬件指纹锁定模型 | arXiv 2024 | 在模型中嵌入硬件指纹触发器，无触发器时模型性能降级 → 可用于模型授权控制 |
| [IPCert: Certified Neural Network Watermarking](https://openaccess.thecvf.com/content/CVPR2023/papers/Bansal_Certified_Neural_Network_Watermarks_With_Randomized_Smoothing_CVPR_2023_paper.pdf) | CVPR 2023 | 基于密码学签名的可证明安全水印方案，讨论抗歧义攻击 |

### 子领域 C：AI 生成内容溯源与水印

| 论文 | 来源 | 关键贡献 |
|------|------|---------|
| [SynthID-Image: Watermarking at Internet Scale](https://arxiv.org/abs/2510.09263) | arXiv 2025 | Google DeepMind。深度学习嵌入不可见水印；**已标记 100 亿+** 图片/视频帧；详述威胁模型和大规模部署挑战 |
| [SynGuard: Robustness Assessment of SynthID-Text](https://arxiv.org/abs/2508.20228) | arXiv 2025 | 揭示 SynthID-Text 对释义/复制粘贴攻击的脆弱性；提出语义对齐+概率水印的混合框架 |
| [SynthID Text (Nature)](https://deepmind.google/technologies/synthid/) | Nature 2024 | SynthID 文本水印的正式技术论文；已开源 |
| C2PA 标准 (Adobe/MS/BBC) | 行业标准 | 基于数字签名的内容来源证明；元数据嵌入图片但可被截屏丢失 |

### 子领域 D：零知识机器学习（ZKML）/ 可验证模型训练

| 论文 | 来源 | 关键贡献 |
|------|------|---------|
| [Kaizen: Zero-Knowledge Proofs of Training for DNN](https://eprint.iacr.org/2024/162) | ePrint 2024 / **CCS'24** | ⭐ **zkPoT 奠基工作**。形式化零知识训练证明；GKR 风格的梯度下降证明系统；VGG-11 (10M参数) prover 15min/iter，proof 1.63MB，verifier 130ms |
| [ZKBoost: ZK Verifiable Training for XGBoost](https://eprint.iacr.org/) | ePrint 2026 | 首个 XGBoost 的 zkPoT 协议；证明在承诺数据集上正确训练而不泄露数据或参数 |
| [ZIP: Zero-Knowledge AI Inference with High Precision](https://eprint.iacr.org/) | ePrint / **CCS'25** | 高精度 ZK-SNARK for AIaaS 推理；支持 IEEE-754 双精度浮点 |
| [ZKTorch: Compiling ML Inference to ZK Proofs](https://arxiv.org/abs/2501.17172) | arXiv 2025 | 通过并行证明累积编译 ML 推理到 ZK 证明；支持 CNN/RNN/LLM 多种层类型 |
| [zkDL: Efficient ZK Proofs of Deep Learning Training](https://arxiv.org/abs/2307.16273) | arXiv 2023 | 前向+反向传播建模为算术电路的 ZK 证明 |
| [ZKML: Optimizing System for ML Inference in ZK Proofs](https://arxiv.org/abs/2402.02726) | arXiv 2024 | TensorFlow → ZK-SNARK 电路编译器；支持视觉模型和蒸馏 GPT-2 |
| [Survey: ZK Proof Based Verifiable ML](https://arxiv.org/abs/2502.15483) | arXiv 2025 | 综述：分为 verifiable training / inference / testing 三类 |
| [EZKL Framework](https://github.com/zkonduit/ezkl) | 开源工具 | ONNX → ZK-SNARK 电路转换框架；链上验证 |

## 下一步行动

- [ ] 深入阅读 Shamir 论文的 CDA 攻击细节和防御方案
- [ ] 阅读 Kaizen (CCS'24) — 当前最实用的 Proof of Training 方案
- [ ] 调研密码学水印在 fine-tuning 后存活性的已有实验结果（CHIP / Authority Backdoor）
- [ ] 关注 SynthID 开源实现，评估与密码学结合的可行性
- [ ] 评估是否可将 CryptoLLM 的密码分析能力用于水印安全性评估
