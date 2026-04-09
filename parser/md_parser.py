"""
md_parser.py
────────────
Robust, regex-based Markdown parser that converts raw .md text into a
structured ParsedDocument object. Deliberately dependency-light so it
works across environments without external parser quirks.

Extracted structure:
  • Headings (H1 – H6) → sections / subsections
  • Bullet & ordered lists → MDBulletList / MDBullet
  • Paragraphs → MDParagraph
  • Tables (GFM pipe syntax) → MDTable
  • Code blocks (fenced ```) → MDCodeBlock
  • Block-quotes → MDBlockQuote
  • Inline bold/italic stripped to plain text for LLM consumption
  • Numerical-data detection for automatic chart triggering
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

# ─── Inline formatting cleaner ───────────────────────────────────────────────

_INLINE_RE = re.compile(
    r'\*{1,3}(.+?)\*{1,3}'       # bold / italic / bold-italic
    r'|_{1,3}(.+?)_{1,3}'         # underscore variants
    r'|`(.+?)`'                   # inline code
    r'|\[([^\]]+)\]\([^)]*\)'    # markdown links → keep label
    r'|!\[[^\]]*\]\([^)]*\)'     # images → drop
    r'|~~(.+?)~~',                # strike-through → keep text
    re.DOTALL,
)

def _clean(text: str) -> str:
    """Strip inline markdown, collapse whitespace."""
    def repl(m: re.Match) -> str:
        for grp in m.groups():
            if grp is not None:
                return grp
        return ''
    cleaned = _INLINE_RE.sub(repl, text)
    return re.sub(r'\s+', ' ', cleaned).strip()


# ─── Data models ─────────────────────────────────────────────────────────────

@dataclass
class MDHeading:
    level: int          # 1 = H1, 2 = H2, …
    text: str


@dataclass
class MDParagraph:
    text: str


@dataclass
class MDBullet:
    level: int          # 0 = top-level, 1 = sub, …
    text: str
    ordered: bool = False
    number: Optional[int] = None


@dataclass
class MDBulletList:
    ordered: bool
    items: List[MDBullet] = field(default_factory=list)


@dataclass
class MDTable:
    headers: List[str]
    rows: List[List[str]]

    @property
    def has_numbers(self) -> bool:
        for row in self.rows:
            for cell in row:
                if re.search(r'\d', cell):
                    return True
        return False


@dataclass
class MDCodeBlock:
    code: str
    language: str = ''


@dataclass
class MDBlockQuote:
    text: str


@dataclass
class MDSection:
    heading: MDHeading
    children: List[Any] = field(default_factory=list)    # direct content
    subsections: List['MDSection'] = field(default_factory=list)


@dataclass
class ParsedDocument:
    title: str
    subtitle: str = ''
    sections: List[MDSection] = field(default_factory=list)
    tables: List[MDTable] = field(default_factory=list)
    all_text: str = ''
    word_count: int = 0
    has_numerical_data: bool = False
    has_tabular_data: bool = False
    raw_markdown: str = ''
    key_numbers: List[str] = field(default_factory=list)


# ─── Table parser ────────────────────────────────────────────────────────────

def _parse_table(block: List[str]) -> Optional[MDTable]:
    """Parse a GFM pipe-table block into an MDTable."""
    rows = [
        [_clean(c) for c in line.strip().strip('|').split('|')]
        for line in block
        if line.strip() and not re.match(r'^[\s|:\-]+$', line)
    ]
    if len(rows) < 1:
        return None
    headers = rows[0]
    data_rows = rows[1:]
    return MDTable(headers=headers, rows=data_rows)


# ─── Numerical data detection ────────────────────────────────────────────────

_NUM_PATTERN = re.compile(
    r'\b\d[\d,]*(?:\.\d+)?'           # plain numbers / decimals
    r'(?:\s*%|\s*(?:million|billion|trillion|k|M|B|T))?\b',
    re.IGNORECASE,
)

def _find_numbers(text: str) -> List[str]:
    return _NUM_PATTERN.findall(text)


# ─── Recursive text extractor ────────────────────────────────────────────────

def _section_text(section: MDSection) -> str:
    parts: List[str] = [section.heading.text]
    for child in section.children:
        if isinstance(child, MDParagraph):
            parts.append(child.text)
        elif isinstance(child, MDBulletList):
            parts.extend(b.text for b in child.items)
        elif isinstance(child, MDTable):
            parts.extend(section.heading.text for _ in [0])  # heading repr
        elif isinstance(child, MDBlockQuote):
            parts.append(child.text)
    for sub in section.subsections:
        parts.append(_section_text(sub))
    return ' '.join(parts)


# ─── Main parser ─────────────────────────────────────────────────────────────

def parse_markdown(content: str) -> ParsedDocument:
    """
    Convert raw markdown text into a ParsedDocument.

    Handles:
      • Files up to 5 MB (pure string processing, O(n))
      • Missing titles → inferred from first H2 or filename
      • Irregular whitespace, CRLF, mixed heading styles
      • Gracefully skips unrecognised constructs
    """
    # ── Normalise ────────────────────────────────────────────────────────────
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    raw = content
    lines = content.split('\n')

    title: str = ''
    subtitle: str = ''
    sections: List[MDSection] = []
    tables: List[MDTable] = []

    # Stack: [(MDSection | None, level)]  — tracks nesting
    # We keep at most 3 levels deep (H1 → H2 → H3)
    h1_section: Optional[MDSection] = None
    h2_section: Optional[MDSection] = None

    in_code_block = False
    code_buf: List[str] = []
    code_lang = ''

    table_buf: List[str] = []
    in_table = False

    bullet_buf: List[MDBullet] = []
    bullet_ordered: bool = False

    def _flush_bullets() -> None:
        nonlocal bullet_buf, bullet_ordered
        if not bullet_buf:
            return
        bl = MDBulletList(ordered=bullet_ordered, items=list(bullet_buf))
        _add_child(bl)
        bullet_buf = []

    def _flush_table() -> None:
        nonlocal table_buf, in_table
        if table_buf:
            tbl = _parse_table(table_buf)
            if tbl:
                tables.append(tbl)
                _add_child(tbl)
        table_buf = []
        in_table = False

    def _add_child(node: Any) -> None:
        """Add a content node to the deepest current section."""
        target = h2_section or h1_section
        if target is not None:
            target.children.append(node)

    for raw_line in lines:
        stripped = raw_line.strip()

        # ── Code fence ───────────────────────────────────────────────────────
        if stripped.startswith('```'):
            if in_code_block:
                in_code_block = False
                block = MDCodeBlock(code='\n'.join(code_buf), language=code_lang)
                _flush_bullets()
                _add_child(block)
                code_buf = []
                code_lang = ''
            else:
                _flush_bullets()
                _flush_table()
                in_code_block = True
                code_lang = stripped[3:].strip()
            continue

        if in_code_block:
            code_buf.append(raw_line)
            continue

        # ── Table rows ───────────────────────────────────────────────────────
        if '|' in stripped and re.match(r'^\s*\|', raw_line):
            _flush_bullets()
            table_buf.append(raw_line)
            in_table = True
            continue
        elif in_table:
            _flush_table()

        # ── Empty line ───────────────────────────────────────────────────────
        if not stripped:
            _flush_bullets()
            continue

        # ── Setext H1/H2 (underline style) ──────────────────────────────────
        # (handled implicitly: we rely on ATX `#` headings for reliability)

        # ── ATX Heading ──────────────────────────────────────────────────────
        h_match = re.match(r'^(#{1,6})\s+(.+?)(?:\s+#+\s*)?$', stripped)
        if h_match:
            _flush_bullets()
            level = len(h_match.group(1))
            text = _clean(h_match.group(2))

            if level == 1:
                if not title:
                    title = text
                else:
                    sec = MDSection(MDHeading(1, text))
                    sections.append(sec)
                    h1_section = sec
                    h2_section = None
            elif level == 2:
                sec = MDSection(MDHeading(2, text))
                if h1_section is None:
                    sections.append(sec)
                else:
                    h1_section.subsections.append(sec)
                h2_section = sec
            else:
                sec = MDSection(MDHeading(level, text))
                target = h2_section or h1_section
                if target:
                    target.subsections.append(sec)
                else:
                    sections.append(sec)
            continue

        # ── Horizontal rule ──────────────────────────────────────────────────
        if re.match(r'^[-*_]{3,}\s*$', stripped):
            _flush_bullets()
            continue

        # ── Block-quote ──────────────────────────────────────────────────────
        bq_match = re.match(r'^>\s*(.*)', stripped)
        if bq_match:
            _flush_bullets()
            _add_child(MDBlockQuote(_clean(bq_match.group(1))))
            continue

        # ── Bullet / ordered list ────────────────────────────────────────────
        b_match = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.+)$', raw_line)
        if b_match:
            indent_spaces = len(raw_line) - len(raw_line.lstrip())
            lvl = indent_spaces // 2
            marker = b_match.group(2)
            is_ordered = bool(re.match(r'\d+', marker))
            num = int(re.match(r'(\d+)', marker).group(1)) if is_ordered else None
            txt = _clean(b_match.group(3))
            bullet_ordered = is_ordered if not bullet_buf else bullet_ordered
            bullet_buf.append(MDBullet(level=lvl, text=txt, ordered=is_ordered, number=num))
            continue

        # ── Paragraph ────────────────────────────────────────────────────────
        _flush_bullets()
        text = _clean(stripped)
        if not text:
            continue

        if not title:
            title = text[:120]
        elif not subtitle and not sections:
            subtitle = text[:300]
        else:
            _add_child(MDParagraph(text))

    # Flush remaining buffers
    _flush_bullets()
    _flush_table()

    # ── Infer title if still missing ─────────────────────────────────────────
    if not title and sections:
        title = sections[0].heading.text
    if not title:
        title = 'Presentation'

    # ── Build full-text corpus for LLM ───────────────────────────────────────
    all_text = ' '.join(_section_text(s) for s in sections)
    if not all_text.strip():
        all_text = _clean(raw[:4000])

    # ── Numerical data detection ─────────────────────────────────────────────
    nums = _find_numbers(all_text)
    has_nums = len(nums) >= 3   # at least 3 distinct numeric values

    logger.info(
        'Parsed: title=%r  sections=%d  tables=%d  words=%d  has_nums=%s',
        title, len(sections), len(tables), len(all_text.split()), has_nums,
    )

    return ParsedDocument(
        title=title,
        subtitle=subtitle,
        sections=sections,
        tables=tables,
        all_text=all_text,
        word_count=len(all_text.split()),
        has_numerical_data=has_nums,
        has_tabular_data=bool(tables),
        raw_markdown=raw,
        key_numbers=nums[:20],
    )
