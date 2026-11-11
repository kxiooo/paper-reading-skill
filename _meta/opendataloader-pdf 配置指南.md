---
tags:
  - meta/tool
created: YYYY-MM-DD
---

# OpenDataLoader PDF 配置指南

## 为什么用

双栏、公式密集、表格多的学术论文直接给 LLM 读 PDF 会：阅读顺序乱、公式靠猜、表格读歪。用 OpenDataLoader 预处理成 Markdown 并保留原图后：

- 文字 / 公式 / 表格 → 结构化文本，便宜且准确
- 架构图 / 结果图 → 原图给模型看，不丢视觉信息

## 安装

### 1. Java 17+

```bash
java -version
```

没有的话安装 OpenJDK 17（或更新版本），并确保 `JAVA_HOME` 指向 JDK 根目录。

### 2. Python 3.10+

```bash
python --version
```

### 3. OpenDataLoader PDF

```bash
pip install opendataloader-pdf
```

安装后可用 `opendataloader-pdf --help` 验证。

### 4. 让脚本找到它们

`_meta/preprocess-pdf.ps1` / `.sh` 会按以下顺序自动探测：

| 组件 | 环境变量 | 回退 |
|------|---------|------|
| Java | `JAVA_BIN` | PATH 中的 `java` → `JAVA_HOME/bin/java` |
| Python | `PYTHON_BIN` | PATH 中的 `python` / `python3` |
| OpenDataLoader JAR | `OPENDATALOADER_JAR` | 通过 Python 包位置自动定位 |

一般装完就能直接用，不需要改脚本。

## 使用方法

### 基本用法（本地模式）

```bash
# Windows
.\_meta\preprocess-pdf.ps1 _staging\你的论文.pdf

# macOS / Linux
bash _meta/preprocess-pdf.sh _staging/你的论文.pdf
```

输出：

```
_staging/parsed/<论文名>/
  ├── <论文名>.md        # 结构化 Markdown（文本 + LaTeX + 表格）
  └── images/            # 提取的原图
```

### 混合模式（表格 / 公式更准，但需先启动后端）

```bash
# 终端 1：启动 AI 后端
opendataloader-pdf-hybrid --port 5002

# 终端 2：预处理
bash _meta/preprocess-pdf.sh _staging/你的论文.pdf --hybrid
```

### Docling 表格增强（可选）

```bash
pip install docling
bash _meta/preprocess-pdf.sh _staging/你的论文.pdf --merge-tables
```

### Claude Code 讨论时自动调用

当你在对话中引用 `_staging/` 下的 PDF 时，Claude 会按 `CLAUDE.md` 的协议自动：

1. 检查 `_staging/parsed/<论文名>/` 是否已存在
2. 不存在则运行 `preprocess-pdf` 脚本
3. 读取生成的 Markdown + 图片目录

## 输出格式说明

| 元素 | 处理方式 | 精度 |
|------|---------|------|
| 文本 + 阅读顺序 | XY-Cut++ 算法 → Markdown | ✅ 确定性正确 |
| 表格 | 结构化提取 → Markdown table（本地模式为扁平文本） | ✅ 数据正确，结构视版本而定 |
| 公式 | → LaTeX 源码 | ✅ 语义精确 |
| 图片 | 原图输出到 `images/`，或内嵌 base64（视版本） | ✅ 不丢失信息 |
| 标题层级 | 自动 H1/H2/H3 | ✅ |
| 多栏布局 | 自动拆分还原 | ✅ |

## 故障排查

- `java: command not found` → 安装 JDK 17+，检查 `JAVA_HOME` 和 PATH
- `opendataloader-pdf: command not found` → `pip install opendataloader-pdf`，确认 pip 的 bin 目录在 PATH 中
- 找不到 JAR → 手动设置 `OPENDATALOADER_JAR` 指向 `opendataloader-pdf-cli.jar`
- 大 PDF 内存不足 → 分页处理（具体参数以 `opendataloader-pdf --help` 为准）
- 混合模式连接失败 → 确认 `opendataloader-pdf-hybrid` 后端在运行
- 中文路径报错 → 脚本已尽量使用纯 ASCII 临时目录；若仍失败，把 PDF 移到英文路径再试
