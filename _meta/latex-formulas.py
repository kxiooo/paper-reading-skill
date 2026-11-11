#!/usr/bin/env python3
"""
Rule-based formula LaTeX converter: converts Unicode math and cleans figure-noise
from OpenDataLoader-generated markdown using deterministic character mapping.

Usage:
  python _meta/latex-formulas.py <markdown-path>

No API key required. Pure Unicode → LaTeX substitution + heuristics.
"""

import re
import sys
from pathlib import Path
from typing import Optional


# ═══════════════════════════════════════════════════════════════════
#  Unicode → LaTeX mapping tables
# ═══════════════════════════════════════════════════════════════════

# Greek lowercase
GREEK_LOWER = {
    'α': r'\alpha',   'β': r'\beta',    'γ': r'\gamma',
    'δ': r'\delta',   'ε': r'\epsilon',  'ζ': r'\zeta',
    'η': r'\eta',     'θ': r'\theta',    'ι': r'\iota',
    'κ': r'\kappa',   'λ': r'\lambda',   'μ': r'\mu',
    'ν': r'\nu',      'ξ': r'\xi',       'π': r'\pi',
    'ρ': r'\rho',     'σ': r'\sigma',    'τ': r'\tau',
    'υ': r'\upsilon', 'φ': r'\phi',      'χ': r'\chi',
    'ψ': r'\psi',     'ω': r'\omega',
}

# Greek uppercase
GREEK_UPPER = {
    'Γ': r'\Gamma',   'Δ': r'\Delta',    'Θ': r'\Theta',
    'Λ': r'\Lambda',  'Ξ': r'\Xi',       'Π': r'\Pi',
    'Σ': r'\Sigma',   'Υ': r'\Upsilon',  'Φ': r'\Phi',
    'Ψ': r'\Psi',     'Ω': r'\Omega',
}

# Math operators & symbols
MATH_SYMBOLS = {
    '∀': r'\forall',   '∂': r'\partial',  '∃': r'\exists',
    '∅': r'\emptyset', '∇': r'\nabla',     '∈': r'\in',
    '∉': r'\notin',    '∋': r'\ni',
    '∑': r'\sum',      '√': r'\sqrt',      '∝': r'\propto',
    '∞': r'\infty',    '∠': r'\angle',
    '∧': r'\land',     '∨': r'\lor',
    '∩': r'\cap',      '∪': r'\cup',       '∫': r'\int',
    '≈': r'\approx',   '≠': r'\neq',
    '≤': r'\leq',      '≥': r'\geq',
    '⊂': r'\subset',   '⊃': r'\supset',
    '⊆': r'\subseteq', '⊇': r'\supseteq',
    '⋅': r'\cdot',     '⋮': r'\vdots',
    '⋯': r'\cdots',    '⋰': r'\ddots',
    '⊥': r'\perp',     '∘': r'\circ',
    '⊙': r'\odot',     '⊕': r'\oplus',     '⊗': r'\otimes',
    '∗': '*',          '×': r'\times',
    '−': '-',          '→': r'\rightarrow',
}

# Double-struck / blackboard bold
BLACKBOARD = {
    'ℕ': r'\mathbb{N}', 'ℙ': r'\mathbb{P}',
    'ℚ': r'\mathbb{Q}', 'ℝ': r'\mathbb{R}',
    'ℤ': r'\mathbb{Z}', 'ℂ': r'\mathbb{C}',
}

# Math alphanumeric italic (U+1D434–U+1D467, U+1D468–U+1D49B, etc.)
# These are "mathematical italic" characters used for variables in papers
# We map them back to ASCII italics (just the regular letter)
import unicodedata

