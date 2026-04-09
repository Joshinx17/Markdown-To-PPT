"""
prompts.py
──────────
LLM prompt templates for the slide-structuring agent.
Separated from llm_structurer.py to make them easy to iterate on without
touching pipeline logic.
"""

from __future__ import annotations

# ─── JSON schema reference embedded in the prompt ────────────────────────────

SLIDE_SCHEMA = """
{
  "presentation_title": "string",
  "total_slides": integer (10-15),
  "slides": [
    // ── TITLE (always slide 1) ────────────────────────────────────────────
    {
      "slide_number": 1,
      "type": "TITLE",
      "title": "Full presentation title",
      "subtitle": "One-line subtitle or tagline",
      "author": "Author name if present",
      "date": "Date string if present",
      "speaker_notes": "..."
    },
    // ── AGENDA (slide 2) ──────────────────────────────────────────────────
    {
      "slide_number": 2,
      "type": "AGENDA",
      "title": "Agenda",
      "bullets": [{"text": "Section name", "level": 0}],
      "speaker_notes": "..."
    },
    // ── EXECUTIVE SUMMARY (slide 3) ───────────────────────────────────────
    {
      "slide_number": 3,
      "type": "EXECUTIVE_SUMMARY",
      "title": "Executive Summary",
      "summary_points": [
        {"icon": "📊", "title": "Key insight title", "description": "2-sentence description"},
        {"icon": "🚀", "title": "Key insight title", "description": "..."},
        {"icon": "💡", "title": "Key insight title", "description": "..."}
      ],
      "speaker_notes": "..."
    },
    // ── SECTION DIVIDER ───────────────────────────────────────────────────
    {
      "slide_number": 4,
      "type": "SECTION_DIVIDER",
      "title": "Section Name",
      "subtitle": "Brief section description (optional)",
      "speaker_notes": "..."
    },
    // ── CONTENT BULLETS ───────────────────────────────────────────────────
    {
      "slide_number": 5,
      "type": "CONTENT_BULLETS",
      "title": "Slide Title",
      "bullets": [
        {"text": "Main point (max 15 words)", "level": 0},
        {"text": "Sub-point", "level": 1}
      ],
      "speaker_notes": "..."
    },
    // ── TWO COLUMN ────────────────────────────────────────────────────────
    {
      "slide_number": 6,
      "type": "TWO_COLUMN",
      "title": "Slide Title",
      "left_title": "Left Column", "left_bullets": ["point", "point"],
      "right_title": "Right Column", "right_bullets": ["point", "point"],
      "speaker_notes": "..."
    },
    // ── CHART BAR ─────────────────────────────────────────────────────────
    {
      "slide_number": 7,
      "type": "CHART_BAR",
      "title": "Chart Slide Title",
      "chart_title": "Descriptive chart title",
      "categories": ["Cat A", "Cat B", "Cat C"],
      "series": [{"name": "Series 1", "values": [10.5, 20.0, 15.3]}],
      "chart_caption": "Source / context sentence",
      "speaker_notes": "..."
    },
    // ── CHART PIE ─────────────────────────────────────────────────────────
    {
      "slide_number": 8,
      "type": "CHART_PIE",
      "title": "Distribution Title",
      "chart_title": "Pie chart title",
      "categories": ["A", "B", "C"],
      "values": [40.0, 35.0, 25.0],
      "chart_caption": "Source / context",
      "speaker_notes": "..."
    },
    // ── CHART LINE ────────────────────────────────────────────────────────
    {
      "slide_number": 9,
      "type": "CHART_LINE",
      "title": "Trend Title",
      "chart_title": "Line chart title",
      "categories": ["2020", "2021", "2022"],
      "series": [{"name": "Metric", "values": [100, 120, 145]}],
      "chart_caption": "Source / context",
      "speaker_notes": "..."
    },
    // ── TABLE ─────────────────────────────────────────────────────────────
    {
      "slide_number": 10,
      "type": "TABLE",
      "title": "Table Title",
      "headers": ["Column 1", "Column 2", "Column 3"],
      "rows": [["r1c1", "r1c2", "r1c3"], ["r2c1", "r2c2", "r2c3"]],
      "speaker_notes": "..."
    },
    // ── PROCESS FLOW ──────────────────────────────────────────────────────
    {
      "slide_number": 11,
      "type": "PROCESS_FLOW",
      "title": "Process Title",
      "steps": [
        {"title": "Step 1", "description": "Brief description"},
        {"title": "Step 2", "description": "Brief description"}
      ],
      "speaker_notes": "..."
    },
    // ── TIMELINE ──────────────────────────────────────────────────────────
    {
      "slide_number": 12,
      "type": "TIMELINE",
      "title": "Timeline Title",
      "events": [
        {"date": "Q1 2024", "title": "Event name", "description": "Brief description"}
      ],
      "speaker_notes": "..."
    },
    // ── CONCLUSION (always last slide) ────────────────────────────────────
    {
      "slide_number": 13,
      "type": "CONCLUSION",
      "title": "Key Takeaways",
      "takeaways": [
        {"number": 1, "title": "Takeaway headline", "description": "2-sentence elaboration"},
        {"number": 2, "title": "Takeaway headline", "description": "..."}
      ],
      "speaker_notes": "..."
    }
  ]
}
"""

