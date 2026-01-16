"""
Input Validation and Sanitization Utilities

Provides robust validation and sanitization for URLs, text, and other inputs
to prevent security vulnerabilities and improve reliability.
"""

import re
import os
import ipaddress
import socket
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union, List
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
        self._dns_cache: Dict[str, Tuple[float, Tuple[str, ...]]] = {}
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

            # SSRF hardening: ensure parsed URL is safe to fetch
            is_safe, reason = self._is_safe_fetch_url(clean_url)
            if not is_safe:
                return False, reason

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

    def _is_safe_fetch_url(self, url: str) -> Tuple[bool, str]:
        """
        SSRF-focused URL safety checks.

        This is intentionally stricter than simple URL syntax validation:
        - blocks credentials in URL (user:pass@host)
        - blocks localhost / private / link-local / multicast / reserved IPs
        - resolves hostnames and blocks if any resolved IP is non-public
        """
        try:
            parsed = urlparse(url)

            if parsed.scheme not in ("http", "https"):
                return False, "Only http/https URLs are allowed"

            # Reject credentials in URL (common SSRF trick + credential leakage risk)
            if parsed.username or parsed.password:
                return False, "URLs containing credentials are not allowed"

            hostname = (parsed.hostname or "").strip().lower()
            if not hostname:
                return False, "URL must include a hostname"

            if self._is_local_hostname(hostname):
                return False, "Localhost URLs are not allowed"

            # If hostname is an IP literal, validate directly
            ip_obj = self._parse_ip_literal(hostname)
            if ip_obj is not None:
                if self._is_non_public_ip(ip_obj):
                    return False, "Private or non-public IP addresses are not allowed"
                return True, ""

            # Resolve hostname and ensure it does not map to private/non-public IP space
            ips = self._resolve_host_ips(hostname)
            if not ips:
                return False, "Could not resolve hostname"

            for ip_str in ips:
                try:
                    ip = ipaddress.ip_address(ip_str)
                except ValueError:
                    continue
                if self._is_non_public_ip(ip):
                    return False, "Hostname resolves to a private or non-public IP address"

            return True, ""

        except Exception as e:
            logger.error(f"Error checking URL safety {url}: {e}")
            return False, "URL failed safety checks"

    def _is_local_hostname(self, hostname: str) -> bool:
        host = hostname.strip().lower().rstrip(".")
        if host in {"localhost"}:
            return True
        # Common local-only names
        if host.endswith(".localhost") or host.endswith(".local"):
            return True
        return False

    def _parse_ip_literal(self, hostname: str) -> Optional[ipaddress._BaseAddress]:
        try:
            return ipaddress.ip_address(hostname)
        except ValueError:
            return None

    def _is_non_public_ip(self, ip: ipaddress._BaseAddress) -> bool:
        # Covers private, loopback, link-local, multicast, unspecified, reserved
        return bool(
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_unspecified
            or ip.is_reserved
        )

    def _resolve_host_ips(self, hostname: str) -> Tuple[str, ...]:
        # Small cache to avoid repeated DNS lookups during queue validation
        now = time.time()
        cache_ttl = 300.0
        if now is not None and hostname in self._dns_cache:
            ts, ips = self._dns_cache[hostname]
            if (now - ts) <= cache_ttl:
                return ips

        try:
            infos = socket.getaddrinfo(hostname, None)
        except Exception as e:
            logger.debug(f"DNS resolution failed for {hostname}: {e}")
            return tuple()

        ips_set = set()
        for family, _type, _proto, _canonname, sockaddr in infos:
            try:
                if family == socket.AF_INET:
                    ips_set.add(sockaddr[0])
                elif family == socket.AF_INET6:
                    ips_set.add(sockaddr[0])
            except Exception:
                continue

        ips = tuple(sorted(ips_set))
        self._dns_cache[hostname] = (now, ips)
        return ips

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

        Dynamically scans adaptive_configs directory for supported sites.
        Uses flexible domain matching to support related domains.

        Args:
            url: URL to check

        Returns:
            True if from supported site
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix for comparison
            if domain.startswith('www.'):
                domain = domain[4:]

            # Get all supported domains from adaptive configs
            supported_domains = self._get_supported_domains_from_configs()

            # Check exact matches and subdomain matches
            for supported in supported_domains:
                if domain == supported or domain.endswith('.' + supported):
                    return True

            # Check for domain family matches (same main domain, different TLD)
            # This allows novelbin.com if novelbin.me is configured, but not unrelated domains
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                # Get the main domain name (e.g., 'novelbin' from 'novelbin.com')
                main_domain_name = domain_parts[-2] if len(domain_parts) >= 2 else domain_parts[0]

                for supported in supported_domains:
                    supported_parts = supported.split('.')
                    if len(supported_parts) >= 2:
                        supported_main_name = supported_parts[-2] if len(supported_parts) >= 2 else supported_parts[0]
                        # Only allow if the main domain name matches exactly
                        if main_domain_name == supported_main_name:
                            logger.info(f"Allowing related domain {domain} (family: {main_domain_name}) "
                                       f"because {supported} is in the same family")
                            return True

            return False

        except Exception:
            return False

    def _get_supported_domains_from_configs(self) -> List[str]:
        """
        Get all supported domains by scanning adaptive config directories.

        Returns:
            List of supported domain names
        """
        supported_domains = set()

        try:
            # Scan built-in configs in src/scraper/adaptive_configs/
            # Use inspect to get the current file path since __file__ is not in method scope
            import inspect
            current_file = inspect.getfile(self.__class__)
            builtin_config_dir = Path(current_file).parent.parent / "scraper" / "adaptive_configs"
            if builtin_config_dir.exists():
                for config_file in builtin_config_dir.glob("*.json"):
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            if 'domain' in config:
                                supported_domains.add(config['domain'])
                    except (json.JSONDecodeError, IOError):
                        continue

            # Scan runtime configs in ~/.act/adaptive_configs/
            runtime_config_dir = Path.home() / ".act" / "adaptive_configs"
            if runtime_config_dir.exists():
                for config_file in runtime_config_dir.glob("*.json"):
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            if 'domain' in config:
                                supported_domains.add(config['domain'])
                    except (json.JSONDecodeError, IOError):
                        continue

        except Exception as e:
            logger.debug(f"Error scanning adaptive configs: {e}")

        return list(supported_domains)

    def add_supported_domain(self, domain: str) -> None:
        """
        Add a domain to the supported list by creating a basic config file.

        This allows the system to automatically support new domains that
        prove successful during scraping.

        Args:
            domain: Domain name to add
        """
        try:
            runtime_config_dir = Path.home() / ".act" / "adaptive_configs"
            runtime_config_dir.mkdir(parents=True, exist_ok=True)

            config_file = runtime_config_dir / f"{domain}.json"

            # Create basic config if it doesn't exist
            if not config_file.exists():
                basic_config = {
                    "domain": domain,
                    "strategy_success_rates": {},
                    "optimal_strategy_order": [],
                    "known_patterns": {},
                    "last_successful_strategy": None,
                    "average_response_times": {},
                    "total_attempts": 0,
                    "successful_attempts": 0,
                    "last_updated": time.time(),
                    "custom_selectors": [],
                    "pagination_patterns": [],
                    "api_endpoints": []
                }

                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(basic_config, f, indent=2)

                logger.info(f"Created basic config for new domain: {domain}")
            else:
                logger.debug(f"Config already exists for domain: {domain}")

        except Exception as e:
            logger.error(f"Failed to add supported domain {domain}: {e}")

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
                # Prevent paths with reserved names (check filename without extension)
                reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                                'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                                'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
                parts = resolved_path.parts
                for part in parts:
                    # Check filename without extension for reserved names
                    stem = Path(part).stem.upper()
                    if stem in reserved_names:
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


# Compatibility shim:
# Some parts of the codebase (and older tests) may import this module under
# different names depending on packaging/layout. Ensure `utils.validation`
# always refers to this module instance so `unittest.mock.patch('utils.validation...')`
# works reliably.
import sys as _sys
_sys.modules.setdefault("utils.validation", _sys.modules[__name__])
