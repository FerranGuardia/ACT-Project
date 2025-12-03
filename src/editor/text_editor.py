"""
Text Editor Widget - PyQt6-based text editor for editing scraped content.

Provides a simple but functional text editor widget that can be integrated
into the main UI. Uses QPlainTextEdit for plain text editing.
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QPlainTextEdit, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor

from core.config_manager import get_config
from core.logger import get_logger

logger = get_logger("editor.text_editor")


class TextEditor(QPlainTextEdit):
    """
    Text editor widget for editing scraped webnovel content.
    
    Features:
    - Plain text editing (QPlainTextEdit)
    - File operations (open, save, new)
    - Configurable font settings
    - Word wrap support
    - Undo/redo support
    - Integration with config manager and logger
    """
    
    # Signals
    text_changed = pyqtSignal()  # Emitted when text content changes
    file_saved = pyqtSignal(str)  # Emitted when file is saved (path)
    file_opened = pyqtSignal(str)  # Emitted when file is opened (path)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize text editor widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.config = get_config()
        self._current_file: Optional[Path] = None
        self._is_modified = False
        
        self._setup_editor()
        self._load_settings()
        
        # Connect signals
        self.textChanged.connect(self._on_text_changed)
        
        logger.debug("Text editor initialized")
    
    def _setup_editor(self) -> None:
        """Setup editor appearance and behavior."""
        # Set tab width (4 spaces)
        self.setTabStopDistance(40)
        
        # Enable undo/redo
        self.setUndoRedoEnabled(True)
        
        # Set placeholder text
        self.setPlaceholderText("Start typing or open a file...")
    
    def _load_settings(self) -> None:
        """Load editor settings from config manager."""
        # Font settings
        font_family = self.config.get("editor.font_family", "Consolas")
        font_size = self.config.get("editor.font_size", 12)
        word_wrap = self.config.get("editor.word_wrap", True)
        
        # Set font
        font = QFont(font_family, font_size)
        self.setFont(font)
        
        # Set word wrap
        if word_wrap:
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        else:
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        logger.debug(f"Editor settings loaded: font={font_family} {font_size}pt, word_wrap={word_wrap}")
    
    def _on_text_changed(self) -> None:
        """Handle text change event."""
        self._is_modified = True
        self.text_changed.emit()
    
    def new_file(self) -> bool:
        """
        Create a new empty file.
        
        Returns:
            True if successful, False otherwise
        """
        if self._is_modified:
            # In a full implementation, you'd ask user to save first
            logger.warning("Current file has unsaved changes")
        
        self.clear()
        self._current_file = None
        self._is_modified = False
        
        logger.info("New file created")
        return True
    
    def open_file(self, file_path: Path) -> bool:
        """
        Open a text file.
        
        Args:
            file_path: Path to file to open
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            self.setPlainText(content)
            self._current_file = file_path
            self._is_modified = False
            
            # Move cursor to beginning
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.setTextCursor(cursor)
            
            self.file_opened.emit(str(file_path))
            logger.info(f"File opened: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error opening file {file_path}: {e}")
            return False
    
    def save_file(self, file_path: Optional[Path] = None) -> bool:
        """
        Save current content to file.
        
        Args:
            file_path: Path to save file. If None, uses current file path
        
        Returns:
            True if successful, False otherwise
        """
        # Use provided path or current file path
        if file_path is None:
            if self._current_file is None:
                logger.error("No file path specified and no current file")
                return False
            file_path = self._current_file
        
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.toPlainText())
            
            self._current_file = file_path
            self._is_modified = False
            
            self.file_saved.emit(str(file_path))
            logger.info(f"File saved: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving file {file_path}: {e}")
            return False
    
    def get_current_file(self) -> Optional[Path]:
        """
        Get current file path.
        
        Returns:
            Current file path or None if no file is open
        """
        return self._current_file
    
    def is_modified(self) -> bool:
        """
        Check if current content has been modified.
        
        Returns:
            True if modified, False otherwise
        """
        return self._is_modified
    
    def set_modified(self, modified: bool) -> None:
        """
        Set modified flag.
        
        Args:
            modified: True if modified, False otherwise
        """
        self._is_modified = modified
    
    def get_text(self) -> str:
        """
        Get current text content.
        
        Returns:
            Current text content
        """
        return self.toPlainText()
    
    def set_text(self, text: str) -> None:
        """
        Set text content.
        
        Args:
            text: Text content to set
        """
        self.setPlainText(text)
        self._is_modified = True
    
    def append_text(self, text: str) -> None:
        """
        Append text to current content.
        
        Args:
            text: Text to append
        """
        self.appendPlainText(text)
        self._is_modified = True
    
    def clear_text(self) -> None:
        """Clear all text content."""
        self.clear()
        self._is_modified = True
    
    def find_text(self, search_text: str, case_sensitive: bool = False) -> bool:
        """
        Find text in editor.
        
        Args:
            search_text: Text to search for
            case_sensitive: Whether search should be case sensitive
        
        Returns:
            True if text found, False otherwise
        """
        flags = QTextCursor.FindFlag(0)
        if case_sensitive:
            flags |= QTextCursor.FindFlag.FindCaseSensitively
        
        cursor = self.textCursor()
        found = self.find(search_text, flags)
        
        if found:
            logger.debug(f"Text found: {search_text}")
        else:
            logger.debug(f"Text not found: {search_text}")
        
        return found
    
    def replace_text(self, search_text: str, replace_text: str, replace_all: bool = False) -> int:
        """
        Replace text in editor.
        
        Args:
            search_text: Text to search for
            replace_text: Text to replace with
            replace_all: If True, replace all occurrences; if False, replace current only
        
        Returns:
            Number of replacements made
        """
        if replace_all:
            # Replace all occurrences
            content = self.toPlainText()
            count = content.count(search_text)
            if count > 0:
                new_content = content.replace(search_text, replace_text)
                self.setPlainText(new_content)
                self._is_modified = True
                logger.info(f"Replaced {count} occurrences of '{search_text}'")
                return count
            return 0
        else:
            # Replace current occurrence
            cursor = self.textCursor()
            if cursor.hasSelection() and cursor.selectedText() == search_text:
                cursor.insertText(replace_text)
                self._is_modified = True
                logger.debug(f"Replaced '{search_text}' with '{replace_text}'")
                return 1
            return 0
    
    def refresh_settings(self) -> None:
        """Reload settings from config manager."""
        self._load_settings()
        logger.debug("Editor settings refreshed")

