"""
orchestrator.py
───────────────
Top-level pipeline that wires all modules together with enhanced stability,
error handling, and validation.

Pipeline:
  1. validate_input  → check file size, extension, readability
  2. parse           → md_parser.parse_markdown()
  3. structure       → llm_structurer.structure_presentation()
  4. render          → slide_builder.render_presentation()
  5. validate_pptx   → ensure PPTX integrity
  6. save            → save with optional compression and backup

Each stage logs progress and raises descriptive exceptions on failure.
Enhanced with stability checks, error recovery, and comprehensive validation.
"""

from __future__ import annotations

import logging
import os
import shutil
import time
import threading
from pathlib import Path
from tempfile import NamedTemporaryFile

from parser.md_parser import parse_markdown, ParsedDocument
from structurer.llm_structurer import structure_presentation
from structurer.context_detector import detect_context, DocumentContext
from structurer.slide_types import PresentationBlueprint
from renderer.slide_builder import render_presentation
from renderer.pptx_stabilizer import (
    validate_presentation_object, pre_save_checks,
    post_save_validation, validate_pptx_file
)

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_B  = MAX_FILE_SIZE_MB * 1024 * 1024
DEFAULT_TEMPLATE_CANDIDATES = (
    Path(__file__).parent / 'templates' / 'Slide_Master.pptx',
    Path(__file__).parent / 'templates' / 'Slide Master.pptx',
    Path(__file__).parent / 'templates' / 'slide_master.pptx',
    Path(__file__).parent / 'templates' / 'master.pptx',
    Path(__file__).parent / 'templates' / 'template.pptx',
)

MIN_SLIDES = 10
MAX_SLIDES = 15


# ─── Pipeline stages ──────────────────────────────────────────────────────────

def validate_input(input_path: str) -> Path:
    """
    Validate that the input file:
      • Exists and is readable
      • Has .md extension
      • Is within the 5 MB size limit
    """
    p = Path(input_path).expanduser().resolve()

    if not p.exists():
        raise FileNotFoundError(f'Input file not found: {p}')
    if not p.is_file():
        raise ValueError(f'Not a file: {p}')
    if p.suffix.lower() not in ('.md', '.markdown', '.txt'):
        raise ValueError(
            f'Unsupported file type: {p.suffix}. Expected .md or .markdown'
        )
    size = p.stat().st_size
    if size > MAX_FILE_SIZE_B:
        raise ValueError(
            f'File too large: {size / 1024 / 1024:.1f} MB > {MAX_FILE_SIZE_MB} MB limit'
        )
    if size == 0:
        raise ValueError('Input file is empty.')

    logger.info('Input validated: %s (%.1f KB)', p.name, size / 1024)
    return p


def resolve_template_path(template_path: str | None) -> Path | None:
    """Resolve an explicit or auto-discovered slide master path."""
    candidates = [Path(template_path).expanduser().resolve()] if template_path else list(DEFAULT_TEMPLATE_CANDIDATES)

    for candidate in candidates:
        if candidate.exists() and candidate.is_file() and candidate.suffix.lower() == '.pptx':
            logger.info('Using slide master template: %s', candidate)
            return candidate

    if template_path:
        raise FileNotFoundError(f'Slide master template not found: {template_path}')

    logger.warning('No slide master template found in templates/. Falling back to built-in renderer.')
    return None


def stage_parse(md_path: Path) -> ParsedDocument:
    """Read and parse the markdown file → ParsedDocument."""
    t0 = time.time()
    text = md_path.read_text(encoding='utf-8', errors='replace')
    doc  = parse_markdown(text)
    logger.info(
        'Stage PARSE completed in %.2fs — %d sections, %d words, has_nums=%s',
        time.time() - t0, len(doc.sections), doc.word_count, doc.has_numerical_data,
    )
    return doc


def stage_structure(
    doc: ParsedDocument,
    api_key: str | None,
    min_slides: int = MIN_SLIDES,
    max_slides: int = MAX_SLIDES,
    model_name: str = 'gemini-2.0-flash',
) -> PresentationBlueprint:
    """Call Gemini to produce a PresentationBlueprint."""
    t0 = time.time()
    bp = structure_presentation(
        doc,
        api_key=api_key,
        min_slides=min_slides,
        max_slides=max_slides,
        model_name=model_name,
    )
    logger.info(
        'Stage STRUCTURE completed in %.2fs — %d slides planned',
        time.time() - t0, bp.total_slides,
    )
    return bp


def stage_render(blueprint: PresentationBlueprint, template_path: str | None = None):
    """Render the blueprint to a python-pptx Presentation object."""
    t0 = time.time()
    prs = render_presentation(blueprint, template_path=template_path)
    logger.info(
        'Stage RENDER completed in %.2fs — %d slides built',
        time.time() - t0, len(prs.slides),
    )
    return prs


