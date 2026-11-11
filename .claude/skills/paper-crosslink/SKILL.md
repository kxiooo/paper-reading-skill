---
name: paper-crosslink
description: "扫描所有笔记的 frontmatter 标签，发现共享标签的笔记对，向用户提议链接，经确认后写入 related_notes。"
---

# Paper Crosslink

> 为共享标签的笔记建议关联链接。不自动写入，不挖深度链接链。

## 触发

- 用户说"链接笔记"、"cross-link"、"关联一下"、"找关联"
- 每次 paper-ingest 完成后自动问"要检查关联笔记吗？"

## 流程

### Step 1: 扫描标签

- 用 `Grep` 搜索 `_staging/notes/` 和 `论文阅读+思路拓展/` 下所有 `.md` 文件的 frontmatter
- **排除 `每日论文推送/` 目录下的文件**（临时推送笔记，不参与知识图谱）
- 提取每篇笔记的 `tags:` 字段，筛选出 `domain/` 和 `method/` 前缀的条目
- 构建 `note → tags` 映射表

### Step 2: 发现并自动应用链接

对每一对笔记 `(A, B)`：

| 规则 | 行动 |
|------|------|
| 共享 ≥1 个 `domain/` 或 `method/` 前缀的 tag | **自动双向加入 `related_notes`** |
| 无共享 tag | 跳过 |

**自动执行，不需要用户确认。** 只做一件事：确保共享 tag 的笔记互相可发现。

### Step 3: 去重与清理

写入前：
- 检查 `related_notes` 是否已存在该链接。不重复添加。
- **检查并移除所有空条目**（`- []`、`- ""` 等），确保写入后 `related_notes` 无残留空值——空条目会破坏 Dataview 查询。
- **强制使用正确格式** `- "[[path/to/note]]"`，禁止写入 `- [["path/to/note"]]` 格式——后者是 YAML 嵌套列表而非 wikilink 字符串，Obsidian 图谱不认。

写入时：
- **使用 Edit 工具做锚定插入**，在 `related_notes:` 列表末尾追加新条目。**不要用 Write 重写整个文件**——那会覆盖用户在 `我的借鉴` 等区域手写的内容。
- 锚点：选择 `related_notes:` 下方最后一个已有条目行，替换为该行 + 新条目行。

---

## 不做的事情

- ❌ 不在正文里嵌 `[[wikilinks]]`——只在 frontmatter related_notes
- ❌ 不为"共享一个宽泛标签"的笔记建链接（如都标了 `Diffusion Model` 但做的事完全无关）
- ❌ 不追深度链接链（A→B→C→D）
- ❌ 不扫描 vault 以外的目录
- ❌ 不碰非论文笔记（如纯思路笔记，除非用户要求）
