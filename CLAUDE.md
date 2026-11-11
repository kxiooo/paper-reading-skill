# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## This is an Obsidian Vault, Not a Code Repository

This vault is a **paper reading knowledge base** with a managed ingest pipeline. There is no build/test/lint. The "code" here is Markdown notes and SKILL specifications.

## 👤 User Profile

> 改成你自己的信息。这一段只影响 AI 讨论时的领域知识倾向，不影响管线运行。

- **Identity**: {{你的名字 / 身份}}
- **Research focus**: {{你的研究方向，例如：3D 人体动作生成与编辑}}
- **Active projects**: {{当前在做的项目}}
- **Preferred language**: {{中文 / English}}

## Vault Structure

```
.
├── CLAUDE.md                 ← 本文件：管线主控指令
├── .claude/skills/           ← Skill 规格，Claude Code 自动加载
├── _staging/
│   ├── archived/             ← 已处理 PDF 归档（按 domain 分文件夹）
│   ├── notes/                ← AI 生成的论文笔记（按 domain 分文件夹）
│   └── parsed/               ← OpenDataLoader 预处理结果（自动生成）
├── _foundation/
│   ├── notes/                ← 基础论文笔记（Diffusion、Transformer 等）
│   └── archived/             ← 基础论文 PDF
├── _meta/
│   ├── index.md              ← 全部笔记索引，按 domain 分类，ingest 时自动更新
│   ├── taxonomy.md           ← 受控标签表（domain + method）
│   ├── ingest-log.md         ← 摄取日志
│   ├── preprocess-pdf.sh     ← macOS / Linux 预处理脚本
│   ├── preprocess-pdf.ps1    ← Windows PowerShell 预处理脚本
│   ├── opendataloader-pdf 配置指南.md
│   └── *.py                  ← 表格 / 公式 / 校验辅助脚本
├── _library/                 ← Problem 驱动的知识图谱（永久资产，持续生长）
│   ├── 00-quick-query.md     ← ⭐ 唯一入口：问题 → 失败 → 机制 → 算子速查总表
│   ├── 1-problem-atlas.md    ← 问题图谱：按失败模式分类
│   ├── 2-mechanism-atlas.md  ← 机制图谱：按算法底层积木分类
│   ├── 3-operator-cookbook.md← 算子速查：机制的具体实现
│   ├── 4-thought-atlas.md    ← 思想图谱：高维哲学范式
│   ├── 5-category-manifest.md← 类别清单：按创新本质分类
│   └── 6-data-methodology.md ← 数据方法论
├── 论文阅读+思路拓展/         ← 你自己写的改进思路笔记（不是论文笔记）
└── examples/                 ← 示例笔记，仅作格式参考
```

## Core Workflow: Paper Ingest

