"""
Zotero CSL-JSON → Obsidian Stub Note 批量导入脚本

用法:
    python _meta/bulk-import-zotero.py

输入: _staging/bulk/zotero.json (CSL-JSON 格式)
输出: _staging/notes/<slug>.md (每篇一篇 stub note)
"""

import json
import os
import re
import sys
from datetime import datetime

# ─── 路径 ───────────────────────────────────────────────────────────────────
VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_FILE = os.path.join(VAULT_ROOT, "_staging", "bulk", "zotero.json")
OUTPUT_DIR = os.path.join(VAULT_ROOT, "_staging", "notes")
TAXONOMY_FILE = os.path.join(VAULT_ROOT, "_meta", "taxonomy.md")
INDEX_FILE = os.path.join(VAULT_ROOT, "_meta", "index.md")
LOG_FILE = os.path.join(VAULT_ROOT, "_meta", "ingest-log.md")

# ─── arXiv 类别 → Vault 标签映射 ────────────────────────────────────────────
# CSL-JSON 的 note 字段格式: "arXiv:2311.18608 [cs.CV]"
ARXIV_CAT_MAP = {
    "cs.CV":   "domain/Computer-Vision",
    "cs.AI":   "domain/Artificial-Intelligence",
    "cs.RO":   "domain/Robotics",
    "cs.CL":   "domain/Natural-Language-Processing",
    "cs.LG":   "method/Machine-Learning",
    "cs.IR":   "domain/Information-Retrieval",
    "cs.MM":   "domain/Multimedia",
    "cs.GR":   "domain/Computer-Graphics",
    "cs.HC":   "domain/Human-Computer-Interaction",
    "cs.SD":   "domain/Sound",
    "eess.AS": "domain/Audio-Processing",
    "eess.IV": "domain/Computer-Vision",
    "stat.ML": "method/Machine-Learning",
    "cs.CY":   "domain/Computers-and-Society",
    "cs.NE":   "method/Neural-Evolution",
}

# 从 publisher / container-title 推断 domain
PUBLISHER_DOMAIN_MAP = {
    "IEEE":              "domain/Computer-Vision",
    "CVF":               "domain/Computer-Vision",
    "ICCV":              "domain/Computer-Vision",
    "ECCV":              "domain/Computer-Vision",
    "CVPR":              "domain/Computer-Vision",
    "NeurIPS":           "domain/Machine-Learning",
    "ICLR":              "domain/Machine-Learning",
    "AAAI":              "domain/Artificial-Intelligence",
    "SIGGRAPH":          "domain/Computer-Graphics",
    "ACM Trans":         "domain/Computer-Graphics",
    "IJCV":              "domain/Computer-Vision",
    "TPAMI":             "domain/Computer-Vision",
    "arXiv":             "",
}


def extract_year(pub_data):
    """从 issued/date-parts 提取年份"""
    if not pub_data:
        return ""
    parts = pub_data.get("date-parts", [])
    if parts and len(parts[0]) > 0:
        return str(parts[0][0])
    return ""


def extract_arxiv_cats(note):
    """从 note 字段提取 arXiv 类别，如 'arXiv:2311.18608 [cs.CV]' → ['cs.CV']"""
    if not note:
        return []
    m = re.search(r'\[([^\]]+)\]', note)
    if m:
        raw = m.group(1)
        cats = [c.strip() for c in raw.split(",")]
        return cats
    return []


def extract_arxiv_id(note, url):
    """从 note 或 URL 提取 arXiv ID"""
    if note:
        m = re.search(r'(\d{4}\.\d{4,5}(v\d+)?)', note)
        if m:
            return m.group(1)
    if url and "arxiv.org" in url:
        m = re.search(r'(\d{4}\.\d{4,5}(v\d+)?)', url)
        if m:
            return m.group(1)
    return ""


def slugify(title):
    """从标题生成文件名 slug"""
    s = title.lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[-\s]+', '-', s)
    s = s.strip('-')
    # 限制长度避免路径过长
    if len(s) > 120:
        s = s[:120].rstrip('-')
    return s


