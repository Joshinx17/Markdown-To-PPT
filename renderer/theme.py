"""
theme.py
────────
Single source of truth for all visual design tokens used throughout the
renderer. Changing values here affects every slide uniformly.

Modern Design Language: "Meridian Professional"
  • Premium navy + bright white + vibrant teal accent + subtle gradients
  • Modern sans-serif (Segoe UI / Aptos — Office default, universal)
  • Professional spacing, modern color harmony, accessibility
  • Enhanced shadows, rounded corners for modern aesthetics
"""

from __future__ import annotations

from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

# ─── Slide dimensions (widescreen 16:9) ──────────────────────────────────────
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# ─── Colour palette ─── Modern & Professional ──────────────────────────────────
# Primary
NAVY_DARK   = RGBColor(0x0F, 0x15, 0x35)   # #0F1535 – deepest navy for headers
NAVY        = RGBColor(0x0D, 0x1E, 0x42)   # #0D1E42 – primary navy
NAVY_LIGHT  = RGBColor(0x2D, 0x5A, 0x8C)   # #2D5A8C – lighter navy for accents

# Accent - Modern Teal (replacing gold for fresh, professional look)
TEAL        = RGBColor(0x00, 0x9E, 0xA6)   # #009EA6 – primary teal accent
TEAL_LIGHT  = RGBColor(0x4D, 0xAD, 0xB3)   # #4DADB3 – light teal
TEAL_BRIGHT = RGBColor(0x00, 0xD4, 0xD4)   # #00D4D4 – bright teal

# Secondary Accent (for variety in data viz)
ORANGE      = RGBColor(0xEA, 0x58, 0x0C)   # #EA580C – warm accent
EMERALD     = RGBColor(0x05, 0x96, 0x69)   # #059669 – secondary green

# Content & Backgrounds
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
OFF_WHITE   = RGBColor(0xF7, 0xF8, 0xFC)   # slide background (subtle blue tint)
CARD_BG     = RGBColor(0xEC, 0xF6, 0xF7)   # card background (teal-tinted)
CARD_BORDER = RGBColor(0x00, 0x9E, 0xA6)   # teal border
BORDER      = RGBColor(0xC1, 0xCF, 0xDB)   # light gray divider
SHADOW_COLOR = RGBColor(0x00, 0x00, 0x00)  # for drop shadows

TEXT_DARK   = RGBColor(0x0F, 0x15, 0x35)   # #0F1535 – headings (deep navy)
TEXT_BODY   = RGBColor(0x37, 0x45, 0x6A)   # #37456A – body text
TEXT_MUTED  = RGBColor(0x73, 0x80, 0x98)   # #738098 – captions

# Chart / data colours (professional, accessible, harmonious)
CHART_COLORS = [
    RGBColor(0x00, 0x9E, 0xA6),   # teal
    RGBColor(0x0D, 0x1E, 0x42),   # navy
    RGBColor(0xEA, 0x58, 0x0C),   # orange
    RGBColor(0x05, 0x96, 0x69),   # emerald
    RGBColor(0x7C, 0x3A, 0xED),   # purple
    RGBColor(0x2D, 0x5A, 0x8C),   # light navy
    RGBColor(0x06, 0x91, 0xB2),   # cyan
    RGBColor(0xDB, 0x27, 0x77),   # rose
]

# ─── Typography ─── Modern sans-serif ──────────────────────────────────────────
FONT_HEADING  = 'Segoe UI'      # modern default Office font
FONT_BODY     = 'Segoe UI'      # consistent throughout
FONT_MONO     = 'Consolas'      # for code

# Font sizes (in points) – enhanced hierarchy
SIZE_TITLE_MAIN  = Pt(48)    # main title – larger, bolder
SIZE_TITLE_SUB   = Pt(24)    # subtitle
SIZE_SLIDE_TITLE = Pt(28)    # content slide headers – larger
SIZE_H2          = Pt(22)
SIZE_H3          = Pt(18)
SIZE_BODY        = Pt(16)    # body text – slightly tighter line-height
SIZE_BODY_SM     = Pt(13)
SIZE_CAPTION     = Pt(11)
SIZE_FOOTER      = Pt(10)

# ─── Layout geometry ───────────────────────────────────────────────────────────
HEADER_H    = Inches(1.15)   # header bar height
FOOTER_H    = Inches(0.40)   # bottom bar height
FOOTER_Y    = SLIDE_H - FOOTER_H
MARGIN_L    = Inches(0.55)
MARGIN_R    = Inches(0.55)
CONTENT_X   = Inches(0.55)
CONTENT_Y   = HEADER_H + Inches(0.25)
CONTENT_W   = SLIDE_W - MARGIN_L - MARGIN_R
CONTENT_H   = FOOTER_Y - CONTENT_Y - Inches(0.15)
# ─── Grid & Alignment System ───────────────────────────────────────────────────
GRID_UNIT = Inches(0.125)  # 1/8 inch grid for fine alignment
PADDING_INNER = Inches(0.1)  # inside elements
SPACING_ELEMENTS = Inches(0.15)  # between elements

def snap_to_grid(value):
    """Snap a position/dimension to the nearest grid unit."""
    return round(value / GRID_UNIT) * GRID_UNIT
# ─── Modern design elements ─────────────────────────────────────────────────────
ACCENT_BAR_W     = Inches(0.08)   # teal accent stripe width
BORDER_RADIUS    = Pt(8)          # rounded corners for modern look
SHADOW_BLUR      = Pt(4)          # shadow blur radius
SHADOW_DISTANCE  = Pt(2)          # shadow offset
LINE_WIDTH_THIN  = Pt(1.0)        # border widths
LINE_WIDTH_MED   = Pt(1.5)
LINE_WIDTH_THICK = Pt(2.5)