def normalize_math_alphanumeric(char: str) -> str:
    """Convert math alphanumeric Unicode to regular ASCII letter."""
    cp = ord(char)
    # Mathematical Italic: A-Z (U+1D434–U+1D44D), a-z (U+1D44E–U+1D467)
    if 0x1D434 <= cp <= 0x1D44D:
        return chr(ord('A') + (cp - 0x1D434))
    if 0x1D44E <= cp <= 0x1D467:
        return chr(ord('a') + (cp - 0x1D44E))
    # Mathematical Bold Italic: A-Z (U+1D468–U+1D481), a-z (U+1D482–U+1D49B)
    if 0x1D468 <= cp <= 0x1D481:
        return chr(ord('A') + (cp - 0x1D468))
    if 0x1D482 <= cp <= 0x1D49B:
        return chr(ord('a') + (cp - 0x1D482))
    # Mathematical Bold: A-Z (U+1D400–U+1D419), a-z (U+1D41A–U+1D433)
    if 0x1D400 <= cp <= 0x1D419:
        return chr(ord('A') + (cp - 0x1D400))
    if 0x1D41A <= cp <= 0x1D433:
        return chr(ord('a') + (cp - 0x1D41A))
    return char


# Combine all math-symbol maps
ALL_MATH_SYMBOLS = {}
ALL_MATH_SYMBOLS.update(GREEK_LOWER)
ALL_MATH_SYMBOLS.update(GREEK_UPPER)
ALL_MATH_SYMBOLS.update(MATH_SYMBOLS)
ALL_MATH_SYMBOLS.update(BLACKBOARD)


# ═══════════════════════════════════════════════════════════════════
#  Detection
# ═══════════════════════════════════════════════════════════════════

# Math Unicode ranges (used for detection, not mapping)
MATH_UNICODE_RANGES = [
    (0x2200, 0x22FF),   # Mathematical Operators
    (0x1D400, 0x1D7FF), # Mathematical Alphanumeric Symbols
    (0x03B1, 0x03C9),   # Greek lowercase
    (0x0393, 0x03A9),   # Greek uppercase (excluding A,B,E,Z,H,I,K,M,N,O,P,T,X but including Gamma,Delta,etc.)
    (0x2100, 0x214F),   # Letterlike Symbols
    (0x2308, 0x230B),   # Ceiling/floor
    (0x2A00, 0x2AFF),   # Supplemental Math Operators
]

FIGURE_NOISE_SYMBOLS = set('✓✗⌑⌒⌘⇥⟰⟱⟲⬆⬇➔◆◇●○◉◎◈⬜⬛▸▹►▻▼▽△▴▲')


def _in_math_range(cp: int) -> bool:
    for lo, hi in MATH_UNICODE_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def count_math_chars(text: str) -> int:
    return sum(1 for c in text if _in_math_range(ord(c)))


