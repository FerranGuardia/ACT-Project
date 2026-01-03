"""
Error Handling Utilities - Standardized error dialog functions.

Provides consistent error handling across all views following industry standards.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget  # type: ignore[unused-import]

from PySide6.QtWidgets import QMessageBox

from ui.ui_constants import DialogMessages


def show_validation_error(parent: "QWidget", message: str) -> None:
    """
    Show validation error dialog.
    
    Args:
        parent: Parent widget for the dialog
        message: Error message to display
    """
    QMessageBox.warning(parent, DialogMessages.VALIDATION_ERROR_TITLE, message)


def show_already_running_error(parent: "QWidget") -> None:
    """
    Show already running error dialog.
    
    Args:
        parent: Parent widget for the dialog
    """
    QMessageBox.warning(
        parent,
        DialogMessages.ALREADY_RUNNING_TITLE,
        DialogMessages.ALREADY_RUNNING_MSG
    )


def show_success(parent: "QWidget", message: str) -> None:
    """
    Show success dialog.
    
    Args:
        parent: Parent widget for the dialog
        message: Success message to display
    """
    QMessageBox.information(parent, DialogMessages.SUCCESS_TITLE, message)


def show_error(parent: "QWidget", message: str) -> None:
    """
    Show error dialog.
    
    Args:
        parent: Parent widget for the dialog
        message: Error message to display
    """
    QMessageBox.warning(parent, DialogMessages.ERROR_TITLE, message)


def show_confirmation(
    parent: "QWidget",
    title: str,
    message: str
) -> bool:
    """
    Show confirmation dialog.
    
    Args:
        parent: Parent widget for the dialog
        title: Dialog title
        message: Confirmation message
        
    Returns:
        True if user clicked Yes, False otherwise
    """
    reply = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )
    return reply == QMessageBox.StandardButton.Yes


def show_no_directory_error(parent: "QWidget") -> None:
    """
    Show no directory selected error dialog.
    
    Args:
        parent: Parent widget for the dialog
    """
    QMessageBox.warning(
        parent,
        DialogMessages.NO_DIRECTORY_TITLE,
        DialogMessages.NO_DIRECTORY_MSG
    )


def show_directory_not_found_error(parent: "QWidget", directory_path: str) -> None:
    """
    Show directory not found error dialog.
    
    Args:
        parent: Parent widget for the dialog
        directory_path: Path to the directory that was not found
    """
    QMessageBox.warning(
        parent,
        DialogMessages.DIRECTORY_NOT_FOUND_TITLE,
        DialogMessages.DIRECTORY_NOT_FOUND_MSG_FORMAT.format(path=directory_path)
    )


def show_error_opening_folder(parent: "QWidget", error: str) -> None:
    """
    Show error opening folder dialog.
    
    Args:
        parent: Parent widget for the dialog
        error: Error message
    """
    QMessageBox.warning(
        parent,
        DialogMessages.ERROR_OPENING_FOLDER_TITLE,
        DialogMessages.ERROR_OPENING_FOLDER_MSG_FORMAT.format(error=error)
    )


__all__ = [
    'show_validation_error',
    'show_already_running_error',
    'show_success',
    'show_error',
    'show_confirmation',
    'show_no_directory_error',
    'show_directory_not_found_error',
    'show_error_opening_folder',
]

