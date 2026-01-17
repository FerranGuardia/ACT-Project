"""
Activity Console Widget - Displays processing activities in the UI.

A Qt widget that displays selective activity logging with proper styling
for different activity types, especially gap detection and merging operations.
"""

from PySide6.QtWidgets import (
    QTextEdit, QVBoxLayout, QWidget, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QFrame, QScrollBar
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QObject
from PySide6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor

from core.activity_console import (
    ActivityConsole, ActivityEntry, ActivityCategory, get_activity_console
)
from ui.styles import get_group_box_style, COLORS


class ActivityConsoleWidget(QFrame):
    """
    Widget for displaying processing activities with selective filtering.

    Shows only meaningful activities to avoid overwhelming users while
    providing critical visibility into gap detection, merging, and errors.
    """

    # Signal emitted when important alerts are shown
    alert_triggered = Signal(str)  # Alert message

    # Signal for thread-safe activity updates
    _activity_received = Signal(object)  # ActivityEntry

    def __init__(self, parent=None, max_lines: int = 100):
        super().__init__(parent)
        self.max_lines = max_lines
        self.activity_console = get_activity_console()
        self._alert_categories = {
            ActivityCategory.GAP_DETECTION_FOUND,
            ActivityCategory.GAP_USER_ALERT,
            ActivityCategory.GAP_USER_MANUAL_NEEDED,
            ActivityCategory.PROCESSING_ERROR,
            ActivityCategory.MERGE_BATCH_FAILED,
        }

        self.setup_ui()
        self.connect_signals()
        self.load_existing_activities()

    def setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header with controls
        header_layout = QHBoxLayout()

        title_label = QLabel("Activity Console")
        title_label.setStyleSheet(f"font-weight: bold; color: {COLORS['text_primary']};")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Filter combo box
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Activities", None)
        self.filter_combo.addItem("Gaps & Merging", [
            ActivityCategory.GAP_DETECTION_START,
            ActivityCategory.GAP_DETECTION_FOUND,
            ActivityCategory.GAP_DETECTION_CHAPTER_MISSING,
            ActivityCategory.GAP_AUTO_RESOLVE_START,
            ActivityCategory.MERGE_BATCH_START,
            ActivityCategory.MERGE_BATCH_PROGRESS,
            ActivityCategory.MERGE_BATCH_COMPLETE,
        ])
        self.filter_combo.addItem("TTS Progress", [
            ActivityCategory.TTS_STRATEGY_SELECTED,
            ActivityCategory.TTS_CHUNKING,
            ActivityCategory.TTS_CONVERTING_CHUNK,
            ActivityCategory.TTS_COMPLETE,
        ])
        self.filter_combo.addItem("Errors Only", [
            ActivityCategory.PROCESSING_ERROR,
            ActivityCategory.TTS_FAILED,
            ActivityCategory.MERGE_BATCH_FAILED,
            ActivityCategory.SCRAPE_FAILED,
        ])
        self.filter_combo.currentIndexChanged.connect(self.apply_filter)
        header_layout.addWidget(QLabel("Filter:"))
        header_layout.addWidget(self.filter_combo)

        # Clear button
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_console)
        header_layout.addWidget(clear_button)

        layout.addLayout(header_layout)

        # Console text area
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setMaximumHeight(300)
        self.console_text.setFont(QFont("Consolas", 9))  # Monospace for better alignment

        # Style the console
        console_style = f"""
        QTextEdit {{
            background-color: {COLORS['bg_content']};
            border: 1px solid {COLORS['border']};
            border-radius: 3px;
            padding: 5px;
        }}
        """
        self.console_text.setStyleSheet(console_style)

        layout.addWidget(self.console_text)

        # Set overall widget style
        self.setStyleSheet(get_group_box_style())
        self.setFrameStyle(QFrame.Box)
        self.setMaximumHeight(400)

    def connect_signals(self):
        """Connect to activity console signals."""
        self.activity_console.add_listener(self.on_new_activity)
        self._activity_received.connect(self._safe_append_activity)

    def disconnect_signals(self):
        """Disconnect from activity console signals."""
        self.activity_console.remove_listener(self.on_new_activity)
        self._activity_received.disconnect(self._safe_append_activity)

    def load_existing_activities(self):
        """Load recent activities on startup."""
        recent_activities = self.activity_console.get_recent_activities(self.max_lines)
        for activity in recent_activities:
            self.append_activity(activity, skip_scroll=True)

        # Scroll to bottom after loading
        self.scroll_to_bottom()

    def on_new_activity(self, activity: ActivityEntry):
        """Handle new activity from the console."""
        # Only show activities meant for UI
        if not activity.show_in_ui:
            return

        # Emit signal to ensure UI update happens in main thread
        self._activity_received.emit(activity)

    def _safe_append_activity(self, activity):
        """Safely append activity from main thread."""
        # activity is passed as object from signal, ensure it's ActivityEntry
        if not isinstance(activity, ActivityEntry):
            return

        self.append_activity(activity)

        # Check for alerts
        if activity.category in self._alert_categories:
            self.alert_triggered.emit(activity.format_for_display())

    def append_activity(self, activity: ActivityEntry, skip_scroll: bool = False):
        """Append an activity to the console."""
        # Apply current filter
        current_filter = self.filter_combo.currentData()
        if current_filter and activity.category not in current_filter:
            return

        # Format for display
        formatted_text = activity.format_for_display()
        timestamp = activity.timestamp.strftime("%H:%M:%S")
        line = f"[{timestamp}] {formatted_text}\n"

        # Determine text format based on category
        text_format = self._get_text_format_for_category(activity.category)

        # Insert text with formatting
        cursor = self.console_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(line, text_format)

        # Maintain max lines
        self._trim_to_max_lines()

        # Scroll to bottom unless loading existing activities
        if not skip_scroll:
            self.scroll_to_bottom()

    def _get_text_format_for_category(self, category: ActivityCategory) -> QTextCharFormat:
        """Get appropriate text formatting for activity category."""
        format = QTextCharFormat()

        # Default formatting
        format.setForeground(QColor(COLORS['text_primary']))

        # Special formatting for different categories
        if category in {ActivityCategory.PROCESSING_ERROR,
                       ActivityCategory.TTS_FAILED,
                       ActivityCategory.MERGE_BATCH_FAILED,
                       ActivityCategory.SCRAPE_FAILED}:
            format.setForeground(QColor("#e74c3c"))  # Red for errors
            format.setFontWeight(700)  # Bold

        elif category in {ActivityCategory.GAP_DETECTION_FOUND,
                          ActivityCategory.GAP_USER_ALERT,
                          ActivityCategory.GAP_USER_MANUAL_NEEDED,
                          ActivityCategory.PROCESSING_WARNING}:
            format.setForeground(QColor("#f39c12"))  # Orange for warnings/alerts
            format.setFontWeight(600)  # Semi-bold

        elif category in {ActivityCategory.GAP_DETECTION_START,
                          ActivityCategory.GAP_AUTO_RESOLVE_START,
                          ActivityCategory.MERGE_BATCH_START}:
            format.setForeground(QColor("#3498db"))  # Blue for operations
            format.setFontWeight(600)

        elif category in {ActivityCategory.GAP_RESOLUTION_COMPLETE,
                          ActivityCategory.TTS_COMPLETE,
                          ActivityCategory.SCRAPE_COMPLETE,
                          ActivityCategory.MERGE_BATCH_COMPLETE,
                          ActivityCategory.FILE_VALIDATION}:
            format.setForeground(QColor("#27ae60"))  # Green for success
            format.setFontWeight(600)

        return format

    def apply_filter(self):
        """Apply the current filter to displayed activities."""
        current_filter = self.filter_combo.currentData()

        # Clear console
        self.console_text.clear()

        # Reload activities with filter
        activities = self.activity_console.get_recent_activities(self.max_lines)

        for activity in activities:
            if not activity.show_in_ui:
                continue
            if current_filter and activity.category not in current_filter:
                continue
            self.append_activity(activity, skip_scroll=True)

        self.scroll_to_bottom()

    def clear_console(self):
        """Clear the console display."""
        self.console_text.clear()

    def scroll_to_bottom(self):
        """Scroll to the bottom of the console."""
        scrollbar = self.console_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _trim_to_max_lines(self):
        """Trim console to maximum lines to prevent memory issues."""
        # Count current lines
        text = self.console_text.toPlainText()
        lines = text.split('\n')

        if len(lines) > self.max_lines:
            # Keep only the most recent lines
            keep_lines = lines[-(self.max_lines):]
            new_text = '\n'.join(keep_lines)

            # Temporarily disconnect to avoid recursion
            self.disconnect_signals()
            self.console_text.setPlainText(new_text)
            self.connect_signals()

    def get_operation_activities(self, operation_id: str) -> str:
        """
        Get all activities for a specific operation as formatted text.

        Useful for debugging or exporting operation logs.
        """
        activities = self.activity_console.get_activities_by_operation(operation_id)
        lines = []

        for activity in activities:
            timestamp = activity.timestamp.strftime("%H:%M:%S")
            formatted = activity.format_for_display()
            lines.append(f"[{timestamp}] {formatted}")

        return '\n'.join(lines)


class ActivityConsoleUpdater(QThread):
    """
    Background thread to periodically update the console.

    Useful if the console widget might miss some activities due to
    threading issues or if you want to batch updates.
    """

    update_needed = Signal()

    def __init__(self, console_widget: ActivityConsoleWidget):
        super().__init__()
        self.console_widget = console_widget
        self.running = True

    def run(self):
        """Run the update loop."""
        while self.running:
            self.update_needed.emit()
            self.sleep(1)  # Update every second

    def stop(self):
        """Stop the update thread."""
        self.running = False