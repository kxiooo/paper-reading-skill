"""
Zotero Stub Note 去重 + 迁移脚本

功能:
  1. 将 stub note 从 _staging/notes/ 迁移到 _staging/zotero/
  2. 按 arxiv_id + 标题去重，保留信息最完整的一篇
  3. 保留原始人写笔记不变
"""

import os
import re
import json
import shutil
from collections import defaultdict
from datetime import datetime

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NOTES_DIR = os.path.join(VAULT_ROOT, "_staging", "notes")
ZOTERO_DIR = os.path.join(VAULT_ROOT, "_staging", "zotero")
INDEX_FILE = os.path.join(VAULT_ROOT, "_meta", "index.md")
LOG_FILE = os.path.join(VAULT_ROOT, "_meta", "ingest-log.md")

# ─── 保护名单：这些笔记是人类写的，不能动 ────────────────────────────
# 按你的实际情况填入笔记文件名（不含 .md）。留空表示不保护任何笔记。
PROTECTED_NOTES: set[str] = set()

def parse_frontmatter(content):
    """从 markdown 中提取 frontmatter 字段"""
    result = {}
    m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not m:
        return result
    fm = m.group(1)
    # 提取 title
    t = re.search(r'^title:\s*"(.+)"', fm, re.MULTILINE)
    if t: result['title'] = t.group(1)
    # 提取 arxiv_id
    a = re.search(r'^arxiv_id:\s*"([^"]*)"', fm, re.MULTILINE)
    if a: result['arxiv_id'] = a.group(1)
    # 提取 year
    y = re.search(r'^year:\s*(\d+|unknown)', fm, re.MULTILINE)
    if y: result['year'] = y.group(1)
    # 提取 tags 数量
    result['tag_count'] = len(re.findall(r'^\s+-\s+domain/', fm, re.MULTILINE)) + len(re.findall(r'^\s+-\s+method/', fm, re.MULTILINE))
    # 是否有 abstract
    result['has_abstract'] = 'Abstract' in content and 'No abstract available' not in content
    # 完整性得分
    score = 0
    if result.get('year') and result['year'] != 'unknown': score += 1
    if result.get('has_abstract'): score += 2
    if result.get('arxiv_id'): score += 1
    if result.get('tag_count', 0) > 0: score += 1
    result['score'] = score
    return result


def dedup_key(info):
    """生成去重用的 key：优先用 arxiv_id，其次用标准化标题"""
    if info.get('arxiv_id'):
        return f"arxiv:{info['arxiv_id']}"
    title = info.get('title', '').lower().strip()
    title = re.sub(r'[^a-z0-9]', '', title)
    return f"title:{title[:80]}"  # 取前80字符


def main():
    os.makedirs(ZOTERO_DIR, exist_ok=True)

    # 读取所有 md 文件
    all_files = [f for f in os.listdir(NOTES_DIR) if f.endswith('.md')]

    # 分离受保护笔记 和 stub notes
    protected = []
    stubs = []
    for fname in all_files:
        base = os.path.splitext(fname)[0]
        if base in PROTECTED_NOTES:
            protected.append(fname)
        else:
            stubs.append(fname)

    print(f"受保护笔记（保留在原位）: {len(protected)}")
    print(f"Stub notes（待处理）: {len(stubs)}")

    # ─── 读取所有 stub note，计算去重 key ──────────────────────
    groups = defaultdict(list)
    for fname in stubs:
        fpath = os.path.join(NOTES_DIR, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        info = parse_frontmatter(content)
        info['fname'] = fname
        info['content'] = content
        key = dedup_key(info)
        groups[key].append(info)

    # ─── 去重 ────────────────────────────────────────────────
    keep = []
    remove = []
    for key, items in groups.items():
        if len(items) == 1:
            keep.append(items[0])
        else:
            # 按完整性得分排序，保留最高的
            items.sort(key=lambda x: -x['score'])
            keep.append(items[0])
            for item in items[1:]:
                remove.append(item)

    print(f"\n去重后保留: {len(keep)}")
    print(f"去重移除: {len(remove)}")

    # ─── 迁移：把 keep 的 stub note 移到 _staging/zotero/ ────
    moved = 0
    for item in keep:
        src = os.path.join(NOTES_DIR, item['fname'])
        dst = os.path.join(ZOTERO_DIR, item['fname'])
        # 避免覆盖
        if os.path.exists(dst):
            base, ext = os.path.splitext(item['fname'])
            dst = os.path.join(ZOTERO_DIR, f"{base}_dup{ext}")
        shutil.move(src, dst)
        moved += 1

    # ─── 删除重复项 ───────────────────────────────────────────
    deleted = 0
    for item in remove:
        src = os.path.join(NOTES_DIR, item['fname'])
        if os.path.exists(src):
            os.remove(src)
            deleted += 1

    # ─── 删除 OmniME 的 stub note 副本（如果已经有一篇在保护名单里） ──
    # 检查 OmniME 的 stub 是否被移走了
    omni_stubs = [f for f in os.listdir(NOTES_DIR) if 'omni-supervised' in f.lower()]
    for f in omni_stubs:
        os.remove(os.path.join(NOTES_DIR, f))
        print(f"  清理 OmniME stub: {f}")

    print(f"\n迁移: {moved}")
    print(f"删除重复: {deleted}")
    print(f"Zotero stub notes: {len(os.listdir(ZOTERO_DIR))}")
    print(f"Notes（清理后）: {len([f for f in os.listdir(NOTES_DIR) if f.endswith('.md')])}")

    # ─── 更新 ingest-log.md ──────────────────────────────────
    today = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            log_content = f.read()
        lines = log_content.split('\n')
        insert_line = f"| {today} | Zotero 去重 & 迁移 | stub → _staging/zotero/, 保留 {len(keep)}, 删除 {deleted} | — |"
        # 在表格最后一行前插入
        for j in range(len(lines) - 1, 0, -1):
            if lines[j].strip().startswith('|'):
                lines.insert(j + 1, insert_line)
                break
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"\ningest-log.md 已更新")

    # ─── 更新 index.md ──────────────────────────────────────
    # 简单追加一条说明
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            index_content = f.read()
        note = f"\n> ⚠️ Zotero 批量导入的 stub notes（{moved} 篇）已移入 `_staging/zotero/`。查询时请同时索引两个目录。\n"
        if note not in index_content:
            index_content += note
            with open(INDEX_FILE, 'w', encoding='utf-8') as f:
                f.write(index_content)
            print(f"index.md 已更新")

    print(f"\n=== 完成 ===")
    print(f"  笔记目录: {NOTES_DIR}/ ← 仅含人类写笔记")
    print(f"  Zotero目录: {ZOTERO_DIR}/ ← 仅含批量导入 stub notes")


if __name__ == '__main__':
    main()
