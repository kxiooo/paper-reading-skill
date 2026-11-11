---
title: "科研问题速查表"
description: "唯一入口：把你遇到的问题映射到机制和算子"
created: YYYY-MM-DD
tags:
  - meta/library
---

# 科研问题速查表（Quick Query Table）

> **这是整个库的唯一入口。**
> 打开库时不是看分类，而是问：**"我现在想让模型做到什么？失败在哪里？"**
> 在下面这张表里找到你的问题 → 跳转到对应机制 / 算子 → 看论文怎么解决 → 找 Gap。

核心链路：

```
Problem（我遇到的问题）
  → Failure Mode（失败表现）
    → Mechanism（底层机制）
      → Operator（怎么接进模型）
        → Paper（谁解决过）
          → Gap（还剩什么没解决）
```

## 使用说明

1. **查表**：按"我想解决的问题"列找最接近的一行。
2. **看本质问题**：同一行内"本质问题"告诉你这是哪一类失败——这是跨领域迁移的钥匙。
3. **跳转**：
   - 本质问题的详细模板 → `[[1-problem-atlas]]`
   - 优先查机制 → `[[2-mechanism-atlas]]`
   - 常用操作 → `[[3-operator-cookbook]]`
4. **查完机制去翻该问题节点的"代表论文"**，看别人怎么解决。
5. **找 Gap**：问题节点底部的 Remaining Gap 就是研究机会。

---

## Quick Query Table（starter 示例）

> 把下面的示例行替换成你领域的问题。每行一句话即可，细节写在对应图谱节点里。

| 我想解决的问题 | 常见失败表现 | 本质问题 | 优先查机制 | 常用操作 |
| ------------- | ------------ | -------- | ---------- | -------- |
| 让生成结果听条件 | 条件被忽略 | Condition Injection Failure | condition injection / alignment | cross-attention, FiLM, adapter |
| 让结果听参考样本 | 参考只影响风格或完全不生效 | Reference Conditioning Failure | retrieval / feature alignment / adapter | encoder, cross-attn |
| 多个条件同时生效 | 一个条件压过另一个 | Multi-condition Conflict | decomposition / routing / CFG composition | alternating CFG, MoE, gated fusion |
| 控制到指定位置 | 语义对了但位置不对 | Grounding Failure | grounding / mask / graph | attention map, region token |
| 只改局部 | 改一处导致全局变化 | Local Control Failure | local control / null-space / mask | part adapter, masked attention |
| 连续调节强弱 | 只能有 / 无 | Continuous Control Failure | slider / latent direction | semantic direction, strength |
| 长序列保持一致 | 单帧好，连起来崩 | Temporal Consistency Failure | memory / propagation / feedback | temporal attention, latent memory |
| 训练类有效、新类崩 | 泛化不足 | Generalization Failure | composition / retrieval / regularization | data augmentation, adapter |

---

## 怎么养这张表

- 每次 ingest 后，问一句：**"这篇论文解决的问题，能对上表里的哪一行？"**
- 对得上 → 在该行补一篇代表论文
- 对不上 → 可能是新失败模式，在 `[[1-problem-atlas]]` 新建节点，再回来加一行
- 表超过 15 行时，考虑拆成两个粒度（任务层 / 机制层）

> **维护铁律**：只在有新增时更新。这张表的价值在于"能一眼扫完"，不要让它变成论文列表。
