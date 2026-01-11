"""
UI Event Logger - Logs all UI interactions to console.

This module provides utilities to log every UI action for debugging:
- Button clicks
- Input field changes
- View navigation
- Menu selections
- Progress updates
- Error handling
"""

import logging
from typing import Callable, Any, Optional
from functools import wraps
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QObject, Signal, QEvent

from core.logger import get_logger

logger = get_logger("ui.event_logger")


class UIEventLogger:
    """Centralized UI event logging system."""
    
    # Event categories for filtering
    CLICK = "CLICK"
    INPUT = "INPUT"
    NAVIGATION = "NAVIGATION"
    PROCESS = "PROCESS"
    ERROR = "ERROR"
    DEBUG = "DEBUG"
    
    _enabled = True
    _console_logger: Optional[logging.Logger] = None
    
    @classmethod
    def enable(cls) -> None:
        """Enable UI event logging."""
        cls._enabled = True
        cls._get_console_logger().info("UI Event Logging ENABLED")
    
    @classmethod
    def disable(cls) -> None:
        """Disable UI event logging."""
        cls._enabled = False
        logger.info("UI Event Logging DISABLED")
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if UI event logging is enabled."""
        return cls._enabled
    
    @classmethod
    def _get_console_logger(cls) -> logging.Logger:
        """Get or create console logger with DEBUG level."""
        if cls._console_logger is None:
            cls._console_logger = logging.getLogger("act.ui.events")
            cls._console_logger.setLevel(logging.DEBUG)
            
            # Ensure console handler exists with DEBUG level
            has_console = False
            for handler in cls._console_logger.handlers:
                if isinstance(handler, logging.StreamHandler):
                    handler.setLevel(logging.DEBUG)
                    has_console = True
            
            if not has_console:
                import sys
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(logging.DEBUG)
                formatter = logging.Formatter(
                    "[UI EVENT] %(levelname)-8s | %(message)s"
                )
                console_handler.setFormatter(formatter)
                cls._console_logger.addHandler(console_handler)
                cls._console_logger.propagate = False
        
        return cls._console_logger
    
    @classmethod
    def log_event(
        cls,
        category: str,
        message: str,
        widget_name: Optional[str] = None,
        details: Optional[dict] = None
    ) -> None:
        """
        Log a UI event.
        
        Args:
            category: Event category (CLICK, INPUT, NAVIGATION, etc.)
            message: Event description
            widget_name: Name of the widget that triggered the event
            details: Additional context as dictionary
        """
        if not cls._enabled:
            return
        
        console = cls._get_console_logger()
        
        # Build message (using text instead of emojis to avoid Unicode encoding issues)
        prefix_map = {
            cls.CLICK: "[CLICK]",
            cls.INPUT: "[INPUT]",
            cls.NAVIGATION: "[NAV]",
            cls.PROCESS: "[PROC]",
            cls.ERROR: "[ERROR]",
            cls.DEBUG: "[DEBUG]",
        }

        prefix = prefix_map.get(category, "[EVENT]")
        
        # Format main message
        full_msg = f"{prefix} [{category}] {message}"
        
        if widget_name:
            full_msg += f" | Widget: {widget_name}"
        
        if details:
            details_str = " | ".join(f"{k}={v}" for k, v in details.items())
            full_msg += f" | {details_str}"
        
        # Log at appropriate level
        if category == cls.ERROR:
            console.error(full_msg)
        else:
            console.debug(full_msg)
    
    @classmethod
    def log_button_click(
        cls,
        button_name: str,
        action: str = "clicked",
        details: Optional[dict] = None
    ) -> None:
        """Log a button click event."""
        cls.log_event(
            cls.CLICK,
            f"Button '{button_name}' {action}",
            details=details
        )
    
    @classmethod
    def log_input_change(
        cls,
        field_name: str,
        new_value: str,
        field_type: str = "text"
    ) -> None:
        """Log an input field change."""
        # Truncate long values for display
        display_value = new_value[:50] + "..." if len(str(new_value)) > 50 else new_value
        cls.log_event(
            cls.INPUT,
            f"Input '{field_name}' changed to: '{display_value}'"
        )
    
    @classmethod
    def log_navigation(
        cls,
        from_view: str,
        to_view: str,
        reason: str = ""
    ) -> None:
        """Log navigation between views."""
        msg = f"Navigation: {from_view} -> {to_view}"
        if reason:
            msg += f" ({reason})"
        cls.log_event(cls.NAVIGATION, msg)
    
    @classmethod
    def log_process(
        cls,
        process_name: str,
        status: str,
        details: Optional[dict] = None
    ) -> None:
        """Log a background process event."""
        cls.log_event(
            cls.PROCESS,
            f"{process_name}: {status}",
            details=details
        )
    
    @classmethod
    def log_error(
        cls,
        error_msg: str,
        context: Optional[str] = None
    ) -> None:
        """Log an error event."""
        msg = error_msg
        if context:
            msg += f" [{context}]"
        cls.log_event(cls.ERROR, msg)


def log_button_click(func: Callable) -> Callable:
    """
    Decorator to log button clicks.
    
    Usage:
        @log_button_click
        def on_click():
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        button_name = func.__name__.replace("on_", "").replace("_", " ").title()
        UIEventLogger.log_button_click(button_name, "activated")
        return func(*args, **kwargs)
    return wrapper


