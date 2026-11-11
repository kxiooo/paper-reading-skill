---
type: taxonomy
created: YYYY-MM-DD
---

# 标签体系

> 标签用 `domain/` 和 `method/` 前缀区分"哪道题"和"用什么解"。
> 在 Obsidian `tags:` 字段中，空格替换为连字符（如 `domain/Human-Mesh-Recovery`）。
>
> **这是 starter 模板**：把下面的示例标签换成你领域的术语。每次 ingest 只增不改，保持受控词表。

## Domain Tags（研究方向）

> "这道题叫什么"。建议 5-20 个，粒度对齐你读论文时实际会用的检索词。

- Example-Domain-A
- Example-Domain-B
- Example-Domain-C

## Method Tags（方法 / 技术）

> "这道题用什么方法解"。建议 10-40 个，跨论文复用。

- Diffusion-Model
- Transformer
- Feed-Forward-Reconstruction
- Reinforcement-Learning
- Implicit-Representation
- Compositional-Generation
- Inversion-Based-Editing
- Flow-Matching
- Retrieval-Augmented
- LoRA / MoE-PEFT

## Foundation Tags（基础 / 先验知识）

> 用于 `_foundation/` 下的基础论文（不属于某一特定 domain，而是跨领域的基础范式）。

- Foundation-Topic-A
- Representation-Learning
- Discrete-Representation
- System-Integration

## 维护规则

1. **先复用，后新增。** ingest 时优先从现有标签里选；确实没有合适的才提议 `[新增]`。
2. **同任务必须共享标签。** 两篇论文做同一类任务时，至少共享一个 domain 或 method 标签，否则 Obsidian 图谱断连。
3. **标签只增不删。** 废弃的标签移到本文件底部 `## Deprecated` 记录，避免旧笔记失效。
4. **命名统一。** 全英文、连字符、首字母大写（`domain/Image-Editing`），不要中英文混用。
