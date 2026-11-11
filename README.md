# 论文阅读知识库 · AI Skill 包

一套基于 **Obsidian + Claude Code** 的论文阅读与知识管理管线。把论文从"读过"变成"能调用"：

```
PDF → 与 AI 讨论 → 结构化笔记 → 标签图谱 → 问题/机制库 → 研究 Gap
```

这不是文献管理器。它管理的是**你对论文的理解，以及理解之间长出来的连接**。

---

## 核心设计

| 设计 | 解决什么 |
|------|---------|
| **PDF 拖入即讨论** | 先多轮提问把论文吃透，再让 AI 整理，而不是直接生成一篇冷冰冰的摘要 |
| **domain / method 双层标签** | `domain/` 是"哪道题"，`method/` 是"用什么解"，交叉形成二维知识图谱 |
| **Problem → Mechanism → Operator** | 把论文拆成"失败模式 / 底层机制 / 实现算子"，让跨领域迁移有路可走 |
| **自动交叉链接 + 健康检查** | 共享标签的笔记自动关联；定期发现孤立笔记、失效链接、标签遗漏 |
| **笔记模板强制写"我的借鉴"** | 重点不是论文说了什么，而是**它改变了你什么** |

---

## 快速开始

### 1. 安装依赖

- [Obsidian](https://obsidian.md/)（知识管理前端）
- [Claude Code](https://claude.com/claude-code)（AI 管线）
- 可选但强烈推荐：[OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf)（PDF → 结构化 Markdown，见 `_meta/opendataloader-pdf 配置指南.md`）

### 2. 打开仓库

```bash
git clone https://github.com/<your-name>/paper-reading-skill.git
cd paper-reading-skill
```

在 Obsidian 中 **Open folder as vault** 选择这个目录；在 Claude Code 中也在同一目录运行 `claude`。

### 3. 换成你自己的研究领域

- 编辑 `CLAUDE.md` 顶部的 `## 👤 User Profile`，填入你的方向和项目
- 编辑 `_meta/taxonomy.md`，把示例标签换成你领域的术语
- （可选）编辑 `_library/` 下的模板，删掉示例、留下骨架

### 4. 开始读第一篇

```text
1. 把 PDF 放进 _staging/
2. 在 Claude Code 里提问、讨论（可以多轮）
3. 说"可以了" → AI 自动：
   - 推荐 domain/method 标签，你来选
   - 生成结构化笔记到 _staging/notes/
   - 把 PDF 归档到 _staging/archived/
   - 更新 _meta/index.md 和 _meta/ingest-log.md
```

---

## Skills 一览

`.claude/skills/` 下每个目录都是一个可独立触发/修改的 Skill：

| Skill | 触发词 | 作用 |
|-------|--------|------|
| `paper-ingest` | "可以了" / "整理笔记" / "ingest" | 把讨论结果沉淀成标准笔记，推荐标签、维护索引 |
| `paper-anatomy` | "扒皮" / "解剖" / "拆深一点" | 对论文做深度解剖：问题定位 + 架构组件 IO + 设计质询 |
| `paper-crosslink` | "链接笔记" / "找关联" | 扫描共享标签，提议 `related_notes` 链接 |
| `note-library` | "library" | 把论文挂进问题/机制/算子/思想/类别/数据六张图谱 |
| `critique` | 质疑论文设计时 | 四层解构：代价、前提、适用边界、演化路径 |
| `tutor` | "金牌导师" | 用大白话分段讲解论文 |
| `wiki-lint` | "lint" / "健康检查" | 检查孤立笔记、失效链接、标签不同步 |
| `wiki-query` | 跨论文提问 | 按标签分层查询，控制 token 消耗 |

> `paper-crosslink` / `wiki-lint` / `wiki-query` 是早期版本，功能与 `paper-ingest`、`note-library` 有部分重叠，可按需保留或删除。

---

## 目录结构

```
.
├── CLAUDE.md                 # 管线主控指令：定义 AI 的行为规范
├── .claude/skills/           # Skill 规格（Claude Code 自动加载）
├── _meta/
│   ├── taxonomy.md           # 标签体系（domain + method）
│   ├── index.md              # 笔记索引（ingest 自动维护）
│   ├── ingest-log.md         # 摄取日志
│   ├── preprocess-pdf.ps1    # Windows 预处理脚本
│   ├── preprocess-pdf.sh     # macOS / Linux 预处理脚本
│   └── *.py                  # 表格/公式/校验等辅助脚本
├── _library/                 # Problem 驱动的知识图谱（骨架模板）
│   ├── 00-quick-query.md     # ⭐ 唯一入口：问题 → 机制 → 算子速查
│   ├── 1-problem-atlas.md    # 问题图谱：按失败模式分类
│   ├── 2-mechanism-atlas.md  # 机制图谱：按算法积木分类
│   ├── 3-operator-cookbook.md# 算子手册：机制的具体实现
│   ├── 4-thought-atlas.md    # 思想图谱：高维哲学范式
│   ├── 5-category-manifest.md# 类别清单：创新的本质类型
│   └── 6-data-methodology.md # 数据方法论
├── _staging/
│   ├── notes/                # ingest 产出的论文笔记（默认不入库）
│   ├── archived/             # 已处理 PDF（默认不入库）
│   └── parsed/               # PDF 预处理结果（默认不入库）
├── _foundation/              # 基础论文（如 Diffusion / Transformer 原始工作）
├── 论文阅读+思路拓展/         # 你自己写的改进思路笔记（默认不入库）
└── examples/example-note.md  # 一篇示例笔记，展示模板长什么样
```

---

## 两个工作流

### A. 读论文（paper-ingest）

```text
_staging/ 丢 PDF
      ↓
AI 预处理 + 阅读，等你提问
      ↓
多轮讨论（这段时间理解才真正发生）
      ↓
"可以了" → 推荐标签 → 你选择
      ↓
生成笔记（把讨论中的洞察写进"我的借鉴"）
      ↓
继承关系扫描（纵向 / 横向 / 范式演进）
      ↓
归档 PDF + 更新 index / ingest-log
```

### B. 建图谱（note-library）

```text
已 ingest 的论文
      ↓
问题挂接 → 1-problem-atlas
机制提取 → 2-mechanism-atlas（2-3 个）
算子补充 → 3-operator-cookbook（只有新算子才写）
思想提取 → 4-thought-atlas（只有新母思想才写）
分类提取 → 5-category-manifest
数据方法 → 6-data-methodology（有条件才写）
```

> 维护铁律：**只在有新增时才更新对应库**。降低维护摩擦 = 提高打开率。

---

## 如何定制

| 想改什么 | 改哪里 |
|---------|--------|
| 研究方向 / 讨论风格 | `CLAUDE.md` → `User Profile` |
| 领域标签、方法标签 | `_meta/taxonomy.md` |
| 笔记模板 | `CLAUDE.md` → `### Note Template` |
| 某个 Skill 的行为 | `.claude/skills/<name>/SKILL.md` |
| 知识图谱分类 | `_library/0*.md` |
| PDF 预处理参数 | `_meta/preprocess-pdf.*` |

所有 Skill 都是纯 Markdown，没有隐藏逻辑，直接改就行。

---

## 常见问题

**为什么不用 Zotero / Papers / Mendeley？**
那些是文献管理工具，解决"PDF 放哪"。这套管线是**知识内化工具**，解决"读完以后怎么用"。管理不是目的，理解并连接才是。

**为什么 AI 讨论在前、ingest 在后？**
讨论过程中你的理解已经深化；ingest 时 AI 能把讨论中的判断一起写进笔记。笔记因此不是摘要，而是有你的思考痕迹。

**为什么笔记必须写"我的借鉴"？**
笔记的核心不是"这篇论文说了什么"，而是"它改变了你什么"。模板要求写具体迁移路径，禁止"值得学习"这类空话。

**支持哪些领域？**
骨架默认面向 CV / ML / 具身智能，但标签体系、问题图谱、机制图谱全部可替换。换成 NLP、系统、HCI 同样适用。

---

## License

建议代码/脚本使用 MIT，文档与模板使用 CC BY 4.0。上传前请自行添加 `LICENSE` 文件并确认。

## 贡献

欢迎开 Issue 或 PR：新增 Skill、补充机制节点、修正模板、改进预处理脚本都可以。