1. User drops a PDF into `_staging/`. **DO NOT auto-ingest.** Preprocess it (see [PDF Preprocessing](#pdf-preprocessing-auto)), read the generated `.md`, and discuss with the user. Be ready for ingest when the user gives the signal.
2. User asks questions and discusses. Multi-turn is fine.
3. When the user says "可以了" / "整理笔记" / "ingest" / "就这样吧", start ingest:
   - Recommend 3-5 domain tags and 3-5 method tags from `_meta/taxonomy.md`. **Prioritize existing tags.** Only propose `[新增]` if no existing tag fits. If the paper does the same task as a previously ingested note, they MUST share a tag.
   - User selects 2-3 domain + 1-2 method.
   - Generate the note in `_staging/notes/<domain-slug>/<Title>.md` using the standard template below.
   - **评价提取**：如果此前对话中用户对论文表达了主观评价（好 / 坏 / 一般），凝练 1-2 句写入 `## 我的评价`；如果全程只讨论技术内容、没有评价，整节省略。
   - **Inheritance check (MANDATORY, three scans — never skip the scans themselves)**:
     1. **纵向·直接继承**：分两层。——**A 层（论文自述）**：论文是否在 Introduction / Related Work 中明确声明 build on / 继承 / 改进自某些前序工作？若有，无论前序工作是否在 vault 中，都要写入 `## 继承关系`，用 ASCII 图示标注继承链和每次推进改变了什么。这是论文自身的学术脉络，必须记录。——**B 层（vault 对照）**：Grep 参考文献作者名、方法名、数据集名在 `_staging/notes/` 中，找到 vault 已有笔记就用 wikilink 链接。A/B 两层可同时写入，互补不互斥。两层都无 → 记录"无"。
     2. **横向·同期并行**：vault 中是否有同 venue + 同 task 的笔记？Grep venue 名（如 "CVPR 2026"、"ICLR 2025"）在 `_staging/notes/` 各子文件夹中（venue 通常出现在笔记正文作者行 `<Authors>, <Venue Year>`）。找到 → 对比范式差异并写入；没找到 → 记录"无"。
     3. **宏观·范式演进**：分两层。——**A 层（论文自述）**：论文是否在 Introduction 中将自己定位为某条技术路线的自然推进（如 "previous methods do X, we extend to Y"、"从全局到局部"、"从 2D 到 3D"）？若有，无论前序工作是否在 vault 中，都要写入，说明推进了什么、改变了什么。——**B 层（vault 对照）**：检查同 domain tag 下的笔记，若 vault 中有可锚定的前序工作，用 wikilink 链接。A/B 两层互补。两层都无 → 记录"无"。
     三步全"无"才跳过 `## 继承关系` 整节。任何一步不确定 → 问用户。禁止不经扫描直接下"无继承关系"的结论。
   - **Tag sufficiency check**: verify the new note shares at least one domain or method tag with existing notes on the same task. If not, add the missing tag (for Obsidian graph connectivity).
   - Write tags in native Obsidian format: `domain/Xxx` and `method/Xxx` in the `tags:` field.
   - Curate `related_notes`: pick ≤3 most relevant existing notes. Only add links from the new note to existing notes — do NOT modify existing notes' `related_notes`.
   - Rename the PDF to the paper title, move it to `_staging/archived/<domain-slug>/`.
   - Delete preprocessed Markdown and images from `_staging/parsed/<paper-slug>/`.
   - Auto-update: `_meta/index.md`, `_meta/taxonomy.md` (if new tags), `_meta/ingest-log.md`.
   - Graph connectivity: shared tags handle this in Obsidian automatically. No wikilink sections in the body.

### Note Template

```yaml
---
tags:
  - domain/Xxx
  - method/Xxx
source_pdf: "[[_staging/archived/<domain-slug>/<Title>.pdf]]"
related_notes:
  - "[[most-relevant-note-1]]"
  - "[[most-relevant-note-2]]"
created: YYYY-MM-DD
---

# <Title>

<Authors>, <Venue Year>

## 一句话
...

## 核心方法
...

## 创新点
...

## 解决的问题
<这篇论文解决的是哪类失败模式（六问 1-3）：本质问题 / 为何已有方法失败 / 属于 [[1-problem-atlas]] 哪个问题节点>

## 我的借鉴
...

## 我的评价 👈 条件性添加
...

## 继承关系 👈 条件性添加。不确定时问用户
...
```

Note sections:
- **一句话**: 一句话概括论文做了什么、最大的贡献是什么
- **核心方法**: 技术方案要点，用 bullet points
- **创新点**: 本文独有的贡献，编号列出
- **解决的问题**: 论文解决的失败模式 + 属于 `[[1-problem-atlas]]` 哪个问题节点
- **我的借鉴**: 哪些思路 / 设计 / 范式可以迁移到自己的工作中
- **我的评价**: 条件性添加，仅当对话中用户表达了对论文的主观评价时写入，不超过 2 句话。没有讨论到好坏则整节省略
- **继承关系**: 条件性添加，规范见下节

### `## 继承关系` 写作规范

**⚠️ 核心原则：有才写，没有就整节跳过。不确定就问用户——不要替用户决定一个脉络关系是否值得记录。**

三种有效情况：

1. **直接继承**：本文直接 build on 的前序工作。若前序工作在 vault 中有笔记，用 wikilink 链接。无论是否在 vault 中，只要论文在 Introduction / Related Work 中明确声明了继承关系（基于某架构、使用某数据 / 代码、延续某条技术路线），都要用 ASCII 图示标注继承链和每次推进改变了什么。写具体技术点（"使用了 X 的数据"），避免"受到启发"这类模糊表述。
2. **同期并行**：与某篇已有笔记同期发表，解决同类问题但方向不同，可做系统性对比。
3. **范式演进**：本文代表某个方向的自然推进（如 全局生成→部位级生成、2D→3D、单帧→时序、回归→生成）。若 vault 中有可锚定的前序工作，用 wikilink 链接。无论是否在 vault 中，只要论文在 Introduction 中明确将自己定位为某条路线的推进，都要写入。写法上说明**推进了什么、改变了什么**。

**反例——以下不算"继承关系"，不要写**：
- 只是同一个大领域但没有任何演进关系 ✗
- "都用 Transformer"这种泛泛的共同点 ✗

**不确定时**：如果觉得可能有范式演进关系但吃不准是否牵强，在 ingest 时主动问用户，由用户决定是否写入。

示例（直接继承，精确到技术组件）：
```
Method A (2023) → Method B (2025) → Method C (2025)
  骨架+解码器        修数据/表示        范式转换+交互
```

示例（范式演进，不精确到技术组件）：
```
全局生成范式（Baseline-1 / Baseline-2 / Baseline-3）
  └→ This Paper (2026)
       控制维度扩展：全局描述 → 部位 / 动作 / 序列三层分级控制
```

无继承关系则**整个 `## 继承关系` 节省略**，不要留空标题，不要在模板里预填此节。

No `## 标签关联` or auto-generated wikilink sections in the body.

### related_notes Selection Criteria

Pick ≤3 notes, ordered by relevance:

1. **Shares both domain AND method tags** — strongest signal, same problem + same approach
2. **Same research task** — e.g., both do multi-view pose, both do image editing
3. **Direct methodological lineage** — the new paper builds on or is directly compared to

Links are unidirectional: the new note points to existing notes. Existing notes are not modified. Shared tags provide bidirectional graph connectivity automatically in Obsidian.

## library Trigger: Problem 驱动的知识图谱更新

当用户说 **"library"**，详细指令见 `.claude/skills/note-library/SKILL.md`。

> 入口是 `_library/00-quick-query.md`。

简要流程（Problem → Mechanism → Operator → Paper → Gap）：
1. 确保论文已被 ingest（笔记在 `_staging/notes/` 或 `_foundation/notes/` 中）
2. 问题挂接 → 更新 `_library/1-problem-atlas.md`（必做，先判断失败模式）
3. 机制提取 → 更新 `_library/2-mechanism-atlas.md`（2-3 个机制）
4. 算子补充 → 更新 `_library/3-operator-cookbook.md`（只有新算子才更新）
5. 思想提取 → 更新 `_library/4-thought-atlas.md`（只有新母思想才更新）
6. 分类提取 → 更新 `_library/5-category-manifest.md`
7. 数据方法论 → 更新 `_library/6-data-methodology.md`（有条件才做）

> **维护铁律**：只在有新增时才更新对应库。降低维护摩擦 = 提高打开率。
> **讨论时联动**：用户问研究问题时，先查 `00-quick-query.md` 总表组织回答——不需要用户说"library"。

## PDF Preprocessing (Auto)

**When the user references a PDF for discussion (in `_staging/`, `_staging/archived/`, or elsewhere in the vault), ALWAYS preprocess it with OpenDataLoader PDF first, then read the resulting Markdown.**

Rationale: double-column academic papers are formula-heavy and table-dense. Direct PDF → LLM causes column confusion, formula guesswork, and table misalignment. OpenDataLoader extracts structured Markdown (text + LaTeX + reading order) and original images, then both are fed to the LLM — text tokens are cheap and accurate, images preserve visual evidence.

### Environment (example — adapt to your machine)

`_meta/preprocess-pdf.ps1` 顶部有一个「Tool paths」配置块；脚本会优先读取环境变量，读不到再尝试从 PATH 自动探测：

| 组件 | 环境变量 | 说明 |
|------|---------|------|
| Java | `JAVA_HOME` | 需要 Java 17+ |
| Python | `PYTHON_BIN` | 用于表格 / 公式增强脚本 |
| OpenDataLoader JAR | `OPENDATALOADER_JAR` | 或让脚本在 Python site-packages 中查找 |

> ⚠ OpenDataLoader 不同版本参数不同。脚本按常见 v1.x 行为编写（图片内嵌 / 输出 images 目录）；若你的版本不支持某参数，按报错删掉对应行即可。

### Auto-preprocessing Protocol

**⚠️ NEVER use `Read` on the raw PDF.** Direct PDF reading is unreliable for double-column papers. Always: check cache → run preprocessing if missing → read the generated `.md`.

1. **Check if already preprocessed**: the script derives `<paper-slug>` from the PDF filename by replacing non-alphanumeric characters (except `_` `-`) with `-` (e.g., `2511.20886v2.pdf` → `2511-20886v2/`). Prefer a broad glob `_staging/parsed/*/<paper-base>*`, or list `_staging/parsed/`. If the `.md` exists and is newer than the PDF, skip preprocessing.
2. **If not preprocessed**: run the script.
   ```
   .\_meta\preprocess-pdf.ps1 <pdf-path>          # Windows
   bash _meta/preprocess-pdf.sh <pdf-path>        # macOS / Linux
   ```
   - Use **local mode** (deterministic, fast, clean text). Tables come out as flat space-separated text — data is correct but unstructured.
   - **When the user asks about specific table data**, cross-reference the flat text (LLM infers structure) AND the original PDF for visual verification.
   - `--merge-tables` / `--MergeTables` is optional and requires `pip install docling`.
3. **Strip supplementary material (NOT appendix)**: locate where genuine supplementary material starts. Strip only sections explicitly marked "Supplementary Material" / "Supplemental Material" or clearly separate supplements after the paper ends. **Do NOT strip "Appendix"** — appendices contain implementation details, training configs, ablations, dataset statistics, and are part of the paper proper.
4. **Read the output**: `_staging/parsed/<paper-slug>/<paper-slug>.md` (main body only, after step 3).
5. **Read key images**: depending on version, images are either separate files under `images/` or embedded as base64 in the Markdown. Read the ones the user asks about.
6. **Discuss**: reference the Markdown text (accurate formulas, tables, reading order) and images (visual evidence) together.

### Output Structure

```
_staging/parsed/<paper-slug>/
  ├── <paper-name>.md        ← Structured Markdown (text, LaTeX, tables, images)
  ├── images/                ← Extracted images (if supported)
  ├── opendataloader.log
  └── opendataloader.err
```

## Tag Rules

- **Single source of truth.** Tags live only in the Obsidian-native `tags:` frontmatter field, using `domain/` and `method/` prefixes. There are no separate `domain_tags` / `method_tags` fields.
- **Prefixed format.** `domain/Human-Mesh-Recovery`, `method/Feed-Forward-Reconstruction`. These appear in the Obsidian graph and power Dataview queries.
- **Hyphens not spaces in YAML tags.** Obsidian treats spaces as tag separators in the `tags:` field. Always use `domain/Example-Domain`, not `domain/Example Domain`. The taxonomy at `_meta/taxonomy.md` keeps human-readable spaces, but frontmatter tags must use hyphens.
- **Prefer reuse.** Existing taxonomy tags first. Only create new ones when necessary.
- **Tag sufficiency check.** After tagging, verify the new note can link to existing notes on the same task via shared tags. If not, add the missing shared tag.
- Taxonomy at `_meta/taxonomy.md`. Keep it updated.

## Key Policies

- **Never delete user notes without asking.**
- **Renaming requires link-repair.** Before renaming any note file, PDF, or tag, identify all files that reference the old name (wikilinks, `source_pdf`, `related_notes`, `_meta/index.md`, frontmatter tags) and update them in the same operation. Never rename without fixing all references.
- **Index and crosslink are auto-maintained.** Every ingest updates both.
- **`论文阅读+思路拓展/` is for the user's own thinking notes**, not paper summaries. Only write there when the user explicitly discusses improvement ideas.
- **思路笔记必须关联来源论文。** 先 ingest 论文 → 再写思路笔记 → frontmatter 的 `related_notes` 必须包含所借鉴的论文笔记（`[[_staging/notes/{子文件夹}/PaperName]]`）。如果思路笔记由讨论中的论文直接引发，该论文就是第一关联对象。
- **`每日论文推送/`（如果有）is excluded** from graph, index, and crosslink.
- **相关笔记存于 frontmatter 的 `related_notes` 字段，≤3 条，人工筛选。共享 tag 在 Obsidian 图谱中自动形成连接，不需要在正文生成 wikilink 区域。**
- **No empty frontmatter entries.** Crosslink and ingest must never produce empty `[]` in list fields like `related_notes` — these break Dataview queries.
- **Prefer targeted edits over full rewrites.** When modifying existing notes (e.g., fixing frontmatter typos, updating `source_pdf`), use Edit for surgical changes anchored to existing content. Never rewrite entire notes — this would overwrite user-written content in `我的借鉴` and other sections. Conversely, never modify existing notes' `related_notes` during ingest.
- **Paper-first linking.** When writing a note that references a paper, link to the **note file** (`[[_staging/notes/{子文件夹}/PaperName]]`), never directly to the PDF. If the paper hasn't been ingested yet, ingest it first.
- **Inline wikilinks for cross-references.** When a note's body text mentions or compares another vault note, always include an inline wikilink at the first mention. This includes comparisons with other methods, references to alternative schemes, and baseline method lists.
