# Processor Module

**Status**: Complete
**Location**: `src/processor/`

## Components

- **`ProcessingPipeline`**: Main workflow orchestration
- **`ProjectManager`**: Project state persistence
- **`ChapterManager`**: Chapter data structures and tracking
- **`FileManager`**: File operations and organization
- **`ProgressTracker`**: Progress reporting and callbacks

## Data Flow

URL → Scraper → TTS → File output

## Key Classes

```python
from processor import ProcessingPipeline, ProjectManager

pipeline = ProcessingPipeline(
    project_name="project",
    on_progress=callback,
    on_status_change=callback
)

manager = ProjectManager("project")
manager.save_project(metadata)
```

## Status Tracking

Chapter statuses: PENDING, SCRAPED, CONVERTED, FAILED, COMPLETED

## Testing

- `tests/unit/processor/` - Unit tests for all components
- `tests/integration/processor/` - Integration tests
