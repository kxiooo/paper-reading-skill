#!/usr/bin/env python3
"""
Post-preprocessing quality validator.
Checks that the generated markdown is structurally complete and
has no known corruption patterns before handing to the LLM.

Usage: python _meta/validate-preprocess.py <markdown-path> [--pdf-pages N]
Exit code 0 = pass, 1 = fail.
"""

import re
import sys
import io
from pathlib import Path
from typing import Optional, Tuple, List

# Fix console encoding for Windows GBK terminals
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ═══════════════════════════════════════════════════════════════════
#  Checks
# ═══════════════════════════════════════════════════════════════════

# Key sections that should exist in any academic paper
REQUIRED_SECTIONS = [
    # Pattern -> human label
    (r'abstract', 'Abstract'),
    (r'introduction', 'Introduction'),
    (r'(method|approach|proposed|framework|model architecture)', 'Method/Approach'),
    (r'(experiment|evaluation|result)', 'Experiments/Evaluation'),
    (r'(conclusion|discussion)', 'Conclusion/Discussion'),
    (r'reference', 'References'),
]

# Section-level headers (## or ###)
SECTION_PATTERN = re.compile(r'^#{2,3}\s+', re.MULTILINE)

# Pipe table markers (should NOT appear unless --merge-tables was used)
PIPE_TABLE_PATTERN = re.compile(r'^\|[-|]+\|$', re.MULTILINE)

# Minimum lines per PDF page (heuristic: CVPR/ICCV ~40-60 lines/page)
MIN_LINES_PER_PAGE = 25


def count_lines(text: str) -> int:
    return len(text.split('\n'))


def count_section_headers(text: str) -> int:
    return len(SECTION_PATTERN.findall(text))


def check_required_sections(text: str) -> List[str]:
    """Return list of missing section labels."""
    text_lower = text.lower()
    missing = []
    for pattern, label in REQUIRED_SECTIONS:
        if not re.search(pattern, text_lower):
            missing.append(label)
    return missing


def check_pipe_tables(text: str) -> int:
    """Return count of pipe table separator lines found."""
    return len(PIPE_TABLE_PATTERN.findall(text))


def check_line_count(text: str, pdf_pages: Optional[int]) -> Tuple[int, Optional[int], bool]:
    """Returns (lines, expected_min, is_ok)."""
    lines = count_lines(text)
    if pdf_pages is None:
        return lines, None, True
    expected_min = pdf_pages * MIN_LINES_PER_PAGE
    return lines, expected_min, lines >= expected_min


# ═══════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <markdown-path> [--pdf-pages N]")
        sys.exit(1)

    md_path = sys.argv[1]

    # Parse optional --pdf-pages N
    pdf_pages = None
    for i, arg in enumerate(sys.argv[2:], start=2):
        if arg == '--pdf-pages' and i + 1 < len(sys.argv):
            try:
                pdf_pages = int(sys.argv[i + 1])
            except ValueError:
                pass

    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    errors = []
    warnings = []

    # 1. Required sections
    missing = check_required_sections(text)
    if missing:
        errors.append(f"Missing sections: {', '.join(missing)}")

    # 2. Pipe table remnants
    pipe_count = check_pipe_tables(text)
    if pipe_count > 0:
        warnings.append(f"Found {pipe_count} pipe table separator(s) — "
                        f"may be Docling merge remnants")

    # 3. Line count sanity
    lines, expected_min, line_ok = check_line_count(text, pdf_pages)
    section_count = count_section_headers(text)
    if not line_ok and pdf_pages is not None:
        errors.append(f"Line count too low: {lines} lines for {pdf_pages}-page PDF "
                      f"(expected ≥{expected_min})")

    # 4. Very few section headers
    if section_count < 3:
        errors.append(f"Only {section_count} section headers found — "
                      f"possible structural corruption")

    # Report
    print(f"Validation: {md_path}")
    print(f"  Lines: {lines}" + (f" (≥{expected_min} expected for {pdf_pages}p PDF)" if pdf_pages else ""))
    print(f"  Sections: {section_count}")
    print(f"  Pipe tables: {pipe_count}")

    if errors:
        print(f"\n  ❌ FAILED ({len(errors)} error(s)):")
        for e in errors:
            print(f"     • {e}")
    if warnings:
        print(f"\n  ⚠  Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"     • {w}")

    if errors:
        print("\n  Preprocessed markdown may be incomplete. Do NOT feed to LLM.")
        sys.exit(1)
    else:
        print("\n  ✅ PASSED — safe for LLM reading.")
        sys.exit(0)


if __name__ == '__main__':
    main()
