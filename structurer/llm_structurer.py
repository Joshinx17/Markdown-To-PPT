"""
Gemini-powered slide planner with a stronger rule-based fallback and compliance pass.
"""

from __future__ import annotations

import json
import logging
import re
import time as _time
from typing import Any, Dict, Optional

from google import genai
from google.genai import types as genai_types

from parser.md_parser import ParsedDocument
from structurer.prompts import FALLBACK_PROMPT, SLIDE_SCHEMA, STRUCTURE_PROMPT
from structurer.rule_based_designer import build_rule_based_blueprint, optimize_blueprint
from structurer.slide_types import PresentationBlueprint, SlideBlueprint, SlideType, Takeaway, blueprint_from_dict

logger = logging.getLogger(__name__)


_JSON_FENCE_RE = re.compile(r'```(?:json)?\s*(.*?)\s*```', re.DOTALL)


def _make_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def _call_llm(
    client: genai.Client,
    model_name: str,
    prompt: str,
    retries: int = 2,
    base_wait: float = 45.0,
) -> str:
    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.25,
                    max_output_tokens=8192,
                ),
            )
            return response.text.strip()
        except Exception as exc:
            err_str = str(exc)
            is_rate_limit = '429' in err_str or 'RESOURCE_EXHAUSTED' in err_str
            if is_rate_limit and attempt < retries:
                wait = base_wait * (2 ** attempt)
                logger.warning(
                    'Rate limit hit (attempt %d/%d). Waiting %.0fs before retry ...',
                    attempt + 1,
                    retries + 1,
                    wait,
                )
                print(f'  [!] Rate limit hit. Waiting {wait:.0f}s before retry ({attempt + 1}/{retries}) ...')
                _time.sleep(wait)
            else:
                raise
    raise RuntimeError('All Gemini retries exhausted')


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    fence = _JSON_FENCE_RE.search(text)
    candidate = fence.group(1) if fence else text

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    start = candidate.find('{')
    end = candidate.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(candidate[start : end + 1])
        except json.JSONDecodeError:
            pass

    logger.warning('Could not extract JSON from LLM response.')
    return None


def _truncate_markdown(text: str, max_chars: int = 24_000) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + '\n\n... [content truncated for brevity] ...\n\n' + text[-half // 2 :]


def _rule_based_fallback(doc: ParsedDocument, target: int) -> PresentationBlueprint:
    logger.warning('Using rule-based fallback blueprint builder.')
    return build_rule_based_blueprint(doc, target)


def _enforce_invariants(
    blueprint: PresentationBlueprint,
    min_slides: int,
    max_slides: int,
) -> PresentationBlueprint:
    slides = list(blueprint.slides)

    if not slides or slides[0].type != SlideType.TITLE:
        slides.insert(0, SlideBlueprint(1, SlideType.TITLE, blueprint.presentation_title))

    if slides[-1].type != SlideType.CONCLUSION:
        slides.append(
            SlideBlueprint(
                len(slides) + 1,
                SlideType.CONCLUSION,
                'Key Takeaways',
                takeaways=[Takeaway(1, 'Summary', blueprint.presentation_title)],
            )
        )

    if len(slides) > max_slides:
        slides = [slides[0]] + slides[1 : max_slides - 1] + [slides[-1]]

    for index, slide in enumerate(slides, 1):
        slide.slide_number = index

    blueprint.slides = slides
    blueprint.total_slides = len(slides)
    return blueprint


def _finalize(
    blueprint: PresentationBlueprint,
    doc: ParsedDocument,
    min_slides: int,
    max_slides: int,
) -> PresentationBlueprint:
    enforced = _enforce_invariants(blueprint, min_slides, max_slides)
    return optimize_blueprint(enforced, doc, min_slides, max_slides)


def _attach_images_to_slides(
    blueprint: PresentationBlueprint,
    doc: ParsedDocument,
) -> PresentationBlueprint:
    if not doc.images:
        return blueprint

    slides = blueprint.slides
    image_index = 0

    if slides and slides[0].type == SlideType.TITLE:
        slides[0].image_url = doc.images[0].url
        slides[0].image_alt = doc.images[0].alt_text
        image_index = 1

    for bp in slides[image_index:]:
        if image_index >= len(doc.images):
            break
        bp.image_url = doc.images[image_index].url
        bp.image_alt = doc.images[image_index].alt_text
        image_index += 1

    blueprint.slides = slides
    return blueprint


def structure_presentation(
    doc: ParsedDocument,
    api_key: str | None,
    min_slides: int = 10,
    max_slides: int = 15,
    model_name: str = 'gemini-2.0-flash',
) -> PresentationBlueprint:
    target = (min_slides + max_slides) // 2

    if not api_key:
        logger.warning('No Gemini API key supplied; using rule-based fallback blueprint builder.')
        return _attach_images_to_slides(_finalize(_rule_based_fallback(doc, target), doc, min_slides, max_slides), doc)

    md_content = _truncate_markdown(doc.raw_markdown)
    prompt = STRUCTURE_PROMPT.format(
        min_slides=min_slides,
        max_slides=max_slides,
        has_numbers=str(doc.has_numerical_data),
        has_tables=str(doc.has_tabular_data),
        markdown_content=md_content,
        schema=SLIDE_SCHEMA,
    )

    client = _make_client(api_key)
    raw: Optional[Dict[str, Any]] = None

    try:
        logger.info('Calling Gemini (%s) for slide structuring ...', model_name)
        llm_text = _call_llm(client, model_name, prompt)
        raw = _extract_json(llm_text)
    except Exception as exc:
        logger.warning('Gemini call 1 failed: %s', exc)

    if raw is None:
        try:
            logger.info('Retrying with fallback prompt ...')
            fallback_prompt = FALLBACK_PROMPT.format(
                min_slides=min_slides,
                max_slides=max_slides,
                markdown_content=_truncate_markdown(doc.raw_markdown, max_chars=8_000),
                schema=SLIDE_SCHEMA,
            )
            llm_text = _call_llm(client, model_name, fallback_prompt)
            raw = _extract_json(llm_text)
        except Exception as exc:
            logger.warning('Gemini call 2 failed: %s', exc)

    if raw is None:
        return _attach_images_to_slides(_finalize(_rule_based_fallback(doc, target), doc, min_slides, max_slides), doc)

    try:
        blueprint = blueprint_from_dict(raw)
    except Exception as exc:
        logger.warning('Blueprint deserialisation failed: %s - using fallback', exc)
        return _attach_images_to_slides(_finalize(_rule_based_fallback(doc, target), doc, min_slides, max_slides), doc)

    return _attach_images_to_slides(_finalize(blueprint, doc, min_slides, max_slides), doc)
