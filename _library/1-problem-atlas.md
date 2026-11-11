---
title: "AI 科研问题图谱"
description: "按失败模式分类的问题库——入口是 00-quick-query.md"
created: YYYY-MM-DD
tags:
  - meta/library
---

# 科研问题图谱（Problem Atlas）

> 记录 AI 研究中**反复出现的问题模式**，而不是具体任务。
> 组织原则：**按"为什么失败"分类**，不按领域分类——这样 A 领域的问题才能连到 B 领域的方法，再迁移回来。

核心链路：`Problem → Failure Mode → Mechanism → Operator → Paper → Gap`

**入口**：先查 `[[00-quick-query]]` 总表，再进对应问题节点。

**维护**：每篇论文 ingest 时，判断它解决了哪个 / 哪几个问题，把论文加进该节点的「代表论文」表。只有全新的失败模式才新建问题节点。

---

## 📋 问题导航（starter 示例）

| # | 问题 | 一句话 |
|---|------|--------|
| 1 | [[#Problem- Condition Injection Failure\|条件无法进入模型]] | 条件喂进去了但生成不听话 |
| 2 | [[#Problem- Reference Conditioning Failure\|参考条件不生效]] | 参考样本没起作用 |
| 3 | [[#Problem- Multi-condition Conflict\|多条件冲突]] | 一个条件压过另一个 |
| 4 | [[#Problem- Grounding Failure\|不知道控制哪里]] | 知道语义但没绑定到空间实体 |
| 5 | [[#Problem- Local Control Failure\|局部控制失败]] | 想改局部，影响全局 |
| 6 | [[#Problem- Temporal Consistency Failure\|时序不一致]] | 单帧好，连起来崩 |
| 7 | [[#Problem- Generalization Failure\|泛化失败]] | 训练类有效，新类崩 |
| 8 | [[#Problem- Evaluation Mismatch\|评估失真]] | 指标好但实际不好 |

---

## Problem: Condition Injection Failure

### 一句话定义
模型拥有额外条件（text / image / depth / trajectory / audio），但生成过程没有有效利用该条件——条件进入了模型，但没有进入"决策"。

### 典型表现
- 文本里的关键属性被忽略
- 换条件后输出几乎不变
- 条件只在早期层生效，后续层又回到无条件分布

### 为什么失败（六问 1-3）
1. **本质问题**：条件信号与生成主干的表示空间不对齐
2. **为何已有方法失败**：只在输入层拼接，缺少逐层的条件注入与监督
3. **失败模式归属**：condition injection / alignment 失败

### 代表论文
| 论文 | 注入方式 | 关键设计 |
|------|---------|---------|
| <!-- [[笔记名]] --> | cross-attention / FiLM / adapter | <!-- 一句话 --> |

### Remaining Gap
- 多条件之间的强度如何自动分配？
- 条件注入与预训练权重的冲突如何缓解？

---

## 新建问题节点模板

> 复制下面这段，替换标题与内容。**只有确实出现了新的失败模式才新建**。

```markdown
## Problem: <名称>

### 一句话定义
...

### 典型表现
- ...

### 为什么失败（六问 1-3）
1. **本质问题**：...
2. **为何已有方法失败**：...
3. **失败模式归属**：...

### 代表论文
| 论文 | 做法 | 关键设计 |
|------|------|---------|
| [[笔记名]] | ... | ... |

### Remaining Gap
- ...
```

---

## 维护规则

1. **一个节点只描述一种失败模式。** 混在一起就无法迁移。
2. **代表论文不超过 8 篇。** 超过就说明节点该拆了。
3. **Gap 必须具体。** "效果不好"不是 Gap，"多条件强度无法自动分配"才是。
4. **跨领域优先。** 同一个节点下尽量收不同领域的论文——这是这个库最大的价值。