def stage_save(prs, output_path: str) -> Path:
    """Save the Presentation to the specified .pptx path with validation."""
    out = Path(output_path).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() != '.pptx':
        out = out.with_suffix('.pptx')

    # Pre-save checks
    warnings = pre_save_checks(prs)
    if warnings:
        logger.warning(f'Pre-save warnings: {warnings}')

    # Write to temporary file first for safety
    tmp_path = None
    try:
        with NamedTemporaryFile(suffix='.pptx', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        logger.info(f'Saving to temporary file: {tmp_path}')
        prs.save(str(tmp_path))
        
        # Validate the temporary file exists and has content
        if not tmp_path.exists() or tmp_path.stat().st_size == 0:
            raise ValueError('PPTX file creation failed or is empty')
        
        logger.info(f'Temporary file created: {tmp_path.stat().st_size} bytes')
        
        # Post-save validation of temp file
        logger.info('Running post-save validation on temporary file...')
        post_save_validation(str(tmp_path))
        
        # Move temp file to final destination
        if out.exists():
            backup_path = out.with_stem(out.stem + '.backup')
            shutil.move(str(out), str(backup_path))
            logger.warning('Existing file backed up to: %s', backup_path)
        
        # Use shutil.move() instead of Path.replace() for cross-drive compatibility
        logger.info(f'Moving {tmp_path} to {out}')
        shutil.move(str(tmp_path), str(out))
        
        # Final validation of output file
        logger.info('Running final validation on output file...')
        validate_pptx_file(str(out))
        
        size_kb = out.stat().st_size / 1024
        logger.info('Saved: %s (%.0f KB)', out, size_kb)
            
    except Exception as e:
        logger.error('Failed to save PPTX: %s', str(e))
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception as cleanup_err:
                logger.warning(f'Could not delete temp file: {cleanup_err}')
        raise

    return out


def validate_pptx(prs) -> bool:
    """
    Validate PPTX presentation integrity using comprehensive checks.
    Returns True if valid, raises exception if invalid.
    """
    logger.info('Validating presentation object...')
    return validate_presentation_object(prs)


# ─── Public API ───────────────────────────────────────────────────────────────

def convert(
    input_path: str,
    output_path: str,
    api_key: str | None = None,
    template_path: str | None = None,
    min_slides: int = MIN_SLIDES,
    max_slides: int = MAX_SLIDES,
    model_name: str = 'gemini-2.0-flash',
    verbose: bool = True,
) -> Path:
    """
    Full pipeline: Markdown file → .pptx file with comprehensive error handling.

    Args:
        input_path  : Path to the input .md file
        output_path : Desired output .pptx path
        api_key     : Google Gemini API key
        min_slides  : Minimum slide count (default 10)
        max_slides  : Maximum slide count (default 15)
        model_name  : Gemini model name (default 'gemini-2.0-flash')
        verbose     : If True, print progress to stdout

    Returns:
        Path of the saved .pptx file

    Raises:
        FileNotFoundError, ValueError  on input problems
        Any exception from Gemini / python-pptx is propagated
    """
    if verbose:
        _log = lambda msg: print(f'  {msg}')
    else:
        _log = lambda msg: None

    try:
        total_t0 = time.time()
        _log('[ ] Validating input ...')
        md_path = validate_input(input_path)
        resolved_template = resolve_template_path(template_path)

        _log('[.] Parsing markdown ...')
        doc = stage_parse(md_path)
        _log(f'     -> {len(doc.sections)} sections · {doc.word_count} words')
        
        _log('[!] Detecting document context ...')
        context = detect_context(doc)
        _log(f'     -> Type: {context.document_type} | Domain: {context.primary_domain}')
        _log(f'     -> Tone: {context.tone} | Audience: {context.estimated_audience_level}')
        _log(f'     -> Color scheme: {context.color_scheme} | Layout: {context.suggested_layout_emphasis}')
        
        # Store context in document for renderer to use
        doc.context = context

        _log('[*] Structuring slides with Gemini ...')
        blueprint = stage_structure(doc, api_key, min_slides, max_slides, model_name)
        _log(f'     -> {blueprint.total_slides} slides planned')

        _log('[~] Rendering presentation ...')
        if resolved_template:
            _log(f'     -> Using slide master: {resolved_template.name}')
        else:
            _log('     -> No slide master detected, using renderer fallback')
        prs = stage_render(blueprint, template_path=str(resolved_template) if resolved_template else None)
        
        _log('[✓] Validating PPTX integrity ...')
        validate_pptx(prs)

        _log('[>] Saving .pptx file ...')
        out_path = stage_save(prs, output_path)

        elapsed = time.time() - total_t0
        _log(f'[✓] Complete in {elapsed:.1f}s -> {out_path.name}')
        return out_path
        
    except FileNotFoundError as e:
        logger.error('File error: %s', str(e))
        raise
    except ValueError as e:
        logger.error('Validation error: %s', str(e))
        raise
    except Exception as e:
        logger.error('Pipeline failed: %s', str(e), exc_info=True)
        raise
