# UI Structure & Design Patterns Guide

## Overview

This guide explains the UI architecture, design patterns, and best practices used in the ACT application. It's designed to help maintain consistency, readability, and robustness.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Key Design Principles](#key-design-principles)
3. [Component Organization](#component-organization)
4. [Common Patterns](#common-patterns)
5. [Best Practices](#best-practices)
6. [Common Pitfalls to Avoid](#common-pitfalls-to-avoid)

---

## Architecture Overview

### Directory Structure

```
src/ui/
├── __init__.py
├── main_window.py          # Main application window
├── styles.py               # Centralized styling system
├── view_config.py          # View configuration constants
├── ui_constants.py         # UI string constants
├── widgets/                # Reusable UI components
│   ├── __init__.py
│   └── base_controls_section.py
├── views/                  # Main view components
│   ├── base_view.py        # Base class for all views
│   ├── base_queue_item_widget.py
│   ├── scraper_view/
│   ├── tts_view/
│   └── full_auto_view/
├── dialogs/                # Dialog windows
└── themes/                 # Theme definitions
```

### Component Hierarchy

```
MainWindow
├── LandingPage
└── StackedWidget
    ├── ScraperView (BaseView)
    │   ├── ControlsSection (BaseControlsSection)
    │   ├── QueueSection
    │   ├── URLInputSection
    │   └── ...
    ├── TTSView (BaseView)
    └── FullAutoView (BaseView)
```

---

## Key Design Principles

### 1. **Separation of Concerns**

Each component has a single, well-defined responsibility:

- **Views**: Orchestrate UI components and handle user interactions
- **Sections**: Self-contained UI groups (e.g., ControlsSection, QueueSection)
- **Handlers**: Business logic separated from UI (e.g., ScraperViewHandlers)
- **Widgets**: Reusable UI components (e.g., BaseControlsSection)

### 2. **DRY (Don't Repeat Yourself)**

- Use base classes for common functionality
- Centralize constants and configuration
- Extract repeated patterns into reusable components

### 3. **Single Source of Truth**

- All constants in `ui_constants.py`
- All configuration in `view_config.py` or `landing_page_config.py`
- All styling in `styles.py`

### 4. **Consistency First**

- Consistent naming conventions
- Consistent patterns across similar components
- Consistent error handling

---

## Component Organization

### Base Classes

#### `BaseView`
**Purpose**: Common structure for all views

**What it provides**:
- Standard layout setup
- Consistent spacing and margins
- Abstract `setup_ui()` method

**Usage**:
```python
class MyView(BaseView):
    def setup_ui(self):
        main_layout = self.get_main_layout()
        # Add your components here
```

#### `BaseControlsSection`
**Purpose**: Common controls section with standard buttons

**What it provides**:
- Standard button layout (Add, Clear, Start, Pause, Stop)
- State management methods (`set_processing_state()`, `set_idle_state()`)
- Consistent styling

**Usage**:
```python
class MyControlsSection(BaseControlsSection):
    def get_start_button_text(self) -> str:
        return ButtonText.START_MY_OPERATION
```

#### `BaseQueueItemWidget`
**Purpose**: Common structure for queue item widgets

**What it provides**:
- Standard layout (icon, info, actions)
- Status and progress display
- Abstract methods for customization

---

## Common Patterns

### Pattern 1: View Structure

Every view follows this structure:

```python
class MyView(BaseView):
    def __init__(self, parent=None):
        # Initialize handlers
        self.handlers = MyViewHandlers(self)
        
        # Initialize data structures
        self.queue_items: list = []
        
        # Call super().__init__() which calls setup_ui()
        super().__init__(parent)
        
        # Connect handlers after UI is set up
        self._connect_handlers()
    
    def setup_ui(self):
        """Set up the view UI."""
        main_layout = self.get_main_layout()
        
        # Add sections
        self.controls_section = MyControlsSection()
        main_layout.addWidget(self.controls_section)
        
        # ... more sections
    
    def _connect_handlers(self):
        """Connect all button handlers."""
        self.controls_section.start_button.clicked.connect(self.start_operation)
        # ... more connections
```

### Pattern 2: State Management

Use state management methods instead of directly manipulating buttons:

```python
# ❌ BAD: Direct manipulation scattered throughout code
self.controls_section.start_button.setEnabled(False)
self.controls_section.pause_button.setEnabled(True)
self.controls_section.stop_button.setEnabled(True)

# ✅ GOOD: Use state management methods
self.controls_section.set_processing_state()
```

### Pattern 3: Constants Usage

Always use constants instead of magic strings:

```python
# ❌ BAD: Magic strings
button.setText("⏸️ Pause")
if button.text() == "↑":
    # ...

# ✅ GOOD: Use constants
from ui.ui_constants import ButtonText
button.setText(ButtonText.PAUSE)
if button.text() == ButtonText.MOVE_UP:
    # ...
```

### Pattern 4: Button Connections

Use object references, not text matching:

```python
# ❌ BAD: Fragile text matching
for button in widget.findChildren(QPushButton):
    if button.text() == "↑":
        button.clicked.connect(...)

# ✅ GOOD: Use object references
widget.up_button.clicked.connect(...)
widget.down_button.clicked.connect(...)
```

### Pattern 5: Error Handling

Standardize error handling:

```python
def start_operation(self):
    """Start the operation."""
    # Validate inputs
    valid, error_msg = self.handlers.validate_inputs(...)
    if not valid:
        QMessageBox.warning(self, DialogMessages.VALIDATION_ERROR_TITLE, error_msg)
        return
    
    # Check if already running
    if self.thread and self.thread.isRunning():
        QMessageBox.warning(self, DialogMessages.ALREADY_RUNNING_TITLE, 
                           DialogMessages.ALREADY_RUNNING_MSG)
        return
    
    # Start operation
    # ...
```

---

## Best Practices

### 1. **Naming Conventions**

- **Views**: `*View` (e.g., `ScraperView`, `TTSView`)
- **Sections**: `*Section` (e.g., `ControlsSection`, `QueueSection`)
- **Handlers**: `*Handlers` (e.g., `ScraperViewHandlers`)
- **Widgets**: `*Widget` (e.g., `QueueItemWidget`)
- **Threads**: `*Thread` (e.g., `ScrapingThread`)

### 2. **Method Organization**

Organize methods in this order:
1. `__init__()`
2. `setup_ui()` (public)
3. `_connect_handlers()` (private)
4. Public methods (user actions)
5. Private methods (helpers, prefixed with `_`)
6. Signal handlers (prefixed with `_on_`)

### 3. **Type Hints**

Always use type hints for better readability:

```python
def add_to_queue(self) -> None:
    """Add current settings to the queue."""
    # ...
```

### 4. **Docstrings**

Every public method should have a docstring:

```python
def start_operation(self) -> None:
    """
    Start the operation.
    
    Validates inputs, checks if already running, then starts
    the operation thread.
    """
    # ...
```

### 5. **Configuration Usage**

Always use config values, never hardcode:

```python
# ❌ BAD
layout.setSpacing(10)
button.setMinimumWidth(300)

# ✅ GOOD
from ui.view_config import ViewConfig
layout.setSpacing(ViewConfig.INPUT_GROUP_SPACING)
button.setMinimumWidth(ViewConfig.COMBO_BOX_VOICE_MIN_WIDTH)
```

---

## Common Pitfalls to Avoid

### 1. **Direct Widget Access**

Don't access child widgets directly from parent views:

```python
# ❌ BAD: Direct access
self.controls_section.start_button.setEnabled(False)

# ✅ GOOD: Use methods
self.controls_section.set_processing_state()
```

### 2. **Magic Strings**

Never use hardcoded strings:

```python
# ❌ BAD
if status == "Processing":
    # ...

# ✅ GOOD
from ui.ui_constants import StatusMessages
if status == StatusMessages.PROCESSING:
    # ...
```

### 3. **Code Duplication**

If you find yourself copying code, extract it:

```python
# ❌ BAD: Duplicated in multiple views
def _on_finished(self, success: bool, message: str):
    self.controls_section.start_button.setEnabled(True)
    self.controls_section.pause_button.setEnabled(False)
    # ... repeated code

# ✅ GOOD: Use base class or helper methods
def _on_finished(self, success: bool, message: str):
    self.controls_section.set_idle_state()
    # ... specific logic
```

### 4. **Fragile Button Connections**

Don't rely on button text for connections:

```python
# ❌ BAD: Breaks if text changes
for button in widget.findChildren(QPushButton):
    if button.text() == "↑":
        # ...

# ✅ GOOD: Use object references
widget.up_button.clicked.connect(...)
```

### 5. **Missing Error Handling**

Always validate inputs and handle errors:

```python
# ❌ BAD: No validation
def start_operation(self):
    url = self.url_input.text()
    # Start immediately - might fail!

# ✅ GOOD: Validate first
def start_operation(self):
    valid, error_msg = self.handlers.validate_inputs(...)
    if not valid:
        QMessageBox.warning(self, "Error", error_msg)
        return
    # ...
```

---

## Adding New Components

### Step 1: Create the Component

```python
# src/ui/views/my_view/my_section.py
from PySide6.QtWidgets import QGroupBox, QVBoxLayout
from ui.styles import get_group_box_style

class MySection(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("My Section", parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        # Add your widgets
        self.setLayout(layout)
        self.setStyleSheet(get_group_box_style())
```

### Step 2: Add Constants

```python
# src/ui/ui_constants.py
class ButtonText:
    MY_BUTTON: Final[str] = "My Button"
```

### Step 3: Use Configuration

```python
# src/ui/view_config.py
class ViewConfig:
    MY_SECTION_SPACING: Final[int] = 15
```

### Step 4: Integrate into View

```python
# src/ui/views/my_view/my_view.py
class MyView(BaseView):
    def setup_ui(self):
        main_layout = self.get_main_layout()
        self.my_section = MySection()
        main_layout.addWidget(self.my_section)
```

---

## Summary

Key takeaways:

1. **Use base classes** - Don't duplicate code
2. **Use constants** - No magic strings
3. **Use configuration** - No hardcoded numbers
4. **Use state methods** - Don't manipulate widgets directly
5. **Use type hints** - Better readability
6. **Use docstrings** - Document your code
7. **Follow patterns** - Consistency is key

Remember: **Code is read more often than it's written**. Write for readability and maintainability!