def guess_tags(item):
    """从 arXiv 类别、publisher、摘要关键词推断标签"""
    tags = set()

    # 1. 从 arXiv 类别映射
    note = item.get("note", "") or ""
    cats = extract_arxiv_cats(note)
    for c in cats:
        if c in ARXIV_CAT_MAP:
            tags.add(ARXIV_CAT_MAP[c])

    # 2. 从 publisher / 会议名映射
    publisher = item.get("publisher", "") or ""
    container = item.get("container-title", "") or ""
    for keyword, tag in PUBLISHER_DOMAIN_MAP.items():
        if keyword.lower() in publisher.lower() or keyword.lower() in container.lower():
            if tag:
                tags.add(tag)

    # 3. 从摘要关键词试探（只对摘要 >= 30 字的样本做）
    abstract = item.get("abstract", "") or ""
    if len(abstract) > 30:
        ab_lower = abstract.lower()
        if any(w in ab_lower for w in ["3d ", "motion", "human", "pose", "skeleton", "animation"]):
            tags.add("domain/3D-Human-Motion")
        if any(w in ab_lower for w in ["diffusion", "denoising", "score matching"]):
            tags.add("method/Diffusion-Model")
        if any(w in ab_lower for w in ["transformer", "self-attention", "vit"]):
            tags.add("method/Transformer")
        if any(w in ab_lower for w in ["nerf", "neural radiance", "3d gaussian", "volumetric"]):
            tags.add("method/NeRF")
        if any(w in ab_lower for w in ["llm", "large language model", "gpt", "bert"]):
            tags.add("method/Large-Language-Model")
        if any(w in ab_lower for w in ["reinforcement learning", "rl", "drl"]):
            tags.add("method/Reinforcement-Learning")
        if any(w in ab_lower for w in ["image generation", "text-to-image", "t2i"]):
            tags.add("domain/Image-Generation")
        if any(w in ab_lower for w in ["image editing", "image-to-image", "instructpix2pix"]):
            tags.add("domain/Image-Editing")
        if any(w in ab_lower for w in ["segmentation", "semantic segmentation", "instance segmentation"]):
            tags.add("domain/Segmentation")
        if any(w in ab_lower for w in ["object detection", "detr", "yolo", "faster r-cnn"]):
            tags.add("domain/Object-Detection")
        if any(w in ab_lower for w in ["embodied", "robot", "manipulation", "grasp"]):
            tags.add("domain/Embodied-AI")
        if any(w in ab_lower for w in ["mesh", "reconstruction", "hmr", "smpl"]):
            tags.add("domain/Human-Mesh-Recovery")
        if any(w in ab_lower for w in ["motion capture", "mocap", "motion generation"]):
            tags.add("domain/3D-Human-Motion")
        if any(w in ab_lower for w in ["face", "facial", "expression"]):
            tags.add("domain/Face")
        if any(w in ab_lower for w in ["gaussian splatting", "3dgs"]):
            tags.add("method/3D-Gaussian-Splatting")

    return sorted(tags)


