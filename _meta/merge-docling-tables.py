#!/usr/bin/env python3
"""
Docling table merger: runs Docling on a PDF, extracts structured pipe tables,
and merges them into the OpenDataLoader-generated markdown (replacing flat-text tables).

Usage: python _meta/merge-docling-tables.py <pdf-path> <opendataloader-md-path>
"""

import re
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict
from docling.document_converter import DocumentConverter


def extract_docling_tables(pdf_path: str) -> Dict[str, Tuple[str, str]]:
    """
    Run Docling on a PDF, return {table_number: (full_caption, pipe_table_md)}.
    """
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    doc = result.document

    tables = {}
    for table in doc.tables:
        caption = table.caption_text(doc)
        if not caption:
            continue
        m = re.match(r'(Table\s+\d+)', caption.strip(), re.IGNORECASE)
        if not m:
            continue
        table_num = m.group(1)
        table_md = table.export_to_markdown().strip()
        tables[table_num] = (caption.strip(), table_md)

    return tables


def _is_prose_line(line: str) -> bool:
    """Detect if a line is natural language prose (not table data)."""
    stripped = line.strip()
    if not stripped:
        return False
    # Section headers
    if stripped.startswith('#'):
        return True
    # Image embeds
    if stripped.startswith('!['):
        return True
    # Markdown list items that are full sentences
    if stripped.startswith('- ') or stripped.startswith('* '):
        # Check for sentence-ending punctuation mid-line (prose, not data)
        if re.search(r'[.?!]\s+\w', stripped):
            return True
    # Contains common prose function words
    prose_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'has', 'have',
                   'this', 'that', 'these', 'those', 'with', 'from', 'they',
                   'which', 'their', 'each', 'also', 'into', 'than', 'then',
                   'its', 'not', 'can', 'may', 'our', 'show', 'figure'}
    words_lower = [w.lower().rstrip(',.;:()[]') for w in stripped.split()]
    if len(words_lower) >= 4:
        match_count = sum(1 for w in words_lower if w in prose_words)
        if match_count >= 2:
            return True
    # Sentence-ending punctuation at end followed by capital letter elsewhere
    if re.search(r'[.?!]\s+[A-Z]', stripped):
        return True
    if re.match(r'^\d+\.\s', stripped):  # Numbered list items
        return True
    return False


def _has_table_pattern(line: str) -> bool:
    """Detect if a line looks like flat table data from OpenDataLoader."""
    stripped = line.strip()
    if not stripped:
        return False
    # Contains ± (common in academic tables with std deviations)
    if '±' in stripped:
        return True
    # High ratio of digit/punctuation characters
    digit_punct = sum(1 for c in stripped if c.isdigit() or c in '±.()[]<>↑↓→')
    alpha = sum(1 for c in stripped if c.isalpha())
    total = digit_punct + alpha
    if total > 0 and digit_punct / total >= 0.25:
        return True
    # Short labels that appear in tables (single line, few words, no prose words)
    words = stripped.split()
    if len(words) <= 6:
        return True
    return False


def find_table_boundaries(md_text: str, caption: str) -> Optional[Tuple[int, int]]:
    """
    Scan BACKWARD from the caption to find the flat table data block
    that PRECEDES it in OpenDataLoader output.
    Returns (table_data_start, caption_start) character offsets,
    or None if caption not found.
    """
    # Find caption position (try exact match first)
    idx = md_text.find(caption)
    if idx == -1:
        m = re.search(re.escape(caption[:20]), md_text, re.IGNORECASE)
        if not m:
            return None
        idx = m.start()

    # Scan backward from caption position to find flat table data start
    pos = idx
    # Skip blank lines immediately before caption
    while pos > 0 and md_text[pos - 1] in '\n':
        pos -= 1
    if pos == 0:
        return None  # Caption at very start of file, no data before it

    # pos now at end of the last content line before blank-separator
    # Find start of this line
    line_end = pos
    line_start = line_end
    while line_start > 0 and md_text[line_start - 1] != '\n':
        line_start -= 1

    # Scan backward line by line, collecting table data
    table_data_end = idx  # region to replace ends right before caption
    scan_pos = line_start

    while scan_pos > 0:
        # Find start of previous line
        prev_end = scan_pos - 1  # skip the \n
        if prev_end <= 0:
            break
        prev_start = prev_end
        while prev_start > 0 and md_text[prev_start - 1] != '\n':
            prev_start -= 1

        line_content = md_text[prev_start:prev_end]

        if _is_prose_line(line_content):
            # Found prose — table data starts after this line
            break

        if _has_table_pattern(line_content):
            # Continue scanning backward through table data
            scan_pos = prev_start
            # Skip blank lines within table data
            while scan_pos > 0 and md_text[scan_pos - 1] == '\n':
                scan_pos -= 1
            continue

        # Empty line within table data: skip it, continue scanning
        if not line_content.strip():
            scan_pos = prev_start
            continue

        # Unclear — stop to avoid eating prose, but only if we've already
        # found table data; if no table data found yet, try continuing
        if _has_table_pattern(line_content):
            scan_pos = prev_start
            continue
        break

    table_data_start = scan_pos
    # Verify we actually found data (not just the caption itself)
    if table_data_start >= table_data_end - 1:
        return None

    return (table_data_start, table_data_end)


def merge_tables(opendataloader_md: str, docling_tables: Dict[str, Tuple[str, str]]) -> str:
    """Replace flat table data blocks with Docling pipe tables.

    OpenDataLoader places flat table data BEFORE the caption, so we scan
    backward from the caption to find and replace the data region.
    """
    result = opendataloader_md

    # Process tables in reverse order (by numeric index) so offsets stay valid
    for table_label in sorted(docling_tables.keys(), key=lambda x: int(re.search(r'\d+', x).group()), reverse=True):
        caption, pipe_table = docling_tables[table_label]
        bounds = find_table_boundaries(result, caption)
        if bounds is None:
            print(f"  ⚠  {table_label}: caption not found in OpenDataLoader output, skipping")
            continue

        data_start, caption_start = bounds
        # Replace flat table data with Docling pipe table, preserve original caption
        result = result[:data_start] + pipe_table + '\n\n' + result[caption_start:]
        print(f"  ✓  {table_label}: merged")

    return result


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <pdf-path> <opendataloader-md-path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    md_path = sys.argv[2]

    print(f"Extracting tables from PDF via Docling...")
    docling_tables = extract_docling_tables(pdf_path)
    table_nums = sorted(docling_tables.keys(), key=lambda x: int(re.search(r'\d+', x).group()))
    print(f"  Found {len(docling_tables)} tables: {table_nums}")

    print(f"Reading OpenDataLoader markdown: {md_path}")
    with open(md_path, 'r', encoding='utf-8') as f:
        original_md = f.read()

    print(f"Merging tables...")
    merged_md = merge_tables(original_md, docling_tables)

    # Write back
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(merged_md)

    print(f"Done. Tables merged into: {md_path}")


if __name__ == '__main__':
    main()
