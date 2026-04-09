from __future__ import annotations

import re
from typing import Iterable, List, Sequence

from parser.md_parser import MDBulletList, MDParagraph, MDSection, MDTable, ParsedDocument
from structurer.slide_types import (
    BulletItem,
    ChartSeries,
    ComparisonItem,
    PresentationBlueprint,
    ProcessStep,
    SlideBlueprint,
    SlideType,
    SummaryPoint,
    Takeaway,
    TimelineEvent,
)


_NUMBER_RE = re.compile(r'-?\d[\d,]*(?:\.\d+)?')
_YEAR_RE = re.compile(r'\b(19|20)\d{2}\b')


def build_rule_based_blueprint(doc: ParsedDocument, target: int) -> PresentationBlueprint:
    slides: list[SlideBlueprint] = []

    slides.append(_title_slide(doc))
    slides.append(_agenda_slide(doc))
    slides.append(_executive_summary_slide(doc))

    sections = [
        s
        for s in doc.sections
        if s.heading.text.lower() not in {'conclusion', 'executive summary'}
    ]
    current_number = 4
    visual_streak = 0

    for index, section in enumerate(sections):
        if len(slides) >= target - 1:
            break

        if index in (0, max(1, len(sections) // 2)) and len(slides) < target - 2:
            slides.append(_section_divider_slide(current_number, section.heading.text))
            current_number += 1

        content_slide = _section_to_slide(section, current_number)
        if content_slide is None:
            continue

        if content_slide.type in _visual_types():
            visual_streak += 1
        else:
            visual_streak = 0

        slides.append(content_slide)
        current_number += 1

        if visual_streak == 0 and len(slides) < target - 1:
            support_slide = _supporting_visual_slide(section, current_number)
            if support_slide is not None:
                slides.append(support_slide)
                current_number += 1
                visual_streak = 1

    if len(slides) < target - 1:
        for table in doc.tables:
            if len(slides) >= target - 1:
                break
            chart_slide = _table_to_chart_slide(table, current_number, 'Data Snapshot')
            if chart_slide is None:
                continue
            slides.append(chart_slide)
            current_number += 1

    slides.append(_conclusion_slide(doc, current_number))
    return PresentationBlueprint(
        presentation_title=doc.title,
        total_slides=len(slides),
        slides=slides,
    )


def optimize_blueprint(
    blueprint: PresentationBlueprint,
    doc: ParsedDocument,
    min_slides: int,
    max_slides: int,
) -> PresentationBlueprint:
    slides = list(blueprint.slides)

    if not slides:
        return build_rule_based_blueprint(doc, (min_slides + max_slides) // 2)

    slides = _ensure_title_and_conclusion(slides, blueprint.presentation_title)
    slides = _trim_bullets(slides)
    slides = _reduce_text_heavy_runs(slides)
    slides = _guarantee_visual_density(slides, doc)

    if len(slides) > max_slides:
        slides = _trim_to_max(slides, max_slides)

    target = max(min_slides, min(max_slides, len(slides)))
    while len(slides) < target:
        filler = _additional_visual(slides, doc, len(slides) + 1)
        if filler is None:
            break
        slides.insert(-1, filler)

    for idx, slide in enumerate(slides, 1):
        slide.slide_number = idx

    return PresentationBlueprint(
        presentation_title=blueprint.presentation_title,
        total_slides=len(slides),
        slides=slides,
    )


def _title_slide(doc: ParsedDocument) -> SlideBlueprint:
    return SlideBlueprint(
        1,
        SlideType.TITLE,
        doc.title,
        subtitle=_shorten(doc.subtitle or _first_sentence(doc.all_text), 110),
        speaker_notes='Open with the headline message and frame the business question this deck answers.',
    )


def _agenda_slide(doc: ParsedDocument) -> SlideBlueprint:
    bullets = [BulletItem(text=_shorten(section.heading.text, 55), level=0) for section in doc.sections[:6]]
    return SlideBlueprint(
        2,
        SlideType.AGENDA,
        'Agenda',
        bullets=bullets or [BulletItem(text='Overview', level=0)],
        speaker_notes='Preview the narrative arc so the audience understands how the story will unfold.',
    )


def _executive_summary_slide(doc: ParsedDocument) -> SlideBlueprint:
    icons = ['AI', 'UP', 'OPS', 'RISK']
    points: list[SummaryPoint] = []

    if doc.key_numbers:
        points.append(
            SummaryPoint(
                icon=icons[0],
                title='Scale of Opportunity',
                description=_shorten(f'The document highlights quantified momentum including {", ".join(doc.key_numbers[:3])}.', 110),
            )
        )

    for section in doc.sections[:3]:
        summary = _best_summary_text(section)
        points.append(
            SummaryPoint(
                icon=icons[len(points) % len(icons)],
                title=_shorten(section.heading.text, 34),
                description=_shorten(summary, 120),
            )
        )
        if len(points) == 4:
            break

    return SlideBlueprint(
        3,
        SlideType.EXECUTIVE_SUMMARY,
        'Executive Summary',
        summary_points=points[:4],
        speaker_notes='Use these cards to cover the strongest signals, then transition into the evidence behind each one.',
    )


def _section_divider_slide(slide_number: int, title: str) -> SlideBlueprint:
    return SlideBlueprint(
        slide_number,
        SlideType.SECTION_DIVIDER,
        _shorten(title, 60),
        subtitle='Key signals, evidence, and strategic implications',
        speaker_notes='Pause briefly here to signal a shift in the story before moving into the next cluster of evidence.',
    )


def _conclusion_slide(doc: ParsedDocument, slide_number: int) -> SlideBlueprint:
    takeaways = [
        Takeaway(i + 1, _shorten(section.heading.text, 48), _shorten(_best_summary_text(section), 100))
        for i, section in enumerate(doc.sections[:4])
    ]
    return SlideBlueprint(
        slide_number,
        SlideType.CONCLUSION,
        'Key Takeaways',
        takeaways=takeaways or [Takeaway(1, doc.title, _shorten(doc.subtitle, 100))],
        speaker_notes='Close on the decisions or actions the audience should take away from the analysis.',
    )


def _section_to_slide(section: MDSection, slide_number: int) -> SlideBlueprint | None:
    title = _shorten(section.heading.text, 60)

    if _is_process_section(section):
        steps = _section_steps(section)
        if len(steps) >= 3:
            return SlideBlueprint(
                slide_number,
                SlideType.PROCESS_FLOW,
                title,
                steps=steps[:6],
                speaker_notes='Walk left to right so the audience sees the sequence rather than reading a dense list.',
            )

    if _is_timeline_section(section):
        events = _section_events(section)
        if len(events) >= 3:
            return SlideBlueprint(
                slide_number,
                SlideType.TIMELINE,
                title,
                events=events[:6],
                speaker_notes='Use the timeline to show progression and where momentum or transition points emerge.',
            )

    table = _first_table(section)
    if table is not None:
        chart_slide = _table_to_chart_slide(table, slide_number, title)
        if chart_slide is not None:
            chart_slide.speaker_notes = 'Lead with the headline trend, then explain the two or three datapoints that matter most.'
            return chart_slide

    if _is_comparison_section(section):
        comparison = _section_comparison(section)
        if len(comparison) >= 2:
            return SlideBlueprint(
                slide_number,
                SlideType.COMPARISON,
                title,
                comparison_items=comparison[:4],
                speaker_notes='Frame the tradeoffs across the columns instead of reading each row verbatim.',
            )

    chart_from_bullets = _bullets_to_chart_slide(section, slide_number)
    if chart_from_bullets is not None:
        chart_from_bullets.title = title
        chart_from_bullets.speaker_notes = 'Use the chart to compare relative magnitude quickly before discussing the implication.'
        return chart_from_bullets

    if len(section.subsections) >= 2:
        left, right = section.subsections[:2]
        return SlideBlueprint(
            slide_number,
            SlideType.TWO_COLUMN,
            title,
            left_title=_shorten(left.heading.text, 28),
            left_bullets=_string_bullets(left)[:4],
            right_title=_shorten(right.heading.text, 28),
            right_bullets=_string_bullets(right)[:4],
            speaker_notes='Use the two columns to compare the two strongest themes without turning them into a wall of bullets.',
        )

    bullets = [BulletItem(text=item, level=0) for item in _string_bullets(section)[:4]]
    if not bullets:
        return None

    return SlideBlueprint(
        slide_number,
        SlideType.CONTENT_BULLETS,
        title,
        bullets=bullets,
        speaker_notes='Keep the verbal explanation richer than the slide; the slide should only carry the strongest anchors.',
    )


def _supporting_visual_slide(section: MDSection, slide_number: int) -> SlideBlueprint | None:
    if len(section.subsections) >= 3:
        items = [
            ComparisonItem(label=_shorten(sub.heading.text, 24), points=_string_bullets(sub)[:3] or [_shorten(_best_summary_text(sub), 48)])
            for sub in section.subsections[:3]
        ]
        return SlideBlueprint(
            slide_number,
            SlideType.COMPARISON,
            _shorten(f'{section.heading.text} Framework', 60),
            comparison_items=items,
            speaker_notes='This supporting framework slide helps the audience compare the categories at a glance.',
        )
    return None


def _additional_visual(slides: Sequence[SlideBlueprint], doc: ParsedDocument, slide_number: int) -> SlideBlueprint | None:
    used_titles = {slide.title for slide in slides}
    for section in doc.sections:
        if section.heading.text in used_titles:
            continue
        candidate = _bullets_to_chart_slide(section, slide_number)
        if candidate is not None:
            candidate.title = _shorten(section.heading.text, 60)
            return candidate
    return None


def _ensure_title_and_conclusion(slides: list[SlideBlueprint], deck_title: str) -> list[SlideBlueprint]:
    if slides[0].type != SlideType.TITLE:
        slides.insert(0, SlideBlueprint(1, SlideType.TITLE, deck_title))
    if slides[-1].type != SlideType.CONCLUSION:
        slides.append(
            SlideBlueprint(
                len(slides) + 1,
                SlideType.CONCLUSION,
                'Key Takeaways',
                takeaways=[Takeaway(1, 'Summary', deck_title)],
            )
        )
    return slides


def _trim_bullets(slides: list[SlideBlueprint]) -> list[SlideBlueprint]:
    for slide in slides:
        if slide.bullets:
            slide.bullets = [BulletItem(text=_tighten_phrase(item.text), level=item.level) for item in slide.bullets[:4]]
        if slide.left_bullets:
            slide.left_bullets = [_tighten_phrase(item) for item in slide.left_bullets[:4]]
        if slide.right_bullets:
            slide.right_bullets = [_tighten_phrase(item) for item in slide.right_bullets[:4]]
        if slide.comparison_items:
            for item in slide.comparison_items:
                item.points = [_tighten_phrase(point) for point in item.points[:4]]
    return slides


def _reduce_text_heavy_runs(slides: list[SlideBlueprint]) -> list[SlideBlueprint]:
    for idx in range(1, len(slides) - 1):
        previous_slide = slides[idx - 1]
        current_slide = slides[idx]
        if (
            previous_slide.type == SlideType.CONTENT_BULLETS
            and current_slide.type == SlideType.CONTENT_BULLETS
            and len(current_slide.bullets) >= 3
        ):
            current_slide.type = SlideType.TWO_COLUMN
            midpoint = max(1, len(current_slide.bullets) // 2)
            current_slide.left_title = 'Priority Themes'
            current_slide.right_title = 'Implications'
            current_slide.left_bullets = [item.text for item in current_slide.bullets[:midpoint]]
            current_slide.right_bullets = [item.text for item in current_slide.bullets[midpoint:]]
            current_slide.bullets = []
    return slides


def _guarantee_visual_density(slides: list[SlideBlueprint], doc: ParsedDocument) -> list[SlideBlueprint]:
    visual_count = sum(1 for slide in slides if slide.type in _visual_types())
    minimum_visual = max(4, len(slides) // 3)
    if visual_count >= minimum_visual:
        return slides

    for idx, slide in enumerate(slides):
        if visual_count >= minimum_visual:
            break
        if slide.type != SlideType.CONTENT_BULLETS or len(slide.bullets) < 3:
            continue
        comparison_items = [
            ComparisonItem(label=f'Point {item_idx + 1}', points=[item.text])
            for item_idx, item in enumerate(slide.bullets[:3])
        ]
        slide.type = SlideType.COMPARISON
        slide.comparison_items = comparison_items
        slide.bullets = []
        visual_count += 1
    return slides


def _trim_to_max(slides: list[SlideBlueprint], max_slides: int) -> list[SlideBlueprint]:
    if len(slides) <= max_slides:
        return slides

    body = slides[1:-1]
    pruned: list[SlideBlueprint] = []
    divider_budget = 1
    for slide in body:
        if len(pruned) >= max_slides - 2:
            break
        if slide.type == SlideType.SECTION_DIVIDER:
            if divider_budget <= 0:
                continue
            divider_budget -= 1
        pruned.append(slide)
    return [slides[0], *pruned[: max_slides - 2], slides[-1]]


def _visual_types() -> set[SlideType]:
    return {
        SlideType.EXECUTIVE_SUMMARY,
        SlideType.TWO_COLUMN,
        SlideType.CHART_BAR,
        SlideType.CHART_PIE,
        SlideType.CHART_LINE,
        SlideType.CHART_AREA,
        SlideType.PROCESS_FLOW,
        SlideType.TIMELINE,
        SlideType.COMPARISON,
        SlideType.CONCLUSION,
    }


def _is_process_section(section: MDSection) -> bool:
    heading = section.heading.text.lower()
    if any(token in heading for token in ('framework', 'roadmap', 'process', 'implementation')):
        return True
    return any(
        sub.heading.text.lower().startswith(('stage', 'phase', 'step', 'quarter', 'year'))
        or re.match(r'^\d+\.', sub.heading.text.strip())
        for sub in section.subsections
    )


def _is_timeline_section(section: MDSection) -> bool:
    heading = section.heading.text.lower()
    if any(token in heading for token in ('timeline', 'trend', 'history', 'roadmap', 'maturity')):
        return True
    text = ' '.join(sub.heading.text for sub in section.subsections)
    return bool(_YEAR_RE.search(text)) or any(re.search(r'\bQ[1-4]\b', sub.heading.text) for sub in section.subsections)


def _is_comparison_section(section: MDSection) -> bool:
    heading = section.heading.text.lower()
    if any(token in heading for token in ('compare', 'comparison', 'build vs', 'versus', 'barrier', 'challenge')):
        return True
    return _comparison_from_table(_first_table(section)) is not None


def _section_steps(section: MDSection) -> list[ProcessStep]:
    steps = []
    for sub in section.subsections[:6]:
        steps.append(ProcessStep(title=_shorten(sub.heading.text.replace('Stage ', ''), 26), description=_shorten(_best_summary_text(sub), 56)))
    if not steps:
        for idx, bullet in enumerate(_string_bullets(section)[:5], 1):
            steps.append(ProcessStep(title=f'Step {idx}', description=_shorten(bullet, 56)))
    return steps


def _section_events(section: MDSection) -> list[TimelineEvent]:
    events = []
    for sub in section.subsections[:6]:
        date_match = _YEAR_RE.search(sub.heading.text) or re.search(r'\bQ[1-4]\b', sub.heading.text)
        label = date_match.group(0) if date_match else sub.heading.text.split(':', 1)[0]
        title = sub.heading.text.split(':', 1)[-1].strip() if ':' in sub.heading.text else sub.heading.text
        events.append(TimelineEvent(date=_shorten(label, 14), title=_shorten(title, 28), description=_shorten(_best_summary_text(sub), 46)))
    return events


def _section_comparison(section: MDSection) -> list[ComparisonItem]:
    from_table = _comparison_from_table(_first_table(section))
    if from_table is not None:
        return from_table

    items = []
    for sub in section.subsections[:3]:
        points = _string_bullets(sub)[:3] or [_shorten(_best_summary_text(sub), 50)]
        items.append(ComparisonItem(label=_shorten(sub.heading.text, 24), points=points))
    return items


def _first_table(section: MDSection) -> MDTable | None:
    for child in section.children:
        if isinstance(child, MDTable):
            return child
    return None


def _table_to_chart_slide(table: MDTable | None, slide_number: int, title: str) -> SlideBlueprint | None:
    if table is None or not table.rows:
        return None

    if _looks_like_time_series(table):
        metric_index = _best_numeric_column(table)
        categories = [row[0] for row in table.rows if row]
        values = [_parse_number(row[metric_index]) for row in table.rows if len(row) > metric_index]
        if categories and all(value is not None for value in values):
            return SlideBlueprint(
                slide_number,
                SlideType.CHART_LINE,
                title,
                chart_title=table.headers[metric_index] if metric_index < len(table.headers) else title,
                categories=categories,
                series=[ChartSeries(name='Trend', values=[float(v) for v in values])],
                chart_caption='Derived directly from the source table to emphasize trajectory rather than raw rows.',
            )

    comparison = _comparison_from_table(table)
    if comparison is not None:
        return SlideBlueprint(
            slide_number,
            SlideType.COMPARISON,
            title,
            comparison_items=comparison,
            speaker_notes='This comparison distills the table into the tradeoffs people actually need to evaluate.',
        )

    categories = []
    values = []
    for row in table.rows[:6]:
        if len(row) < 2:
            continue
        value = _parse_number(row[1])
        if value is None:
            continue
        categories.append(_shorten(row[0], 24))
        values.append(float(value))
    if categories and values:
        return SlideBlueprint(
            slide_number,
            SlideType.CHART_BAR,
            title,
            chart_title=table.headers[1] if len(table.headers) > 1 else title,
            categories=categories,
            series=[ChartSeries(name='Value', values=values)],
            chart_caption='Chart generated from the source data to make the ranking easier to read.',
        )
    return None


def _bullets_to_chart_slide(section: MDSection, slide_number: int) -> SlideBlueprint | None:
    categories = []
    values = []
    for bullet in _all_bullet_texts(section):
        label, value = _split_label_value(bullet)
        if label is None or value is None:
            continue
        categories.append(_shorten(label, 26))
        values.append(float(value))
    if len(categories) < 3:
        return None

    total = sum(values)
    slide_type = SlideType.CHART_PIE if 95 <= total <= 105 else SlideType.CHART_BAR
    slide = SlideBlueprint(slide_number, slide_type, section.heading.text)
    slide.chart_title = _shorten(section.heading.text, 44)
    slide.categories = categories[:6]
    slide.chart_caption = 'Values extracted from labeled bullet points in the source content.'
    if slide_type == SlideType.CHART_PIE:
        slide.values = values[:6]
    else:
        slide.series = [ChartSeries(name='Value', values=values[:6])]
    return slide


def _comparison_from_table(table: MDTable | None) -> list[ComparisonItem] | None:
    if table is None or len(table.headers) < 3:
        return None
    if len(table.headers) > 5:
        return None
    if not any(_parse_number(cell) is not None for row in table.rows for cell in row[1:]):
        return None

    columns = table.headers[1:]
    items = [ComparisonItem(label=_shorten(column, 18), points=[]) for column in columns]
    for row in table.rows[:6]:
        if not row:
            continue
        dimension = _shorten(row[0], 18)
        for idx, cell in enumerate(row[1 : 1 + len(items)]):
            items[idx].points.append(_shorten(f'{dimension}: {cell}', 52))
    return items


def _looks_like_time_series(table: MDTable) -> bool:
    first_col = [row[0] for row in table.rows if row]
    if len(first_col) < 3:
        return False
    return all(_YEAR_RE.search(value) or re.search(r'\bQ[1-4]\b', value) for value in first_col[:4])


def _best_numeric_column(table: MDTable) -> int:
    best_index = 1
    best_score = -1
    max_width = max(len(row) for row in table.rows)
    for idx in range(1, max_width):
        score = sum(1 for row in table.rows if len(row) > idx and _parse_number(row[idx]) is not None)
        if score > best_score:
            best_score = score
            best_index = idx
    return best_index


def _all_bullet_texts(section: MDSection) -> list[str]:
    texts = []
    for bullet_list in _bullet_lists(section):
        texts.extend(item.text for item in bullet_list.items)
    for subsection in section.subsections:
        for bullet_list in _bullet_lists(subsection):
            texts.extend(item.text for item in bullet_list.items)
    return texts


def _bullet_lists(section: MDSection) -> Iterable[MDBulletList]:
    for child in section.children:
        if isinstance(child, MDBulletList):
            yield child


def _string_bullets(section: MDSection) -> list[str]:
    items = _all_bullet_texts(section)
    if items:
        return [_tighten_phrase(item) for item in items]

    paragraphs = [child.text for child in section.children if isinstance(child, MDParagraph)]
    if paragraphs:
        return [_tighten_phrase(paragraph) for paragraph in paragraphs[:4]]

    if section.subsections:
        return [_tighten_phrase(_best_summary_text(sub)) for sub in section.subsections[:4]]

    return []


def _best_summary_text(section: MDSection) -> str:
    for child in section.children:
        if isinstance(child, MDParagraph) and len(child.text.split()) > 6:
            return child.text
    bullet_texts = _all_bullet_texts(section)
    if bullet_texts:
        return bullet_texts[0]
    if section.subsections:
        return section.subsections[0].heading.text
    return section.heading.text


def _first_sentence(text: str) -> str:
    if not text:
        return ''
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return parts[0] if parts else text


def _shorten(text: str, limit: int) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + '…'


def _tighten_phrase(text: str) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    words = text.split()
    if len(words) <= 15:
        return text
    return ' '.join(words[:15]) + '…'


def _split_label_value(text: str) -> tuple[str | None, float | None]:
    if ':' not in text:
        return None, None
    label, raw_value = text.split(':', 1)
    value = _parse_number(raw_value)
    if value is None:
        return None, None
    return label.strip(' -*'), value


def _parse_number(text: str) -> float | None:
    match = _NUMBER_RE.search(text.replace('$', '').replace('A$', ''))
    if not match:
        return None
    try:
        value = float(match.group(0).replace(',', ''))
    except ValueError:
        return None

    lowered = text.lower()
    if 'billion' in lowered or re.search(r'\b\d+(?:\.\d+)?b\b', lowered):
        value *= 1_000
    elif 'million' in lowered or re.search(r'\b\d+(?:\.\d+)?m\b', lowered):
        value *= 1
    return value