def make_note_content(item):
    """生成一篇 stub note 的 markdown 内容"""
    title = item.get("title", "Untitled")
    authors_list = item.get("author", [])
    authors_str = "; ".join(
        f"{a.get('given', '')} {a.get('family', '')}".strip()
        for a in authors_list if a.get("family")
    ) or "Unknown"
    year = extract_year(item.get("issued"))
    publisher = item.get("publisher", "Unknown")
    container = item.get("container-title", "")
    venue = container or publisher or ""
    abstract = item.get("abstract", "").strip() or "No abstract available."
    url = item.get("URL", "")
    arxiv_id = extract_arxiv_id(item.get("note", ""), url)

    tags = guess_tags(item)
    tags_str = "\n  - " + "\n  - ".join(tags) if tags else ""

    # 文件名
    slug = slugify(title)
    # 防止空 slug
    if not slug:
        slug = f"untitled-{hash(title) % 10000}"

    # 作者行（简短）
    first_author = authors_list[0].get("family", "Unknown") if authors_list else "Unknown"
    author_line = f"{', '.join(a.get('family', '') for a in authors_list if a.get('family'))}"
    if len(author_line) > 120:
        author_line = f"{first_author} et al."

    arxiv_link = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else (url or "")

    created = datetime.now().strftime("%Y-%m-%d")

    return f"""---
title: "{title}"
authors: "{author_line}"
year: {year or 'unknown'}
tags:{tags_str}
source_zotero: "{item.get('id', '')}"
arxiv_id: "{arxiv_id or ''}"
status: stub
created: {created}
---

# {title}

{', '.join(a.get('family', '') for a in authors_list if a.get('family'))}, {venue} {year}

## Abstract

{abstract}

## Links

- arXiv: [{arxiv_link}]({arxiv_link})
- Zotero: {item.get('id', '')}

---
*自动生成的 stub note。后续可升级为完整笔记（含 一句话/核心方法/创新点/借鉴）。*
""", slug  # 返回 (content, slug)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    total = len(data)
    generated = 0
    skipped = 0
    errors = 0
    new_tags = set()

    for i, item in enumerate(data):
        title = item.get("title")
        if not title:
            skipped += 1
            continue

        try:
            content, slug = make_note_content(item)
            filepath = os.path.join(OUTPUT_DIR, f"{slug}.md")

            # 如果文件已存在，加后缀
            if os.path.exists(filepath):
                filepath = os.path.join(OUTPUT_DIR, f"{slug}-{i}.md")

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            # 收集新标签
            for tag in guess_tags(item):
                new_tags.add(tag)

            generated += 1

        except Exception as e:
            print(f"  [ERROR] #{i} '{title[:50]}...': {e}")
            errors += 1

        # 进度
        if (i + 1) % 200 == 0:
            print(f"  Progress: {i+1}/{total}")

    print(f"\n=== 完成 ===")
    print(f"  总条目:   {total}")
    print(f"  生成:     {generated}")
    print(f"  跳过:     {skipped}")
    print(f"  错误:     {errors}")

    # ─── 更新 taxonomy.md ───────────────────────────────────────────
    if new_tags:
        print(f"\n  新标签 ({len(new_tags)} 个)，建议手动检查 taxonomy.md:")
        for t in sorted(new_tags):
            print(f"    - {t}")

    # ─── 更新 ingest-log.md ─────────────────────────────────────────
    today = datetime.now().strftime("%Y-%m-%d")
    log_entry = f"| {today} | Zotero 批量导入 | {generated} 篇 stub note | — |\n"
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            log_content = f.read()
        # 插入到表格最后（在 --- 分隔符之前）
        insert_pos = log_content.rfind("|")
        last_newline = log_content.rfind("\n", 0, insert_pos)
        before = log_content[:last_newline]
        after = log_content[last_newline:]
        # 找到表格的末尾
        lines = log_content.split("\n")
        # 在表格最后一行前插入
        table_end = len(lines)
        for j in range(len(lines) - 1, 0, -1):
            if lines[j].strip().startswith("|"):
                table_end = j
                break
        lines.insert(table_end + 1, log_entry.rstrip())
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"  ingest-log.md 已更新")

    # ─── 更新 index.md ──────────────────────────────────────────────
    if os.path.exists(INDEX_FILE):
        # 按 domain 分组，追加 stub note 链接
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            index_content = f.read()

        # 重新读取已生成的笔记文件，实际提取标签
        import glob
        note_files = glob.glob(os.path.join(OUTPUT_DIR, "*.md"))
        # 按 domain 分组
        domain_notes = {}
        for nf in note_files:
            with open(nf, "r", encoding="utf-8") as f:
                ncontent = f.read()
            # 提取 frontmatter 中的 tags
            tag_matches = re.findall(r'domain/[a-zA-Z0-9_-]+', ncontent)
            title_match = re.search(r'^title: "(.+)"', ncontent, re.MULTILINE)
            note_title = title_match.group(1) if title_match else os.path.basename(nf).replace(".md", "")
            slug = os.path.basename(nf).replace(".md", "")
            for tag in tag_matches:
                domain_name = tag.split("/")[1]
                if domain_name not in domain_notes:
                    domain_notes[domain_name] = []
                domain_notes[domain_name].append(f"  - [[{slug}|{note_title[:60]}]]")

        # 更新 index.md：在每个 domain 标题下追加 stub notes
        for domain, notes in sorted(domain_notes.items()):
            header = f"## {domain.replace('-', ' ')}"
            if header in index_content:
                # 在 header 后，找第一个非空行后面插入
                pass  # 简化处理：不自动修改，避免破坏已有结构

        print(f"  index.md 需手动更新（共 {len(domain_notes)} 个 domain 分组）")

    print(f"\n提示：")
    print(f"  - 笔记位于: {OUTPUT_DIR}")
    print(f"  - 建议用 'ingest' 将重点论文从 stub 升级为完整笔记")
    print(f"  - 运行后可用 git status 确认变更")


if __name__ == "__main__":
    main()