def is_figure_noise(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    words = stripped.split()
    # Short line with diagram symbols
    if len(stripped) < 60 and any(c in FIGURE_NOISE_SYMBOLS for c in stripped):
        return True
    # Shape annotations: "(L, 3) (L, 512)" etc.
    if re.match(r'^[\s\(\)\[\]L,×x\d+\-]+$', stripped) and len(words) <= 5:
        return True
    # Sparse symbol-heavy short text
    if len(words) <= 3:
        alpha_ratio = sum(1 for c in stripped if c.isalpha()) / max(len(stripped), 1)
        if alpha_ratio < 0.3 and len(stripped) < 40:
            return True
    # Diagram labels: ALL CAPS short phrases with no sentences (e.g., "Camera Frame SMPL")
    # These are typically extracted from architecture diagrams
    if len(words) <= 6 and len(stripped) < 80:
        # Check if it looks like a diagram label: mostly single words, no punctuation, no articles
        has_sentence = bool(re.search(r'[.?!]\s|the |a |an |is |are |was |were |has |have ', stripped.lower()))
        has_math = count_math_chars(stripped) > 0
        if not has_sentence and not has_math:
            # Multi-line blocks of diagram labels (consecutive short lines)
            lines = stripped.split('\n')
            if len(lines) >= 2 and all(len(l.strip()) < 50 for l in lines):
                return True
    return False


def needs_conversion(text: str) -> bool:
    if is_figure_noise(text):
        return True
    if count_math_chars(text) >= 2:
        return True
    return False


# ═══════════════════════════════════════════════════════════════════
#  Rule-based conversion
# ═══════════════════════════════════════════════════════════════════

def convert_math_run(run: str) -> str:
    """
    Convert a single run of math characters to LaTeX.
    Handles: Greek, symbols, math alphanumerics, subscript/superscript Unicode.
    Uses NFKD normalization to map math-style characters to base form.
    """
    result = []
    i = 0
    while i < len(run):
        c = run[i]

        # Math alphanumeric → NFKD normalize first, then process as base char
        if 0x1D400 <= ord(c) <= 0x1D7FF:
            base = unicodedata.normalize('NFKD', c)
            # If base is a single Greek char, map to LaTeX
            if len(base) == 1 and base in ALL_MATH_SYMBOLS:
                result.append(ALL_MATH_SYMBOLS[base])
            elif len(base) == 1 and base in GREEK_LOWER:
                result.append(GREEK_LOWER[base])
            elif len(base) == 1 and base in GREEK_UPPER:
                result.append(GREEK_UPPER[base])
            else:
                # ASCII letter or digit — just use the base form
                result.append(base)
            i += 1
            continue

        # Try exact match in math symbol table
        if c in ALL_MATH_SYMBOLS:
            result.append(ALL_MATH_SYMBOLS[c])
            i += 1
            continue

        # Unicode subscript digits (₀-₉)
        if '₀' <= c <= '₉':
            result.append(f'_{ord(c) - 0x2080}')
            i += 1
            continue

        # Unicode superscript (⁰,¹,²,³,⁴-⁹,⁺,⁻)
        if c in '⁰¹²³⁴⁵⁶⁷⁸⁹':
            sup_map = {'⁰': '0', '¹': '1', '²': '2', '³': '3',
                       '⁴': '4', '⁵': '5', '⁶': '6',
                       '⁷': '7', '⁸': '8', '⁹': '9'}
            result.append(f'^{sup_map.get(c, c)}')
            i += 1
            continue
        if c in '⁺⁻':
            result.append(f'^{"+" if c == "⁺" else "-"}')
            i += 1
            continue

        # Unicode superscript letters (modifier letters)
        if 0x1D2C <= ord(c) <= 0x1D6A or 0x1D9C <= ord(c) <= 0x1DBF:
            mod_map = {0x1D40: 'T', 0x1D2C: 'A', 0x1D2E: 'B', 0x1D30: 'D',
                       0x1D31: 'E', 0x1D33: 'G', 0x1D34: 'H', 0x1D35: 'I',
                       0x1D36: 'J', 0x1D37: 'K', 0x1D38: 'L', 0x1D39: 'M',
                       0x1D3A: 'N', 0x1D3C: 'O', 0x1D3E: 'P', 0x1D3F: 'R',
                       0x1D41: 'U', 0x1D42: 'W', 0x1D43: 'a', 0x1D47: 'b',
                       0x1D9C: 'c', 0x1D48: 'd', 0x1D49: 'e', 0x1DA0: 'f',
                       0x1D4D: 'g', 0x1D50: 'h', 0x1D51: 'i', 0x1D52: 'j',
                       0x1D53: 'k', 0x1D54: 'l', 0x1D55: 'm', 0x1D56: 'n',
                       0x1D58: 'u', 0x1D5A: 'r', 0x1D5B: 't', 0x1D5B: 's',
                       0x1D60: 'w', 0x1D61: 'x', 0x1D62: 'y', 0x1D63: 'z'}
            letter = mod_map.get(ord(c), c)
            result.append(f'^{letter}')
            i += 1
            continue

        # Regular character, pass through
        result.append(c)
        i += 1

    return ''.join(result)


def wrap_math(text: str) -> str:
    """
    Wrap math runs in $...$ and convert characters.
    A "math run" is a sequence containing math-mode Unicode characters
    plus adjacent alphanumerics/punctuation, separated by spaces from prose.
    """
    # Strategy: split text into tokens. Tokens that contain math chars
    # get converted and wrapped in $...$. Pure text tokens pass through.

    # Simple approach: find runs of characters that include math symbols
    # and are delimited by spaces or punctuation boundaries.
    result = []
    i = 0
    in_math = False
    math_buf = []
    text_buf = []

    while i < len(text):
        c = text[i]

        is_math_char = c in ALL_MATH_SYMBOLS or _in_math_range(ord(c)) or (0x1D400 <= ord(c) <= 0x1D7FF)

        if is_math_char:
            # Flush text buffer
            if text_buf:
                result.append(''.join(text_buf))
                text_buf = []
            math_buf.append(c)
            in_math = True
        elif in_math:
            # Decide whether to continue math or end it
            if c in ' \t\n,.;:()[]{}':
                # End of math run (space/punctuation boundary)
                result.append('$' + convert_math_run(''.join(math_buf)) + '$')
                math_buf = []
                in_math = False
                text_buf.append(c)
            elif c.isalnum() or c in '+-=<>':
                # Continue math run (adjacent alphanumeric likely part of formula)
                math_buf.append(c)
            else:
                # Other char: end math, keep as text
                result.append('$' + convert_math_run(''.join(math_buf)) + '$')
                math_buf = []
                in_math = False
                text_buf.append(c)
        else:
            text_buf.append(c)

        i += 1

    # Flush remaining
    if math_buf:
        result.append('$' + convert_math_run(''.join(math_buf)) + '$')
    if text_buf:
        result.append(''.join(text_buf))

    # Clean up
    result_str = ''.join(result)
    # Merge "$X$$Y$" (directly adjacent, no space) → "$XY$"
    result_str = re.sub(r'\$([^$]+)\$\$([^$]+)\$', r'$\1\2$', result_str)
    # Remove empty math markers
    result_str = re.sub(r'\$\s+\$', ' ', result_str)
    # Fix double spaces
    result_str = re.sub(r'  +', ' ', result_str)
    return result_str


def convert_block(block_text: str) -> Optional[str]:
    """Rule-based conversion of a text block. Returns None to remove block."""
    if not block_text.strip():
        return block_text
    if is_figure_noise(block_text):
        return None  # Remove

    # Count math density to decide whole-block vs inline
    math_count = count_math_chars(block_text)
    total_chars = len(block_text.strip())

    if math_count == 0:
        return block_text

    return wrap_math(block_text)


# ═══════════════════════════════════════════════════════════════════
#  Markdown processing
# ═══════════════════════════════════════════════════════════════════

def process_markdown(md_text: str) -> str:
    lines = md_text.split('\n')
    result_lines = []
    pending_block = []
    converted_count = 0
    removed_count = 0

    def flush_block():
        nonlocal converted_count, removed_count
        if not pending_block:
            return

        block = '\n'.join(pending_block)
        pending_block.clear()

        stripped = block.strip()
        if not stripped:
            result_lines.append(block)
            return
        # Skip tables
        if all(l.startswith('|') or l.startswith('|-') or l.strip() == '' for l in block.split('\n') if l.strip()):
            result_lines.append(block)
            return
        # Skip images
        if re.match(r'^!\[', stripped):
            result_lines.append(block)
            return
        # Skip single-line headers
        if re.match(r'^#+\s', stripped) and '\n' not in stripped:
            result_lines.append(block)
            return
        # Skip non-math bullets
        if stripped.startswith('- ') and not needs_conversion(stripped):
            result_lines.append(block)
            return

        if needs_conversion(block):
            result = convert_block(block)
            if result is None:
                removed_count += 1
                return
            else:
                converted_count += 1
                result_lines.append(result)
        else:
            result_lines.append(block)

    for line in lines:
        if line.strip() == '':
            flush_block()
            result_lines.append(line)
        else:
            pending_block.append(line)

    flush_block()

    print(f"  Converted: {converted_count} blocks, Removed: {removed_count} noise blocks")
    return '\n'.join(result_lines)


# ═══════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <markdown-path>")
        sys.exit(1)

    md_path = sys.argv[1]

    print(f"Reading: {md_path}")
    with open(md_path, 'r', encoding='utf-8') as f:
        original = f.read()

    print(f"Processing ({len(original)} chars, rule-based, no API needed)...")
    processed = process_markdown(original)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(processed)

    print(f"Done. Written to: {md_path}")


if __name__ == '__main__':
    main()