# ─── Main structuring prompt ─────────────────────────────────────────────────

STRUCTURE_PROMPT = """You are an expert presentation strategist and content designer.
Your task is to transform a Markdown document into a compelling slide deck blueprint.

════════════════════════════════════════════
MANDATORY SLIDE STRUCTURE (in this order):
════════════════════════════════════════════
1. TITLE slide (slide 1) — always present
2. AGENDA slide (slide 2) — always present
3. EXECUTIVE_SUMMARY slide (slide 3) — always present, 3-5 key insights
4. SECTION_DIVIDER slides — one per major topic/section
5. CONTENT_BULLETS, TWO_COLUMN, CHART_*, TABLE, PROCESS_FLOW, TIMELINE slides — as appropriate
6. CONCLUSION slide (last slide) — always present

════════════════════════════════════════════
CONSTRAINTS:
════════════════════════════════════════════
• Total slides: {min_slides} – {max_slides}
• Maximum 5 bullet points per CONTENT_BULLETS slide
• Maximum 15 words per bullet point
• NO walls of text — break long content across multiple slides
• Has numerical data: {has_numbers}
• Has tabular data: {has_tables}

════════════════════════════════════════════
CONTENT RULES:
════════════════════════════════════════════
• Generate CHART_BAR / CHART_PIE / CHART_LINE slides ONLY if has_numbers=True
  and you can extract real values from the markdown. Do NOT fabricate numbers.
• Generate TABLE slides ONLY if has_tables=True and real tabular data exists.
• Use PROCESS_FLOW for any sequential steps, workflows, or processes.
• Use TIMELINE for any chronological events, roadmaps, or milestones.
• Use TWO_COLUMN for comparisons, pros/cons, or before/after content.
• Use SECTION_DIVIDER between major topic areas (but not before every single slide).
• Use icons (single emoji) for EXECUTIVE_SUMMARY summary_points.
• Speaker notes should expand on the slide content with ~2-3 sentences.

════════════════════════════════════════════
MARKDOWN INPUT:
════════════════════════════════════════════
{markdown_content}

════════════════════════════════════════════
OUTPUT REQUIREMENTS:
════════════════════════════════════════════
Return ONLY valid JSON matching the schema below. No markdown fences, no explanation.
{schema}
"""

# ─── Fallback prompt (shorter, for retry on parse failure) ───────────────────

FALLBACK_PROMPT = """Convert this markdown to a presentation blueprint JSON.
Return ONLY valid JSON with {min_slides}-{max_slides} slides.
Required slide order: TITLE → AGENDA → EXECUTIVE_SUMMARY → content slides → CONCLUSION.
Use types: TITLE, AGENDA, EXECUTIVE_SUMMARY, SECTION_DIVIDER, CONTENT_BULLETS, TWO_COLUMN,
CHART_BAR, CHART_PIE, CHART_LINE, TABLE, PROCESS_FLOW, TIMELINE, CONCLUSION.

Markdown:
{markdown_content}

JSON Schema:
{schema}
"""
