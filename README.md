# MD -> PPTX: Meridian Presentation Generator

Converts Markdown (`.md`) files into polished 10-15 slide `.pptx` presentations using Google Gemini when available, with a built-in offline fallback when it is not. When a shared Slide Master `.pptx` is present, the renderer loads that template and builds slides from its layouts/placeholders instead of starting from an independent theme.

## Features

- ✨ **Modern UI** - Professional web interface with drag-and-drop upload
- 🎨 **Professional Design** - Contemporary teal and navy color scheme with modern typography  
- 🔒 **Stable & Reliable** - Enhanced error handling, ZIP integrity validation, PPTX corruption prevention with multi-stage validation and post-save checks
- 🧠 **AI-Powered** - Google Gemini integration for intelligent slide structuring
- 📊 **Rich Slide Types** - 17 different slide layouts including charts, tables, timelines
- 🎯 **Context-Aware Styling** - Automatically detects document type (technical, business, educational, training, research) and applies appropriate themes, colors, and layouts
- 🌍 **Smart Theme Selection** - Dynamically chooses color schemes and layout emphasis based on content domain (AI/ML, Finance, Technology, etc.) and audience level
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

# Use the shared hackathon Slide Master explicitly
python cli.py -i report.md -o output/report.pptx --template templates/Slide_Master.pptx

# Bias toward a 14-slide deck
python cli.py -i report.md -o output/report.pptx --slides 14

# Use a different Gemini model
python cli.py -i report.md -o output/report.pptx --model gemini-1.5-pro

# Inline API key
python cli.py -i report.md --api-key YOUR_KEY
```

## Deployment as a Website

To deploy this application as a public website, you can use Docker and a cloud platform like Azure App Service.

### Using Docker

1. Build the Docker image:
   ```bash
   docker build -t md-to-pptx .
   ```

2. Run locally to test:
   ```bash
   docker run -p 5000:5000 md-to-pptx
   ```
   Open http://localhost:5000

### Deploy to Azure App Service

1. **Prerequisites**:
   - Azure CLI installed (`az` command)
   - Azure subscription
   - Docker installed locally

2. **Login to Azure**:
   ```bash
   az login
   ```

3. **Create a resource group** (if needed):
   ```bash
   az group create --name mdppt-rg --location eastus
   ```

4. **Create an App Service plan**:
   ```bash
   az appservice plan create --name mdppt-plan --resource-group mdppt-rg --sku B1 --is-linux
   ```

5. **Create the web app**:
   ```bash
   az webapp create --resource-group mdppt-rg --plan mdppt-plan --name your-unique-app-name --deployment-container-image-name md-to-pptx:latest
   ```

6. **Set environment variables** (optional, for Gemini API):
   ```bash
   az webapp config appsettings set --resource-group mdppt-rg --name your-unique-app-name --setting GOOGLE_GENAI_API_KEY=your_api_key
   ```

7. **Deploy the image**:
   ```bash
   az webapp config container set --resource-group mdppt-rg --name your-unique-app-name --docker-custom-image-name md-to-pptx:latest --docker-registry-server-url https://index.docker.io
   ```

Your website will be available at `https://your-unique-app-name.azurewebsites.net`

### Alternative: Deploy to Heroku

1. Install Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create your-app-name`
4. Set buildpack: `heroku buildpacks:set heroku/python`
5. Deploy: `git push heroku main`
6. Set environment variables: `heroku config:set GOOGLE_GENAI_API_KEY=your_key`

## How It Works

1. **Parser** (`parser/md_parser.py`) - Parses Markdown into structured sections
2. **Structurer** (`structurer/`) - AI or rule-based slide planning
3. **Renderer** (`renderer/`) - Converts blueprint into a PowerPoint using the shared slide master when available
4. **Orchestrator** (`orchestrator.py`) - Manages pipeline with validation & error handling

### Architecture

```
Input (.md)
    ↓
[Validate] - Check file integrity and size limits
    ↓
[Parse] - Extract structure, headings, content
    ↓
[Detect Context] - Analyze document type, tone, domain, audience
    ↓
[Structure] - Plan slide layout with Gemini or rules + context-aware styling
    ↓
[Render] - Generate beautiful PPTX slides with theme from context
    ↓
[Validate] - Ensure PPTX integrity, check all slides and content
    ↓
[Post-Save Check] - Verify ZIP integrity and XML validity
    ↓
Output (.pptx)
```

### Context-Aware Styling

The system automatically detects:
- **Document Type**: Technical, Business, Educational, Training, Research, or General
- **Content Domain**: AI/ML, Finance, Technology, Education, etc.
- **Tone**: Formal, Casual, Technical, or Storytelling
- **Audience Level**: Beginner, Intermediate, or Advanced
- **Content Patterns**: Code blocks, diagrams, numerical data, tables

Based on these factors, it:
- **Selects appropriate color schemes**: Purple for AI/ML (modern), Blue for Finance (trust), Teal for Tech (innovation), Navy for Business (corporate), Green for Education (growth)
- **Chooses layout emphasis**: Visual-focused for code/diagrams, Data-driven for analytics, Textual for general content
- **Applies relevant slide types and transitions** that match the document's purpose

### PPTX Stability & Integrity

The system includes comprehensive safeguards:
- **ZIP Integrity Validation**: Verifies PPTX file format and structure
- **XML Structure Checks**: Validates all XML files within the PPTX
- **Multi-stage Validation**: Checks presentation object, then temporary file, then final output
- **Corruption Prevention**: Detects and prevents invalid shapes, text frames, and properties
- **Automatic Backup**: Creates backup of existing files before overwriting
- **Cross-drive file handling**: Safely moves files across disk drives on Windows

These features prevent corruption that requires file repair and data loss.

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

### Slide Master Support
- Place the hackathon master file in `templates/` as `Slide_Master.pptx`, `Slide Master.pptx`, `slide_master.pptx`, `master.pptx`, or `template.pptx` for auto-detection
- Or pass it explicitly with `--template path/to/master.pptx`
- When a master is loaded, the renderer uses the master layouts and placeholders first and only falls back to custom drawing when the template is unavailable

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
