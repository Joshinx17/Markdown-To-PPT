# MD -> PPTX: Meridian Presentation Generator

Converts Markdown (`.md`) files into polished 10-15 slide `.pptx` presentations using Google Gemini when available, with a built-in offline fallback when it is not.

## Features

- ✨ **Modern UI** - Professional web interface with drag-and-drop upload
- 🎨 **Professional Design** - Contemporary teal and navy color scheme with modern typography
- 🔒 **Stable & Reliable** - Enhanced error handling, file validation, PPTX integrity checks
- 🧠 **AI-Powered** - Google Gemini integration for intelligent slide structuring
- 📊 **Rich Slide Types** - 17 different slide layouts including charts, tables, timelines
- 🚀 **Flexible** - Use web UI, CLI, or Python API

## Quick Start - Web UI (Recommended)

```bash
cd mdppt
pip install -r requirements.txt

# Set API key (optional if using environment variable)
export GOOGLE_GENAI_API_KEY=your_api_key

# Start the web server
python app.py
```

Open: **http://localhost:5000**

Then simply:
1. Drag your `.md` file onto the upload area
2. Configure slide count and AI model
3. Click "Convert to PowerPoint"
4. Download your presentation

See [WEB_UI_README.md](WEB_UI_README.md) for detailed web UI documentation.

## Quick Start - Command Line

```bash
cd mdppt
pip install -r requirements.txt

# Optional: enable Gemini-powered structuring
copy .env.example .env

python cli.py --input samples/enterprise_ai.md --output output/result.pptx
```

Or use the drop-folder workflow:

```bash
copy your_file.md input/
python cli.py
```

## Requirements

