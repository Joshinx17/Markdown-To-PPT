# Web UI - MD to PPTX Converter

A professional, modern web interface for converting Markdown documents to PowerPoint presentations.

## Features

- **📁 Drag-and-Drop Upload** - Simply drag your markdown file onto the drop zone
- **⚡ Real-Time Progress Tracking** - Visual feedback for each conversion stage
- **🎨 Professional Styling** - Modern, responsive dark-mode design with teal accents
- **📊 Smart Configuration** - Control slide count and AI model selection
- **🔒 Secure Handling** - File validation, error handling, and automatic cleanup
- **📥 Direct Download** - Get your PPTX file immediately after conversion
- **🌐 No Installation** - Works in any modern browser

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variable (Optional)

If you have a Google Gemini API key, set it as an environment variable:

```bash
# Windows PowerShell:
$env:GOOGLE_GENAI_API_KEY = "your-api-key-here"

# Windows CMD:
set GOOGLE_GENAI_API_KEY=your-api-key-here

# Linux/Mac:
export GOOGLE_GENAI_API_KEY="your-api-key-here"
```

Or provide it via the web UI.

### 3. Run the Flask App

```bash
python app.py
```

The web UI will be available at: **http://localhost:5000**

## Usage

1. **Upload** - Click the drop zone or drag your `.md` file
2. **Configure** - Set slide count (10-15), choose AI model
3. **Convert** - Click "Convert to PowerPoint" button
4. **Download** - Get your presentation when ready

## Configuration Options

- **Minimum Slides**: 10-14 slides
- **Maximum Slides**: 11-15 slides
- **AI Model Options**:
  - `gemini-2.0-flash` - Faster, good for general content
  - `gemini-1.5-pro` - Better quality, takes longer
- **API Key**: Optional (uses environment variable if not provided)

## File Handling

- **Maximum Size**: 5 MB per file
- **Supported Formats**: `.md`, `.markdown`, `.txt`
- **Automatic Cleanup**: Old files are cleaned up after 24 hours
- **Backup**: Existing files are backed up before overwriting

## Error Handling

The application includes comprehensive error handling:
- File size validation
- File type validation
- PPTX integrity checking
- Graceful error messages to the user
- Detailed logging for debugging

## Deployment

### Local Testing
```bash
python app.py
```

### Production Deployment with Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker (Optional)
Create a `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:
```bash
docker build -t mdppt-web .
docker run -p 5000:5000 -e GOOGLE_GENAI_API_KEY=your-key mdppt-web
```

## Architecture

```
app.py                 - Flask application server
├── /api/convert       - File upload & conversion endpoint
├── /api/download      - Download generated PPTX
└── /api/check-api-key - Check API key configuration

templates/
└── index.html         - Main web interface

static/
├── style.css          - Professional styling (teal theme)
└── script.js          - Frontend interactions & API calls

uploads/               - Temporary upload storage
downloads/             - Generated PPTX files
```

## Technical Details

- **Framework**: Flask 2.3+
- **Frontend**: Vanilla JavaScript, modern CSS3
- **File Handling**: Secure temporary file management
- **Conversion Pipeline**: Uses existing orchestrator.py
- **Cleanup**: Automatic removal of files older than 24 hours

## Troubleshooting

### Port 5000 already in use
```bash
python app.py --port 5001
```

### CORS issues
The app uses same-origin requests, no CORS headers needed.

### File upload hangs
Check the file size (max 5 MB) and network connection.

### API key errors
Verify your Google Gemini API key at https://aistudio.google.com

## Security Notes

- Files are stored in temporary directories
- Filenames are sanitized
- File sizes are validated before processing
- Automatic cleanup prevents storage bloat
- No persistent user data is stored

## Future Enhancements

- [ ] Batch file processing
- [ ] Queue system for handling multiple requests
- [ ] S3 integration for file storage
- [ ] Custom theme selection
- [ ] Presentation preview
- [ ] Email delivery of results
- [ ] User accounts & history
- [ ] Advanced formatting options
