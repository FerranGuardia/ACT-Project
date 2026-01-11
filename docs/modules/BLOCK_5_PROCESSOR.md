# Processor Module

**Status**: Complete (Refactored)
**Location**: `src/processor/`

## Architecture Overview

The processor module has been refactored from a monolithic `ProcessingPipeline` class into a clean, modular architecture following SOLID principles.

### New Modular Architecture

```
ProcessingContext
├── Shared state and configuration
├── Callback management
└── Processing control

ScrapingCoordinator
├── URL discovery and chapter fetching
├── Content extraction from web pages
└── Progress tracking integration

ConversionCoordinator
├── TTS conversion workflow
├── File management (text/audio)
└── Temp file cleanup

AudioPostProcessor
├── Audio file merging
├── Batch processing
└── Output format handling

PipelineOrchestrator
├── High-level workflow coordination
├── Coordinator management
└── Public API compatibility
```

## Components

### Core Classes

- **`ProcessingContext`**: Shared state and configuration management
- **`ScrapingCoordinator`**: Handles all web scraping operations
- **`ConversionCoordinator`**: Manages TTS conversion and file operations
- **`AudioPostProcessor`**: Handles audio file merging and post-processing

### Legacy Components (Maintained for Compatibility)

- **`ProcessingPipeline`**: Alias for `PipelineOrchestrator` (backward compatibility)
- **`ProjectManager`**: Project state persistence
- **`ChapterManager`**: Chapter data structures and tracking
- **`FileManager`**: File operations and organization
- **`ProgressTracker`**: Progress reporting and callbacks

## Data Flow

```
URL → ScrapingCoordinator → ConversionCoordinator → AudioPostProcessor
       ↓                        ↓                        ↓
   Chapter URLs            Audio Files            Merged Audio
   Content Extraction      File Management        Output Formats
```

## Key Classes

### New Architecture Usage

```python
from processor import (
    PipelineOrchestrator,
    ProcessingContext,
    ScrapingCoordinator,
    ConversionCoordinator,
    AudioPostProcessor
)

# Create shared context
context = ProcessingContext(
    project_name="my_novel",
    novel_title="My Novel Title"
)

# Initialize coordinators
scraping = ScrapingCoordinator(context)
conversion = ConversionCoordinator(context)
audio = AudioPostProcessor(context)

# Or use the high-level orchestrator
orchestrator = PipelineOrchestrator("my_novel")
result = orchestrator.run_full_pipeline(toc_url="https://example.com/toc")
```

### Legacy API (Still Supported)

```python
from processor import ProcessingPipeline  # Still works!

pipeline = ProcessingPipeline(
    project_name="project",
    on_progress=callback,
    on_status_change=callback
)
result = pipeline.run_full_pipeline(toc_url="https://example.com/toc")
```

## Status Tracking

Chapter statuses: PENDING, SCRAPED, CONVERTING, COMPLETED, FAILED

## Benefits of Refactoring

- **Single Responsibility**: Each class has one clear purpose
- **Testability**: Individual coordinators can be tested in isolation
- **Maintainability**: Changes are localized to specific coordinators
- **Extensibility**: New coordinators can be added without affecting existing code
- **Backward Compatibility**: Existing code continues to work unchanged

## Testing

- `tests/unit/processor/test_coordinators.py` - Unit tests for new coordinators
- `tests/unit/processor/test_pipeline.py` - Legacy API tests (updated imports)
- `tests/integration/processor/test_coordinator_integration.py` - Integration tests
- `tests/integration/processor/test_processor_integration.py` - Legacy integration tests