- Python 3.10+
- `pip install -r requirements.txt`
- Optional: a [Google Gemini API key](https://aistudio.google.com/) for AI slide structuring

If no API key is configured, the app still works and uses its deterministic rule-based slide planner.

## Usage

### Web UI (Recommended)
```bash
python app.py
# Opens at http://localhost:5000
```

### Command Line

```bash
python cli.py -i your_document.md -o output/presentation.pptx
```

If you omit `--input`, the CLI automatically picks the newest `.md` file inside `input/`.

### Advanced CLI Options

```bash
# Standard conversion
python cli.py -i report.md -o output/report.pptx

# Bias toward a 14-slide deck
python cli.py -i report.md -o output/report.pptx --slides 14

# Use a different Gemini model
python cli.py -i report.md -o output/report.pptx --model gemini-1.5-pro

# Inline API key
python cli.py -i report.md --api-key YOUR_KEY
```

## How It Works

1. **Parser** (`parser/md_parser.py`) - Parses Markdown into structured sections
2. **Structurer** (`structurer/`) - AI or rule-based slide planning
3. **Renderer** (`renderer/`) - Converts blueprint to beautiful PowerPoint
4. **Orchestrator** (`orchestrator.py`) - Manages pipeline with validation & error handling

### Architecture

```
Input (.md)
    ↓
[Parse] - Extract structure, headings, content
    ↓
[Structure] - Plan slide layout with Gemini or rules
    ↓
[Render] - Generate beautiful PPTX slides
    ↓
[Validate] - Ensure PPTX integrity
    ↓
Output (.pptx)
```

## Supported Slide Types

- `TITLE` - Professional title slide with metadata
- `AGENDA` - 2-column agenda with numbering
- `EXECUTIVE_SUMMARY` - High-level overview
- `SECTION_DIVIDER` - Modern section breaks
- `CONTENT_BULLETS` - Up to 5 bullet points
- `CONTENT_TEXT` - Free-form text content
- `TWO_COLUMN` - Side-by-side layout
- `CHART_BAR` - Bar charts with auto-coloring
- `CHART_PIE` - Pie/donut charts
- `CHART_LINE` - Line graphs with trends
- `CHART_AREA` - Area/stacked charts
- `TABLE` - Professional data tables
- `PROCESS_FLOW` - Step-by-step flowcharts
- `TIMELINE` - Chronological timelines
- `COMPARISON` - Side-by-side comparisons
- `CONCLUSION` - Summary/closing slides
- `QUOTE` - Highlighted quotations

## Design Language

### Modern Professional Theme ("Meridian")
- **Primary Colors**: Deep Navy (#0D1E42) with vibrant Teal (#009EA6) accents
- **Typography**: Segoe UI for clean, modern readability
- **Layout**: Generous whitespace with professional spacing
- **Accessibility**: WCAG-compliant color contrasts
- **Styling**: Modern rounded corners, subtle shadows

## Stability & Quality Improvements

- ✅ Enhanced error handling with try-catch blocks
- ✅ PPTX file validation before saving
- ✅ Temporary file handling (safe file operations)
- ✅ Automatic backup of existing files
- ✅ Comprehensive logging and diagnostics
- ✅ File size and type validation
- ✅ Input sanitization and security checks

## Project Structure

```text
mdppt/
├── app.py                    # Flask web application
├── cli.py                    # Command-line interface
├── orchestrator.py           # Pipeline coordinator (enhanced)
├── templates/
│   └── index.html           # Web UI interface
├── static/
│   ├── style.css            # Modern styling
│   └── script.js            # Frontend logic
├── parser/
│   ├── __init__.py
│   └── md_parser.py         # Markdown parsing
├── structurer/
│   ├── __init__.py
│   ├── llm_structurer.py    # Gemini integration
│   ├── rule_based_designer.py
│   ├── prompts.py
│   └── slide_types.py
├── renderer/
│   ├── __init__.py
│   ├── slide_builder.py    # Main slide rendering (enhanced)
│   ├── theme.py            # Design tokens (modernized)
│   ├── chart_builder.py
│   ├── infographic_builder.py
│   └── table_builder.py
├── samples/
│   └── enterprise_ai.md
├── tests/
│   └── test_pipeline.py
├── input/                   # Input folder for CLI
├── output/                  # Output folder for CLI
├── uploads/                 # Web UI temp uploads
├── downloads/               # Web UI temp downloads
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Examples

### Basic Usage
```bash
python cli.py -i sample.md -o result.pptx
```

### Web UI Upload
1. Go to http://localhost:5000
2. Drag markdown file to drop zone
3. Click "Convert to PowerPoint"
4. Download results

### With Custom Settings
```bash
python cli.py -i document.md -o output.pptx --slides 12 --model gemini-1.5-pro --api-key sk-xxx
```

## Configuration

### Environment Variables
```bash
GOOGLE_GENAI_API_KEY=your_api_key      # Gemini API key
FLASK_ENV=development                   # Flask environment (optional)
FLASK_DEBUG=1                           # Enable debug mode (optional)
```

### .env File
Create a `.env` file in the project root:
```
GOOGLE_GENAI_API_KEY=your_api_key
```

## API Key Setup

1. Get free API key from [Google AI Studio](https://aistudio.google.com/)
2. Set environment variable OR provide via:
   - `.env` file
   - Web UI form
   - CLI `--api-key` option

## Performance

- **Parsing**: < 1 second
- **AI Structuring**: 10-30 seconds (depends on content & model)
- **Rendering**: 2-5 seconds  
- **Total**: ~15-40 seconds end-to-end

## Troubleshooting

### "API key not found"
Set `GOOGLE_GENAI_API_KEY` environment variable or provide via web UI/CLI

### "File too large"
Maximum file size is 5 MB. Reduce document size or split content.

### "PPTX won't open"
Run latest Office version or use LibreOffice. File is automatically validated before saving.

### Port already in use
```bash
python app.py --port 5001
```

## Development

### Run Tests
```bash
python -m pytest tests/
```

### Run with Debug Logging
```bash
python cli.py -vi input/sample.md -o output/result.pptx
```

### Web UI Development
```bash
export FLASK_ENV=development
python app.py  # Auto-reloads on file changes
```

## Contributing

Contributions welcome! Areas for enhancement:
- Additional slide layouts
- Custom color themes
- Batch processing
- Cloud storage integration
- More export formats

## License

MIT License - see LICENSE file for details

## Support & Feedback

- Report issues on GitHub
- Request features on Discussions
- See [WEB_UI_README.md](WEB_UI_README.md) for web-specific documentation

