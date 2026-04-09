"""
Web UI for MD -> PPTX presentation generator.

Features:
  • Drag-and-drop file upload
  • Real-time progress tracking
  • Configuration panel for slide count and API key
  • Direct download of generated PPTX
  • Professional, responsive UI
  • Error handling and user feedback
"""

import os
import logging
import secrets
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, send_file, flash

from orchestrator import convert
from orchestrator import MAX_FILE_SIZE_MB

# ─── Configuration ────────────────────────────────────────────────────────────

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = secrets.token_hex(16)

# File upload settings
UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)
DOWNLOAD_FOLDER = Path(__file__).parent / 'downloads'
DOWNLOAD_FOLDER.mkdir(exist_ok=True)

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['DOWNLOAD_FOLDER'] = str(DOWNLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS = {'.md', '.markdown', '.txt'}

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def cleanup_old_files(folder: Path, max_age_hours: int = 24) -> None:
    """Remove files older than max_age_hours from folder."""
    import time
    cutoff = time.time() - (max_age_hours * 3600)
    for f in folder.glob('*'):
        if f.is_file() and f.stat().st_mtime < cutoff:
            try:
                f.unlink()
                logger.info('Cleaned up: %s', f.name)
            except Exception as e:
                logger.warning('Could not clean up %s: %s', f.name, str(e))


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html', max_size_mb=MAX_FILE_SIZE_MB)


@app.route('/api/convert', methods=['POST'])
def api_convert():
    """
    Handle file upload and conversion.
    Returns JSON with status, download URL, or error message.
    """
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Get options from form
        min_slides = int(request.form.get('minSlides', 10))
        max_slides = int(request.form.get('maxSlides', 15))
        api_key = request.form.get('apiKey', '').strip() or os.getenv('GOOGLE_GENAI_API_KEY')
        model_name = request.form.get('model', 'gemini-2.0-flash')

        # Validate slide count
        if not (10 <= min_slides <= 15) or not (10 <= max_slides <= 15):
            return jsonify({
                'success': False,
                'error': 'Slide count must be between 10 and 15'
            }), 400

        if min_slides > max_slides:
            return jsonify({
                'success': False,
                'error': 'Minimum slides must be less than maximum'
            }), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f'{timestamp}_{filename}'
        input_path = Path(app.config['UPLOAD_FOLDER']) / unique_filename

        file.save(str(input_path))
        logger.info('Uploaded: %s (%d bytes)', unique_filename, input_path.stat().st_size)

        # Generate output filename
        output_filename = f'{input_path.stem}_presentation_{timestamp}.pptx'
        output_path = Path(app.config['DOWNLOAD_FOLDER']) / output_filename

        # Convert
        logger.info('Starting conversion: %s -> %s', input_path.name, output_path.name)
        result_path = convert(
            str(input_path),
            str(output_path),
            api_key=api_key,
            min_slides=min_slides,
            max_slides=max_slides,
            model_name=model_name,
            verbose=False
        )

        logger.info('Conversion successful: %s', result_path)

        # Cleanup upload
        try:
            input_path.unlink()
        except Exception as e:
            logger.warning('Could not delete upload: %s', str(e))

        # Return download URL
        return jsonify({
            'success': True,
            'download_url': f'/api/download/{output_filename}',
            'filename': output_path.name,
            'size_mb': round(output_path.stat().st_size / (1024 * 1024), 2)
        })

    except ValueError as e:
        logger.error('Validation error: %s', str(e))
        return jsonify({'success': False, 'error': f'Error: {str(e)}'}), 400
    except Exception as e:
        logger.error('Conversion error: %s', str(e), exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Conversion failed: {str(e)}'
        }), 500


@app.route('/api/download/<filename>')
def api_download(filename: str):
    """Download generated PPTX file."""
    try:
        # Security: validate filename
        filename = secure_filename(filename)
        file_path = Path(app.config['DOWNLOAD_FOLDER']) / filename

        if not file_path.exists():
            logger.warning('Download requested for non-existent file: %s', filename)
            return jsonify({'error': 'File not found'}), 404

        logger.info('Downloading: %s', filename)
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation'
        )

    except Exception as e:
        logger.error('Download error: %s', str(e))
        return jsonify({'error': 'Download failed'}), 500


@app.route('/api/check-api-key', methods=['POST'])
def check_api_key():
    """Check if API key is configured."""
    api_key = request.json.get('api_key', '').strip() or os.getenv('GOOGLE_GENAI_API_KEY')
    return jsonify({'has_api_key': bool(api_key)})


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file size exceeded error."""
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size: {MAX_FILE_SIZE_MB} MB'
    }), 413


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors."""
    logger.error('Internal error: %s', str(error), exc_info=True)
    return jsonify({'success': False, 'error': 'Internal server error'}), 500


# ─── Startup/Shutdown ──────────────────────────────────────────────────────────

@app.before_request
def cleanup_files():
    """Periodically clean up old files (every 100 requests)."""
    import random
    if random.random() < 0.01:  # ~1% of requests
        cleanup_old_files(UPLOAD_FOLDER)
        cleanup_old_files(DOWNLOAD_FOLDER)


if __name__ == '__main__':
    logger.info('Starting MD -> PPTX Web UI on http://localhost:5000')
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_ENV') == 'development',
        threaded=True
    )
