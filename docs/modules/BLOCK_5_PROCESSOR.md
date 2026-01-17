# Processor Module

**Status**:  Complete
**Location**: `src/processor/`

## Overview

Handles the conversion pipeline from web scraping to audio output using a modular coordinator architecture.

## Architecture

The processor module follows a **coordinator pattern** with clear separation of concerns:

### Core Coordinators
- **PipelineOrchestrator**: High-level workflow coordination (140 lines)
- **ScrapingCoordinator**: Web scraping and content extraction
- **ConversionCoordinator**: Text-to-speech conversion
- **AudioPostProcessor**: Audio file merging

### Specialized Coordinators
- **BatchProcessingCoordinator**: Complex batch processing and incremental merging
- **ProcessingMetadataService**: Metadata saving and processing summaries
- **PauseStopManager**: Centralized pause/stop state management
- **BackwardCompatibilityAdapter**: Legacy API compatibility layer

### Shared Components
- **ProcessingContext**: Shared state and configuration with PauseStopManager integration

## Usage

### Simple Usage (Recommended)
```python
from processor import PipelineOrchestrator

# Full pipeline execution
orchestrator = PipelineOrchestrator("my_project")
result = orchestrator.run_full_pipeline(toc_url="https://example.com/toc")
```

### Advanced Usage (Modular)
```python
from processor import (
    ProcessingContext,
    ScrapingCoordinator,
    ConversionCoordinator,
    BatchProcessingCoordinator
)

# Custom coordinator setup
context = ProcessingContext(project_name="my_novel")
scraping = ScrapingCoordinator(context)
conversion = ConversionCoordinator(context)
batch_processor = BatchProcessingCoordinator(context, scraping, conversion)

# Use individual coordinators
result = batch_processor.process_all_chapters()
```

### Legacy API (Backward Compatible)
```python
from processor import ProcessingPipeline  # Alias for PipelineOrchestrator

# All existing code continues to work unchanged
pipeline = ProcessingPipeline("my_project")
pipeline.initialize_project(toc_url="https://example.com/toc")
chapters = pipeline.fetch_chapter_urls(toc_url)
# ... existing API methods work
```

## Key Features

### Architecture Benefits
- **Single Responsibility**: Each coordinator has one clear purpose
- **Testability**: Focused classes are easier to unit test
- **Maintainability**: Changes isolated to relevant coordinators
- **Reusability**: Coordinators can be used independently
- **Zero Breaking Changes**: All legacy APIs maintained

### Processing Features
- Modular processing pipeline with coordinator pattern
- Progress tracking with callbacks and status updates
- Comprehensive error handling and recovery mechanisms
- Project state persistence and resume capability
- Pause/stop control with centralized management
- Batch processing with incremental merging support
- Metadata generation and file tracking

