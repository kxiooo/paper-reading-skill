---
# ⚠️ 这是一篇虚构的示例笔记，仅用于展示 paper-ingest 的输出格式。
# 论文标题、作者、venue、数据均为占位内容，不要当成真实论文引用。
tags:
  - domain/Example-Domain-A
  - method/Diffusion-Model
  - method/Compositional-Generation
source_pdf: "[[_staging/archived/example-domain-a/ExamplePaper - Controllable Composition of Two Conditions.pdf]]"
related_notes:
  - "[[Other Paper - A Related Baseline]]"
created: YYYY-MM-DD
---

# ExamplePaper: Controllable Composition of Two Conditions

Jane Doe, John Smith, Example Venue 2026

## 一句话

提出一个把两个独立条件组合进同一个生成过程的两阶段框架，在不重训主干的前提下实现了可独立调节强度的组合控制。

## 核心方法

- **条件分解**：把复合条件拆成两个子条件，分别编码为独立的条件嵌入
- **两阶段注入**：第一阶段用 cross-attention 注入主条件，第二阶段用 gated residual 注入次条件
- **强度解耦**：为每个条件学习一个标量门控，推理时可独立调节
- **训练策略**：先冻结主干训练门控，再联合微调 10% 参数

## 创新点

1. 提出条件门控的加法分解形式，使两个条件的梯度互不干扰
2. 给出强度可调性的理论条件，并据此设计训练目标
3. 在两个 benchmark 上证明组合控制不牺牲单条件性能

## 解决的问题

解决 **Multi-condition Conflict**（多条件互相压制）——属于 [[1-problem-atlas]] 的 `Problem: Multi-condition Conflict` 节点。

本质问题是：两个条件在共享的注意力空间中竞争同一批 token，强势条件会吞掉另一条件的信号。

## 我的借鉴

- **门控分解**可以迁移到我的多条件编辑任务：把"内容保持"和"属性编辑"当成两个条件，用独立门控调节
- **先冻结后微调**的两阶段训练，适合我这种只有单卡、不能全量微调的设定
- 强度可调的理论条件可以借来设计消融实验，证明"不是调参调出来的"

## 我的评价 👈 条件性添加

思路干净，但只在两个 benchmark 上验证，跨域泛化存疑；门控的额外参数量在附录里没有充分讨论。

## 继承关系 👈 条件性添加

```
Classifier-Free Guidance (2022)
  └→ Composable Diffusion (2022)
       条件可加组合
         └→ ExamplePaper (2026)
              条件门控可加 + 强度独立调节
```

直接继承了 score composition 的可加性假设，把"固定权重相加"推进到"可学习门控 + 独立强度"。
