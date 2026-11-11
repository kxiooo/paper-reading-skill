#!/bin/bash
# ============================================================
# 自动预处理：检测 _staging/ 中未处理的 PDF，自动运行完整管线
# 由 launchd 定时触发（每 60s）或手动调用
# 用法: bash _meta/auto-preprocess.sh
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VAULT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STAGING_DIR="$VAULT_ROOT/_staging"
PIPELINE_SCRIPT="$SCRIPT_DIR/preprocess-pdf.sh"
LOCK_FILE="/tmp/auto-preprocess.lock"

# 防止并发：上次还在跑就跳过
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    exit 0
fi

# 遍历 _staging/ 中的 PDF（不含子目录）
shopt -s nullglob
for pdf in "$STAGING_DIR"/*.pdf; do
    [ -f "$pdf" ] || continue

    pdf_name=$(basename "$pdf" .pdf)
    slug=$(echo "$pdf_name" | sed 's/[^a-zA-Z0-9_\-]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')
    output_dir="$VAULT_ROOT/_staging/parsed/$slug"

    # 已处理过则跳过
    if [ -d "$output_dir" ] && [ -f "$output_dir/$slug.md" ]; then
        continue
    fi

    echo "[$(date '+%H:%M:%S')] 检测到新 PDF: $pdf_name"
    bash "$PIPELINE_SCRIPT" "$pdf" 2>&1 | sed 's/^/  /'
    echo ""
done