def log_input_change(field_name: str) -> Callable:
    """
    Decorator to log input field changes.
    
    Usage:
        @log_input_change("email")
        def on_email_changed(text):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to extract the new value from args
            new_value = args[0] if args else kwargs.get("text", "")
            UIEventLogger.log_input_change(field_name, str(new_value))
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_navigation(from_view: str) -> Callable:
    """
    Decorator to log navigation events.
    
    Usage:
        @log_navigation("LandingPage")
        def show_scraper_view():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            to_view = func.__name__.replace("show_", "").replace("_", " ").title()
            UIEventLogger.log_navigation(from_view, to_view)
            return func(*args, **kwargs)
        return wrapper
    return decorator


class EventLoggingMixin:
    """
    Mixin class to add event logging to widgets.
    
    Usage:
        class MyButton(EventLoggingMixin, QPushButton):
            pass
    """
    
    def log_ui_event(
        self,
        category: str,
        message: str,
        details: Optional[dict] = None
    ) -> None:
        """Log a UI event with this widget as context."""
        widget_name = self.objectName() or self.__class__.__name__
        UIEventLogger.log_event(
            category,
            message,
            widget_name=widget_name,
            details=details
        )
    
    def log_click(self, action: str = "clicked") -> None:
        """Log a click event."""
        widget_name = self.objectName() or self.__class__.__name__
        UIEventLogger.log_button_click(widget_name, action)
    
    def log_change(self, value: Any, field_type: str = "generic") -> None:
        """Log a change event."""
        widget_name = self.objectName() or self.__class__.__name__
        UIEventLogger.log_input_change(widget_name, str(value), field_type)


# Helper function to connect signals with logging
def connect_with_logging(
    signal: Signal,
    slot: Callable,
    event_name: str,
    category: str = UIEventLogger.CLICK
) -> None:
    """
    Connect a signal to a slot with automatic logging.
    
    Usage:
        connect_with_logging(button.clicked, self.on_click, "Save Button")
    """
    def logged_slot(*args, **kwargs):
        UIEventLogger.log_event(category, f"{event_name} triggered")
        return slot(*args, **kwargs)
    
    signal.connect(logged_slot)


