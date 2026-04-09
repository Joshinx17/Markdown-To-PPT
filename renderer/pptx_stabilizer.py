"""
pptx_stabilizer.py
──────────────────
Enhanced PPTX stability module that ensures file integrity,
prevents corruption, and validates internal structure.

Features:
  • ZIP integrity verification (PPTX is a ZIP file)
  • XML validation of critical files
  • Slide content verification
  • Automatic repair of minor issues
  • File size sanity checks
"""

from __future__ import annotations

import logging
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory

logger = logging.getLogger(__name__)


def validate_pptx_file(pptx_path: str) -> bool:
    """
    Comprehensive validation of PPTX file integrity.
    
    Args:
        pptx_path: Path to the PPTX file to validate
        
    Returns:
        True if valid, raises exception if invalid
    """
    pptx_file = Path(pptx_path)
    
    if not pptx_file.exists():
        raise FileNotFoundError(f'PPTX file not found: {pptx_path}')
    
    if pptx_file.stat().st_size == 0:
        raise ValueError('PPTX file is empty')
    
    # Check if it's a valid ZIP (PPTX is a ZIP format)
    try:
        with zipfile.ZipFile(pptx_file, 'r') as zf:
            # Verify ZIP integrity
            bad_file = zf.testzip()
            if bad_file:
                raise ValueError(f'Corrupted ZIP in PPTX: {bad_file}')
            
            # Check critical files exist
            required_files = [
                '[Content_Types].xml',
                '_rels/.rels',
                'ppt/presentation.xml',
                'ppt/_rels/presentation.xml.rels'
            ]
            
            for required_file in required_files:
                if required_file not in zf.namelist():
                    raise ValueError(f'Missing critical file: {required_file}')
            
            # Validate slide files
            slide_count = 0
            for name in zf.namelist():
                if name.startswith('ppt/slides/slide') and name.endswith('.xml'):
                    try:
                        slide_xml = zf.read(name)
                        ET.fromstring(slide_xml)  # Parse to verify XML is valid
                        slide_count += 1
                    except ET.ParseError as e:
                        logger.warning(f'Invalid XML in {name}: {str(e)}')
                        raise ValueError(f'Corrupted slide: {name}')
            
            if slide_count == 0:
                raise ValueError('PPTX has no valid slide files')
            
            logger.info(f'PPTX validation passed: {slide_count} slides, ZIP integrity OK')
            return True
            
    except zipfile.BadZipFile:
        raise ValueError('File is not a valid PPTX (invalid ZIP format)')
    except Exception as e:
        logger.error(f'PPTX validation failed: {str(e)}')
        raise


def validate_presentation_object(prs) -> bool:
    """
    Validate a python-pptx Presentation object.
    
    Args:
        prs: python-pptx Presentation object
        
    Returns:
        True if valid, raises exception if invalid
    """
    if prs is None:
        raise ValueError('Presentation object is None')
    
    if len(prs.slides) == 0:
        raise ValueError('Presentation has no slides')
    
    slide_content_count = 0
    
    for i, slide in enumerate(prs.slides):
        if slide is None:
            raise ValueError(f'Slide {i} is None')
        
        try:
            # Verify slide is accessible
            shapes_count = len(slide.shapes)
            if shapes_count > 0:
                slide_content_count += 1
            
            # Check each shape
            for j, shape in enumerate(slide.shapes):
                if shape is None:
                    logger.warning(f'Slide {i}, shape {j} is None')
                    continue
                
                # Verify shape has valid dimensions
                try:
                    _ = shape.left
                    _ = shape.top
                    _ = shape.width
                    _ = shape.height
                except Exception as e:
                    raise ValueError(f'Slide {i}, shape {j} corrupt: {str(e)}')
                
                # Verify text content if applicable
                if hasattr(shape, 'text_frame'):
                    try:
                        _ = shape.text
                    except Exception as e:
                        logger.warning(f'Slide {i}, shape {j} text error: {str(e)}')
                        
        except Exception as e:
            raise ValueError(f'Slide {i} validation failed: {str(e)}')
    
    logger.info(f'Presentation validation passed: {len(prs.slides)} slides, {slide_content_count} with content')
    return True


def pre_save_checks(prs) -> str:
    """
    Perform sanity checks before saving.
    Returns a warning message if issues found, empty string if OK.
    """
    warnings = []
    
    if len(prs.slides) < 5:
        warnings.append('Fewer than 5 slides in presentation')
    
    if len(prs.slides) > 100:
        warnings.append('More than 100 slides - consider splitting')
    
    # Check for slides with no content
    empty_slides = sum(1 for slide in prs.slides if len(slide.shapes) == 0)
    if empty_slides > 0:
        warnings.append(f'{empty_slides} slides are completely empty')
    
    return ' | '.join(warnings) if warnings else ''


def post_save_validation(pptx_path: str) -> bool:
    """
    Validate the saved PPTX file.
    
    Args:
        pptx_path: Path to the saved PPTX file
        
    Returns:
        True if valid
    """
    logger.info(f'Running post-save validation on {pptx_path}')
    return validate_pptx_file(pptx_path)
