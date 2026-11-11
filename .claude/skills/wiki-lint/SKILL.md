---
name: wiki-lint
description: "定期检查知识库健康状态：缺失标签、索引不同步、孤立笔记、失效链接、过期内容。"
---

# Wiki Lint

> 知识库的定期健康检查。找矛盾、找孤儿、找过期、找遗漏。不自动修——报告问题，等用户决定。

## 触发

- 用户说"lint"、"健康检查"、"检查笔记"、"wiki 状态"
- 每 ingest 5 篇论文后自动建议一次
- 用户说"最近加了挺多论文，检查一下"

## 检查项目

### 1. 缺失 frontmatter

扫描 `_staging/notes/` 和 `论文阅读+思路拓展/` 下所有 `.md`：
- `tags:` 中缺少 `domain/` 前缀的标签 → 标记
- `tags:` 中缺少 `method/` 前缀的标签 → 标记
- `related_notes` 为空但与其他笔记共享 `domain/` 或 `method/` tag → 建议 crosslink

### 2. index.md 不同步

- 笔记存在但不在 index 中的 → 建议添加
- index 中有条目但对应笔记已删除 → 建议清理
- 笔记的 `tags:` 中 `domain/` 分类变了但 index 没更新 → 建议修正

### 3. 孤立笔记

- `related_notes` 为空但 `method/` 前缀 tags 与其他笔记共享
- 没有任何其他笔记的 `related_notes` 指向它
- 判断：如果该笔记有 ≥2 个 `method/` 前缀 tags 与至少 1 篇其他笔记共享 → 建议 crosslink

### 4. 标签不在 taxonomy 中

- 笔记中使用的 `domain/` 和 `method/` 前缀 tags 不在 `_meta/taxonomy.md` 中（匹配时忽略前缀）
- 如果是用户有意使用的新标签 → 建议同步到 taxonomy

### 5. 失效 wikilinks

- `related_notes` 中的链接指向不存在的文件
- `source_pdf` 指向不存在的 PDF

### 6. 过期笔记

- `status: draft` 且 30 天以上未更新
- 没有 `related_notes` 也没有后续跟进 → 标记为可能需要归档或补完

## 输出格式

```
📋 Wiki 健康检查报告（2026-05-22）

⚠️ 缺失标签（2）
  [[_staging/notes/某论文]] - tags: 中缺少 domain/ 前缀标签
  [[论文阅读+思路拓展/某改进]] - tags: 中缺少 method/ 前缀标签

🔗 建议 Crosslink（3）
  [[A]] ↔ [[B]] - 共享 Contact Feedback，但未关联
  [[C]] ↔ [[D]] - 共享 Temporal Smoothing，但未关联

📇 Index 不同步（1）
  [[_staging/notes/某论文]] 在 index 中缺少

🏷️ 新标签未收录（2）
  "Sketch-Based Editing" 在笔记中出现但 taxonomy 中没有

💀 失效链接（0）
  无

📅 过期草稿（1）
  [[某旧笔记]] - 35 天未更新，status: draft

---
需要我处理哪些？
```

## 不自动修

- 所有问题只报告，不自动修改
- 用户逐项确认后才执行修正
- crosslink 建议 → 用户确认 → 运行 paper-crosslink
- taxonomy 更新 → 用户确认 → 追加到 taxonomy.md