class GlobalEventFilter(QObject):
    """
    Global event filter to automatically log all widget interactions.

    Install this on QApplication to capture all widget clicks, input changes,
    and other interactions across the entire application.
    """

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._tracking_widgets = set()
        self._event_count = 0
        self._init_phase = True  # Suppress noisy events during initialization
        self._init_threshold = 10000  # Events before considering init phase done
    
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Filter all events and log relevant interactions."""
        if not UIEventLogger.is_enabled():
            return False

        # Periodic debug logging to show filter is active (much less frequent)
        self._event_count += 1

        # Only log event count milestones, not during init
        if self._event_count % 10000 == 0:  # Every 10000 events
            UIEventLogger.log_event(
                UIEventLogger.DEBUG,
                f"Event filter processed {self._event_count} events"
            )

        event_type = event.type()
        
        # Log window close events
        if event_type == QEvent.Type.Close:
            if isinstance(watched, QWidget):
                widget_name = watched.objectName() or watched.__class__.__name__
                UIEventLogger.log_event(
                    UIEventLogger.DEBUG,
                    f"Window closing: {widget_name}",
                    widget_name=widget_name
                )
        
        # Log window show/hide (only for main windows and dialogs, not all widgets)
        elif event_type == QEvent.Type.Show:
            if isinstance(watched, QWidget) and hasattr(watched, 'windowTitle') and watched.windowTitle():
                widget_name = watched.objectName() or watched.__class__.__name__
                UIEventLogger.log_event(
                    UIEventLogger.DEBUG,
                    f"Window shown: {widget_name}",
                    widget_name=widget_name
                )

        elif event_type == QEvent.Type.Hide:
            if isinstance(watched, QWidget) and hasattr(watched, 'windowTitle') and watched.windowTitle():
                widget_name = watched.objectName() or watched.__class__.__name__
                UIEventLogger.log_event(
                    UIEventLogger.DEBUG,
                    f"Window hidden: {widget_name}",
                    widget_name=widget_name
                )
        
        # Log mouse button clicks on any widget
        elif event_type == QEvent.Type.MouseButtonPress:
            if isinstance(watched, QWidget):
                widget_name = watched.objectName() or watched.__class__.__name__
                widget_text = ""

                # Try to get button text if it's a button
                if hasattr(watched, 'text'):
                    try:
                        text = watched.text()
                        if text:
                            widget_text = f" '{text}'"
                    except:
                        pass

                # Get widget hierarchy for better identification
                hierarchy = []
                parent = watched.parent()
                while parent and len(hierarchy) < 3:  # Limit depth to avoid too much noise
                    parent_name = parent.objectName() or parent.__class__.__name__
                    hierarchy.append(parent_name)
                    parent = parent.parent()

                hierarchy_str = f" (in {'.'.join(reversed(hierarchy))})" if hierarchy else ""

                # Log ALL widget clicks without filtering
                UIEventLogger.log_event(
                    UIEventLogger.CLICK,
                    f"Mouse press on {widget_name}{widget_text}{hierarchy_str}",
                    widget_name=widget_name
                )
        
        # Log mouse button double clicks
        elif event_type == QEvent.Type.MouseButtonDblClick:
            if isinstance(watched, QWidget):
                widget_name = watched.objectName() or watched.__class__.__name__
                widget_text = ""

                if hasattr(watched, 'text'):
                    try:
                        text = watched.text()
                        if text:
                            widget_text = f" '{text}'"
                    except:
                        pass

                UIEventLogger.log_event(
                    UIEventLogger.CLICK,
                    f"Double-click on {widget_name}{widget_text}",
                    widget_name=widget_name
                )

        # Log mouse button release (for buttons that activate on release)
        elif event_type == QEvent.Type.MouseButtonRelease:
            if isinstance(watched, QWidget):
                widget_name = watched.objectName() or watched.__class__.__name__
                class_name = watched.__class__.__name__
                
                # Log for interactive widgets
                if any(x in class_name for x in ['Button', 'CheckBox', 'RadioButton', 'ComboBox', 'Slider', 'Tab']):
                    widget_text = ""
                    if hasattr(watched, 'text'):
                        try:
                            text = watched.text()
                            if text:
                                widget_text = f" '{text}'"
                        except:
                            pass
                    
                    UIEventLogger.log_event(
                        UIEventLogger.CLICK,
                        f"{class_name} activated{widget_text}",
                        widget_name=widget_name
                    )
        
        # Log text input changes
        elif event_type == QEvent.Type.KeyPress:
            if isinstance(watched, QWidget):
                # Only log for input widgets
                class_name = watched.__class__.__name__
                if any(x in class_name for x in ['LineEdit', 'TextEdit', 'ComboBox', 'SpinBox']):
                    widget_name = watched.objectName() or class_name
                    # Get the key pressed
                    key_event = event
                    key_text = key_event.text() if hasattr(key_event, 'text') else ""
                    
                    UIEventLogger.log_event(
                        UIEventLogger.INPUT,
                        f"Key pressed in {widget_name}" + (f": '{key_text}'" if key_text and len(key_text) == 1 else ""),
                        widget_name=widget_name
                    )

        # Log focus events
        elif event_type == QEvent.Type.FocusIn:
            if isinstance(watched, QWidget):
                widget_name = watched.objectName() or watched.__class__.__name__
                UIEventLogger.log_event(
                    UIEventLogger.DEBUG,
                    f"Focus gained: {widget_name}",
                    widget_name=widget_name
                )

        elif event_type == QEvent.Type.FocusOut:
            if isinstance(watched, QWidget):
                widget_name = watched.objectName() or watched.__class__.__name__
                UIEventLogger.log_event(
                    UIEventLogger.DEBUG,
                    f"Focus lost: {widget_name}",
                    widget_name=widget_name
                )

        # Log enter/leave events (hover) - only for interactive widgets
        elif event_type == QEvent.Type.Enter:
            if isinstance(watched, QWidget) and any(x in watched.__class__.__name__ for x in ['Button', 'ComboBox', 'LineEdit', 'TextEdit', 'CheckBox']):
                widget_name = watched.objectName() or watched.__class__.__name__
                UIEventLogger.log_event(
                    UIEventLogger.DEBUG,
                    f"Mouse entered: {widget_name}",
                    widget_name=widget_name
                )

        elif event_type == QEvent.Type.Leave:
            if isinstance(watched, QWidget) and any(x in watched.__class__.__name__ for x in ['Button', 'ComboBox', 'LineEdit', 'TextEdit', 'CheckBox']):
                widget_name = watched.objectName() or watched.__class__.__name__
                UIEventLogger.log_event(
                    UIEventLogger.DEBUG,
                    f"Mouse left: {widget_name}",
                    widget_name=widget_name
                )

        # Don't consume the event - let it propagate
        return False
    
    @classmethod
    def install_on_app(cls, app) -> 'GlobalEventFilter':
        """
        Install the global event filter on a QApplication.

        Args:
            app: QApplication instance

        Returns:
            The created GlobalEventFilter instance
        """
        event_filter = cls()
        app.installEventFilter(event_filter)
        UIEventLogger.log_event(
            UIEventLogger.DEBUG,
            "Global event filter installed - monitoring all widget interactions"
        )
        # Test the filter is working by logging a test event
        UIEventLogger.log_event(
            UIEventLogger.DEBUG,
            "Event filter test: If you see this, the filter is active!"
        )
        return event_filter
