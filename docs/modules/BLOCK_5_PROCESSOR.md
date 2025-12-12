# Block 5: Processor Module

**Status**: ✅ **COMPLETE**  
**Last Updated**: 2025-12-12  
**Location**: `src/processor/`

---

## Overview

The Processor module orchestrates the complete audiobook creation workflow, coordinating between the Scraper, TTS, and File Manager modules.

### Data Flow
```
User Input (URL) 
  → Processor (ProcessingPipeline)
    → Scraper (fetch chapters) 
      → Optional: Editor (clean/edit text)
        → TTS (convert to audio)
          → File Manager (save output)
```

---

## Components

### 1. ProcessingPipeline (`pipeline.py`)

Main orchestration class that coordinates the entire workflow.

**Key Features**:
- Accepts novel URL and settings
- Coordinates: Scraper → Editor (optional) → TTS → Output
- Handles errors and retries
- Progress callbacks for UI integration
- Stop/pause functionality

**Usage**:
```python
from processor import ProcessingPipeline

pipeline = ProcessingPipeline(
    project_name="My Project",
    on_progress=lambda p: print(f"Progress: {p*100}%"),
    on_status_change=lambda s: print(f"Status: {s}"),
    on_chapter_update=lambda n, s, m: print(f"Chapter {n}: {s}")
)

# Initialize and process
pipeline.initialize_project(novel_url="https://example.com/novel")
pipeline.process_all_chapters()
```

### 2. ProjectManager (`project_manager.py`)

Manages project state and persistence.

**Key Features**:
- Save/load project state (JSON format)
- Project metadata (title, author, chapters, progress)
- Resume interrupted projects
- Project directory management

**Usage**:
```python
from processor import ProjectManager

manager = ProjectManager("My Project")
manager.save_project(metadata={...})
project = manager.load_project()
```

### 3. ChapterManager (`chapter_manager.py`)

Organizes and tracks chapter data.

**Key Features**:
- Chapter data structures (`Chapter` dataclass)
- Chapter sequencing and ordering
- Chapter metadata (number, title, URL, status)
- Status tracking (PENDING, SCRAPED, EDITED, CONVERTED, FAILED, SKIPPED)

**Usage**:
```python
from processor import ChapterManager, Chapter, ChapterStatus

manager = ChapterManager()
chapter = Chapter(
    number=1,
    title="Chapter 1",
    url="https://example.com/ch1",
    status=ChapterStatus.PENDING
)
manager.add_chapter(chapter)
```

### 4. FileManager (`file_manager.py`)

Handles file operations and output management.

**Key Features**:
- Create output directories
- Save scraped text files
- Save generated audio files
- Organize files by project/chapter
- Clean up temporary files

**Usage**:
```python
from processor import FileManager

file_manager = FileManager("My Project")
text_path = file_manager.save_text_file(chapter_num=1, content="...")
audio_path = file_manager.save_audio_file(chapter_num=1, audio_data=...)
```

### 5. ProgressTracker (`progress_tracker.py`)

Tracks processing progress throughout the workflow.

**Key Features**:
- Track overall progress (0-100%)
- Track per-chapter progress
- Progress callbacks for UI
- Status reporting (PENDING, SCRAPING, SCRAPED, EDITING, EDITED, CONVERTING, COMPLETED, FAILED, SKIPPED)

**Usage**:
```python
from processor import ProgressTracker, ProcessingStatus

tracker = ProgressTracker(total_chapters=10)
tracker.update_chapter_status(1, ProcessingStatus.SCRAPING)
progress = tracker.get_overall_progress()  # 0.0 to 1.0
```

---

## Module Exports

All components are exported from `src/processor/__init__.py`:

```python
from processor import (
    ProcessingPipeline,
    ProjectManager,
    ChapterManager,
    Chapter,
    ChapterStatus,
    FileManager,
    ProgressTracker,
    ProcessingStatus
)
```

---

## Integration

### With Scraper (Block 2)
```python
from scraper.generic_scraper import GenericScraper

scraper = GenericScraper()
chapters = scraper.fetch_chapter_urls(novel_url)
content = scraper.scrape_chapter(chapter_url)
```

### With TTS (Block 3)
```python
from tts import TTSEngine

tts_engine = TTSEngine()
audio_data = tts_engine.convert_text_to_speech(text, voice="en-US-AndrewNeural")
```

### With Core (Block 1)
```python
from core.logger import get_logger
from core.config_manager import get_config

logger = get_logger("processor")
config = get_config()
output_dir = config.get("paths.output")
```

---

## Testing

**Test Location**: `ACT REFERENCES/PROCESSOR REFERENCES/TESTS/`

- Unit tests for all components
- Integration tests with Scraper and TTS modules
- End-to-end workflow tests

---

## Next Steps

1. **Testing**: Unit and integration tests
2. **Documentation**: Usage examples and API docs
3. **Enhancements**: Editor module integration (Block 4), performance optimizations

---

**See Also**:
- [Project Status](../CURRENT_STATUS_SUMMARY.md)
- [Architecture](../ARCHITECTURE.md)
