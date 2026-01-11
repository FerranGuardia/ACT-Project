# Processor Module

**Status**: ✅ Complete
**Location**: `src/processor/`

## Overview

Handles the conversion pipeline from web scraping to audio output.

## Components

- **ProcessingContext**: Shared state and configuration
- **ScrapingCoordinator**: Web scraping and content extraction
- **ConversionCoordinator**: Text-to-speech conversion
- **AudioPostProcessor**: Audio file merging
- **PipelineOrchestrator**: High-level workflow coordination

## Usage

```python
from processor import PipelineOrchestrator

# Simple usage
orchestrator = PipelineOrchestrator("my_project")
result = orchestrator.run_full_pipeline(toc_url="https://example.com/toc")

# Advanced usage with custom coordinators
from processor import ProcessingContext, ScrapingCoordinator

context = ProcessingContext(project_name="my_novel")
scraping = ScrapingCoordinator(context)
# ... configure and run
```

## Features

- Modular processing pipeline
- Progress tracking and callbacks
- Error handling and recovery
- Project state persistence
- Backward compatibility with legacy API

## Testing

- `tests/unit/processor/` - Unit tests for components
- `tests/integration/processor/` - Integration tests for workflows
