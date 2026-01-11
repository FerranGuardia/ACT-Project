"""
Input Validation and Sanitization Utilities

Provides robust validation and sanitization for URLs, text, and other inputs
to prevent security vulnerabilities and improve reliability.
"""

import re
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
from urllib.parse import urlparse
from cerberus import Validator
import bleach

from core.logger import get_logger

logger = get_logger("utils.validation")


class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


class InputValidator:
    """Comprehensive input validation and sanitization"""

    def __init__(self):
        """Initialize validator with schemas"""
        self.url_schema = {
            'url': {
                'type': 'string',
                'regex': r'^https?://[^\s/$.?#].[^\s]*$',
                'required': True,
                'maxlength': 2048  # Reasonable URL length limit
            }
        }

        self.tts_request_schema = {
            'text': {
                'type': 'string',
                'required': True,
                'maxlength': 50000,  # Reasonable text limit
                'minlength': 1
            },
            'voice': {
                'type': 'string',
                'required': True,
                'regex': r'^[a-zA-Z0-9\-_\.]+$',  # Alphanumeric with safe chars
                'maxlength': 100
            },
            'rate': {
                'type': 'number',
                'required': False,
                'min': -100,
                'max': 100
            },
            'pitch': {
                'type': 'number',
                'required': False,
                'min': -100,
                'max': 100
            },
            'volume': {
                'type': 'number',
                'required': False,
                'min': -100,
                'max': 100
            }
        }

        self.url_validator = Validator(self.url_schema)
        self.tts_validator = Validator(self.tts_request_schema)

    def validate_url(self, url: str) -> Tuple[bool, str]:
        """
        Validate URL for scraping requests

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, error_message_or_clean_url)
        """
        try:
            # Basic type checking
            if url is None:
                return False, "URL cannot be None"
            if not isinstance(url, str):
                return False, f"URL must be a string, got {type(url).__name__}"

            # Check for malicious patterns BEFORE sanitization
            if self._is_malicious_url(url):
                return False, "Potentially malicious URL detected"

            # Check for null bytes (security risk)
            if '\x00' in url or '%00' in url:
                return False, "URL contains null bytes"

            # Sanitize URL
            clean_url = self._sanitize_url(url)

            # Validate against schema
            if not self.url_validator.validate({'url': clean_url}):
                error_msg = "; ".join(self.url_validator.errors.get('url', ['Invalid URL']))
                return False, f"URL validation failed: {error_msg}"

            # Check for known novel sites
            if not self._is_supported_site(clean_url):
                logger.warning(f"URL {clean_url} may not be a supported novel site")

            return True, clean_url

        except Exception as e:
            logger.error(f"Error validating URL {url}: {e}")
            return False, f"URL validation error: {str(e)}"

    def validate_tts_request(self, request_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate TTS conversion request

        Args:
            request_data: Dictionary containing TTS request parameters

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Sanitize text content
            if 'text' in request_data:
                request_data['text'] = self._sanitize_text(request_data['text'])

            # Validate against schema
            if not self.tts_validator.validate(request_data):
                errors = []
                for field, field_errors in self.tts_validator.errors.items():
                    errors.extend([f"{field}: {error}" for error in field_errors])
                error_msg = "; ".join(errors)
                return False, f"TTS validation failed: {error_msg}"

            # Additional content checks
            text = request_data.get('text', '')
            if self._is_suspicious_content(text):
                return False, "Text content appears suspicious or potentially harmful"

            return True, ""

        except Exception as e:
            logger.error(f"Error validating TTS request: {e}")
            return False, f"TTS validation error: {str(e)}"

    def _sanitize_url(self, url: str) -> str:
        """
        Sanitize and normalize URL

        Args:
            url: Raw URL string

        Returns:
            Sanitized URL
        """
        # Remove potentially dangerous characters while preserving URL structure
        url = bleach.clean(url, tags=[], strip=True)

        # Remove any null bytes or other dangerous characters
        url = url.replace('\x00', '').replace('\r', '').replace('\n', '')

        # Normalize the URL
        try:
            parsed = urlparse(url)
            # Reconstruct URL with proper encoding
            clean_url = parsed.geturl()
            return clean_url
        except Exception:
            # If parsing fails, return the cleaned version
            return url

    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text content for TTS

        Args:
            text: Raw text content

        Returns:
            Sanitized text
        """
        # Remove HTML tags and potentially harmful content
        import bleach
        text = bleach.clean(text, tags=[], strip=True)

        # Remove dangerous URL schemes
        import re
        text = re.sub(r'javascript:[^\s]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'data:[^\s]*', '', text, flags=re.IGNORECASE)
        # Remove event handlers
        text = re.sub(r'on\w+\s*=\s*[^\s>]*', '', text, flags=re.IGNORECASE)

        # Remove potentially harmful characters but preserve readability
        # Allow basic punctuation and common characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')

        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 consecutive newlines
        text = re.sub(r' {2,}', ' ', text)  # Max 1 consecutive space

        # Limit total length (reasonable for TTS)
        if len(text) > 50000:
            text = text[:50000] + "..."
            logger.warning("Text truncated to 50,000 characters for TTS processing")

        return text.strip()

    def _is_malicious_url(self, url: str) -> bool:
        """
        Check if URL appears malicious

        Args:
            url: URL to check

        Returns:
            True if potentially malicious
        """
        try:
            parsed = urlparse(url)

            # Check for suspicious patterns
            suspicious_patterns = [
                r'\.\.\.?[/\\]',  # Directory traversal (forward or backward slashes)
                r'<script',  # Script injection
                r'javascript:',  # JavaScript URLs
                r'data:',  # Data URLs (can be dangerous)
                r'\x00',  # Null bytes
                r'%00',  # URL-encoded null bytes
            ]

            url_str = url.lower()
            for pattern in suspicious_patterns:
                if re.search(pattern, url_str, re.IGNORECASE):
                    logger.warning(f"Malicious URL pattern detected: {pattern}")
                    return True

            # Check for extremely long domain/path segments
            if len(parsed.netloc) > 253 or any(len(part) > 63 for part in parsed.netloc.split('.')):
                return True

            return False

        except Exception:
            # If we can't parse it, be conservative and flag as suspicious
            return True

    def _is_supported_site(self, url: str) -> bool:
        """
        Check if URL is from a known supported novel site

        Args:
            url: URL to check

        Returns:
            True if from supported site
        """
        supported_domains = [
            'novelfull.com',
            'novelbin.com',
            'novelbin.net',
            'novelfull.net',
            'lightnovelworld.com',
            'readlightnovel.org',
            # Add more as needed
        ]

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Check exact matches and subdomain matches
            for supported in supported_domains:
                if domain == supported or domain.endswith('.' + supported):
                    return True

            return False

        except Exception:
            return False

    def _is_suspicious_content(self, text: str) -> bool:
        """
        Check if text content appears suspicious

        Args:
            text: Text to check

        Returns:
            True if potentially suspicious
        """
        # Check for excessive special characters
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s]', text)) / max(len(text), 1)
        if special_char_ratio > 0.3:  # More than 30% special characters
            return True

        # Check for potential script injection
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe',
            r'<object',
        ]

        text_lower = text.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, text_lower):
                logger.warning(f"Suspicious content pattern detected: {pattern}")
                return True

        return False

    def validate_file_path(self, file_path: Union[str, Path], allow_create: bool = True) -> Tuple[bool, str]:
        """
        Validate file path for security and safety.

        Args:
            file_path: Path to validate
            allow_create: Whether to allow paths that don't exist yet (for output files)

        Returns:
            Tuple of (is_valid, error_message_or_clean_path)
        """
        try:
            # Convert to Path object
            if isinstance(file_path, str):
                path = Path(file_path)
            else:
                path = file_path

            # Resolve to absolute path to prevent relative path attacks
            resolved_path = path.resolve()

            # Check for dangerous path patterns
            path_str = str(resolved_path)

            # Prevent directory traversal attacks
            if '..' in path_str or path_str.startswith('~'):
                return False, "Path contains directory traversal patterns"

            # Prevent absolute path manipulation
            if os.path.isabs(path_str):
                # For Windows, prevent UNC paths and other dangerous patterns
                if os.name == 'nt':
                    if path_str.startswith('\\\\') or ':\\' not in path_str:
                        return False, "Invalid Windows path format"
                else:
                    # For Unix-like systems, ensure path is under allowed directories
                    if not (path_str.startswith('/tmp/') or path_str.startswith('/home/') or
                           path_str.startswith('/var/tmp/') or path_str.startswith(str(Path.home()))):
                        return False, "Path must be under user home or temporary directory"

            # Check file extension for safety
            if resolved_path.suffix.lower() not in ['.txt', '.mp3', '.wav', '.json', '.log']:
                return False, f"Unsafe file extension: {resolved_path.suffix}"

            # Check path length
            if len(path_str) > 4096:  # Common filesystem path limit
                return False, "Path too long"

            # Check if parent directory exists (for safety)
            if not allow_create and not resolved_path.parent.exists():
                return False, f"Parent directory does not exist: {resolved_path.parent}"

            # Additional Windows-specific checks
            if os.name == 'nt':
                # Prevent paths with reserved names
                reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                                'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                                'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
                parts = resolved_path.parts
                for part in parts:
                    if part.upper() in reserved_names or part.upper().endswith(('.TXT', '.MP3', '.WAV')):
                        return False, f"Reserved filename detected: {part}"

            return True, str(resolved_path)

        except Exception as e:
            logger.error(f"Error validating file path {file_path}: {e}")
            return False, f"Path validation error: {str(e)}"

    def validate_directory_path(self, dir_path: Union[str, Path], allow_create: bool = True) -> Tuple[bool, str]:
        """
        Validate directory path for security and safety.

        Args:
            dir_path: Directory path to validate
            allow_create: Whether to allow directories that don't exist yet

        Returns:
            Tuple of (is_valid, error_message_or_clean_path)
        """
        try:
            # Convert to Path object
            if isinstance(dir_path, str):
                path = Path(dir_path)
            else:
                path = dir_path

            # Resolve to absolute path
            resolved_path = path.resolve()
            path_str = str(resolved_path)

            # Check for dangerous patterns
            if '..' in path_str or path_str.startswith('~'):
                return False, "Path contains directory traversal patterns"

            # Prevent absolute path manipulation
            if os.path.isabs(path_str):
                if os.name == 'nt':
                    if path_str.startswith('\\\\') or ':\\' not in path_str:
                        return False, "Invalid Windows path format"
                else:
                    # Allow common user directories
                    allowed_prefixes = ['/tmp/', '/home/', '/var/tmp/', str(Path.home())]
                    if not any(path_str.startswith(prefix) for prefix in allowed_prefixes):
                        return False, "Path must be under user home or temporary directory"

            # Check path length
            if len(path_str) > 4096:
                return False, "Path too long"

            # Check if directory exists or can be created
            if not allow_create and not resolved_path.exists():
                return False, f"Directory does not exist: {resolved_path}"

            if resolved_path.exists() and not resolved_path.is_dir():
                return False, f"Path exists but is not a directory: {resolved_path}"

            # Additional Windows-specific checks
            if os.name == 'nt':
                # Prevent paths with reserved names
                reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                                'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                                'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
                parts = resolved_path.parts
                for part in parts:
                    if part.upper() in reserved_names:
                        return False, f"Reserved directory name detected: {part}"

            return True, str(resolved_path)

        except Exception as e:
            logger.error(f"Error validating directory path {dir_path}: {e}")
            return False, f"Directory path validation error: {str(e)}"


# Global validator instance
_validator_instance: Optional[InputValidator] = None


def get_validator() -> InputValidator:
    """Get global validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = InputValidator()
    return _validator_instance


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Convenience function to validate URL

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message_or_clean_url)
    """
    return get_validator().validate_url(url)


def validate_tts_request(request_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Convenience function to validate TTS request

    Args:
        request_data: TTS request data

    Returns:
        Tuple of (is_valid, error_message)
    """
    return get_validator().validate_tts_request(request_data)


def validate_file_path(file_path: Union[str, Path], allow_create: bool = True) -> Tuple[bool, str]:
    """
    Convenience function to validate file path

    Args:
        file_path: Path to validate
        allow_create: Whether to allow paths that don't exist yet

    Returns:
        Tuple of (is_valid, error_message_or_clean_path)
    """
    return get_validator().validate_file_path(file_path, allow_create)


def validate_directory_path(dir_path: Union[str, Path], allow_create: bool = True) -> Tuple[bool, str]:
    """
    Convenience function to validate directory path

    Args:
        dir_path: Directory path to validate
        allow_create: Whether to allow directories that don't exist yet

    Returns:
        Tuple of (is_valid, error_message_or_clean_path)
    """
    return get_validator().validate_directory_path(dir_path, allow_create)
