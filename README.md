# ACT - Audiobook Creator Tools

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-v1.0.0-success)](https://github.com/FerranGuardia/ACT-Project)

A complete and modular Python tool for creating audiobooks from webnovels using AI voices. Transform your favorite web novels into high-quality audiobooks with automated scraping, multi-provider text-to-speech, and a modern GUI.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/ferrangp)

## Features

- **Automated Scraping**: Extracts content from webnovel sites (NovelFull, NovelBin, etc.)
- **Multi-Provider Text-to-Speech**: Converts text to audio using:
  - **Edge TTS** (Cloud, high quality, free) - Standard and alternative methods
  - **pyttsx3** (Offline, system voices, fallback)
- **Automatic Fallback**: Seamlessly switches between TTS providers when needed
- **Complete Pipeline**: Automated workflow from novel URL to finished audiobook
- **Modern GUI**: PySide6-based interface with 4 operational modes
- **Project Management**: Save, load, and resume projects
- **Queue System**: Process multiple novels in sequence
- **Progress Tracking**: Real-time progress updates and status monitoring

## Requirements

- **Python 3.8 or higher**
- **Windows, macOS, or Linux**
- **Internet connection** (for Edge TTS and web scraping)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/FerranGuardia/ACT-Project.git
cd ACT-Project
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Optional: Install Playwright for Advanced Scraping

For better scraping support on JavaScript-heavy sites:

```bash
pip install playwright
playwright install chromium
```

### 5. Optional: Install ffmpeg for Audio Merging

Required for the Merger view (combining audio files):

- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt-get install ffmpeg` (or equivalent)

## Usage

### Launching the Application

**Option 1: Using the launcher script**
```bash
python launch_ui.py
```

**Option 2: Using the batch file (Windows)**
```bash
launch_ui.bat
```

**Option 3: Using the main module**
```bash
python -m src.main
```

### Application Modes

The application provides 4 operational modes:

1. **Scraper Mode**: Extract chapter content from webnovel URLs
2. **TTS Mode**: Convert text files to audio using AI voices
3. **Merger Mode**: Combine multiple audio files into a single audiobook
4. **Full Automation Mode**: Complete pipeline with queue system (Scrape → TTS → Save)

### Basic Workflow

1. Launch the application
2. Select a mode from the landing page
3. For **Full Automation**:
   - Click "Add to Queue"
   - Enter novel URL
   - Select TTS provider (Edge TTS or pyttsx3)
   - Choose voice
   - Select chapters (All/Range/Specific)
   - Click "Start Processing"
4. Monitor progress in real-time
5. Audio files are saved to Desktop (or specified output folder)

### Output Structure

```
Desktop/
└── novel_title/
    ├── novel_title_scraps/      # Text files
    │   └── chapter_0001_Title.txt
    └── novel_title_audio/       # Audio files
        └── chapter_0001_Title.mp3
```

## Project Structure

```
ACT/
├── src/
│   ├── core/           # Logger, Config Manager
│   ├── scraper/        # Web scraping module
│   ├── tts/            # Text-to-speech module
│   ├── processor/      # Processing pipeline
│   └── ui/             # Graphical interface
├── tests/              # Test suite
├── launch_ui.py        # UI launcher script
└── requirements.txt    # Python dependencies
```

## Configuration

Configuration is stored in `~/.act/config.json` and managed automatically. You can edit this file to customize:

- Default output directory
- Default TTS voice
- Log level
- Other application settings

## Known Limitations

1. **pyttsx3 Blocking**: TTS conversion with pyttsx3 cannot be interrupted mid-way (limitation of pyttsx3 library). Stop will take effect after current conversion completes.

2. **Editor Module**: Not implemented (optional feature). Text editing must be done externally if needed.

3. **Styling**: Default Qt appearance (no custom theme yet).

4. **Dependencies**: Some features require optional libraries:
   - `pydub`: Required for audio merging (Merger mode)
   - `ffmpeg`: Required by pydub for format conversion
   - `playwright`: Optional, improves scraping on JavaScript-heavy sites

## Troubleshooting

### UI Won't Launch

**Error**: `ModuleNotFoundError: No module named 'PySide6'`

**Solution**: Install PySide6:
```bash
pip install PySide6
```

### TTS Conversion Fails

**Error**: "No audio was received"

**Possible Causes**:
- Edge TTS service is down (system should auto-fallback to pyttsx3)
- Invalid voice name
- Network connectivity issues

**Solution**: 
- Check internet connection
- Try selecting pyttsx3 provider instead
- Verify voice is available in selected provider

### Scraping Fails

**Error**: "Failed to fetch chapters"

**Possible Causes**:
- Invalid URL
- Website structure changed
- Network issues
- Cloudflare protection

**Solution**:
- Verify URL is correct
- Try installing Playwright for better JavaScript support
- Check internet connection

## Documentation

Comprehensive documentation is available in the [`docs/`](docs/) folder:

- **[Architecture](docs/ARCHITECTURE.md)** - System design and architecture
- **[Current Status](docs/CURRENT_STATUS_SUMMARY.md)** - Project status and module completion
- **[Module Documentation](docs/modules/)** - Detailed documentation for each module
- **[Testing Guide](docs/tests/)** - Test documentation and procedures

See [docs/README.md](docs/README.md) for the complete documentation index.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
```

### Project Status

- **Block 1 (Core)**: Complete
- **Block 2 (Scraper)**: Complete
- **Block 3 (TTS)**: Complete (Multi-provider with fallback)
- **Block 4 (Editor)**: Optional, not implemented
- **Block 5 (Processor)**: Complete
- **Block 6 (UI)**: Complete

**Status**: v1.0.0 Complete

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## Issues & Support

For issues, questions, or feature requests, please open an issue on the [GitHub Issues](https://github.com/FerranGuardia/ACT-Project/issues) page.

## Support This Project

If you find this project helpful, consider supporting its development:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/ferrangp)

[Support on Buy Me a Coffee](https://buymeacoffee.com/ferrangp) - Your support helps maintain and improve this project!

---

**Version**: 1.0.0  
**Last Updated**: 2025-12-12
