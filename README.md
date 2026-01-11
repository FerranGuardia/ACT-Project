# ACT - Web Novel to Audiobook Converter

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Convert web novels to audiobooks using automated scraping and text-to-speech conversion.

## Features

- **Web Scraping**: Extract chapters from web novel sites
- **Text-to-Speech**: Convert text to speech using online or offline TTS engines
- **Audio Processing**: Combine audio files into complete audiobooks
- **Project Management**: Resume interrupted conversions
- **Graphical Interface**: Desktop application with multiple operational modes

## Quick Start

```bash
pip install -r requirements.txt
python launch_ui.py
```

## Requirements

- Python 3.8+
- Internet connection (for online TTS)

## Installation

```bash
git clone https://github.com/FerranGuardia/ACT-Project.git
cd ACT-Project
pip install -r requirements.txt
```

## Usage

### Graphical Interface

```bash
python launch_ui.py
```

### Operational Modes

1. **Scraper**: Extract chapters from web novel URLs
2. **TTS**: Convert text files to speech
3. **Merger**: Combine audio files into audiobooks
4. **Full Pipeline**: Complete workflow from URL to audiobook

## Configuration

Settings are stored in `~/.act/config.json` and include:

- Output directories
- TTS voice preferences
- UI preferences

## Troubleshooting

### Common Issues

- **UI won't start**: `pip install PySide6`
- **TTS conversion fails**: Check internet connection or try offline TTS
- **Audio merging fails**: Install ffmpeg system-wide
- **Scraping fails**: Some sites require additional setup

## License

MIT License - see [LICENSE](LICENSE)
