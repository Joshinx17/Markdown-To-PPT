"""
slide_types.py
──────────────
Slide-blueprint data-model.  Every slide the LLM produces maps to one of the
SlideType variants below.  The Pydantic-free dataclasses are intentionally
plain so they serialise cleanly to / from JSON.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ─── Slide type catalogue ─────────────────────────────────────────────────────

class SlideType(str, Enum):
    TITLE              = 'TITLE'
    AGENDA             = 'AGENDA'
    EXECUTIVE_SUMMARY  = 'EXECUTIVE_SUMMARY'
    SECTION_DIVIDER    = 'SECTION_DIVIDER'
    CONTENT_BULLETS    = 'CONTENT_BULLETS'
    CONTENT_TEXT       = 'CONTENT_TEXT'
    TWO_COLUMN         = 'TWO_COLUMN'
    CHART_BAR          = 'CHART_BAR'
    CHART_PIE          = 'CHART_PIE'
    CHART_LINE         = 'CHART_LINE'
    CHART_AREA         = 'CHART_AREA'
    TABLE              = 'TABLE'
    PROCESS_FLOW       = 'PROCESS_FLOW'
    TIMELINE           = 'TIMELINE'
    COMPARISON         = 'COMPARISON'
    CONCLUSION         = 'CONCLUSION'
    QUOTE              = 'QUOTE'


# ─── Per-type payload dataclasses ────────────────────────────────────────────

@dataclass
class SummaryPoint:
    icon: str           # single emoji or short symbol
    title: str
    description: str


@dataclass
class BulletItem:
    text: str
    level: int = 0      # 0 = top-level, 1 = sub-bullet


@dataclass
class ChartSeries:
    name: str
    values: List[float]


@dataclass
class ProcessStep:
    title: str
    description: str = ''


@dataclass
class TimelineEvent:
    date: str
    title: str
    description: str = ''


@dataclass
class Takeaway:
    number: int
    title: str
    description: str = ''


@dataclass
class ComparisonItem:
    label: str
    points: List[str] = field(default_factory=list)


# ─── Master blueprint ─────────────────────────────────────────────────────────

@dataclass
class SlideBlueprint:
    slide_number: int
    type: SlideType
    title: str
    speaker_notes: str = ''

    # ── TITLE
    subtitle: str = ''
    author: str = ''
    date: str = ''

    # ── AGENDA / CONTENT_BULLETS
    bullets: List[BulletItem] = field(default_factory=list)

    # ── EXECUTIVE_SUMMARY
    summary_points: List[SummaryPoint] = field(default_factory=list)

    # ── CONTENT_TEXT / QUOTE
    body_text: str = ''

    # ── TWO_COLUMN / COMPARISON
    left_title: str = ''
    left_bullets: List[str] = field(default_factory=list)
    right_title: str = ''
    right_bullets: List[str] = field(default_factory=list)
    comparison_items: List[ComparisonItem] = field(default_factory=list)

    # ── CHART_*
    chart_title: str = ''
    categories: List[str] = field(default_factory=list)
    series: List[ChartSeries] = field(default_factory=list)
    values: List[float] = field(default_factory=list)     # for PIE
    chart_caption: str = ''

    # ── TABLE
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)

    # ── PROCESS_FLOW
    steps: List[ProcessStep] = field(default_factory=list)

    # ── TIMELINE
    events: List[TimelineEvent] = field(default_factory=list)

    # ── CONCLUSION
    takeaways: List[Takeaway] = field(default_factory=list)


@dataclass
class PresentationBlueprint:
    presentation_title: str
    total_slides: int
    slides: List[SlideBlueprint]


# ─── JSON → Blueprint deserialiser ───────────────────────────────────────────

def blueprint_from_dict(data: Dict[str, Any]) -> PresentationBlueprint:
    """Convert the LLM's JSON dict into strongly-typed blueprint objects."""
    slides: List[SlideBlueprint] = []

    for s in data.get('slides', []):
        stype_raw = s.get('type', 'CONTENT_BULLETS').upper()
        try:
            stype = SlideType(stype_raw)
        except ValueError:
            stype = SlideType.CONTENT_BULLETS

        bp = SlideBlueprint(
            slide_number=int(s.get('slide_number', len(slides) + 1)),
            type=stype,
            title=s.get('title', ''),
            speaker_notes=s.get('speaker_notes', ''),
        )

        # --TITLE
        bp.subtitle = s.get('subtitle', '')
        bp.author   = s.get('author', '')
        bp.date     = s.get('date', '')

        # --BULLETS
        raw_bullets = s.get('bullets', []) or s.get('items', [])
        for b in raw_bullets:
            if isinstance(b, str):
                bp.bullets.append(BulletItem(text=b, level=0))
            elif isinstance(b, dict):
                bp.bullets.append(BulletItem(
                    text=b.get('text', str(b)),
                    level=int(b.get('level', 0)),
                ))

        # --EXECUTIVE SUMMARY
        for sp in s.get('summary_points', []):
            if isinstance(sp, dict):
                bp.summary_points.append(SummaryPoint(
                    icon=sp.get('icon', '●'),
                    title=sp.get('title', ''),
                    description=sp.get('description', ''),
                ))

        # --BODY TEXT
        bp.body_text = s.get('body_text', '') or s.get('text', '')

        # --TWO COLUMN
        bp.left_title   = s.get('left_title', '')
        bp.right_title  = s.get('right_title', '')
        bp.left_bullets = [str(x) for x in s.get('left_bullets', [])]
        bp.right_bullets = [str(x) for x in s.get('right_bullets', [])]

        # --COMPARISON
        for ci in s.get('comparison_items', []):
            if isinstance(ci, dict):
                bp.comparison_items.append(ComparisonItem(
                    label=ci.get('label', ''),
                    points=[str(p) for p in ci.get('points', [])],
                ))

        # --CHART
        bp.chart_title  = s.get('chart_title', bp.title)
        bp.categories   = [str(c) for c in s.get('categories', [])]
        bp.chart_caption = s.get('chart_caption', '')
        bp.values = [float(v) for v in s.get('values', [])
                     if str(v).replace('.', '', 1).replace('-', '', 1).isdigit() or isinstance(v, (int, float))]
        for sr in s.get('series', []):
            if isinstance(sr, dict):
                try:
                    vals = [float(v) for v in sr.get('values', [])]
                    bp.series.append(ChartSeries(name=sr.get('name', 'Series'), values=vals))
                except (TypeError, ValueError):
                    pass

        # --TABLE
        bp.headers = [str(h) for h in s.get('headers', [])]
        bp.rows    = [[str(c) for c in row] for row in s.get('rows', [])]

        # --PROCESS FLOW
        for step in s.get('steps', []):
            if isinstance(step, dict):
                bp.steps.append(ProcessStep(
                    title=step.get('title', ''),
                    description=step.get('description', ''),
                ))
            elif isinstance(step, str):
                bp.steps.append(ProcessStep(title=step))

        # --TIMELINE
        for ev in s.get('events', []):
            if isinstance(ev, dict):
                bp.events.append(TimelineEvent(
                    date=str(ev.get('date', '')),
                    title=ev.get('title', ''),
                    description=ev.get('description', ''),
                ))

        # --CONCLUSION
        for i, tk in enumerate(s.get('takeaways', []), 1):
            if isinstance(tk, dict):
                bp.takeaways.append(Takeaway(
                    number=tk.get('number', i),
                    title=tk.get('title', ''),
                    description=tk.get('description', ''),
                ))
            elif isinstance(tk, str):
                bp.takeaways.append(Takeaway(number=i, title=tk))

        slides.append(bp)

    return PresentationBlueprint(
        presentation_title=data.get('presentation_title', 'Presentation'),
        total_slides=int(data.get('total_slides', len(slides))),
        slides=slides,
    )
