#!/bin/bash
# ============================================================
# OpenDataLoader PDF 预处理脚本
# 用法: bash _meta/preprocess-pdf.sh <pdf-path> [--hybrid] [--merge-tables]
# 输出: _staging/parsed/<name>/<name>.md + images/
#
# 默认使用本地模式（确定性，表格扁平但数据正确）
# --hybrid 切换混合模式（表格结构化，但偶有数据错位，需手动启动后端）
#
# 依赖：Java 17+、Python 3.10+、`pip install opendataloader-pdf`
# 如果 java / python / opendataloader-pdf 不在 PATH 中，取消下面注释并修改：
# export JAVA_HOME="/path/to/jdk-17"
# export PATH="$JAVA_HOME/bin:$PATH"
# export PYTHON_BIN="/path/to/python3"
# ============================================================
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
HYBRID_PORT=5002

# --- 参数 ---
show_usage() {
    echo "用法: bash _meta/preprocess-pdf.sh <pdf-path> [--hybrid] [--merge-tables]"
    echo "  <pdf-path>      PDF 文件路径"
    echo "  --hybrid        混合模式（表格更结构化，但可能有 AI 错位；需先启动后端）"
    echo "  --merge-tables  Docling 表格增强（将扁平表格转为 pipe table；复杂表格可能错乱，按需开启）"
    exit 1
}
[ $# -lt 1 ] && show_usage

PDF_PATH="$1"; shift
USE_HYBRID=false
USE_MERGE_TABLES=false

for arg in "$@"; do
    case "$arg" in
        --hybrid)        USE_HYBRID=true ;;
        --merge-tables)  USE_MERGE_TABLES=true ;;
        *)               show_usage ;;
    esac
done

# --- 依赖检查 ---
if ! command -v opendataloader-pdf &>/dev/null; then
    echo "错误: 找不到 opendataloader-pdf。请先安装："
    echo "  pip install opendataloader-pdf"
    exit 1
fi
if ! command -v java &>/dev/null; then
    echo "错误: 找不到 java。请安装 Java 17+ 并加入 PATH。"
    exit 1
fi

# --- 文件名处理 ---
PDF_NAME=$(basename "$PDF_PATH" .pdf)
SLUG=$(echo "$PDF_NAME" | sed 's/[^a-zA-Z0-9_\-]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VAULT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="$VAULT_ROOT/_staging/parsed/$SLUG"

echo "============================================"
echo "OpenDataLoader PDF 预处理"
echo "============================================"
echo "PDF:     $PDF_PATH"
echo "输出:    $OUTPUT_DIR/"
echo "============================================"

mkdir -p "$OUTPUT_DIR/images"

# --- 混合模式：需要手动启动的后端 ---
if [ "$USE_HYBRID" = true ]; then
    if ! curl -s "http://localhost:$HYBRID_PORT/health" >/dev/null 2>&1; then
        echo "错误: 混合后端未运行。请先在另一个终端执行："
        echo "  opendataloader-pdf-hybrid --port $HYBRID_PORT"
        exit 1
    fi
    echo "后端:    ✅ 已连接 (port $HYBRID_PORT)"
    echo "模式:    混合 (docling-fast) — 表格结构化，注意检查数据正确性"
    CMD=(opendataloader-pdf
        "$PDF_PATH"
        -o "$OUTPUT_DIR"
        -f markdown
        --image-output external
        --image-format png
        --image-dir "$OUTPUT_DIR/images"
        --hybrid docling-fast --hybrid-url "http://localhost:$HYBRID_PORT"
        -q
    )
else
    echo "模式:    本地 — 确定性，表格为扁平文本（数据正确，列映射靠 LLM 推断）"
    CMD=(opendataloader-pdf
        "$PDF_PATH"
        -o "$OUTPUT_DIR"
        -f markdown
        --image-output external
        --image-format png
        --image-dir "$OUTPUT_DIR/images"
        -q
    )
fi

echo "--------------------------------------------"

# --- 执行 ---
"${CMD[@]}"

# --- 检查输出 ---
echo ""
echo "完成! 输出文件:"

MD_FILE="$OUTPUT_DIR/$SLUG.md"
if [ -f "$MD_FILE" ]; then
    echo "  📄 $MD_FILE"
else
    MD_FILE=$(ls "$OUTPUT_DIR"/*.md 2>/dev/null | head -1)
    [ -n "$MD_FILE" ] && echo "  📄 $MD_FILE" || { echo "  ❌ Markdown 未生成"; exit 1; }
fi

IMG_COUNT=$(ls "$OUTPUT_DIR/images/" 2>/dev/null | wc -l | tr -d ' ')
echo "  🖼️  $OUTPUT_DIR/images/ ($IMG_COUNT 张图)"
echo ""

# --- Python 可用性 ---
if ! command -v "$PYTHON_BIN" &>/dev/null; then
    echo "提示: 找不到 $PYTHON_BIN，跳过表格 / 公式 / 验证增强。"
    echo "  如需启用，设置 PYTHON_BIN 或安装 Python 3.10+。"
    exit 0
fi

# --- 表格增强: Docling pipe-table 合并 (可选) ---
if [ "$USE_MERGE_TABLES" = true ]; then
    MERGE_SCRIPT="$SCRIPT_DIR/merge-docling-tables.py"
    if [ -f "$MERGE_SCRIPT" ]; then
        echo "--------------------------------------------"
        echo "Docling 表格增强..."

        "$PYTHON_BIN" "$MERGE_SCRIPT" "$PDF_PATH" "$MD_FILE" 2>&1 | sed 's/^/  /'
        echo "  表格已转换为结构化 pipe table 格式。"
    else
        echo "  提示: merge-docling-tables.py 未找到，跳过表格增强。"
    fi
fi

# --- 公式增强: Unicode math → LaTeX (rule-based, no API needed) ---
LATEX_SCRIPT="$SCRIPT_DIR/latex-formulas.py"
if [ -f "$LATEX_SCRIPT" ]; then
    echo "--------------------------------------------"
    echo "LaTeX 公式增强 (规则引擎)..."

    "$PYTHON_BIN" "$LATEX_SCRIPT" "$MD_FILE" 2>&1 | sed 's/^/  /'
    echo "  公式已转换为标准 LaTeX 格式。"
fi

# --- 完整性验证 ---
echo "--------------------------------------------"
echo "完整性验证..."

# Get PDF page count (macOS mdls / Linux pdfinfo)
PDF_PAGES=""
if command -v mdls &>/dev/null; then
    PDF_PAGES=$(mdls -name kMDItemNumberOfPages -raw "$PDF_PATH" 2>/dev/null)
elif command -v pdfinfo &>/dev/null; then
    PDF_PAGES=$(pdfinfo "$PDF_PATH" 2>/dev/null | awk '/Pages:/ {print $2}')
fi
if [ -n "$PDF_PAGES" ]; then
    PAGE_ARG="--pdf-pages $PDF_PAGES"
else
    PAGE_ARG=""
fi

VALIDATE_SCRIPT="$SCRIPT_DIR/validate-preprocess.py"
if [ -f "$VALIDATE_SCRIPT" ]; then
    if ! "$PYTHON_BIN" "$VALIDATE_SCRIPT" "$MD_FILE" $PAGE_ARG 2>&1 | sed 's/^/  /'; then
        echo ""
        echo "❌ 完整性验证失败 — 预处理结果可能不完整，请检查 PDF 或手动处理。"
        exit 1
    fi
else
    echo "  提示: validate-preprocess.py 未找到，跳过验证。"
fi
